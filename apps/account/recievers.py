from django.contrib.auth.signals import user_logged_in, user_logged_out
# from django.db.models.signals import post_save
from django.dispatch import receiver
# from django_celery_beat.models import PeriodicTask

from apps.core.utils import Logger
from apps.profiles.services import ProfileService
from .models import InstagramAccount

logger = Logger()
profile_svc = ProfileService()


# @receiver(post_save, sender=InstagramAccount)
# def sync_account_analyses_status_with_task_status(sender, instance, created, **kwargs):
#     op = "sync_account_analyses_status_with_task_status"
#     logger.log_event(op, "Instagram account signal received")
#     update_follow_task_name = profile_svc.config.update_follow_task.format(account_id=instance.id)
#     growth_logs_task_name = profile_svc.config.growth_data_task.format(account_id=instance.id)
#     update_follow_task_queryset = PeriodicTask.objects.filter(name=update_follow_task_name)
#     growth_logs_task_queryset = PeriodicTask.objects.filter(name=growth_logs_task_name)
#     if update_follow_task_queryset.exists() and growth_logs_task_queryset.exists():
#         if instance.is_analyses_paused:
#             update_follow_task_queryset.update(enabled=False)
#             growth_logs_task_queryset.update(enabled=False)
#
#         else:
#             update_follow_task_queryset.update(enabled=True)
#             growth_logs_task_queryset.update(enabled=True)


@receiver(user_logged_in)
def resume_periodic_analysis(sender, request, user, **kwargs):
    op = resume_periodic_analysis.__name__
    try:
        account = InstagramAccount.objects.get(user=user)
    except InstagramAccount.DoesNotExist:
        return

    if account.is_analyses_paused and account.is_initialized:
        logger.log_event(op, "user logged in, resuming periodic tasks...")
        profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account.pk, pause=False)
        profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account.pk, pause=False)
        account.is_analyses_paused = False
        account.save(update_fields=("is_analyses_paused",))
        logger.log_event(op, "periodic tasks resumed")


@receiver(user_logged_out)
def pause_periodic_analysis(sender, request, user, **kwargs):
    op = pause_periodic_analysis.__name__
    try:
        account = InstagramAccount.objects.get(user=user)
    except InstagramAccount.DoesNotExist:
        return

    if not account.is_analyses_paused and account.is_initialized:
        logger.log_event(op, "user logged out, pausing periodic tasks...")
        profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account.pk, pause=True)
        profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account.pk, pause=True)
        account.is_analyses_paused = True
        account.save(update_fields=("is_analyses_paused",))
        logger.log_event(op, "periodic tasks paused")
