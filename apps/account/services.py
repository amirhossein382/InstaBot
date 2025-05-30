import json

from django.contrib.auth import get_user_model
from instagrapi import Client

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


class AccountService:
    User = get_user_model()
    config = AccountConfig()
    client = Client()

    def _create_device_settings(self, device: dict):
        device = device
        device["app_version"] = self.config.app_version
        device["version_code"] = self.config.version_code
        return device

    def _create_user_agent(self, device: dict):
        return self.config.user_agent_template.format(
            app_version=self.config.app_version, android_version=device["android_version"],
            android_release=device["android_release"], dpi=device["dpi"], resolution=device["resolution"],
            manufacturer=device["manufacturer"], model=device["model"], device=device["device"],
            cpu=device["cpu"], locale=self.config.locale, version_code=self.config.version_code
        )

    def login_by_user_pass(self, username, password, device):
        self.client.delay_range = range(1, 3)
        try:
            user = self.User.objects.get(username=username)
            if user.check_password(password):
                if not user.is_acitve:
                    raise UserUnActiveException()

                self.client.set_device(device=json.loads(user.settings["device_settings"]))
                self.client.set_user_agent(json.loads(user.settings["user_agent"]))

            else:
                raise BadPassword("Your account password is wrong!")

        except self.User.DoesNotExist:
            device = self._create_device_settings(device)
            user_agent = self._create_user_agent(device)
            self.client.set_device(device)
            self.client.set_user_agent(user_agent)

        self.client.login(username=username, password=password)

        return self.client
