from django.urls import path

from .views import DailyFollowerGrowthLogAPIView, FollowerSummaryAPIView

urlpatterns = (
    path("growth-logs/", DailyFollowerGrowthLogAPIView.as_view(), name="growth_logs"),
    path("followers-summary/", FollowerSummaryAPIView.as_view(), name="followers_summary"),

)
