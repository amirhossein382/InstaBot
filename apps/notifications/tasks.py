from celery import shared_task

from .services import NotificationService

notification_svc = NotificationService()


@shared_task
def send_push_notif_to_account(account_id, title, body):
    from apps.account.models import InstagramAccount
    account = InstagramAccount.objects.get(id=account_id)
    notification_svc.send_push_notif_to_account(account, title, body)
