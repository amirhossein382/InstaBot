from rest_framework import views, status
from rest_framework.response import Response

from apps.account.models import InstagramAccount
from ..account.exceptions import base_response_with_error
from .serializers import DailyFollowerGrowthLogSerializer
from .models import DailyFollowerGrowthLog
from .services import AnalyticsService

_analytics_svc = AnalyticsService()


class DailyFollowerGrowthLogAPIView(views.APIView):
    serializer_class = DailyFollowerGrowthLogSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return DailyFollowerGrowthLog.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        try:
            logs = self.get_queryset()
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        serializer = DailyFollowerGrowthLogSerializer(logs, many=True)
        return Response(serializer.data)


class FollowerSummaryAPIView(views.APIView):

    def get(self, request, *args, **kwargs):
        account = request.user.instagram_account
        days = int(request.query_params.get("days", 7))

        data = _analytics_svc.get_follower_summary(account, days)

        return Response({
            "range": f"last_{days}_days",
            "new_followers": data["new_followers"],
            "lost_followers": data["lost_followers"],
            "net_growth": data["new_followers"] - data["lost_followers"],
        })
