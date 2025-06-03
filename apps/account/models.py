from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    first_name = None
    last_name = None
    client_pk = models.BigIntegerField(unique=True)
    client_settings = models.JSONField()
