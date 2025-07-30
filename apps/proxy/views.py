from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status as rest_status

from .serializers import ProxySerializer
from .services import ProxyService

from .models import Proxy

proxy_svc = ProxyService()


class CreateProxyAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProxySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        proxies = [line.strip() for line in serializer.validated_data.proxies.splitlines() if line.strip()]

        valid = []
        invalid = []

        for proxy in proxies:
            is_valid, error = proxy_svc.ping_proxy(proxy)
            if is_valid:
                valid.append(proxy)
                Proxy.objects.create(temp_id=serializer.validated_data.temp_id, proxy=proxy)
            else:
                invalid.append(proxy)

            if is_valid:
                valid.append(proxy)
            else:
                invalid.append({"proxy": proxy, "error": error})

        if valid:
            return Response(f"Valid proxies: {valid}", status=status.HTTP_200_OK)
        return Response(f"Invalid proxies: {invalid}", status=rest_status.HTTP_400_BAD_REQUEST)
