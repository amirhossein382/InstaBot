from django.db import models


class SuperUserManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super(SuperUserManager, self).get_queryset().filter(is_superuser=True)


class AdminUserManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super(AdminUserManager, self).get_queryset().filter(is_superuser=False, is_staff=True)
