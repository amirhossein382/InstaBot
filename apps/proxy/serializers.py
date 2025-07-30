from rest_framework import serializers

from .services import ProxyService

proxy_svc = ProxyService()


class ProxySerializer(serializers.Serializer):
    temp_id = serializers.UUIDField(required=True,allow_null=False)
    proxies = serializers.CharField(required=True,allow_null=False)

    def validate_proxies(self, value):
        pass
