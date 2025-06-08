from django.dispatch import receiver
from django.contrib.auth import user_logged_out

from apps.core.utils import Logger
from apps.account.models import InstagramAccount
from .services import ProfileService
from .signals import profile_initialized

profile_svc = ProfileService()
logger = Logger()


@receiver(profile_initialized)
def start_periodic_analysis(sender, account, **kwargs):
    op = start_periodic_analysis.__name__
    logger.log_event(op, "creating analyze and update follow data task...")
    profile_svc.config.create_analyze_update_follow_data_periodic_task(account.id)
    logger.log_event(op, "analyze and update follow data task created.")
    logger.log_event(op, "creating analyze growth data task..")
    profile_svc.config.create_analyze_growth_logs_periodic_task(account.id)
    logger.log_event(op, "analyze growth data task created.")


@receiver(user_logged_out)
def end_periodic_analysis(sender, request, user, **kwargs):
    op = end_periodic_analysis.__name__
    account = InstagramAccount.objects.get(user=user)
    logger.log_event(op, "user logged out, deleting periodic tasks...")
    profile_svc.config.delete_analyze_update_follow_data_periodic_task(account.id)
    profile_svc.config.delete_analyze_growth_logs_periodic_task(account.id)
    logger.log_event(op, "periodic tasks deleted")
