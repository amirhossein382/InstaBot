from celery import Task, shared_task
from celery.exceptions import Ignore, MaxRetriesExceededError
from django.utils.timezone import now, timedelta

from apps.account.models import InstagramAccount
from apps.enums import NotificationsTypeEnum
from apps.proxy.services import ProxyService
from apps.account.services import AccountService
from apps.analytics.services import AnalyticsService
from apps.profiles.services import ProfileService
from apps.notifications import tasks as notifications_tasks
from apps.core.utils.logger import Logger
from apps.core.utils.instagram_client.exceptions import (
    InstagramConnectionError, InstagramLoginRequired, InstagramThrottled,
    InstagramTwoFactorRequired, InstagramUnauthorized, InstagramActionBlocked
)

_logger = Logger()
_proxy_svc = ProxyService()
_account_svc = AccountService()
_profile_svc = ProfileService()
_analytics_svc = AnalyticsService()


class BaseRetryTask(Task):
    autoretry_for = (ConnectionError, TimeoutError)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True


class AuthenticatedAccountTask(BaseRetryTask):
    abstract = True

    def before_start(self, task_id, args, kwargs):
        account_id = kwargs.get("account_id")
        account = InstagramAccount.objects.select_related("user").get(pk=account_id)

        if not account.user.is_authenticated:
            pause_all_account_periodic_tasks(account)
            raise Ignore()


def instagram_api_task_exception_handler(self, op, exception, account):
    if isinstance(exception, InstagramConnectionError):
        _logger.log_event(
            op, f"[{account.pk}] Connection error!", level="ERROR"
        )
        try:
            self.retry(exc=exception, countdown=120)
        except MaxRetriesExceededError:
            proxy, error = _proxy_svc.get_valid_proxy()
            if not proxy:
                pause_all_account_periodic_tasks(account)
                notifications_tasks.create_notification(
                    account_id=account.pk, profile=None, title="Connection Error",
                    message="No proxy available!",
                    notif_type=NotificationsTypeEnum.ERROR,
                    # push=True
                )
            else:
                account.internal_proxy = proxy
                account.save(update_fields=("internal_proxy",))
    elif isinstance(exception, InstagramLoginRequired):
        _logger.log_event(
            op, f"Login required: {str(exception)} ---> pausing tasks for account {account.pk}",
            level="ERROR"
        )
        pause_all_account_periodic_tasks(account)
        _account_svc.logout_django_by_user(account.user)
        notifications_tasks.create_notification(
            account_id=account.pk, profile=None, title="Authentication",
            message="Your account logged out. please login again!",
            notif_type=NotificationsTypeEnum.ERROR,
            # push=True
        )
    elif isinstance(exception, InstagramThrottled):
        _logger.log_event(
            op, f"Rate limited: delaying 1 hour for account {account.pk} --> {str(exception)}",
            level="ERROR"
        )
        notifications_tasks.create_notification(
            account_id=account.pk, profile=None, title="Rate Limit",
            message="Rate limit from instagram, delay analyses for 1 hour",
            notif_type=NotificationsTypeEnum.ERROR,
            # push=True
        )
        raise self.retry(exc=exception, countdown=3600)
    elif isinstance(exception, InstagramTwoFactorRequired):
        _logger.log_event(op, log_data=f" getting new data failed because challenge required -> {str(exception)}",
                          level="ERROR")
        pause_all_account_periodic_tasks(account)
        notifications_tasks.create_notification(
            account_id=account.pk, profile=None, title="Challenge",
            message="Challenge required from instagram. go to instagram website and login to resolve challenges",
            notif_type=NotificationsTypeEnum.ERROR,
            # push=True
        )
    elif isinstance(exception, InstagramActionBlocked):
        _logger.log_event(
            op, log_data=f" getting new data failed because feedback required -->{str(exception)}",
            level="ERROR"
        )
        pause_all_account_periodic_tasks(account)
        reenable_time = now() + timedelta(hours=12)
        apply_sync_resume_all_account_tasks.apply_async(
            (account.pk,), eta=reenable_time
        )
        notifications_tasks.create_notification(
            account_id=account.pk, profile=None, title="Feedback Required",
            message="Feedback required from instagram. paused analyses for 12 hours!",
            notif_type=NotificationsTypeEnum.ERROR,
            # push=True
        )
    elif isinstance(exception, InstagramUnauthorized):
        _logger.log_event(
            op, f"[{account.pk}] Authorization error during analyses: {str(exception)}", level="ERROR"
        )
        pause_all_account_periodic_tasks(account)
        notifications_tasks.create_notification(
            account_id=account.pk, profile=None, title="Authorization Error",
            message="Analyses failed for Authorization error, login again!",
            notif_type=NotificationsTypeEnum.ERROR,
            # push=True
        )
    else:
        _logger.log_event(
            op, f"[{account.pk}] Unhandled exception during analyses: {str(exception)}", level="WARNING"
        )
        pause_all_account_periodic_tasks(account)
        notifications_tasks.create_notification(
            account_id=account.pk, profile=None, title="Unknown Error",
            message="Analysed failed for unknown error. try to open app or login again.",
            notif_type=NotificationsTypeEnum.ERROR,
            # push=True
        )


def pause_all_account_periodic_tasks(account: InstagramAccount):
    _profile_svc.config.pause_or_resume_update_profile_info_periodic_task(account.pk, pause=True)
    _analytics_svc.config.pause_or_resume_daily_growth_logs_periodic_task(account.pk, pause=True)
    account.is_analyses_paused = True
    account.save(update_fields=("is_analyses_paused",))


@shared_task
def apply_sync_resume_all_account_tasks(account_id):
    _profile_svc.config.pause_or_resume_update_profile_info_periodic_task(account_id, False)
    _analytics_svc.config.pause_or_resume_daily_growth_logs_periodic_task(account_id, False)
    account = InstagramAccount.objects.get(id=account_id)
    account.is_analyses_paused = False
    account.save(update_fields=("is_analyses_paused",))
