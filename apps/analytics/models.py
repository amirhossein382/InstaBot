from django.db import models


class DailyFollowerGrowthLog(models.Model):
    account = models.ForeignKey(
        "account.InstagramAccount", on_delete=models.CASCADE, related_name="growth_logs"
    )
    date = models.DateField()
    followers_count = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('account', 'date')
        ordering = ('-date',)


class TopPosts(models.Model):
    account = models.ForeignKey(
        "account.InstagramAccount", on_delete=models.CASCADE, related_name="top_posts"
    )
    post = models.ForeignKey('profiles.Post', on_delete=models.CASCADE, related_name="top_posts")
    score = models.FloatField(default=0.0)

    class Meta:
        ordering = ('-score',)
