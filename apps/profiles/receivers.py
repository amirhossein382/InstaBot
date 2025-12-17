from django.dispatch import receiver
# from django.db.models.signals import post_save
# from django.contrib.auth import user_logged_out, user_logged_in
# from django_celery_beat.models import PeriodicTask

from apps.core.utils import Logger
# from apps.account.models import InstagramAccount
from .services import ProfileService
from .signals import profile_initialized

profile_svc = ProfileService()
logger = Logger()


@receiver(profile_initialized)
def start_periodic_analysis(requests, account_id, **kwargs):
    op = start_periodic_analysis.__name__
    logger.log_event(op, "creating analyze and update follow data task...")
    profile_svc.config.create_analyze_update_follow_data_periodic_task(account_id)
    logger.log_event(op, "analyze and update follow data task created.")
    logger.log_event(op, "creating analyze growth data task..")
    profile_svc.config.create_analyze_growth_logs_periodic_task(account_id)
    logger.log_event(op, "analyze growth data task created.")

# @receiver(post_save, sender=PeriodicTask)
# def sync_periodic_task_paused_status_with_account_analyses_status(sender, instance, created, **kwargs):
#     extracted_account_id = profile_svc.config.extract_account_id(instance.name)
#     account = InstagramAccount.objects.filter(id=extracted_account_id)
#     if instance.enabled:
#         if account.is_analyses_paused:
#             account.is_analyses_paused = False
#             account.save()
#     else:
#         if not account.is_analyses_paused:
#             account.is_analyses_paused = True
#             account.save()
