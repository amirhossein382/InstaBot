import json
from datetime import timedelta

from django.db.models import Count, Q
from django.utils.timezone import datetime
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.core.utils.instagram_client import get_instagram_account_client
from apps.core.utils.instagram_client.exceptions import exception_mapper
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

    def create_top_posts_periodic_task(self, account_id: int, schedule):
        task_name_ = self.top_3_posts_task_name.format(account_id=account_id)
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
    def calculate_top_posts(account):
        client = get_instagram_account_client(account.client_settings, account.internal_proxy)
        try:
            top_posts = client.get_top_posts()
        except Exception as exc:
            exception_mapper(exc)
        else:
            followers_count = account.profile.follower_count
            for post in top_posts:
                media_url = post.get("media_url")
                media_urls = post.get("media_urls")
                post_type = post.get("post_type")
                view_count = post.get("view_count")
                like_count = post.get("like_count")
                comment_count = post.get("comment_count")
                taken_at = post.get("taken_at")
                caption = post.get("caption")
                hashtags = post.get("hashtags")
                engagement_rate = (like_count + comment_count) / followers_count
                TopPosts.objects.update_or_create(
                    account=account, media_type=post_type, media_url=media_url, media_urls=media_urls,
                    caption=caption, taken_at=taken_at, view_count=view_count, like_count=like_count,
                    comment_count=comment_count, hashtags=hashtags, engagement_rate=engagement_rate)

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
