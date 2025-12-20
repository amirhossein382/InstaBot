from rest_framework import serializers
from .models import DailyFollowerGrowthLog


class DailyFollowerGrowthLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyFollowerGrowthLog
        fields = ("date", "followers_count", "created_at")
