import json

from instagrapi import Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from apps.proxy.services import ProxyService
from apps.core.utils import Logger, decrypt_client_settings
from .models import InstagramAccount
from .exceptions import (
    UserUnActiveException, BadPassword, ProxyError,
    HTTPError, ClientConnectionError, GenericRequestError
)

logger = Logger()
proxy_svc = ProxyService()


class AccountConfig:
    app_version = "269.0.0.18.75"
    version_code = "314665256"
    locale = "en_US"
    user_agent_template = (
        "Instagram {app_version} "
        "Android ({android_version}/{android_release}; "
        "{dpi}; {resolution}; {manufacturer}; "
        "{model}; {device}; {cpu}; {locale}; {version_code})"
    )

    @staticmethod
    def get_client():
        client = Client()
        client.delay_range = range(3, 6)
        return client

    def get_account_client(self, account: InstagramAccount):
        client = self.get_client()
        client.set_settings(decrypt_client_settings(account.client_settings))
        client.set_proxy(account.internal_proxy.proxy)
        return client

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


class AccountService:
    User = get_user_model()
    config = AccountConfig()

    @staticmethod
    def force_logout(user):
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except Exception as err:
                pass

    @staticmethod
    def get_tokens_for_user(user):
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def block_token(refresh_token):
        token = RefreshToken(refresh_token)
        token.blacklist()

    def login_by_user_pass(self, username, password, device, proxy: str, code=None):
        op = "login_by_user_pass"
        client = self.config.get_client()
        client.set_proxy(proxy)
        ig_settings_is_correct = False
        max_retries = 3
        retries = 0
        try:
            user = self.User.objects.get(username=username)
            logger.log_event(op, log_data="User already exists")
            if user.check_password(password):
                if not user.is_active:
                    raise UserUnActiveException()

                account = InstagramAccount.objects.get(user=user)
                for _ in range(max_retries):
                    retries += 1
                    try:
                        client.set_settings(decrypt_client_settings(account.client_settings))
                        client.get_timeline_feed()
                        logger.log_event(op, log_data="User instagram session is valid.")
                    except (ProxyError, HTTPError, GenericRequestError, ClientConnectionError) as err:
                        logger.log_event(op,
                                         f"Connection error, retries :{retries}/{max_retries} -->{str(err)}")
                        if retries == max_retries:
                            logger.log_event(op, f"attempt {retries}/{max_retries}: {proxy} is not working...")
                            raise ProxyError(f"{proxy} is not working!")

                    except Exception as err:
                        logger.log_event(op, log_data=f"User instagram session is not valid --> {err}", level="ERROR")
                        client.set_settings({})  # remove invalid settings
                        settings = decrypt_client_settings(account.client_settings)
                        client.set_device(device=settings["device_settings"])
                        client.set_user_agent(settings["user_agent"])
                        client.set_uuids(settings["uuids"])
                        break
                    else:
                        ig_settings_is_correct = True
                        break

            else:
                raise BadPassword("Your account password is wrong!")

        except self.User.DoesNotExist:
            logger.log_event(op, log_data="User does not exist.")
            device_ = self.config.create_device_settings(device)
            user_agent = self.config.create_user_agent(device_)
            client.set_device(device_)
            client.set_user_agent(user_agent)

        if not ig_settings_is_correct:
            if code is not None:
                logger.log_event(op, log_data="Login user to instagram with verification code")
                client.login(username=username, password=password, verification_code=str(code))
            else:
                logger.log_event(op, log_data="Login user to instagram")
                client.login(username=username, password=password)

        return client
