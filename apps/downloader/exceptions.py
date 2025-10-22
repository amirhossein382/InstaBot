from instagrapi.exceptions import MediaNotFound


class UnknownMediaUrlType(BaseException):
    def __str__(self):
        return "Unknown media type url!"
