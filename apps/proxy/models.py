import uuid

from django.db import models

from apps.account.models import InstagramAccount
from apps.core.models import BaseTimeStampedModel


class Proxy(BaseTimeStampedModel):
    account = models.ForeignKey(
        InstagramAccount, on_delete=models.CASCADE,
        related_name="proxies", null=True, blank=True
    )
    temp_id = models.UUIDField(default=uuid.uuid4, editable=False)
    proxy = models.CharField(max_length=300)
    is_valid = models.BooleanField(default=True)

    class Meta:
        unique_together = (
            ('account', 'proxy'), ('temp_id', 'proxy'),
        )
