from django.contrib.auth import get_user_model

from instagrapi import Client
from instagrapi.types import Media, Story

from apps.account.exceptions import UserUnActiveException
from apps.account.models import InstagramAccount
from apps.downloader.exceptions import UnknownMediaUrlType
from apps.enums import MediasTypeEnum, UrlTypeEnum
from ..exceptions.instagrapi_exceptions import (
    BadPassword, ProxyError, HTTPError,
    ClientConnectionError, GenericRequestError
)
from ..instagram_base_client import InstagramBaseClient
from ... import decrypt_client_settings, Logger

_USER = get_user_model()
_logger = Logger()


class _InstagrapiConfig:
    app_version = "269.0.0.18.75"
    version_code = "314665256"
    locale = "en_US"
    user_agent_template = (
        "Instagram {app_version} "
        "Android ({android_version}/{android_release}; "
        "{dpi}; {resolution}; {manufacturer}; "
        "{model}; {device}; {cpu}; {locale}; {version_code})"
    )

    def create_device_settings(self, device: dict):
        device = device
        device["app_version"] = self.app_version
        device["version_code"] = self.version_code
        return device

    def create_user_agent(self, device: dict):
        return self.user_agent_template.format(
            app_version=self.app_version, android_version=device["android_version"],
            android_release=device["android_release"], dpi=device["dpi"], resolution=device["resolution"],
            manufacturer=device["manufacturer"], model=device["model"], device=device["device"],
            cpu=device["cpu"], locale=self.locale, version_code=self.version_code
        )

    @staticmethod
    def extract_url_from_album(media_info: Media) -> dict:
        resources = getattr(media_info, "resources", [])
        urls = [resource.video_url or resource.thumbnail_url for resource in resources]
        return {"type": MediasTypeEnum.ALBUM, "urls": urls}

    @staticmethod
    def extract_url_from_reel(media_info: Media) -> dict:
        url = getattr(media_info, "video_url", None) or getattr(media_info, "thumbnail_url", None)
        return {"type": MediasTypeEnum.REEL_OR_POST, "urls": url}

    @staticmethod
    def extract_url_from_story(story_info: Story) -> dict:
        url = getattr(story_info, "video_url", None) or getattr(story_info, "thumbnail_url", None)
        return {"type": MediasTypeEnum.STORY, "urls": url}

    def resolve_post_url(self, url, client):
        media_pk = client.media_pk_from_url(url)
        media_info = client.media_info_v1(media_pk)
        if media_info.media_type == 8:
            return self.extract_url_from_album(media_info)
        return self.extract_url_from_reel(media_info)

    def resolve_story_url(self, url, client):
        story_pk = client.story_pk_from_url(url)
        story_info = client.story_info_v1(story_pk)
        return self.extract_url_from_story(story_info)


class InstagrapiClient(InstagramBaseClient):
    config = _InstagrapiConfig()
    batch_size = 1000

    def __init__(self, settings: dict = None, proxy: str = None):
        self.op = self.__class__.__name__
        self.client = Client()
        self.client.delay_range = range(5, 16)
        if settings:
            self.set_session(settings)
        if proxy:
            self.set_proxy(proxy)

    @property
    def get_user_id(self):
        return str(self.client.user_id)

    @classmethod
    def get_account_client(cls, settings, proxy):
        return cls(settings, proxy)

    def get_session(self):
        return self.client.get_settings()

    def set_session(self, session_data: dict):
        self.client.set_settings(session_data)

    def set_proxy(self, proxy: str):
        self.client.set_proxy(proxy)

    def load_profile(self, account, **kwargs):
        data = self.client.user_info(self.get_user_id, use_cache=False).model_dump()
        return self._clean_profile_object(data, account.pk)

    def load_followers_in_chunk(self, account, **kwargs):
        max_id = ""
        max_amount = 20
        buffer = []
        while True:
            self._do_sleep()
            users, max_id = self.client.user_followers_v1_chunk(
                user_id=self.get_user_id, max_amount=max_amount, max_id=max_id
            )
            print(f"Following requests count {self.client.private_requests_count}")
            self._normalize_requests(users, self.client)
            for user in users:
                buffer.append(self._clean_user_object(user))
                if len(buffer) >= self.batch_size:
                    yield buffer
                    buffer = []
            if not max_id:
                break

        if buffer:
            yield buffer

    def load_followings_in_chunk(self, account, **kwargs):
        max_id = ""
        max_amount = 20
        buffer = []
        while True:
            self._do_sleep()
            users, max_id = self.client.user_following_v1_chunk(
                user_id=self.get_user_id, max_amount=max_amount, max_id=max_id
            )
            print(f"Following requests count {self.client.private_requests_count}")
            self._normalize_requests(users, self.client)
            for user in users:
                buffer.append(self._clean_user_object(user))
                if len(buffer) >= self.batch_size:
                    yield buffer
                    buffer = []
            if not max_id:
                break

        if buffer:
            yield buffer

    def resolve_media_url(self, url) -> dict:
        url_type = self._detect_instagram_url_type(url)
        match url_type:
            case UrlTypeEnum.POST:
                return self.config.resolve_post_url(url, self.client)
            case UrlTypeEnum.STORY:
                return self.config.resolve_story_url(url, self.client)
            case _:
                raise UnknownMediaUrlType()

    def get_top_posts(self, top_post_count=5) -> list:
        end_cursor = None
        top_posts = []
        page_size = 5

        while True:
            medias, end_cursor = self.client.user_medias_paginated(
                self.get_user_id,
                amount=page_size,
                end_cursor=end_cursor
            )

            if not medias:
                break

            for media in medias:
                score = media.view_count + (media.like_count or 0) + (media.comment_count or 0)

                if len(top_posts) < top_post_count:
                    top_posts.append((score, media))
                    top_posts.sort(reverse=True, key=lambda x: x[0])

                else:
                    if score > top_posts[-1][0]:
                        top_posts[-1] = (score, media)
                        top_posts.sort(reverse=True, key=lambda x: x[0])

            if not end_cursor:
                break

        return [m for _, m in top_posts]

    def login(self, username: str, password: str, proxy: str, **kwargs):
        op = self.op + ".login"
        device = kwargs.get("device")
        code = kwargs.get("code")
        self.client.set_proxy(proxy)
        ig_settings_is_correct = False
        max_retries = 3
        retries = 0
        try:
            user = _USER.objects.get(username=username)
            _logger.log_event(op, log_data="User already exists")
            if user.check_password(password):
                if not user.is_active:
                    raise UserUnActiveException()

                account = InstagramAccount.objects.get(user=user)
                for _ in range(max_retries):
                    retries += 1
                    try:
                        self.client.set_settings(decrypt_client_settings(account.client_settings))
                        self.client.get_timeline_feed()
                        _logger.log_event(op, log_data="User instagram session is valid.")
                    except (ProxyError, HTTPError, GenericRequestError, ClientConnectionError) as err:
                        err_cls = err.__class__.__name__
                        _logger.log_event(op,
                                          f"{err_cls} error: {str(err)}, retries :{retries}/{max_retries}.")
                        if retries == max_retries:
                            _logger.log_event(op, f"attempt {retries}/{max_retries}: {proxy} is not working...")
                            raise ProxyError(f"{proxy} is not working!")

                    except Exception as err:
                        err_cls = err.__class__.__name__
                        _logger.log_event(
                            op, log_data=f"User instagram session is not valid, {err_cls} error: {err}",
                            level="ERROR"
                        )
                        self.client.set_settings({})  # remove invalid settings
                        settings = decrypt_client_settings(account.client_settings)
                        self.client.set_device(device=settings["device_settings"])
                        self.client.set_user_agent(settings["user_agent"])
                        self.client.set_uuids(settings["uuids"])
                        break
                    else:
                        ig_settings_is_correct = True
                        break

            else:
                raise BadPassword("Your account password is wrong!")

        except _USER.DoesNotExist:
            _logger.log_event(op, log_data="User does not exist.")
            device_ = self.config.create_device_settings(device)
            user_agent = self.config.create_user_agent(device_)
            self.client.set_device(device_)
            self.client.set_user_agent(user_agent)

        if not ig_settings_is_correct:
            if code is not None:
                _logger.log_event(op, log_data="Login user to instagram with verification code")
                self.client.login(username=username, password=password, verification_code=str(code))
            else:
                _logger.log_event(op, log_data="Login user to instagram")
                self.client.login(username=username, password=password)

    def logout(self, username: str, password: str):
        self.client.logout()
