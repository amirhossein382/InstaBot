import json

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.hashers import make_password

from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView

from .serializers import LoginSerializer
from .services import AccountService
from .exceptions import BadPassword, PleaseWaitFewMinutes, LoginRequired, base_response_with_error

account_svc = AccountService()
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
            return base_response_with_error(msg=str(msg), status=status.HTTP_401_UNAUTHORIZED)
        except PleaseWaitFewMinutes as msg:
            return base_response_with_error(msg=str(msg), status=status.HTTP_202_ACCEPTED)
        except LoginRequired:
            return base_response_with_error(
                msg="Too many request, try after 30 minutes.",
                status=status.HTTP_400_BAD_REQUEST
            )

        else:
            user, created = User.objects.get_or_create(
                username=serializer.validated_data["username"],
                defaults={
                    "password": make_password(serializer.validated_data['password']),
                    "username": serializer.validated_data["username"],
                    "settings": json.dumps(client.get_settings()),
                }
            )
            if created:
                user.full_clean()
                user.save()

            login(request=request, user=user)
        return Response(data="logged in success")


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        logout(request)

        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
