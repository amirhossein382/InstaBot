from requests.exceptions import ConnectionError, ProxyError, HTTPError
from instagrapi.exceptions import (
    BadPassword, PleaseWaitFewMinutes, LoginRequired, MediaNotFound, MediaUnavailable,
    ClientUnauthorizedError, ChallengeError, ClientUnauthorizedError, UnknownError,
    FeedbackRequired, ClientConnectionError, GenericRequestError, ClientConnectionError,
)
