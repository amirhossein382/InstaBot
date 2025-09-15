from rest_framework import serializers

from .models import Proxy
from .services import ProxyService

proxy_svc = ProxyService()


class ProxyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proxy
        fields = '__all__'


class ProxySerializer(serializers.Serializer):
    temp_id = serializers.UUIDField(required=True)
    proxy = serializers.CharField(required=True, allow_null=False)

    def validate_proxy(self, value):
        if not proxy_svc.is_valid_proxy_format(value):
            raise serializers.ValidationError(f"Invalid proxy format: {value}")

        return value
