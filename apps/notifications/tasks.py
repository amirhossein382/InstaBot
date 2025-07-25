from celery import shared_task

from apps.profiles.models import FollowerChange
from apps.enums import FollowerChangeStatusEnum
from .models import Notification
from .services import NotificationService

notification_svc = NotificationService()


@shared_task
def notify_change(change_ids: list[int]):
    changes = FollowerChange.objects.filter(id__in=change_ids)
    for change in changes:
        if change.change_type == FollowerChangeStatusEnum.NEW_FOLLOW:
            Notification.create_new_follower_notif(change)
        elif change.change_type == FollowerChangeStatusEnum.UNFOLLOW:
            Notification.create_un_follower_notif(change)


@shared_task
def send_push_notif_to_account(account_id, title, body):
    from apps.account.models import InstagramAccount
    account = InstagramAccount.objects.get(id=account_id)
    notification_svc.send_push_notif_to_account(account, title, body)
