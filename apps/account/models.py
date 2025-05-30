from django.db import models
from django.contrib.auth.models import AbstractUser

from apps.core.models import BaseTimeStampedModel


class CustomUser(AbstractUser):
    first_name = None
    last_name = None
    settings = models.JSONField()
