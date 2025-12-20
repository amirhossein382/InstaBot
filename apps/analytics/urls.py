from django.urls import path

from .views import DailyFollowerGrowthLogAPIView

urlpatterns = (
    path("growth-logs/", DailyFollowerGrowthLogAPIView.as_view(), name="growth_logs"),

)
