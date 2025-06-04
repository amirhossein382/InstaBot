from django.db import models
from django.contrib.auth.models import AbstractUser

from apps.core.models import BaseTimeStampedModel


class CustomUser(AbstractUser):
    pass


class InstagramAccount(BaseTimeStampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="instagram_account")
    client_pk = models.BigIntegerField(unique=True)
    client_settings = models.JSONField()
