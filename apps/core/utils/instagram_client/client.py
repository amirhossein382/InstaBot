from django.conf import settings
from .clients.instagrapi_client import InstagrapiClient


# from .clients.instaloader_client import InstaloaderClient // Not Implemented

def get_instagram_client():
    if getattr(settings, "INSTAGRAM_CLIENT", "instaloader") == "":
        return InstagrapiClient()
    raise NotImplementedError("Instaloader Client not implemented.")
