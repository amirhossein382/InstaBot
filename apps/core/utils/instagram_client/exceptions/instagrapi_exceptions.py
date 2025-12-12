from requests.exceptions import ConnectionError, ProxyError, HTTPError
from instagrapi.exceptions import (
    BadPassword, PleaseWaitFewMinutes, LoginRequired, MediaNotFound, MediaUnavailable,
    ClientUnauthorizedError, ChallengeRequired, ClientUnauthorizedError,
    FeedbackRequired, ClientConnectionError, GenericRequestError, ClientConnectionError,
)
