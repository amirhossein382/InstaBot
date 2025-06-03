from django.utils.translation import gettext_lazy as _


class FollowerChangeStatusEnum:
    NEW_FOLLOW = "new"
    UNFOLLOW = "unfollow"
    NOT_BACK = "not_back"
    MUTUAL = "mutual"

    ALL_TOPICS = (NEW_FOLLOW, UNFOLLOW, NOT_BACK, MUTUAL)

    CHOICES = (
        (NEW_FOLLOW, _("New Follower")),
        (UNFOLLOW, _("Unfollowed")),
        (NOT_BACK, _("Not Following Back")),
        (MUTUAL, _("Mutual Follow")),
    )
