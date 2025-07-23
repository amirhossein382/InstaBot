from django.utils.translation import gettext_lazy as _


class NotificationsTypeEnum:
    RELATIONS = "relations"
    ERRORS = "errors"

    ALL_TOPICS = (RELATIONS, ERRORS)

    CHOICES = (
        (RELATIONS, _("Relations")),
        (ERRORS, _("Errors")),
    )
