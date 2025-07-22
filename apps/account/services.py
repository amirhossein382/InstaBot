import json

from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model, SESSION_KEY
from instagrapi import Client

from .models import InstagramAccount
from .exceptions import UserUnActiveException, BadPassword


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
    client = Client()

    def __init__(self):
        self.client.delay_range = range(1, 3)

    @staticmethod
    def logout_django_by_user(user):
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            if data.get(SESSION_KEY) == str(user.id):
                session.delete()

    def get_client_by_user_id(self, account_id):
        account = InstagramAccount.objects.get(pk=account_id)
        self.client.set_settings(json.loads(account.client_settings))
        return self.client

    def login_by_user_pass(self, username, password, device):
        ig_settings_is_correct = False
        try:
            user = self.User.objects.get(username=username)
            if user.check_password(password):
                if not user.is_active:
                    raise UserUnActiveException()

                account = InstagramAccount.objects.get(user=user)

                try:
                    self.client.set_settings(json.loads(account.client_settings))
                    self.client.get_timeline_feed()
                except Exception:
                    self.client.settings = {}  # remove invalid settings
                    self.client.set_device(device=json.loads(account.client_settings["device_settings"]))
                    self.client.set_user_agent(json.loads(account.client_settings["user_agent"]))
                    self.client.set_uuids(json.loads(account.client_settings["uuids"]))
                else:
                    ig_settings_is_correct = True

            else:
                raise BadPassword("Your account password is wrong!")

        except self.User.DoesNotExist:
            device = self.config.create_device_settings(device)
            user_agent = self.config.create_user_agent(device)
            self.client.set_device(device)
            self.client.set_user_agent(user_agent)

        if not ig_settings_is_correct:
            self.client.login(username=username, password=password)

        return self.client
