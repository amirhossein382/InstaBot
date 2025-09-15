from django.db import models
from django.contrib.auth.models import AbstractUser

from apps.core.models import BaseTimeStampedModel


class CustomUser(AbstractUser):
    pass


class SuperUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = "Super User"
        verbose_name_plural = "Super Users"


class AdminUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = "Admin User"
        verbose_name_plural = "Admin Users"


class InstagramAccount(BaseTimeStampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="instagram_account")
    client_pk = models.BigIntegerField(unique=True)
    client_settings = models.JSONField()
    is_initialized = models.BooleanField(default=False)
    is_analyses_paused = models.BooleanField(default=False)
