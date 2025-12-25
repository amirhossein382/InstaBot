from rest_framework import serializers
from .models import DailyFollowerGrowthLog, TopPosts, BestTimeStats

from apps.profiles.serializers import PostSerializer


class DailyFollowerGrowthLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyFollowerGrowthLog
        fields = ("id", "date", "followers_count", "created_at")
        read_only_fields = "__all__"


class TopPostSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)

    class Meta:
        model = TopPosts
        fields = "__all__"
        read_only_fields = "__all__"


class BestPostTimeStatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = BestTimeStats
        fields = "__all__"
        read_only_fields = "__all__"
