from django.db import models

from apps.account.models import InstagramAccount
from apps.core.models import BaseInstagramUser
from apps.enums import NotificationsTypeEnum


class Notification(models.Model):
    account = models.ForeignKey(
        InstagramAccount, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=20, choices=NotificationsTypeEnum.CHOICES)
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
    def create_new_follower_notif(cls, account, relation: BaseInstagramUser):
        data = {
            "profile_pic_url": relation.profile_pic_url,
            "full_name": relation.full_name,
            "username": relation.username
        }
        message = f"{relation.username} followed you recently"
        return cls._create_relation_notification(account=account, message=message, extra_data=data)

    @classmethod
    def create_un_follower_notif(cls, account, relation: BaseInstagramUser):
        data = {
            "profile_pic_url": relation.profile_pic_url,
            "full_name": relation.full_name,
            "username": relation.username
        }
        message = f"{relation.username} un followed you recently"
        return cls._create_relation_notification(account=account, message=message, extra_data=data)
