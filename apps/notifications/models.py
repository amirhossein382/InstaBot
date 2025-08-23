from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.account.models import InstagramAccount
from apps.core.models import BaseInstagramUser, BaseTimeStampedModel
from apps.enums import NotificationsTypeEnum


class Notification(models.Model):
    account = models.ForeignKey(
        InstagramAccount, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=20, choices=NotificationsTypeEnum.CHOICES)
    title = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField()

    extra_data = models.JSONField(blank=True, null=True, default=dict)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def create_error_notification(cls, account, message):
        return cls.objects.create(account=account, type=NotificationsTypeEnum.ERRORS, message=message)

    @classmethod
    def _create_relation_notification(cls, account, message, extra_data):
        return cls.objects.create(
            account=account, type=NotificationsTypeEnum.RELATIONS, message=message, extra_data=extra_data
        )

    @classmethod
    def create_new_follower_notif(cls,account, follower_change):
        data = {
            "profile_pic_url": follower_change.profile_pic_url,
            "full_name": follower_change.full_name,
            "username": follower_change.username
        }
        message = f"{follower_change.username} followed you recently"
        return cls._create_relation_notification(account=account, message=message, extra_data=data)

    @classmethod
    def create_un_follower_notif(cls,account, follower_change):
        data = {
            "profile_pic_url": follower_change.profile_pic_url,
            "full_name": follower_change.full_name,
            "username": follower_change.username
        }
        message = f"{follower_change.username} un followed you recently"
        return cls._create_relation_notification(account=account, message=message, extra_data=data)


class PushNotifDevice(BaseTimeStampedModel):
    account = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name="Devices")
    token = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(
        verbose_name=_("Is active"),
        default=True,
        help_text=_("Inactive devices will not be sent notifications"),
    )
    last_notified_at = models.DateTimeField(null=True, blank=True)
