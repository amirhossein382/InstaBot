from rest_framework import serializers
from .models import DailyFollowerGrowthLog, TopPosts

from apps.profiles.serializers import PostSerializer


class DailyFollowerGrowthLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyFollowerGrowthLog
        fields = ("id", "date", "followers_count", "created_at")


class TopPostSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)

    class Meta:
        model = TopPosts
        fields = "__all__"
        read_only_fields = "__all__"
