from django.db import models

from apps.enums import PostType


class DailyFollowerGrowthLog(models.Model):
    account = models.ForeignKey(
        "account.InstagramAccount", on_delete=models.CASCADE, related_name="growth_logs"
    )
    date = models.DateField()
    followers_count = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('account', 'date')
        ordering = ['-date']


class TopPosts(models.Model):
    account = models.ForeignKey(
        'account.InstagramAccount', on_delete=models.CASCADE, related_name="posts"
    )
    media_url = models.URLField(null=True, blank=True)
    media_urls = models.JSONField(null=True, blank=True, default=list)
    media_type = models.SmallIntegerField(choices=PostType.CHOICES)
    caption = models.TextField(blank=True)
    taken_at = models.DateTimeField()

    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    hashtags = models.JSONField(default=list, null=True, blank=True)
