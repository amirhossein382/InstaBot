from django.utils import timezone
from celery import shared_task

from apps.enums import MediaTaskTypeEnum
from apps.core.utils import is_image, is_video
from apps.account.services import AccountService
from .models import MediaTask

account_svc = AccountService()


@shared_task
def upload_media_to_instagram(task_id):
    task = MediaTask.objects.select_related("account").get(id=task_id)
    client = account_svc.get_client_by_user_id(task.account.id)

    try:
        task.to_state_uploading()
        task.save()
        match task.task_type:
            case MediaTaskTypeEnum.POST:
                if is_image(task.media_file.path):
                    client.photo_upload(
                        task.media_file.path,
                        task.caption,
                        extra_data={
                            "like_and_view_counts_disabled": task.disable_like_and_view_counts,
                            "disable_comments": task.disable_comments,
                        }
                    )
                elif is_video(task.media_file.path):
                    client.video_upload(
                        task.media_file.path,
                        task.caption,
                        extra_data={
                            "like_and_view_counts_disabled": task.disable_like_and_view_counts,
                            "disable_comments": task.disable_comments,
                        }
                    )

            case MediaTaskTypeEnum.STORY:
                if is_image(task.media_file.path):
                    client.photo_upload_to_story(
                        task.media_file.path,
                        task.caption,

                    )
                elif is_video(task.media_file.path):
                    client.video_upload_to_story(
                        task.media_file.path,
                        task.caption,
                    )

    except Exception as e:
        task.error_message = str(e)
        task.to_state_failed()
        task.save()
    else:
        task.posted_at = timezone.now()
        task.to_state_success()
        task.save()
