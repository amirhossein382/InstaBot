from celery import shared_task

from apps.account.models import InstagramAccount
from apps.core.utils import Logger

from .services import AnalyticsService

_analytics_svc = AnalyticsService()
_logger = Logger()


@shared_task
def analyze_daily_follower_growth_logs(account_id):
    op = analyze_daily_follower_growth_logs.__name__
    _logger.log_event(op, "task is running...")
    account = InstagramAccount.objects.prefetch_related("profile").get(pk=account_id)
    _analytics_svc.calculate_daily_growth_logs(account)
    _logger.log_event(op, "task done!.")
