from rest_framework import views
from rest_framework.response import Response
from rest_framework import permissions

from apps.enums import FollowerChangeStatusEnum
from .models import Following, Follower, FollowerChange, Profile
from .serializers import FollowingSerializer, FollowerSerializer, FollowerChangeSerializer, ProfileSerializer


class ProfileView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return Profile.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        profile = self.get_queryset()
        serializer = ProfileSerializer(instance=profile)
        return Response(serializer.data)


class FollowersView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowerSerializer

    def get_queryset(self):
        return Follower.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        followers = self.get_queryset()
        serializer = FollowerSerializer(instance=followers, many=True)
        return Response(serializer.data)


class FollowingsView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowingSerializer

    def get_queryset(self):
        return Following.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        followings = self.get_queryset()
        serializer = FollowerSerializer(instance=followings, many=True)
        return Response(serializer.data)


class FollowerChangesView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowerChangeSerializer

    def get_queryset(self, **kwargs):
        return FollowerChange.objects.filter(user=self.request.user, **kwargs)

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
