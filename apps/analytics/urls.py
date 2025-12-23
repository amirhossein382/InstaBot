from django.urls import path

from .views import (
    DailyFollowerGrowthLogAPIView, FollowerSummaryAPIView,
    TopPostListAPIView, TopPostDetailAPIView
)

urlpatterns = (
    path("growth-logs/", DailyFollowerGrowthLogAPIView.as_view(), name="growth_logs"),
    path("followers-summary/", FollowerSummaryAPIView.as_view(), name="followers_summary"),
    path("top-posts/", TopPostListAPIView.as_view(), name="top_posts"),
    path("top-posts/<int:pk>/", TopPostDetailAPIView.as_view(), name="top_posts_detail"),

)
