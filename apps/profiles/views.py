from rest_framework import views
from rest_framework.response import Response
from rest_framework import permissions

from apps.account.models import InstagramAccount
from apps.enums import FollowerChangeStatusEnum
from .models import (
    Following, Follower, FollowerChange, Profile,
    AccountGrowthLog
)
from .serializers import (
    FollowingSerializer, FollowerSerializer,
    FollowerChangeSerializer, ProfileSerializer,
    AccountGrowthLogSerializer
)


class ProfileView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return Profile.objects.get(account=account)

    def get(self, request, *args, **kwargs):
        profile = self.get_queryset()
        serializer = ProfileSerializer(instance=profile)
        return Response(serializer.data)


class FollowersView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowerSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return Follower.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        followers = self.get_queryset()
        serializer = FollowerSerializer(instance=followers, many=True)
        return Response(serializer.data)


class FollowingsView(views.APIView):
    serializer_class = FollowingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return Following.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        followings = self.get_queryset()
        serializer = FollowerSerializer(instance=followings, many=True)
        return Response(serializer.data)


class FollowerChangesView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowerChangeSerializer

    def get_queryset(self, **kwargs):
        account = InstagramAccount.objects.get(user=self.request.user)
        return FollowerChange.objects.filter(account=account, **kwargs)

    def get(self, request, *args, **kwargs):
        query_param = "change_type"
        data = request.GET
        match data.get(query_param):
            case FollowerChangeStatusEnum.MUTUAL:
                follower_changes = self.get_queryset(change_type=FollowerChangeStatusEnum.MUTUAL)
            case FollowerChangeStatusEnum.NOT_BACK:
                follower_changes = self.get_queryset(change_type=FollowerChangeStatusEnum.NOT_BACK)
            case FollowerChangeStatusEnum.NEW_FOLLOW:
                follower_changes = self.get_queryset(change_type=FollowerChangeStatusEnum.NEW_FOLLOW)
            case FollowerChangeStatusEnum.UNFOLLOW:
                follower_changes = self.get_queryset(change_type=FollowerChangeStatusEnum.UNFOLLOW)
            case _:
                follower_changes = self.get_queryset()

        serializer = FollowerChangeSerializer(follower_changes, many=True)
        return Response(serializer.data)


class AccountGrowthLogView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AccountGrowthLogSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return AccountGrowthLog.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        logs = self.get_queryset()
        serializer = AccountGrowthLogSerializer(logs, many=True)
        return Response(serializer.data)
