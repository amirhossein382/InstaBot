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


class InstagramActionBlocked(InstagramError):
    status_code = 429
    message = "Instagram blocked this action. Please wait and try again later."


class InstagramUnauthorized(InstagramError):
    status_code = 401
    message = "Session expired or unauthorized. Please login again."


def exception_mapper(exception: Exception):
    if isinstance(exception, BadPassword):
        raise InstagramInvalidCredentials()
    elif isinstance(exception, ChallengeRequired):
        raise InstagramTwoFactorRequired()
    elif isinstance(exception, PleaseWaitFewMinutes):
        raise InstagramThrottled()
    elif isinstance(exception, LoginRequired):
        raise InstagramLoginRequired()
    elif isinstance(exception, (ProxyError, HTTPError, GenericRequestError, ClientConnectionError)):
        raise InstagramProxyFailed()
    elif isinstance(exception, FeedbackRequired):
        raise InstagramActionBlocked()
    elif isinstance(exception, ClientUnauthorizedError):
        raise InstagramUnauthorized()
    else:
        raise Exception("Unknow error.")
