import json

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView

from apps.profiles.signals import profile_initialized
from apps.profiles.services import ProfileService
from .models import InstagramAccount
from .serializers import LoginSerializer
from .services import AccountService
from .exceptions import (
    BadPassword, PleaseWaitFewMinutes, LoginRequired,
    base_response_with_error, ChallengeRequired
)

account_svc = AccountService()
profile_svc = ProfileService()
User = get_user_model()


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            client = account_svc.login_by_user_pass(
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"],
                device=serializer.validated_data["device_settings"]
            )
        except BadPassword as msg:
            return base_response_with_error(msg=str(msg), _status=status.HTTP_401_UNAUTHORIZED)
        except PleaseWaitFewMinutes as msg:
            return base_response_with_error(msg=str(msg), _status=status.HTTP_202_ACCEPTED)
        except LoginRequired:
            return base_response_with_error(
                msg="Too many request, try after 30 minutes.",
                _status=status.HTTP_400_BAD_REQUEST
            )
        except ChallengeRequired:
            return base_response_with_error(
                msg='Open your browser and login to your account for fix Challenge Required',
                _status=status.HTTP_400_BAD_REQUEST
            )

        else:
            user, created = User.objects.get_or_create(
                username=serializer.validated_data["username"],
                defaults={
                    "password": make_password(serializer.validated_data['password']),
                }
            )
            account, account_created = InstagramAccount.objects.get_or_create(
                user=user,
                defaults={
                    "client_settings": json.dumps(client.get_settings()),
                    "client_pk": client.user_id
                }
            )
            if created:
                user.full_clean()
                user.save()

            if account_created:
                account.save()

            login(request=request, user=user)
        return Response(data="logged in success")


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        logout(request)

        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


class AccountInitialView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        account = InstagramAccount.objects.get(user=user)
        try:
            with transaction.atomic():
                profile_svc.fetch_profile_info(account)
                followers = profile_svc.fetch_followers(account)
                followings = profile_svc.fetch_followings(account)
                profile_svc.analyze_follower_changes(account=account, followers=followers, followings=followings)
        except Exception as e:
            return Response(data={"detail": f"Initialization failed: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        profile_initialized.send(sender=self.__class__, account=account)
        return Response(data="initialized successfully", status=status.HTTP_201_CREATED)
