import json

from django.utils.timezone import datetime
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from .models import DailyFollowerGrowthLog


class AnalyticsConfig:
    daily_growth_data_task_name = "daily_growth_logs_task_{account_id}"

    @staticmethod
    def _create_schedule():
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )
        return schedule

    def create_daily_growth_logs_periodic_task(self, account_id: int):
        schedule = self._create_schedule()
        task_name_ = self.daily_growth_data_task_name.format(account_id=account_id)
        if not PeriodicTask.objects.filter(name=task_name_).exists():
            PeriodicTask.objects.create(
                interval=schedule,
                name=task_name_,
                task="apps.analyzer.tasks.analyze_daily_growth_logs",
                args=json.dumps([account_id]),
                enabled=True,
                one_off=False,
                start_time=timezone.now()
            )

    def pause_or_resume_daily_growth_logs_periodic_task(self, account_id: int, pause: bool):
        try:
            task = PeriodicTask.objects.get(
                name=self.daily_growth_data_task_name.format(account_id=account_id)
            )
        except PeriodicTask.DoesNotExist:
            pass
        else:
            if pause:
                task.enabled = False
            else:
                task.enabled = True
            task.save(update_fields=("enabled",))


class AnalyticsService:
    config = AnalyticsConfig()

    @staticmethod
    def calculate_daily_growth_logs(account):
        today = datetime.today()
        return DailyFollowerGrowthLog.objects.update_or_create(
            account=account,
            date=today,
            defaults={
                'followers_count': account.profile.follower_count,
            },
            create_defaults={
                'followers_count': account.profile.follower_count,
            }
        )
