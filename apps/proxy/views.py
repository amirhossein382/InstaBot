from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status as rest_status

from .serializers import ProxySerializer
from .services import ProxyService

from .models import Proxy
from ..account.exceptions import base_response_with_error

proxy_svc = ProxyService()


class CreateProxyAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProxySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        proxy = serializer.validated_data["proxy"]
        temp_id = serializer.validated_data["temp_id"]
        is_valid, error = proxy_svc.ping_proxy(proxy)
        if is_valid:
            Proxy.create_temp_proxy(temp_id=temp_id, proxy=proxy, is_valid=True)
            return Response(f"Valid proxy: {proxy}", status=status.HTTP_200_OK)
        else:
            return base_response_with_error(
                f"Invalid proxies: {proxy}", _status=rest_status.HTTP_400_BAD_REQUEST
            )
