from django.contrib import admin
from django.utils.html import format_html

from .models import Profile


class ProfileAdmin(admin.TabularInline):
    model = Profile
    extra = 0
    fields = ("username", "full_name", "profile_pic", "external_url",
              "follower_count", "following_count", "media_count",
              "is_private", "is_verified", "is_business")
    readonly_fields = ("profile_pic",)

    @admin.display(description="Profile Pic")
    def profile_pic(self, obj):
        if obj.profile_pic_url:
            return format_html(
                '<a href="{}" target="_blank">View Pic</a>',
                obj.profile_pic_url
            )
        return "-"

    def has_change_permission(self, request, obj = ...):
        return False