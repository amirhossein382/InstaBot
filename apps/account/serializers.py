from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.core.serializers import DynamicFieldsModelSerializer

User = get_user_model()


class UserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class DeviceSettingsSerializer(serializers.Serializer):
    android_version = serializers.IntegerField(required=True)
    android_release = serializers.CharField(required=True)
    dpi = serializers.CharField(required=True)
    resolution = serializers.CharField(required=True)
    manufacturer = serializers.CharField(required=True)
    device = serializers.CharField(required=True)
    model = serializers.CharField(required=True)
    cpu = serializers.CharField(required=True)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, allow_null=False, allow_blank=False, required=True)
    password = serializers.CharField(allow_null=False, allow_blank=False, required=True, write_only=True)
    device_settings = DeviceSettingsSerializer(required=True)
