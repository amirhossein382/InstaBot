import json

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView

from apps.core.utils import Logger
from apps.profiles.signals import profile_initialized
from apps.profiles.services import ProfileService
from apps.proxy.services import ProxyService
from apps.core.utils import encrypt_client_settings
from .models import InstagramAccount
from .serializers import LoginSerializer
from .services import AccountService
from .exceptions import (
    BadPassword, PleaseWaitFewMinutes, LoginRequired,
    base_response_with_error, ChallengeRequired, ClientConnectionError,
    ProxyError, HTTPError, GenericRequestError
)

account_svc = AccountService()
profile_svc = ProfileService()
proxy_svc = ProxyService()
User = get_user_model()
logger = Logger()


class LoginAPIView(APIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        verification_code = request.query_params.get("verification_code")
        print(verification_code)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        proxy, err = proxy_svc.get_user_valid_proxy(temp_id=serializer.validated_data["temp_id"])

        if proxy:
            try:
                client = account_svc.login_by_user_pass(
                    username=serializer.validated_data["username"],
                    password=serializer.validated_data["password"],
                    device=serializer.validated_data["device_settings"],
                    proxy=proxy,
                    code=verification_code
                )
            except BadPassword as msg:
                logger.log_event(self.__class__.__name__, log_data=" login failed because bad password", level="ERROR")
                return base_response_with_error(msg=str(msg), _status=status.HTTP_401_UNAUTHORIZED)
            except PleaseWaitFewMinutes as msg:
                logger.log_event(self.__class__.__name__, log_data="Login failed because throttled", level="ERROR")
                return base_response_with_error(msg=str(msg), _status=status.HTTP_202_ACCEPTED)
            except LoginRequired:
                logger.log_event(self.__class__.__name__, log_data="Login failed because blocked", level="ERROR")
                return base_response_with_error(
                    msg="Too many request, try after 30 minutes.",
                    _status=status.HTTP_400_BAD_REQUEST
                )
            except ChallengeRequired:
                logger.log_event(self.__class__.__name__, log_data=":Login failed because challenge required",
                                 level="ERROR")
                return base_response_with_error(
                    msg='Open your browser and login to your account for fix Challenge Required',
                    _status=status.HTTP_400_BAD_REQUEST
                )
            except(ProxyError, HTTPError, GenericRequestError, ClientConnectionError) as err:
                logger.log_event(self.__class__.__name__,
                                 log_data=f"Login failed because connection error -->{str(err)}",
                                 level="ERROR")
                return base_response_with_error(
                    msg='Connection error.',
                    _status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as err:
                logger.log_event(
                    self.__class__.__name__, log_data=f"Login failed because unknown error ---> {err}",
                    level="WARNING"
                )
                if "EOF when reading a line" in str(err):
                    return base_response_with_error(
                        msg="Open to your instagram app and accept your login and try again or go to instagram website and login to your account then try to login here again",
                        _status=status.HTTP_400_BAD_REQUEST
                    )
                elif "We can't find an account with" in str(err):
                    return base_response_with_error(
                        msg=str(err),
                        _status=status.HTTP_400_BAD_REQUEST
                    )

                return base_response_with_error(
                    msg=" login failed because unknown error!",
                    _status=status.HTTP_400_BAD_REQUEST
                )
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
                            "client_settings": encrypt_client_settings(client.get_settings()),
                        },
                        create_defaults={
                            "client_settings": encrypt_client_settings(client.get_settings()),
                            "client_pk": client.user_id
                        }
                    )
                if created:
                    user.full_clean()
                    user.save()

                if account_created:
                    account.save()

                proxy_svc.set_account_proxy(temp_id=serializer.validated_data["temp_id"], account=account)
                tokens = account_svc.get_tokens_for_user(user)
                user_logged_in.send(sender=user.__class__, request=request, user=user)
                return Response(data=tokens, status=status.HTTP_201_CREATED)

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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            refresh_token = request.data["refresh"]
            account_svc.block_token(refresh_token)
        except KeyError:
            return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        user_logged_out.send(sender=user.__class__, request=request, user=request.user)
        return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)


class AccountInitialAPIView(APIView):

    def get(self, request, *args, **kwargs):
        user = request.user
        account = InstagramAccount.objects.get(user=user)
        if account.is_initialized:
            logger.log_event(self.__class__.__name__, log_data="account already initialized!.")
            return Response(data="initialized successfully", status=status.HTTP_201_CREATED)

        logger.log_event(self.__class__.__name__, log_data="initializing account...")
        try:
            client = account_svc.config.get_account_client(account)
            with transaction.atomic():
                logger.log_event(self.__class__.__name__, log_data="fetching profile..")
                profile_svc.fetch_profile_info(account, client)
                logger.log_event(self.__class__.__name__, log_data="fetching followers..")
                followers = profile_svc.fetch_followers(account, client)
                logger.log_event(self.__class__.__name__, log_data="fetching followings..")
                followings = profile_svc.fetch_followings(account, client)
                logger.log_event(self.__class__.__name__, log_data="fetching analyses..")
                profile_svc.analyze_follower_changes(account=account, followers=followers, followings=followings)
                account.is_initialized = True
                account.save()
                transaction.on_commit(lambda: profile_initialized.send(
                    sender=self.__class__.__name__, account_id=account.id
                ))
        except ProxyError as err:
            logger.log_event(
                self.__class__.__name__, f"Connection error on initializing: {str(err)}", level="ERROR"
            )
            return base_response_with_error(msg=f"Connection error: {str(err)}", _status=status.HTTP_305_USE_PROXY)
        except Exception as e:
            logger.log_event(self.__class__.__name__, log_data=f"account initial failed --> {str(e)}", level="ERROR")
            return Response(data={"detail": f"Initialization failed: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.log_event(self.__class__.__name__, log_data="account initial done")
        return Response(data="initialized successfully", status=status.HTTP_201_CREATED)
