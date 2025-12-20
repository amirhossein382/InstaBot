from django.dispatch import receiver

from apps.core.utils import Logger
from .services import ProfileService
from .signals import profile_initialized

_profile_svc = ProfileService()
_logger = Logger()


@receiver(profile_initialized)
def create_profile_app_periodic_tasks(requests, account_id, **kwargs):
    op = create_profile_app_periodic_tasks.__name__
    _logger.log_event(op, "receiver is running...")
    _profile_svc.config.create_analyze_update_follow_data_periodic_task(account_id)
    _logger.log_event(op, "receiver done!")
