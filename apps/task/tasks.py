from django.utils import timezone
from celery import shared_task

from apps.enums import MediaTaskTypeEnum
from apps.core.utils import is_image, is_video, Logger
from apps.account.services import AccountService
from .models import MediaTask

account_svc = AccountService()
logger = Logger()


@shared_task
def upload_media_to_instagram(task_id):
    op = upload_media_to_instagram.__name__
    logger.log_event(op, log_data=f"task {task_id} is running...")
    task = MediaTask.objects.get(id=task_id)
    try:
        client = account_svc.config.get_account_client(task.account)
    except Exception as err:
        logger.log_event(op, log_data=f"proxy error accord --> {str(err)}")
        return

    try:
        task.to_state_uploading()
        task.save()
        match task.task_type:
            case MediaTaskTypeEnum.POST:
                if is_image(task.media_file.path):
                    logger.log_event(op, f"uploading photo {task_id} to the post...")
                    client.photo_upload(
                        task.media_file.path,
                        task.caption,
                        extra_data={
                            "like_and_view_counts_disabled": task.disable_like_and_view_counts,
                            "disable_comments": task.disable_comments,
                        }
                    )
                elif is_video(task.media_file.path):
                    logger.log_event(op, f"uploading video {task_id} to the post...")
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
                    logger.log_event(op, f"uploading photo {task_id} to the story...")
                    client.photo_upload_to_story(
                        task.media_file.path,
                        task.caption,

                    )
                elif is_video(task.media_file.path):
                    logger.log_event(op, f"uploading video {task_id} to the story...")
                    client.video_upload_to_story(
                        task.media_file.path,
                        task.caption,
                    )

    except Exception as e:
        logger.log_event(op, f"failed to upload media {task_id} on story or post", level="ERROR")
        task.error_message = str(e)
        task.to_state_failed()
        task.save()
    else:
        task.posted_at = timezone.now()
        task.to_state_success()
        task.save()
        logger.log_event(op, f"media {task_id} uploaded successfully to story or post.")
