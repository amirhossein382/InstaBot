from django.utils.translation import gettext_lazy as _


class UrlTypeEnum:
    POST = "post"
    STORY = "story"
    UNKNOWN = "unknown"

    ALL_TOPICS = (POST, STORY, UNKNOWN)
    CHOICES = (
        (POST, _("Post")),
        STORY, _("Story"),
        (UNKNOWN, _("Unknown")),
    )


class MediasTypeEnum:
    REEL_OR_POST = "reel_or_post"
    ALBUM = "album"
    STORY = "story"

    ALL_TOPICS = (REEL_OR_POST, ALBUM, STORY)

    CHOICES = (
        (REEL_OR_POST, _("Reel or Post")),
        (ALBUM, _("Album")),
        STORY, _("Story"),
    )
