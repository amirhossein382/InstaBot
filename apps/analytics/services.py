from django.utils.timezone import datetime

from .models import DailyFollowerGrowthLog


class AnalyticsService:
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
