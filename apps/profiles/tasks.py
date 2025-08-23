from django.db.models import Q
from django.db import transaction
from django.utils.timezone import datetime, now, timedelta
from celery import shared_task, Task

from apps.account.exceptions import PleaseWaitFewMinutes, LoginRequired, ChallengeRequired, FeedbackRequired
from apps.account.models import InstagramAccount
from apps.notifications.tasks import send_push_notif_to_account, notify_change
from apps.notifications.models import Notification
from apps.core.utils import Logger
from apps.enums import FollowerChangeStatusEnum
from .models import Follower, Following, FollowerChange, Profile, AccountGrowthLog
from .serializers import ProfileSerializer
from .services import ProfileService

profile_svc = ProfileService()
logger = Logger()
reenable_time = now() + timedelta(hours=12)


class BaseRetryTask(Task):
    autoretry_for = (ConnectionError, TimeoutError)
    retry_kwargs = {"max_retries": 2}
    retry_backoff = True


@shared_task(bind=True, base=BaseRetryTask)
def analyze_and_update_follow_data(self, account_id):
    op = analyze_and_update_follow_data.__name__
    logger.log_event(op, "task is running...")

    account = InstagramAccount.objects.select_related("user").get(pk=account_id)
    if (not account.user.is_authenticated) or (not profile_svc.is_ig_authenticated(account)):
        profile_svc.account_svc.logout_django_by_user(account.user)

        logger.log_event(op, f"not authenticated!. pausing tasks for user {account.user.id}", level="WARNING")
        profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account_id, pause=True)
        profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account_id, pause=True)
        # send_push_notif_to_account.delay(account_id, "Logged Out", "Your account logged out. please login again!")
        Notification.create_error_notification(
            account, message="Your account logged out. please login again!"
        )
        return

    try:
        logger.log_event(op, f"getting new data from instagram for user {account.user.id}")
        new_profile_info = profile_svc.load_profile_info(account)
        new_followers = profile_svc.load_followers(account)
        new_followings = profile_svc.load_followings(account)

    except PleaseWaitFewMinutes as err:
        logger.log_event(op, f"Rate limited: delaying 1 hour for user {account.user.id} --> {str(err)}", level="ERROR")
        # send_push_notif_to_account.delay(
        #     account_id, "Rate Limit", "Rate limit from instagram, delay analys for 1 hour!"
        # )
        Notification.create_error_notification(
            account, message="Rate limit from instagram, delay analys for 1 hour"
        )
        raise self.retry(exc=err, countdown=3600)

    except LoginRequired as err:
        logger.log_event(op, f"Login required: {err} ---> pausing tasks for user {account.user.id}", level="ERROR")
        profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account_id, pause=True)
        profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account_id, pause=True)
        profile_svc.account_svc.logout_django_by_user(account.user)
        # send_push_notif_to_account.delay(
        #     account_id, "Logged Out", "Your account logged out. please login again!"
        # )
        Notification.create_error_notification(account, message="Your account logged out. please login again!")

    except ChallengeRequired as err:
        logger.log_event(op, log_data=f" getting new data failed because challenge required -> {str(err)}",
                         level="ERROR")
        profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account_id, pause=True)
        profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account_id, pause=True)
        # send_push_notif_to_account.delay(
        #     account_id, "Challenge Required",
        #     "Challenge required from instagram. go to instagram website and login to resolve challenges"
        # )
        Notification.create_error_notification(
            account,
            message="Challenge required from instagram. go to instagram website and login to resolve challenges"
        )

    except FeedbackRequired as err:
        logger.log_event(
            op, log_data=f" getting new data failed because feedback required -->{str(err)}",
            level="ERROR"
        )
        profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account_id, pause=True)
        profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account_id, pause=True)
        profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task.apply_async(
            (account_id, False,), eta=reenable_time
        )
        profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task.apply_async(
            (account_id, False,), eta=reenable_time
        )
        # send_push_notif_to_account.delay(
        #     account_id, "FeedBack Required",
        #     "Feedback required from instagram. pausing analyses for 12 hours"
        # )
        Notification.create_error_notification(
            account, message="Feedback required from instagram. pausing analyses for 12 hours!"
        )

    except Exception as err:
        logger.log_event(op, f"[{account_id}] Unhandled exception during analyze: {str(err)}", level="WARNING")
        profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account_id, pause=True)
        profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account_id, pause=True)
        # send_push_notif_to_account.delay(
        #     account_id, "Unknown Error",
        #     "Analysed failed for unknown error. try to open app or login again"
        # )

    else:
        logger.log_event(op, f"analyze instagram new data for user {account.user.id}")
        new_followers_dict = {item["user_pk"]: item for item in new_followers}
        new_followings_dict = {item["user_pk"]: item for item in new_followings}

        old_profile_info = Profile.objects.get(account=account)
        old_followers = Follower.objects.filter(account=account)
        old_followings = Following.objects.filter(account=account)

        old_followers_dict = {f.user_pk: f for f in old_followers}
        old_followings_dict = {f.user_pk: f for f in old_followings}

        old_follower_pks = set(old_followers_dict.keys())
        old_following_pks = set(old_followings_dict.keys())
        new_follower_pks = set(new_followers_dict.keys())
        new_following_pks = set(new_followings_dict.keys())
        logger.log_event(op, f"new following pks-->{new_following_pks}")
        logger.log_event(op, f"old following pks-->{old_following_pks}")

        new_followers_set = new_follower_pks - old_follower_pks
        unfollowers_set = old_follower_pks - new_follower_pks

        new_followings_set = new_following_pks - old_following_pks
        unfollowings_set = old_following_pks - new_following_pks

        mutual_set = new_follower_pks.intersection(new_following_pks)
        not_back_set = new_following_pks - new_follower_pks

        logger.log_event(op, f"new followers --> {new_followers_set}")
        logger.log_event(op, f"un followers --> {unfollowers_set}")
        logger.log_event(op, f"new followings --> {new_followings_set}")
        logger.log_event(op, f"un followings --> {unfollowings_set}")
        logger.log_event(op, f"mutual followings --> {mutual_set}")
        logger.log_event(op, f"notback followings --> {not_back_set}")

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

        with transaction.atomic():
            # Update profile...
            logger.log_event(op, "updating user profile info ...")
            serializer = ProfileSerializer(instance=old_profile_info, data=new_profile_info)
            if serializer.is_valid():
                serializer.save()
                logger.log_event(op, "user profile info updated!")

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

            # Add new changes
            append_changes(new_followers_set, FollowerChangeStatusEnum.NEW_FOLLOW, new_followers_dict, existing_changes)
            append_changes(unfollowers_set, FollowerChangeStatusEnum.UNFOLLOW, old_followers_dict, existing_changes)
            append_changes(not_back_set, FollowerChangeStatusEnum.NOT_BACK, new_followings_dict, existing_changes)
            append_changes(mutual_set, FollowerChangeStatusEnum.MUTUAL, new_followings_dict, existing_changes)

            if changes:
                logger.log_event(op, "adding user new changes...")
                bulk_insert_in_batches(FollowerChange, changes)

                # Create internal change notifications
                logger.log_event(op, "notifying changes...")
                notify_change.delay([c.user_pk for c in changes])

                # Delete expired Changes...
                logger.log_event(op, f"deleting user expire changes...")
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
                logger.log_event(op, "updating user new followers ...")
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
                bulk_insert_in_batches(Follower, new_follower_objs)

            # Add new followings
            if new_followings_set:
                logger.log_event(op, "updating user new followings ...")
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
                bulk_insert_in_batches(Following, new_following_objs)

            # Remove expire follower, following
            if unfollowers_set:
                logger.log_event(op, "deleting user expire followers...")
                Follower.objects.filter(account=account, user_pk__in=unfollowers_set).delete()
            if unfollowings_set:
                logger.log_event(op, "deleting user expire followings...")
                Following.objects.filter(account=account, user_pk__in=unfollowings_set).delete()

    finally:
        next_run_time = profile_svc.config.reschedule_analyze_update_follow_data_periodic_task(account_id)
        logger.log_event(
            op, f"Rescheduling follow data task to every {next_run_time} hours..."
        )


@shared_task
def analyze_account_growth_logs(account_id):
    op = analyze_account_growth_logs.__name__
    logger.log_event(op, "task is running...")

    try:
        account = InstagramAccount.objects.prefetch_related("profile").get(pk=account_id)
    except InstagramAccount.DoesNotExist:
        logger.log_event(op, f"Account {account_id} does not exist!")
        profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account_id, pause=True)
        profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account_id, pause=True)
        return

    today = datetime.today()
    logger.log_event(op, "update or create growth logs...")
    AccountGrowthLog.objects.update_or_create(
        account=account,
        date=today,
        defaults={
            'followers_count': account.profile.follower_count,
        }
    )
    logger.log_event(op, "update or create growth logs done!")
