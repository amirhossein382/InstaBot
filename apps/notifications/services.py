import firebase_admin
from firebase_admin import messaging, initialize_app
from firebase_admin import credentials
from django.conf import settings
from django.utils import timezone

from .models import PushNotifDevice
from apps.core.utils import Logger

logger = Logger()


class NotificationService:
    def __init__(self):
        if not len(firebase_admin._apps):
            self._initialize_push_service()

    @staticmethod
    def _initialize_push_service():
        cred = credentials.Certificate(settings.FIREBASE_CRED_PATH)
        initialize_app(cred)

    @staticmethod
    def send_push_notif_to_account(account, title, body):
        try:
            device = PushNotifDevice.objects.get(account=account, is_active=True)
        except PushNotifDevice.DoesNotExist:
            return None

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=device.token
        )
        try:
            response = messaging.send(message)
            device.last_notified_at = timezone.now()
            device.save(update_fields=["last_notified_at"])
            return response
        except Exception as err:
            logger.log_event(
                "send_push_notif_to_account",
                log_data=f"failed to send notif --> {str(err)}", level="ERROR"
            )
            return None
