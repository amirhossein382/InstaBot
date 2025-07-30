import re
import time
import requests

from .models import Proxy


class ProxyService:
    @staticmethod
    def ping_proxy(proxy, retries=3):
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
                    return True, None
            except Exception as e:
                sleep_time *= 2
                last_error = str(e)
        return False, last_error

    @staticmethod
    def is_valid_proxy_format(proxy):
        regex = r"^(http|https|socks5)://((\w+:\w+)@)?([0-9\.]+):(\d+)$"
        return re.match(regex, proxy) is not None

    @staticmethod
    def is_exists_proxy(temp_id):
        proxies = Proxy.objects.filter(temp_id=temp_id)
        if proxies.exists():
            return proxies

        return False
