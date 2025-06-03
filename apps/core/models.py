from django.db import models


class BaseTimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseInstagramUser(BaseTimeStampedModel):
    username = models.CharField(max_length=100)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    profile_pic_url = models.URLField(max_length=1000, null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.username
