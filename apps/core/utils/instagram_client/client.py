from django.conf import settings as django_settings
from .clients import InstagrapiClient


def get_instagram_client():
    """Get pure client without settings and proxy"""
    if getattr(django_settings, "INSTAGRAM_PROVIDER", "Another Provider") == "instagrapi":
        return InstagrapiClient()
    raise NotImplementedError("Another provider Client not implemented.")


def get_instagram_account_client(settings, proxy):
    """Get client with settings and proxy for related user."""
    if getattr(django_settings, "INSTAGRAM_PROVIDER", "Another Provider") == "instagrapi":
        return InstagrapiClient.get_account_client(settings=settings, proxy=proxy)
    raise NotImplementedError("Another provider is not implemented.")
