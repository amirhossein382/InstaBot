from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status as rest_status

from apps.account.exceptions import base_response_with_error
from apps.account.models import InstagramAccount
from apps.profiles.services import ProfileService
from .serializers import ProxySerializer, ProxyListSerializer
from .services import ProxyService
from .models import Proxy

profile_svc = ProfileService()
proxy_svc = ProxyService()


class ProxyListAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ProxyListSerializer

    def get(self, request, *args, **kwargs):
        user = self.request.user if self.request.user.is_authenticated else None
        temp_id = self.request.query_params.get("temp_id")
        proxies = Proxy.objects.filter(Q(account__user=user) | Q(temp_id=temp_id))
        serializer = self.serializer_class(proxies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProxyCreateAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProxySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.request.user if self.request.user.is_authenticated else None
        account = getattr(user, "instagram_account", None)
        proxy = serializer.validated_data["proxy"]
        temp_id = serializer.validated_data["temp_id"]
        is_valid, error = proxy_svc.ping_proxy(proxy)
        if is_valid:
            Proxy.objects.create(temp_id=temp_id, account=account, proxy=proxy)
            if account and account.is_analyses_paused:
                _resume_account_tasks(account=account)
            return Response(f"Valid proxy: {proxy}", status=status.HTTP_200_OK)
        else:
            return base_response_with_error(
                f"Invalid proxy: {proxy}", _status=rest_status.HTTP_400_BAD_REQUEST
            )


def _resume_account_tasks(account: InstagramAccount):
    profile_svc.config.pause_or_resume_analyze_growth_logs_periodic_task(account.id, False)
    profile_svc.config.pause_or_resume_analyze_update_follow_data_periodic_task(account.id, False)
    account.is_analyses_paused = False
    account.save()
