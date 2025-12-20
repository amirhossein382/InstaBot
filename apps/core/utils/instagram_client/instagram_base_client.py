import re
import time
import random
from abc import ABC, abstractmethod

from apps.enums import UrlTypeEnum


class InstagramBaseClient(ABC):
    _INSTAGRAM_URL_PATTERNS = {
        UrlTypeEnum.POST: re.compile(r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[A-Za-z0-9_-]+"),
        UrlTypeEnum.STORY: re.compile(r"https?://(?:www\.)?instagram\.com/stories/[^/]+/\d+"),
    }

    def _detect_instagram_url_type(self, url: str):
        if self._INSTAGRAM_URL_PATTERNS[UrlTypeEnum.POST].match(url):
            return UrlTypeEnum.POST
        elif self._INSTAGRAM_URL_PATTERNS[UrlTypeEnum.STORY].match(url):
            return UrlTypeEnum.STORY
        return UrlTypeEnum.UNKNOWN

    @staticmethod
    def _clean_user_object(user):
        return {
            "user_pk": int(user.pk),
            "username": user.username,
            "full_name": user.full_name,
            "profile_pic_url": str(user.profile_pic_url),
        }

    @staticmethod
    def _do_sleep(start_time=6, end_time=20):
        sleep_time = random.uniform(start_time, end_time)
        print(f"Sleeping for {sleep_time}")
        time.sleep(sleep_time)

    def _normalize_requests(self, users, client):
        if random.choice([True, False, False]):
            print("Normalizing requests..")
            check_profile_count = random.randint(1, 3)
            random_users_to_check_profile = random.sample(users, check_profile_count)
            for user in random_users_to_check_profile:
                self._do_sleep()
                client.user_info(str(user.user_id), use_cache=False)
            print("Requests normalized.")

    @staticmethod
    def _clean_profile_object(data, account_pk):
        data["account"] = account_pk
        data["user_pk"] = int(data["pk"])
        data["profile_pic_url"] = str(data["profile_pic_url"])
        return data

    @abstractmethod
    def __init__(self, settings: dict = None, proxy: str = None):
        """
        __init__ method has to get just settings and proxy params

        params:
            settings: settings of session.
            proxy: proxy for client.
        """
        pass

    @abstractmethod
    def get_account_client(self, settings, proxy):
        """Get account client"""
        raise NotImplementedError

    @property
    @abstractmethod
    def get_user_id(self):
        """Return user id"""
        raise NotImplementedError

    @abstractmethod
    def get_session(self) -> dict:
        """Return JSON serializable session."""
        raise NotImplementedError

    @abstractmethod
    def set_session(self, session_data: dict):
        """Load saved session."""
        raise NotImplementedError

    @abstractmethod
    def set_proxy(self, proxy: str):
        """Set proxy to each client."""
        raise NotImplementedError

    @abstractmethod
    def load_profile(self, account, **kwargs):
        """Return dict: self.__clean_profile_object"""
        raise NotImplementedError

    @abstractmethod
    def load_followers_in_chunk(self, account, **kwargs):
        """Return list of dict: self._clean_user_object"""
        raise NotImplementedError

    @abstractmethod
    def load_followings_in_chunk(self, account, **kwargs):
        """Return list of dict: self._clean_user_object"""
        raise NotImplementedError

    @abstractmethod
    def resolve_media_url(self, url: str) -> dict:
        """
        Resolves Instagram post or story URLs and returns media URLs.
        Return:
            dict: {"type": urls}
        """
        raise NotImplementedError

    @abstractmethod
    def get_top_posts(self, top_post_count=5) -> list[dict]:
        """
        Get top posts
        Return:
            list[dict]: [
            {"media_url":"url"or"", "media_urls":"urls"or"", "post_type":1,
            "view_count":5, "like_count":5,"comment_count":35, "taken_at":85452.2598,
            "caption" :"some caption", "hashtags":["some hashtag",...]}, ...
            ]
        """
        raise NotImplementedError

    @abstractmethod
    def login(self, username: str, password: str, proxy: str, **kwargs):
        """Login user to instagram"""
        raise NotImplementedError

    @abstractmethod
    def logout(self, username: str, password: str):
        """Logout user from instagram"""
        raise NotImplementedError
