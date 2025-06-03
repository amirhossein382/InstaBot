from django.urls import path

from .views import FollowersView, FollowingsView, FollowerChangesView, ProfileView

urlpatterns = [
    path("<str:user>/", ProfileView.as_view(), name="profile"),
    path("<str:user>/followers/", FollowersView.as_view(), name="followers"),
    path("<str:user>/followings/", FollowingsView.as_view(), name="followings"),
    path("<str:user>/follower_changes/", FollowerChangesView.as_view(), name="follower_changes")
]
