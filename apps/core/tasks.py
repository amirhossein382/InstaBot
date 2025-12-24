from celery import Task
from celery.exceptions import Ignore

from apps.account.models import InstagramAccount


class BaseRetryTask(Task):
    autoretry_for = (ConnectionError, TimeoutError)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True


class AuthenticatedAccountTask(BaseRetryTask):
    abstract = True

    def before_start(self, task_id, args, kwargs):
        account_id = args[0]
        account = InstagramAccount.objects.select_related("user").get(pk=account_id)

        if not account.user.is_authenticated:
            raise Ignore()
