from celery import Task


class BaseRetryTask(Task):
    autoretry_for = (ConnectionError, TimeoutError)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
