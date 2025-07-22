from django.db import models
from django_fsm import FSMField, transition

from apps.account.models import InstagramAccount
from apps.enums import PostStatusEnum, TaskStateEnum, MediaTaskTypeEnum
from apps.core.utils import change_filename
from apps.core.models import BaseTimeStampedModel


def task_media_upload_to(_, filename):
    return "tasks/medias/" + change_filename(filename=filename)


class MediaTask(BaseTimeStampedModel):
    account = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=120)
    description = models.TextField()
    task_type = models.CharField(max_length=10, choices=MediaTaskTypeEnum.CHOICES)

    media_file = models.FileField(upload_to=task_media_upload_to)
    scheduled_time = models.DateTimeField()
    state = FSMField(default=TaskStateEnum.PENDING, protected=True, choices=TaskStateEnum.CHOICES)
    caption = models.TextField(blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    # post task fields
    disable_comments = models.PositiveSmallIntegerField(default=0, choices=PostStatusEnum.CHOICES)
    disable_like_and_view_counts = models.PositiveSmallIntegerField(default=0, choices=PostStatusEnum.CHOICES)

    # story task fields
    link = models.URLField(blank=True, null=True)
    mention_username = models.CharField(max_length=255, blank=True, null=True)

    @transition(field=state, source=TaskStateEnum.PENDING, target=TaskStateEnum.UPLOADING)
    def to_state_uploading(self):
        return "State switched to Uploading!"

    @transition(field=state, source=TaskStateEnum.UPLOADING, target=TaskStateEnum.SUCCESS)
    def to_state_success(self):
        return "State switched to success of uploading!"

    @transition(field=state, source=TaskStateEnum.UPLOADING, target=TaskStateEnum.FAILED)
    def to_state_failed(self):
        return "State switched to success of uploading!"
