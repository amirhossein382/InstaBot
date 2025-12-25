from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from apps.core.utils import Logger
from apps.core.tasks import resum_all_account_periodic_tasks, pause_all_account_periodic_tasks
from apps.profiles.services import ProfileService
from .models import InstagramAccount

logger = Logger()
profile_svc = ProfileService()


@receiver(user_logged_in)
def resume_periodic_analysis(sender, request, user, **kwargs):
    op = resume_periodic_analysis.__name__
    try:
        account = InstagramAccount.objects.get(user=user)
    except InstagramAccount.DoesNotExist:
        return

    if account.is_analyses_paused and account.is_initialized:
        logger.log_event(op, "user logged in, resuming periodic tasks...")
        resum_all_account_periodic_tasks(account)
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
        pause_all_account_periodic_tasks(account)
        logger.log_event(op, "periodic tasks paused")
