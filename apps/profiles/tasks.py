import logging

from django.db.models import Q
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from celery import shared_task, Task

from apps.account.exceptions import PleaseWaitFewMinutes, LoginRequired
from apps.account.models import InstagramAccount
from apps.enums import FollowerChangeStatusEnum
from .models import Follower, Following, FollowerChange, Profile, AccountGrowthLog
from .serializers import ProfileSerializer
from .services import ProfileService

profile_svc = ProfileService()
LOCK_EXPIRE = 60 * 10
logger = logging.getLogger(__name__)


class BaseRetryTask(Task):
    autoretry_for = (ConnectionError, TimeoutError)
    retry_kwargs = {"max_retries": 2}
    retry_backoff = True


@shared_task(bind=True, base=BaseRetryTask)
def analyze_and_update_follow_data(self, account_id):
    lock_id = f"analyze-lock-{account_id}"
    if not cache.add(lock_id, "LOCKED", LOCK_EXPIRE):
        logger.warning(f"[{account_id}] Analysis task already running. Skipping.")
        return

    try:
        account = InstagramAccount.objects.get(pk=account_id)
        if not account.user.is_authenticated:
            profile_svc.config.delete_analyze_update_follow_data_periodic_task(account_id)
            profile_svc.config.delete_analyze_growth_logs_periodic_task(account_id)
            return
    except InstagramAccount().DoesNotExist:
        profile_svc.config.delete_analyze_update_follow_data_periodic_task(account_id)
        profile_svc.config.delete_analyze_growth_logs_periodic_task(account_id)
    else:
        try:
            new_profile_info = profile_svc.load_profile_info(account)
            new_followers = profile_svc.load_followers(account)
            new_followings = profile_svc.load_followings(account)

        except PleaseWaitFewMinutes as e:
            logger.warning(f"[{account_id}] Rate limited: delaying 1 hour")
            raise self.retry(exc=e, countdown=3600)
        except LoginRequired as e:
            logger.exception(f"[{account_id}] Login required: {e}")
            profile_svc.config.delete_analyze_update_follow_data_periodic_task(account_id)
            profile_svc.config.delete_analyze_growth_logs_periodic_task(account_id)
        except Exception as e:
            logger.exception(f"[{account_id}] Unhandled exception during analyze: {e}")
            raise self.retry(exc=e)

        else:
            new_followers_dict = {item["user_pk"]: item for item in new_followers}
            new_followings_dict = {item["user_pk"]: item for item in new_followings}

            old_profile_info = Profile.objects.get(user=account)
            old_followers = Follower.objects.filter(user=account)
            old_followings = Following.objects.filter(user=account)

            old_followers_dict = {f.user_pk: f for f in old_followers}
            old_followings_dict = {f.user_pk: f for f in old_followings}

            old_follower_pks = set(old_followers_dict.keys())
            old_following_pks = set(old_followings_dict.keys())
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
                    username=data.get("username"),
                    full_name=data.get("full_name", None),
                    profile_pic_url=data.get("profile_pic_url", None),
                )

            for pk in new_followers_set:
                changes.append(build_change(pk, FollowerChangeStatusEnum.NEW_FOLLOW, new_followers_dict))
            for pk in unfollowers_set:
                changes.append(build_change(pk, FollowerChangeStatusEnum.UNFOLLOW, old_followers_dict))
            for pk in mutual_set:
                changes.append(build_change(pk, FollowerChangeStatusEnum.MUTUAL, new_followers_dict))
            for pk in not_back_set:
                changes.append(build_change(pk, FollowerChangeStatusEnum.NOT_BACK, new_followings_dict))

            with transaction.atomic():
                # Update profile...
                serializer = ProfileSerializer(instance=old_profile_info, data=new_profile_info)
                if serializer.is_valid():
                    serializer.save()

                # Delete expired Changes...
                FollowerChange.objects.filter(
                    Q(user_pk__in=unfollowers_set) | Q(user_pk__in=unfollowings_set),
                    account=account,
                    change_type=FollowerChangeStatusEnum.MUTUAL,
                ).delete()
                FollowerChange.objects.filter(
                    Q(user_pk__in=unfollowings_set) | Q(user_pk__in=new_followers_set),
                    account=account,
                    change_type=FollowerChangeStatusEnum.NOT_BACK,
                ).delete()
                FollowerChange.objects.filter(
                    change_type=FollowerChangeStatusEnum.NEW_FOLLOW,
                    account=account,
                    user_pk__in=unfollowers_set
                ).delete()
                FollowerChange.objects.filter(
                    account=account,
                    change_type=FollowerChangeStatusEnum.UNFOLLOW,
                    user_pk__in=new_followers_set
                )
                # Add new changes
                FollowerChange.objects.bulk_create(changes, ignore_conflicts=True)

                # Add new followers
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
                Follower.objects.bulk_create(new_follower_objs, ignore_conflicts=True)

                # add new followings
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
                Following.objects.bulk_create(new_following_objs, ignore_conflicts=True)

                # remove expire follower, following
                if unfollowers_set:
                    Follower.objects.filter(account=account, user_pk__in=unfollowers_set).delete()
                if unfollowings_set:
                    Following.objects.filter(account=account, user_pk__in=unfollowings_set).delete()


@shared_task
def analyze_account_growth_logs(account_id):
    account = InstagramAccount.objects.get(pk=account_id)
    profile = Profile.objects.get(account=account)
    today = timezone.datetime.today()
    AccountGrowthLog.objects.update_or_create(
        account=account,
        date=today,
        defaults={
            'followers_count': profile.followers_count,
        }
    )
