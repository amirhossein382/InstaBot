from django.dispatch import receiver
from django.contrib.auth import user_logged_out, user_logged_in

from apps.core.utils import Logger
from apps.account.models import InstagramAccount
from .services import ProfileService
from .signals import profile_initialized

profile_svc = ProfileService()
logger = Logger()


@receiver(profile_initialized)
def start_periodic_analysis(sender, account_id, **kwargs):
    op = start_periodic_analysis.__name__
    logger.log_event(op, "creating analyze and update follow data task...")
    profile_svc.config.create_analyze_update_follow_data_periodic_task(account_id)
    logger.log_event(op, "analyze and update follow data task created.")
    logger.log_event(op, "creating analyze growth data task..")
    profile_svc.config.create_analyze_growth_logs_periodic_task(account_id)
    logger.log_event(op, "analyze growth data task created.")


@receiver(user_logged_in)
def resume_periodic_analysis(sender, request, user, **kwargs):
    op = resume_periodic_analysis.__name__
    try:
        account = InstagramAccount.objects.get(user=user)
    except InstagramAccount.DoesNotExist:
        return

    logger.log_event(op, "user logged in, resuming periodic tasks...")
    profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account.id, pause=False)
    profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account.id, pause=False)
    logger.log_event(op, "periodic tasks resumed")


@receiver(user_logged_out)
def end_periodic_analysis(sender, request, user, **kwargs):
    op = end_periodic_analysis.__name__
    try:
        account = InstagramAccount.objects.get(user=user)
    except InstagramAccount.DoesNotExist:
        return

    logger.log_event(op, "user logged out, pausing periodic tasks...")
    profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account.id, pause=True)
    profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account.id, pause=True)
    logger.log_event(op, "periodic tasks paused")
