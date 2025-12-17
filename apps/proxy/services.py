import re
import time
import requests

from .models import InternalProxy


class ProxyService:
    Op = "ProxyService"

    @staticmethod
    def check_internet_connection(retries=3) -> bool:
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

    def get_valid_proxy(self, **kwargs) -> tuple:
        proxies = InternalProxy.objects.filter(**kwargs, is_valid=True, is_active=True)
        err = None
        if proxies.exists():
            for proxy in proxies:
                if not proxy.has_capacity():
                    continue

                proxy_str, err = self.ping_proxy(proxy.proxy)
                if proxy_str:
                    return proxy, err
                proxy.is_valid = False
                proxy.is_active = False
                proxy.save()

        return False, err
