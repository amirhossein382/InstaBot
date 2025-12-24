from django.urls import path

from .views import (
    DailyFollowerGrowthLogAPIView, FollowerSummaryAPIView,
    TopPostListAPIView, TopPostDetailAPIView, BestTimeToPostAPIView
)

urlpatterns = (
    path("growth-logs/", DailyFollowerGrowthLogAPIView.as_view(), name="growth_logs"),
    path("followers-summary/", FollowerSummaryAPIView.as_view(), name="followers_summary"),
    path("top-posts/", TopPostListAPIView.as_view(), name="top_posts"),
    path("top-posts/<int:pk>/", TopPostDetailAPIView.as_view(), name="top_posts_detail"),
    path("best-time-to-post/", BestTimeToPostAPIView.as_view(), name="best_time"),

)
