from django.contrib.auth import get_user_model

from instagrapi import Client

from apps.account.exceptions import UserUnActiveException
from apps.account.models import InstagramAccount
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


class InstagrapiClient(InstagramBaseClient):
    config = _InstagrapiConfig()
    batch_size = 1000

    def __init__(self, settings=None, proxy=None):
        self.client = Client()
        self.client.delay_range = range(5, 16)
        if settings:
            self.client.set_settings(settings)
        if proxy:
            self.client.set_proxy(proxy)

    @classmethod
    def get_account_client(cls, settings, proxy):
        return cls(settings, proxy)

    def login(self, username: str, password: str, proxy: str, **kwargs):
        op = "login_by_user_pass"
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
                        _logger.log_event(op,
                                          f"Connection error, retries :{retries}/{max_retries} -->{str(err)}")
                        if retries == max_retries:
                            _logger.log_event(op, f"attempt {retries}/{max_retries}: {proxy} is not working...")
                            raise ProxyError(f"{proxy} is not working!")

                    except Exception as err:
                        _logger.log_event(op, log_data=f"User instagram session is not valid --> {err}",
                                          level="ERROR")
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

    def load_profile(self, username: str, **kwargs):
        account = kwargs.get("account")
        data = self.client.user_info(str(account.client_pk), use_cache=False).model_dump()
        return self._clean_profile_object(data, account.pk)

    def load_followers_in_chunk(self, account, **kwargs):
        max_id = ""
        max_amount = 200
        buffer = []
        while True:
            users, max_id = self.client.user_followers_v1_chunk(
                user_id=str(account.client_pk), max_amount=max_amount, max_id=max_id
            )
            for user in users:
                buffer.append(self._clean_user_object(user))
                if len(buffer) >= self.batch_size:
                    yield buffer
                    buffer.clear()
            if not max_id:
                break

        if buffer:
            yield buffer

    def load_followings_in_chunk(self, account, **kwargs):
        max_id = ""
        max_amount = 50
        buffer = []
        while True:
            users, max_id = self.client.user_following_v1_chunk(
                user_id=str(account.client_pk), max_amount=max_amount, max_id=max_id
            )
            for user in users:
                buffer.append(self._clean_user_object(user))
                if len(buffer) >= self.batch_size:
                    yield buffer
                    buffer.clear()
            if not max_id:
                break

        if buffer:
            yield buffer

    def get_session(self):
        return self.client.get_settings()

    def set_session(self, session_data: dict):
        self.client.set_settings(session_data)

    def set_proxy(self, proxy: str):
        self.client.set_proxy(proxy)

    @property
    def get_user_id(self):
        return self.client.user_id
