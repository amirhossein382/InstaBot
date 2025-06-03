from django.db import models
from django.contrib.auth import get_user_model

from apps.core.models import BaseInstagramUser
from apps.enums import FollowerChangeStatusEnum

User = get_user_model()


class Profile(BaseInstagramUser):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    user_pk = models.BigIntegerField(unique=True)

    class Meta:
        unique_together = (['user', 'user_pk'])


class Following(BaseInstagramUser):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followings")
    user_pk = models.BigIntegerField(unique=True)

    class Meta:
        unique_together = (['user', 'user_pk'])


class FollowerChange(BaseInstagramUser):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower_changes")
    user_pk = models.BigIntegerField(unique=True)
    change_type = models.CharField(max_length=20, choices=FollowerChangeStatusEnum.CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (["user", "user_pk", "change_type"])
