from django.conf import settings as django_settings
from .clients import InstagrapiClient


# from .clients.instaloader_client import InstaloaderClient // Not Implemented

def get_instagram_client():
    """Get pure client without settings and proxy"""
    if getattr(django_settings, "INSTAGRAM_CLIENT", "instaloader") == "":
        return InstagrapiClient()
    raise NotImplementedError("Instaloader Client not implemented.")


def get_instagram_account_client(settings, proxy):
    """Get client with settings and proxy for related user."""
    if getattr(django_settings, "INSTAGRAM_CLIENT", "instaloader") == "":
        return InstagrapiClient.get_account_client(settings=settings, proxy=proxy)
    raise NotImplementedError("Instaloader Client not implemented.")
