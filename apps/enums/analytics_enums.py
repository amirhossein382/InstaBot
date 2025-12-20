from django.utils.translation import gettext_lazy as _


class PostType:
    PHOTO = 1
    VIDEO = 2
    ALBUM = 8

    ALL_TOPICS = (PHOTO, ALBUM, VIDEO)

    CHOICES = (
        (PHOTO, _("Photo")),
        (VIDEO, _("Video")),
        (ALBUM, _("Album")),
    )
