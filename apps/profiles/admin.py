from django.contrib import admin

from .models import Profile, Follower, Following, FollowerChange, AccountGrowthLog


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "full_name", "follower_count", "following_count")
    list_filter = ("is_private", "is_business")
    search_fields = ("username", "user_pk")


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    pass


@admin.register(Following)
class FollowingAdmin(admin.ModelAdmin):
    pass


@admin.register(FollowerChange)
class FollowerChangeAdmin(admin.ModelAdmin):
    pass


@admin.register(AccountGrowthLog)
class AccountGrowthLogAdmin(admin.ModelAdmin):
    pass
