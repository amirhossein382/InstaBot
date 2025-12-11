from instagrapi import Client
from ..instagram_base_client import InstagramBaseClient


class InstagrapiClient(InstagramBaseClient):
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

    def login(self, username: str, password: str):
        self.client.login(username, password)

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
