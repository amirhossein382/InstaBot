from rest_framework import serializers


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
    temp_id = serializers.UUIDField(required=True, allow_null=False)
    username = serializers.CharField(max_length=150, allow_null=False, allow_blank=False, required=True)
    password = serializers.CharField(allow_null=False, allow_blank=False, required=True, write_only=True)
    device_settings = DeviceSettingsSerializer(required=True)
