from abc import ABC, abstractmethod
from .instagrapi_exceptions import *

from apps.downloader.exceptions import UnknownMediaUrlType


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


class InstagramMediaError(InstagramError):
    status_code = 500
    message = "Failed to resolve Instagram media URL."


class InstagramMediaNotFound(InstagramMediaError):
    status_code = 404
    message = "Media not found or no longer available."


class InstagramUnknownMediaUrlType(InstagramMediaError):
    status_code = 400
    message = "Invalid or unsupported Instagram media URL."


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
    elif isinstance(exception, MediaNotFound):
        raise InstagramMediaNotFound()
    elif isinstance(exception, UnknownMediaUrlType):
        raise InstagramUnknownMediaUrlType()
    else:
        raise Exception("Unknow error.")
