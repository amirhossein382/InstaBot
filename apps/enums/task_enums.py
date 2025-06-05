from django.utils.translation import gettext_lazy as _


class MediaTaskTypeEnum:
    POST = "post"
    STORY = "story"

    ALL_TOPICS = (POST, STORY)

    CHOICES = (
        (POST, _("Post")),
        (STORY, _("Story")),
    )


class TaskStateEnum:
    PENDING = "pending"
    UPLOADING = "uploading"
    SUCCESS = "success"
    FAILED = "failed"

    ALL_TOPICS = (PENDING, UPLOADING, SUCCESS, FAILED)

    CHOICES = (
        (PENDING, _("Pending")),
        (UPLOADING, _("Uploading")),
        (SUCCESS, _("Success")),
        (FAILED, _("Failed")),

    )


class PostStatusEnum:
    ENABLED = 1
    DISABLED = 0

    ALL_TOPICS = (ENABLED, DISABLED)

    CHOICES = (
        (ENABLED, _("Enabled")),
        (DISABLED, _("Disabled")),
    )
