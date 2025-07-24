from rest_framework import serializers

from .models import Notification, PushNotifDevice


class NotificationTypeSerializer(serializers.Serializer):
    profile_pic_url = serializers.URLField(max_length=1000, null=True, blank=True)
    full_name = serializers.CharField(max_length=100, blank=True, null=True)
    username = serializers.CharField(max_length=100)


class NotificationSerializer(serializers.ModelSerializer):
    extra_data = NotificationTypeSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ("type", "message", "extra_data", "created_at")


class PushNotifDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushNotifDevice
        fields = ("account", "token", "is_active")
