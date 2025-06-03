from rest_framework import serializers

from apps.enums import FollowerChangeStatusEnum
from .models import Profile, Follower, Following, FollowerChange


class ProfileSerializer(serializers.ModelSerializer):
    new_followers_count = serializers.SerializerMethodField()
    mutual_followers_count = serializers.SerializerMethodField()
    not_back_followers_count = serializers.SerializerMethodField()
    un_followers_count = serializers.SerializerMethodField()

    def get_new_followers_count(self, obj):
        return FollowerChange.objects.filter(user=obj.user, change_type=FollowerChangeStatusEnum.NEW_FOLLOW).count()

    def get_mutual_followers_count(self, obj):
        return FollowerChange.objects.filter(user=obj.user, change_type=FollowerChangeStatusEnum.MUTUAL).count()

    def get_not_back_followers_count(self, obj):
        return FollowerChange.objects.filter(user=obj.user, change_type=FollowerChangeStatusEnum.NOT_BACK).count()

    def get_un_followers_count(self, obj):
        return FollowerChange.objects.filter(user=obj.user, change_type=FollowerChangeStatusEnum.UNFOLLOW).count()

    class Meta:
        model = Profile
        fields = '__all__'


class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follower
        fields = '__all__'


class FollowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Following
        fields = '__all__'


class FollowerChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowerChange
        fields = '__all__'
