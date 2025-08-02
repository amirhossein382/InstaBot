import re
import time
import requests

from apps.core.utils import Logger
from .models import Proxy

logger = Logger


class ProxyService:
    Op = "ProxyService"

    @staticmethod
    def ping_proxy(proxy, retries=3) -> tuple:
        sleep_time = 0.5
        last_error = None
        for _ in range(retries):
            time.sleep(sleep_time)
            try:
                res = requests.get("https://instagram.com/", proxies={
                    "http": proxy,
                    "https": proxy
                }, timeout=5)
                if res.status_code == 200:
                    return proxy, None
            except Exception as e:
                sleep_time *= 2
                last_error = str(e)
        return False, last_error

    @staticmethod
    def is_valid_proxy_format(proxy):
        regex = r"^(http|https|socks5)://((\w+:\w+)@)?([0-9\.]+):(\d+)/?$"
        return re.match(regex, proxy) is not None

    @staticmethod
    def get_user_proxy_if_exist(temp_id):
        proxy = Proxy.objects.filter(temp_id=temp_id, is_valid=True)
        if proxy.exists():
            return proxy.first()

        return False

    def get_user_valid_proxy(self, **kwargs) -> tuple:
        proxies = Proxy.objects.filter(**kwargs, is_valid=True)
        err = None
        if proxies.exists():
            for proxy in proxies:
                proxy_str, err = self.ping_proxy(proxy.proxy)
                if proxy_str:
                    return proxy_str, err

        return False, err

    @staticmethod
    def set_account_proxy(temp_id, account):
        return Proxy.set_account_to_proxy(temp_id, account)
