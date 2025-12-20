from django.dispatch import receiver

from apps.profiles.receivers import profile_initialized
from apps.core.utils import Logger
from .services import AnalyticsService

_logger = Logger()
_analyzer_svc = AnalyticsService()


@receiver(profile_initialized)
def create_analytics_periodic_tasks(sender, account_id, **kwargs):
    op = create_analytics_periodic_tasks.__name__
    _logger.log_event(op, "task is running...")
    _analyzer_svc.config.create_daily_growth_logs_periodic_task(account_id=account_id)
    _logger.log_event(op, "task done!")
