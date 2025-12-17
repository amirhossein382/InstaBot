# import json

from django.contrib.auth import get_user_model, login, logout
# from django.contrib.auth.signals import user_logged_in, user_logged_out
# from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView

from apps.core.utils import Logger, encrypt_client_settings
from apps.core.utils.instagram_client import get_instagram_account_client
from apps.core.utils.instagram_client.exceptions import InstagramError
from apps.profiles.signals import profile_initialized
from apps.profiles.services import ProfileService
from apps.proxy.services import ProxyService
from .models import InstagramAccount
from .serializers import LoginSerializer
from .services import AccountService
from .exceptions import base_response_with_error

account_svc = AccountService()
profile_svc = ProfileService()
proxy_svc = ProxyService()
User = get_user_model()
_logger = Logger()


class LoginAPIView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        verification_code = request.query_params.get("verification_code")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        proxy, err = proxy_svc.get_valid_proxy()

        if proxy:
            try:
                client = account_svc.login_user_to_instagram(
                    username=serializer.validated_data["username"],
                    password=serializer.validated_data["password"],
                    device=serializer.validated_data["device_settings"],
                    proxy=proxy.proxy,
                    code=verification_code
                )
            except InstagramError as exc:
                status_code = getattr(exc, "status_code", 500)
                return base_response_with_error(str(exc), _status=status_code)
            except Exception as exc:
                exc_cls = exc.__class__.__name__
                _logger.log_event(
                    self.__class__.__name__, log_data=f"Login {exc_cls} error: {err}",
                    level="WARNING"
                )
                return base_response_with_error("Internal server error!.", _status=500)
            else:
                with transaction.atomic():
                    user, created = User.objects.get_or_create(
                        username=serializer.validated_data["username"],
                        defaults={
                            "password": make_password(serializer.validated_data['password']),
                        }
                    )
                    account, account_created = InstagramAccount.objects.update_or_create(
                        user=user,
                        defaults={
                            "client_settings": encrypt_client_settings(client.get_session()),
                            "internal_proxy": proxy
                        },
                        create_defaults={
                            "client_settings": encrypt_client_settings(client.get_session()),
                            "client_pk": client.get_user_id,
                            "internal_proxy": proxy
                        }
                    )
                if created:
                    user.full_clean()
                    user.save()

                if account_created:
                    account.save()

                # tokens = account_svc.get_tokens_for_user(user)
                # user_logged_in.send(sender=user.__class__, request=request, user=user)
                # return Response(data=tokens, status=status.HTTP_201_CREATED)
                login(request=request, user=user)
                return Response(data="Logged in success")

        else:
            if err is None:
                return base_response_with_error(
                    f"Account does not have a proxy.", _status=status.HTTP_401_UNAUTHORIZED
                )
            else:
                return base_response_with_error(
                    f"Proxy error --> {str(err)}", _status=status.HTTP_401_UNAUTHORIZED
                )


class LogoutAPIView(APIView):

    def get(self, **kwargs):
        _logger.log_event(self.__class__.__name__, log_data="user logged out")
        logout(self.request)
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
        # try:
        #     refresh_token = request.data["refresh"]
        #     account_svc.block_token(refresh_token)
        # except KeyError:
        #     return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        # except TokenError:
        #     return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        # user_logged_out.send(sender=user.__class__, request=request, user=request.user)
        # return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)


class AccountInitialAPIView(APIView):

    def get(self, request, *args, **kwargs):
        user = request.user
        account = InstagramAccount.objects.get(user=user)
        if account.is_initialized:
            return Response(data="Account already initialized.", status=status.HTTP_200_OK)

        _logger.log_event(self.__class__.__name__, log_data="initializing account...")
        try:
            client = get_instagram_account_client(account.client_settings, account.internal_proxy)
            with transaction.atomic():
                _logger.log_event(self.__class__.__name__, log_data="fetching profile..")
                profile_svc.fetch_profile_info(account, client)
                _logger.log_event(self.__class__.__name__, log_data="fetching followers..")
                profile_svc.fetch_followers(account, client)
                _logger.log_event(self.__class__.__name__, log_data="fetching followings..")
                profile_svc.fetch_followings(account, client)
                _logger.log_event(self.__class__.__name__, log_data="fetching analyses..")
                profile_svc.analyze_follower_changes(account=account)
                account.is_initialized = True
                account.save()
                transaction.on_commit(lambda: profile_initialized.send(
                    sender=self.__class__.__name__, account_id=account.pk
                ))
        except InstagramError as exc:
            status_code = getattr(exc, "status_code", 500)
            return base_response_with_error(
                msg=str(exc), _status=status_code
            )
        except Exception as msg:
            err_cls = msg.__class__.__name__
            _logger.log_event(self.__class__.__name__, log_data=f"Error {err_cls}: {str(msg)}", level="WARNING")
            return base_response_with_error(
                msg="Initialization failed for unknown error!",
                _status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        _logger.log_event(self.__class__.__name__, log_data="Account initial done.")
        return Response(data="initialized successfully", status=status.HTTP_201_CREATED)
