from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from requests.exceptions import ConnectionError, ProxyError, HTTPError
from instagrapi.exceptions import (
    BadPassword, PleaseWaitFewMinutes, LoginRequired,
    ClientUnauthorizedError, ChallengeRequired,ClientUnauthorizedError,
    FeedbackRequired, ClientConnectionError, GenericRequestError, ClientConnectionError,
)


class UserUnActiveException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Your account is not active, you cant login!')


def base_response_with_error(msg: str, _status):
    return Response(data={"detail": msg}, status=_status)
