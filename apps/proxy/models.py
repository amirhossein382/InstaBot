from django.db import models

from apps.core.models import BaseTimeStampedModel


class InternalProxy(BaseTimeStampedModel):
    proxy = models.CharField(max_length=300)
    is_valid = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField(default=5)
    used_slots = models.PositiveIntegerField(default=0)
    last_checked = models.DateTimeField(auto_now=True)

    def has_capacity(self):
        return self.is_valid and self.used_slots < self.capacity
