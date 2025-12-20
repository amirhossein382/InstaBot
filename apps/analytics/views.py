from rest_framework import views, status
from rest_framework.response import Response

from apps.account.models import InstagramAccount
from .serializers import DailyFollowerGrowthLogSerializer
from .models import DailyFollowerGrowthLog
from ..account.exceptions import base_response_with_error


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
