import re
import time
import requests

from apps.core.utils import Logger
from .models import Proxy

logger = Logger


class ProxyService:
    Op = "ProxyService"

    @staticmethod
    def check_internet(retries=3) -> bool:
        sleep_time = 0.5
        for _ in range(retries):
            time.sleep(sleep_time)
            try:
                res = requests.get("https://google.com/", timeout=5)
                if res.status_code == 200:
                    return True
            except Exception:
                sleep_time *= 2
        return False

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

    def get_user_valid_proxy(self, **kwargs) -> tuple:
        proxies = Proxy.objects.filter(**kwargs, is_valid=True).order_by("created_at")
        err = None
        if proxies.exists():
            for proxy in proxies:
                proxy_str, err = self.ping_proxy(proxy.proxy)
                if proxy_str:
                    return proxy_str, err
                proxy.is_valid = False
                proxy.save()

        return False, err

    @staticmethod
    def set_account_proxy(temp_id, account):
        return Proxy.objects.filter(temp_id=temp_id).update(account=account)
