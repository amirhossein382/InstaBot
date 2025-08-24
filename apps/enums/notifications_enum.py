from django.utils.translation import gettext_lazy as _


class NotificationsTypeEnum:
    RELATION = "relation"
    ERROR = "errors"

    ALL_TOPICS = (RELATION, ERROR)

    CHOICES = (
        (RELATION, _("Relation")),
        (ERROR, _("Error")),
    )
