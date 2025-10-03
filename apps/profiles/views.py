from rest_framework import views, status
from rest_framework.response import Response

from apps.account.models import InstagramAccount
from apps.account.exceptions import base_response_with_error
from apps.enums import FollowerChangeStatusEnum
from .services import ProfileService
from .models import (
    Following, Follower, FollowerChange, Profile,
    AccountGrowthLog
)
from .serializers import (
    FollowingSerializer, FollowerSerializer,
    FollowerChangeSerializer, ProfileSerializer,
    AccountGrowthLogSerializer
)

profile_svc = ProfileService()


class ProfileView(views.APIView):
    serializer_class = ProfileSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return Profile.objects.get(account=account)

    def get(self, request, *args, **kwargs):
        try:
            profile = self.get_queryset()
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)
        serializer = ProfileSerializer(instance=profile)
        return Response(serializer.data)


class FollowersView(views.APIView):
    serializer_class = FollowerSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return Follower.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        try:
            followers = self.get_queryset()
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        serializer = FollowerSerializer(instance=followers, many=True)
        return Response(serializer.data)


class FollowingsView(views.APIView):
    serializer_class = FollowingSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return Following.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        try:
            followings = self.get_queryset()
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        serializer = FollowerSerializer(instance=followings, many=True)
        return Response(serializer.data)


class FollowerChangesView(views.APIView):
    serializer_class = FollowerChangeSerializer

    def get_queryset(self, **kwargs):
        account = InstagramAccount.objects.get(user=self.request.user)
        return FollowerChange.objects.filter(account=account, **kwargs)

    def get(self, request, *args, **kwargs):
        query_param = "change_type"
        data = request.GET
        try:
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
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        serializer = FollowerChangeSerializer(follower_changes, many=True)
        return Response(serializer.data)


class AccountGrowthLogView(views.APIView):
    serializer_class = AccountGrowthLogSerializer

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return AccountGrowthLog.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        try:
            logs = self.get_queryset()
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        serializer = AccountGrowthLogSerializer(logs, many=True)
        return Response(serializer.data)


class UserUnfollowAPIView(views.APIView):

    def get_queryset(self, user_pk):
        account = InstagramAccount.objects.get(user=self.request.user)
        following = Following.objects.get(account=account, user_pk=user_pk)
        return account, following

    def delete(self, request, *args, **kwargs):
        user_pk = kwargs.get('following_pk', None)
        if user_pk:
            try:
                account, following = self.get_queryset(user_pk)
            except InstagramAccount.DoesNotExist as err:
                return base_response_with_error(str(err), _status=status.HTTP_404_NOT_FOUND)
            except Following.DoesNotExist as err:
                return base_response_with_error(str(err), _status=status.HTTP_404_NOT_FOUND)

            is_unfollowed = profile_svc.unfollow_user(account, user_pk)
            if is_unfollowed:
                following.delete()
                return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
