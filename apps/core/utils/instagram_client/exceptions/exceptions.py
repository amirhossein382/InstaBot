from abc import ABC, abstractmethod
from .instagrapi_exceptions import *

from apps.downloader.exceptions import UnknownMediaUrlType


class InstagramError(Exception, ABC):
    """Base error for all Instagram providers."""

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_message

    @property
    @abstractmethod
    def default_message(self):
        """Each subclass must define message"""
        pass

    @property
    @abstractmethod
    def status_code(self):
        """Each subclass must define status_code"""
        pass

    def __str__(self):
        return self.detail


class InstagramInvalidCredentials(InstagramError):
    status_code = 401
    default_message = "Wrong username or password."


class InstagramTwoFactorRequired(InstagramError):
    status_code = 403
    default_message = "Two-factor verification required."


class InstagramThrottled(InstagramError):
    status_code = 202
    default_message = "Too many requests, retry after 30 minutes."


class InstagramLoginRequired(InstagramError):
    status_code = 429
    default_message = "Instagram login required."


class InstagramConnectionError(InstagramError):
    status_code = 400
    default_message = "Proxy connection error."


class InstagramActionBlocked(InstagramError):
    status_code = 429
    default_message = "Instagram blocked this action. Please wait and try again later."


class InstagramUnauthorized(InstagramError):
    status_code = 401
    default_message = "Session expired or unauthorized. Please login again."


class InstagramMediaError(InstagramError):
    status_code = 500
    default_message = "Failed to resolve Instagram media URL."


class InstagramMediaNotFound(InstagramMediaError):
    status_code = 404
    default_message = "Media not found or no longer available."


class InstagramUnknownMediaUrlType(InstagramMediaError):
    status_code = 400
    default_message = "Invalid or unsupported Instagram media URL."


def exception_mapper(exception: Exception):
    if isinstance(exception, BadPassword):
        raise InstagramInvalidCredentials()
    elif isinstance(exception, ChallengeError):
        raise InstagramTwoFactorRequired(str(exception))
    elif isinstance(exception, PleaseWaitFewMinutes):
        raise InstagramThrottled(str(exception))
    elif isinstance(exception, LoginRequired):
        raise InstagramLoginRequired()
    elif isinstance(exception, (
            ProxyError, HTTPError, GenericRequestError, ClientConnectionError,
            ConnectionError, ClientConnectionError,
    )):
        raise InstagramConnectionError(str(exception))
    elif isinstance(exception, FeedbackRequired):
        raise InstagramActionBlocked(str(exception))
    elif isinstance(exception, ClientUnauthorizedError):
        raise InstagramUnauthorized(str(exception))
    elif isinstance(exception, MediaNotFound):
        raise InstagramMediaNotFound()
    elif isinstance(exception, UnknownMediaUrlType):
        raise InstagramUnknownMediaUrlType()
    else:
        raise Exception("Unknow error.")
