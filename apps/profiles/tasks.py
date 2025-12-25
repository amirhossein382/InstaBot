from django.db.models import Q
from django.db import transaction
from django.utils.timezone import now
from celery import shared_task

from apps.account.models import InstagramAccount
from apps.account.services import AccountService
from apps.notifications import tasks as notifications_tasks
from apps.core.utils import Logger
from apps.core.utils.instagram_client import get_instagram_account_client
from apps.core.tasks import AuthenticatedAccountTask, instagram_api_task_exception_handler
from apps.enums import FollowerChangeStatusEnum
from apps.proxy.services import ProxyService
from apps.analytics.tasks import analyze_user_top_posts_and_best_time_to_post
from .models import Follower, Following, FollowerChange, Profile, Post
from .services import ProfileService

_account_svc = AccountService()
_profile_svc = ProfileService()
_proxy_svc = ProxyService()
_logger = Logger()


@shared_task(bind=True, base=AuthenticatedAccountTask)
def update_profile_info(self, account_id):
    from datetime import timedelta
    media_force_delta = timedelta(days=3)
    follower_force_delta = timedelta(days=1)
    op = "update_profile_info"
    account = InstagramAccount.objects.get(pk=account_id)
    client = get_instagram_account_client(account.client_settings, account.internal_proxy)
    try:
        _logger.log_event(op, f"getting profile data from instagram...")
        new_profile_info = _profile_svc.load_profile_info(account, client)
        old_profile_info = Profile.objects.get(account=account)
        if (
                (new_profile_info["media_count"] != old_profile_info.media_count)
                or ((now - account.last_media_check) > media_force_delta)
        ):
            update_user_medias.delay(account_id)
        if (
                ((new_profile_info["follower_count"] != old_profile_info.follower_count)
                 or (new_profile_info["following_count"] != old_profile_info.following_count))
                or ((now - account.last_followers_check) > follower_force_delta)
        ):
            update_user_followers_followings_and_log_changes.delay(account_id)
        Profile.objects.filter(account=account).update(**new_profile_info)
    except Exception as exception:
        instagram_api_task_exception_handler(self, op, exception, account)
    finally:
        next_run_time = _profile_svc.config.reschedule_update_profile_info_periodic_task(account_id)
        _logger.log_event(
            op, f"Rescheduling task to every {next_run_time} minutes..."
        )


@shared_task(bind=True, base=AuthenticatedAccountTask)
def update_user_medias(self, account_id):
    op = "update_user_medias"
    _logger.log_event(op, "task is running...")
    account = InstagramAccount.objects.get(pk=account_id)
    client = get_instagram_account_client(account.client_settings, account.internal_proxy)
    try:
        objs = []
        for chunk in _profile_svc.load_user_posts(account, client):
            objs.extend(Post(account=account, **item) for item in chunk)
        with transaction.atomic():
            Post.objects.filter(account=account).delete()
            Post.objects.bulk_create(objs)
            account.last_media_check = now()
            account.save(update_fields=("last_media_check",))
            transaction.on_commit(
                lambda: analyze_user_top_posts_and_best_time_to_post.delay(account_id)
            )
    except Exception as exception:
        instagram_api_task_exception_handler(self, op, exception, account)
    _logger.log_event(op, "task done.")


@shared_task(bind=True, base=AuthenticatedAccountTask)
def update_user_followers_followings_and_log_changes(self, account_id):
    op = "update_user_followers_followings_and_log_changes"
    _logger.log_event(op, "task is running...")

    account = InstagramAccount.objects.select_related("user").get(pk=account_id)

    if not _proxy_svc.check_internet_connection():
        _logger.log_event(
            op, f"Internet not available!. passing the task {account_id} ...", level="WARNING"
        )
        return

    try:
        _logger.log_event(op, f"getting client for account {account.pk}")
        client = get_instagram_account_client(account.client_settings, account.internal_proxy)
        _logger.log_event(op, f"getting new data from instagram for account {account.pk}")
        new_followers_dict = {}
        for chunk in _profile_svc.load_followers(account, client):
            for follower in chunk:
                new_followers_dict[follower["user_pk"]] = follower

        new_followings_dict = {}
        for chunk in _profile_svc.load_followings(account, client):
            for following in chunk:
                new_followings_dict[following["user_pk"]] = following
    except Exception as exception:
        instagram_api_task_exception_handler(self, op, exception, account)

    else:
        _logger.log_event(
            op, f"analyze instagram new followers, followings for account {account.pk}"
        )
        old_followers_dict = {
            f.user_pk: f for f in Follower.objects.filter(account=account).iterator(chunk_size=1000)
        }
        # There is no need to full data of Following yet!
        # old_followings_dict = {
        #     f.user_pk: f for f in
        #     Following.objects.filter(account=account).values_list("user_pk", flat=True)
        # }

        old_follower_pks = set(old_followers_dict.keys())
        old_following_pks = set(Following.objects.filter(account=account).values_list("user_pk", flat=True))
        new_follower_pks = set(new_followers_dict.keys())
        new_following_pks = set(new_followings_dict.keys())

        new_followers_set = new_follower_pks - old_follower_pks
        unfollowers_set = old_follower_pks - new_follower_pks
        new_followings_set = new_following_pks - old_following_pks
        unfollowings_set = old_following_pks - new_following_pks
        mutual_set = new_follower_pks.intersection(new_following_pks)
        not_back_set = new_following_pks - new_follower_pks

        changes = []

        def build_change(user_pk, change_type, source_dict):
            data = source_dict[user_pk]
            return FollowerChange(
                account=account,
                user_pk=user_pk,
                change_type=change_type,
                username=data.get("username") if isinstance(data, dict) else data.username,
                full_name=data.get("full_name") if isinstance(data, dict) else data.full_name,
                profile_pic_url=data.get("profile_pic_url") if isinstance(data, dict) else data.profile_pic_url
            )

        def bulk_insert_in_batches(model_cls, objects, batch_size=1000):
            for i in range(0, len(objects), batch_size):
                model_cls.objects.bulk_create(objects[i:i + batch_size])

        def append_changes(pks, change_type, source_dict, already_changes):
            for user_pk in pks:
                if (user_pk, change_type) not in already_changes:
                    changes.append(build_change(user_pk, change_type, source_dict))

        existing_changes = set(
            FollowerChange.objects.filter(
                account=account,
                user_pk__in=(
                        new_followers_set |
                        unfollowers_set |
                        not_back_set |
                        mutual_set
                )
            ).values_list('user_pk', 'change_type')
        )
        append_changes(
            new_followers_set, FollowerChangeStatusEnum.NEW_FOLLOW, new_followers_dict, existing_changes
        )
        append_changes(
            unfollowers_set, FollowerChangeStatusEnum.UNFOLLOW, old_followers_dict, existing_changes
        )
        append_changes(
            not_back_set, FollowerChangeStatusEnum.NOT_BACK, new_followings_dict, existing_changes
        )
        append_changes(
            mutual_set, FollowerChangeStatusEnum.MUTUAL, new_followings_dict, existing_changes
        )
        if new_followers_set:
            new_follower_objs = [
                Follower(
                    account=account,
                    user_pk=pk,
                    username=data["username"],
                    full_name=data.get("full_name", ""),
                    profile_pic_url=data.get("profile_pic_url", ""),
                )
                for pk, data in new_followers_dict.items() if pk in new_followers_set
            ]
        if new_followings_set:
            _logger.log_event(op, "updating user new followings ...")
            new_following_objs = [
                Following(
                    account=account,
                    user_pk=pk,
                    username=data["username"],
                    full_name=data.get("full_name", ""),
                    profile_pic_url=data.get("profile_pic_url", ""),
                )
                for pk, data in new_followings_dict.items() if pk in new_followings_set
            ]
        with transaction.atomic():
            if changes:
                _logger.log_event(op, "adding user new changes...")
                bulk_insert_in_batches(FollowerChange, changes)

                # Create internal change notifications
                _logger.log_event(op, "notifying changes...")
                notifications_tasks.notify_changes.delay([c.user_pk for c in changes])

                # Delete expired Changes...
                _logger.log_event(op, f"deleting user expire changes...")
                FollowerChange.objects.filter(
                    Q(account=account) &
                    (
                            Q(change_type=FollowerChangeStatusEnum.MUTUAL,
                              user_pk__in=unfollowers_set | unfollowings_set) |
                            Q(change_type=FollowerChangeStatusEnum.NOT_BACK,
                              user_pk__in=unfollowings_set | new_followers_set) |
                            Q(change_type=FollowerChangeStatusEnum.NEW_FOLLOW, user_pk__in=unfollowers_set) |
                            Q(change_type=FollowerChangeStatusEnum.UNFOLLOW, user_pk__in=new_followers_set)
                    )
                ).delete()

            # Add new followers
            if new_followers_set:
                _logger.log_event(op, "updating user new followers ...")
                bulk_insert_in_batches(Follower, new_follower_objs)

            # Add new followings
            if new_followings_set:
                _logger.log_event(op, "updating user new followings ...")
                bulk_insert_in_batches(Following, new_following_objs)

            # Remove expire follower, following
            if unfollowers_set:
                _logger.log_event(op, "deleting user expire followers...")
                Follower.objects.filter(account=account, user_pk__in=unfollowers_set).delete()
            if unfollowings_set:
                _logger.log_event(op, "deleting user expire followings...")
                Following.objects.filter(account=account, user_pk__in=unfollowings_set).delete()
            account.last_followers_check = now()
            account.save(update_fields=("last_followers_check",))
