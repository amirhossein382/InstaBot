from celery import shared_task

from apps.profiles.models import FollowerChange
from apps.enums import FollowerChangeStatusEnum, NotificationsTypeEnum
from .services import NotificationService

notification_svc = NotificationService()


@shared_task
def notify_changes(change_ids: list[int], push=False):
    changes = FollowerChange.objects.filter(user_pk__in=change_ids)
    account = changes.first().account

    push_messages = []
    for change in changes:
        profile = change.profile_pic_url
        title = change.username

        if change.change_type == FollowerChangeStatusEnum.NEW_FOLLOW:
            message = f"{title} followed you recently!"
        elif change.change_type == FollowerChangeStatusEnum.UNFOLLOW:
            message = f"{title} unfollowed you recently!"
        else:
            continue

        notification_svc.create_notification(
            account=account, profile=profile, title=title, message=message,
            notif_type=NotificationsTypeEnum.RELATION
        )
        push_messages.append((title, message, profile))

    if push:
        if len(push_messages) == 1:
            title, message, profile = push_messages[0]
            notification_svc.send_push_notif_to_account(account=account, title=title, body=message, image=profile)

        elif len(push_messages) == 2:
            for title, message, profile in push_messages:
                notification_svc.send_push_notif_to_account(account=account, title=title, body=message, image=profile)

        else:
            usernames = [t for t, _, _ in push_messages[:3]]
            extra = len(push_messages) - len(usernames)

            usernames_str = ", ".join(usernames)
            if extra > 0:
                usernames_str += f" and {extra} others"

            message = f"{usernames_str} updated their follow status recently!"
            notification_svc.send_push_notif_to_account(account=account, title="Followers update", body=message)


@shared_task
def create_notification(account_id, profile, title, message, notif_type, image=None, push=False):
    from apps.account.models import InstagramAccount
    account = InstagramAccount.objects.get(id=account_id)
    notification_svc.create_notification(
        account=account, profile=profile, title=title, message=message, notif_type=notif_type
    )
    if push:
        notification_svc.send_push_notif_to_account(account, title, message, image)
