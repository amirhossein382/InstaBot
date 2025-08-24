from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.account.models import InstagramAccount
from apps.core.models import BaseInstagramUser, BaseTimeStampedModel
from apps.enums import NotificationsTypeEnum


class Notification(models.Model):
    account = models.ForeignKey(
        InstagramAccount, on_delete=models.CASCADE, related_name="notifications"
    )
    profile = models.CharField(max_length=1000, null=True, blank=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NotificationsTypeEnum.CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PushNotifDevice(BaseTimeStampedModel):
    account = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name="Devices")
    token = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(
        verbose_name=_("Is active"),
        default=True,
        help_text=_("Inactive devices will not be sent notifications"),
    )
    last_notified_at = models.DateTimeField(null=True, blank=True)
