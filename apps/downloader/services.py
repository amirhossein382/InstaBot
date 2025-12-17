from apps.core.utils.instagram_client import get_instagram_account_client
from apps.core.utils.instagram_client.exceptions import exception_mapper


class DownloaderService:
    @staticmethod
    def resolve_media_url(account, url):
        try:
            client = get_instagram_account_client(account.client_settings, account.internal_proxy)
            return client.resolve_media_url(url)
        except Exception as exc:
            exception_mapper(exc)
