from django.urls import path

from .views import (
    FollowersView, FollowingsView, FollowerChangesView,
    ProfileView, AccountGrowthLogView
)

urlpatterns = [
    path("", ProfileView.as_view(), name="profile"),
    path("followers/", FollowersView.as_view(), name="followers"),
    path("followings/", FollowingsView.as_view(), name="followings"),
    path("followings/", FollowingsView.as_view(), name="followings"),
    path("follower-changes/", FollowerChangesView.as_view(), name="follower_changes"),
    path("growth-logs/", AccountGrowthLogView.as_view(), name="growth_logs"),
]
