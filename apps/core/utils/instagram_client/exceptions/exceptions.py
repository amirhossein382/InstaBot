from abc import ABC, abstractmethod
from .instagrapi_exceptions import *


class InstagramError(Exception, ABC):
    """Base error for all Instagram providers."""

    @property
    @abstractmethod
    def message(self):
        """Each subclass must define message"""
        pass

    @property
    @abstractmethod
    def status_code(self):
        """Each subclass must define status_code"""
        pass


class InstagramInvalidCredentials(InstagramError):
    status_code = 401
    message = "Wrong username or password."


class InstagramTwoFactorRequired(InstagramError):
    status_code = 403
    message = "Two-factor verification required."


class InstagramThrottled(InstagramError):
    status_code = 202
    message = "Too many requests, retry after 30 minutes."


class InstagramLoginRequired(InstagramError):
    status_code = 429
    message = "Instagram blocked login."


class InstagramProxyFailed(InstagramError):
    status_code = 400
    message = "Proxy connection error."


def exception_mapper(exception: Exception):
    if isinstance(exception, BadPassword):
        return InstagramInvalidCredentials()
    elif isinstance(exception, ChallengeRequired):
        return InstagramTwoFactorRequired()
    elif isinstance(exception, PleaseWaitFewMinutes):
        return InstagramThrottled()
    elif isinstance(exception, LoginRequired):
        return InstagramLoginRequired()
    elif isinstance(exception, (ProxyError, HTTPError, GenericRequestError, ClientConnectionError)):
        return InstagramProxyFailed()
    else:
        return Exception("Unknow error.")
