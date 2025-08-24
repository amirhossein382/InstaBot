import firebase_admin
from firebase_admin import messaging, initialize_app
from firebase_admin import credentials
from django.conf import settings
from django.utils import timezone

from .models import PushNotifDevice, Notification
from apps.core.utils import Logger

logger = Logger()


class NotificationService:
    def __init__(self):
        self.Op = self.__class__.__name__

        if not len(firebase_admin._apps):
            self._initialize_push_service()

    @staticmethod
    def _initialize_push_service():
        cred = credentials.Certificate(settings.FIREBASE_CRED_PATH)
        initialize_app(cred)

    @classmethod
    def create_notification(cls, account, profile, title, message, notif_type):
        return Notification.objects.create(
            account=account, profile=profile, title=title, message=message, type=notif_type
        )

    def send_push_notif_to_account(self, account, title, body, image=None):
        op = f"{self.Op}.send_push_notif_to_account"
        try:
            device = PushNotifDevice.objects.get(account=account, is_active=True)
        except PushNotifDevice.DoesNotExist:
            return None

        if device.is_active:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body, image=image),
                token=device.token
            )
            try:
                response = messaging.send(message)
                device.last_notified_at = timezone.now()
                device.save(update_fields=["last_notified_at"])
                logger.log_event(
                    op,
                    log_data="sent notification."
                )
                return response
            except Exception as err:
                logger.log_event(
                    op,
                    log_data=f"failed to send notif --> {str(err)}", level="ERROR"
                )

        else:
            logger.log_event(
                op,
                log_data="notification device is not active!"
            )
            return None
