import re

from apps.enums import MediasTypeEnum
from instagrapi.types import Media, Story

from apps.account.services import AccountService
from apps.enums import UrlTypeEnum
from .exceptions import UnknownMediaUrlType

account_svc = AccountService()


class DownloaderService:
    _INSTAGRAM_URL_PATTERNS = {
        UrlTypeEnum.POST: re.compile(r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[A-Za-z0-9_-]+"),
        UrlTypeEnum.STORY: re.compile(r"https?://(?:www\.)?instagram\.com/stories/[^/]+/\d+"),
    }

    @staticmethod
    def _detect_instagram_url_type(url: str):
        if _INSTAGRAM_URL_PATTERNS[UrlTypeEnum.POST].match(url):
            return UrlTypeEnum.POST
        elif _INSTAGRAM_URL_PATTERNS[UrlTypeEnum.STORY].match(url):
            return UrlTypeEnum.STORY
        return UrlTypeEnum.UNKNOWN

    @staticmethod
    def _extract_url_from_album(media_info: Media) -> dict:
        resources = getattr(media_info, "resources", [])
        urls = [resource.video_url or resource.thumbnail_url for resource in resources]
        return {"type": MediasTypeEnum.ALBUM, "urls": urls}

    @staticmethod
    def _extract_url_from_reel(media_info: Media) -> dict:
        video_url = getattr(media_info, "video_url", None)
        thumbnail_url = getattr(media_info, "thumbnail_url", None)
        return {"type": MediasTypeEnum.REEL_OR_POST, "video_url": video_url, "thumbnail_url": thumbnail_url}

    @staticmethod
    def _extract_url_from_story(story_info: Story) -> dict:
        thumbnail_url = getattr(story_info, "thumbnail_url", None)
        video_url = getattr(story_info, "video_url", None)
        return {"type": MediasTypeEnum.STORY, "video_url": video_url, thumbnail_url: "thumbnail_url"}

    def _resolve_post_url(self, url, client):
        media_pk = client.media_pk_from_url(url)
        media_info = client.media_info_v1(media_pk)
        if media_info.media_type == 8:
            return self._extract_url_from_album(media_info)
        else:
            return self._extract_url_from_reel(media_info)

    def _resolve_story_url(self, url, client):
        story_pk = client.story_pk_from_url(url)
        story_info = client.story_info_v1(story_pk)
        return self.extract_url_from_story(story_info)

    def resolve_media_url(self, account, url) -> dict:
        client = account_svc.config.get_account_client(account)
        url_type = self._detect_instagram_url_type(url)
        match url_type:
            case UrlTypeEnum.POST:
                return self._resolve_post_url(url, client)
            case UrlTypeEnum.STORY:
                return self._resolve_story_url(url, client)
            case _:
                raise UnknownMediaUrlType()
