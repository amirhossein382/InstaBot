from django.dispatch import receiver
from django.contrib.auth import user_logged_out

from apps.account.models import InstagramAccount
from .services import ProfileService
from .signals import profile_initialized

profile_svc = ProfileService()


@receiver(profile_initialized)
def start_periodic_analysis(sender, account, **kwargs):
    profile_svc.config.create_analyze_update_follow_data_periodic_task(account.id)
    profile_svc.config.create_analyze_growth_logs_periodic_task(account.id)


@receiver(user_logged_out)
def end_periodic_analysis(sender, request, user, **kwargs):
    account = InstagramAccount.objects.get(user=user)
    profile_svc.config.delete_analyze_update_follow_data_periodic_task(account.id)
    profile_svc.config.delete_analyze_growth_logs_periodic_task(account.id)
