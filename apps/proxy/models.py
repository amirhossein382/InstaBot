import uuid

from django.db import models

from apps.account.models import InstagramAccount
from apps.core.models import BaseTimeStampedModel


class Proxy(BaseTimeStampedModel):
    account = models.ForeignKey(
        InstagramAccount, on_delete=models.CASCADE,
        related_name="account_proxies", null=True, blank=True
    )
    temp_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    proxy = models.CharField(max_length=300)
    is_valid = models.BooleanField(default=True)

    class Meta:
        unique_together = (['account', 'proxy'])

    @classmethod
    def create_temp_proxy(cls, temp_id, proxy, is_valid):
        cls.objects.create(temp_id=temp_id, proxy=proxy, is_valid=is_valid)

    @classmethod
    def set_account_to_proxy(cls, temp_id, account):
        proxy = cls.objects.get(temp_id=temp_id)
        proxy.account = account
        proxy.save()
