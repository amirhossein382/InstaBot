from rest_framework import serializers

from .models import MediaTask


class MediaTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaTask
        fields = '__all__'
