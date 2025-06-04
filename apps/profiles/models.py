from django.db import models

from apps.account.models import InstagramAccount
from apps.core.models import BaseInstagramUser
from apps.enums import FollowerChangeStatusEnum


class Profile(BaseInstagramUser):
    account = models.OneToOneField(InstagramAccount, on_delete=models.CASCADE, related_name="profile")
    user_pk = models.UUIDField(unique=True)
    external_url = models.URLField(null=True, blank=True)
    media_count = models.IntegerField(default=0)
    follower_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    biography = models.TextField(blank=True, null=True)
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_business = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Follower(BaseInstagramUser):
    account = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name="followers")
    user_pk = models.BigIntegerField(unique=True)

    class Meta:
        unique_together = (['account', 'user_pk'])


class Following(BaseInstagramUser):
    account = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name="followings")
    user_pk = models.BigIntegerField(unique=True)

    class Meta:
        unique_together = (['account', 'user_pk'])


class FollowerChange(BaseInstagramUser):
    account = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name="follower_changes")
    user_pk = models.BigIntegerField(unique=True)
    change_type = models.CharField(max_length=20, choices=FollowerChangeStatusEnum.CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (["account", "user_pk", "change_type"])
        ordering = ['-created_at']


class AccountGrowthLog(models.Model):
    account = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name="growth_logs")
    date = models.DateField()
    followers_count = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('account', 'date')
        ordering = ['-date']
