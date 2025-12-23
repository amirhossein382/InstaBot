import json
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q, ExpressionWrapper, F, FloatField
from django.utils.timezone import datetime
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.profiles.models import Post
from .models import DailyFollowerGrowthLog, TopPosts
from ..enums import FollowerChangeStatusEnum
from ..profiles.models import FollowerChange


class AnalyticsConfig:
    daily_growth_data_task_name = "daily_growth_logs_task_{account_id}"
    top_3_posts_task_name = "top_3_posts_task_{account_id}"

    @staticmethod
    def _create_schedule(days=1):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=days,
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
                task="apps.analytics.tasks.analyze_daily_follower_growth_logs",
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

    def create_top_posts_periodic_task(self, account_id: int):
        task_name_ = self.top_3_posts_task_name.format(account_id=account_id)
        schedule = self._create_schedule()
        if not PeriodicTask.objects.filter(name=task_name_).exists():
            PeriodicTask.objects.create(
                interval=schedule,
                name=task_name_,
                task="apps.analytics.tasks.analyze_user_top_posts",
                args=json.dumps([account_id]),
                enabled=True,
                one_off=False,
                start_time=timezone.now()
            )

    def pause_or_resume_top_posts_periodic_task(self, account_id: int, pause: bool):
        try:
            task = PeriodicTask.objects.get(
                name=self.top_3_posts_task_name.format(account_id=account_id)
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

    @staticmethod
    def _calculate_top_posts(account, limit=5, days=90):
        since = timezone.now() - timedelta(days=days)

        qs = (
            Post.objects
            .filter(account=account, taken_at__gte=since)
            .annotate(
                score=ExpressionWrapper(
                    F("like_count") +
                    F("comment_count") * 2 +
                    F("view_count") * 0.5,
                    output_field=FloatField()
                )
            )
            .order_by("-score")
        )

        return qs[:limit]

    def fetch_top_posts(self, account):
        top_posts = self._calculate_top_posts(account)
        with transaction.atomic():
            TopPosts.objects.filter(account=account).delete()
            TopPosts.objects.bulk_create([
                TopPosts(
                    account=account,
                    post=post,
                    score=post.score,
                )
                for post in top_posts
            ])

    @staticmethod
    def get_follower_summary(account, days=7):
        start = timezone.now() - timedelta(days=days)

        qs = FollowerChange.objects.filter(
            Q(account=account) & Q(created_at__gte=start) &
            Q(change_type=FollowerChangeStatusEnum.NEW_FOLLOW) | Q(change_type=FollowerChangeStatusEnum.UNFOLLOW),
        ).values("change_type").annotate(count=Count("id"))

        result = {
            "new_followers": 0,
            "lost_followers": 0,
        }

        for row in qs:
            if row["change_type"] == FollowerChangeStatusEnum.NEW_FOLLOW:
                result["new_followers"] = row["count"]
            else:
                result["lost_followers"] = row["count"]

        return result
