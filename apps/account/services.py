# import json

# from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth import SESSION_KEY

from django.utils import timezone
from django.contrib.auth import get_user_model
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from apps.core.utils.instagram_client import get_instagram_client
from apps.core.utils.instagram_client.exceptions import exception_mapper


class AccountService:
    User = get_user_model()

    @staticmethod
    def logout_django_by_user(user):
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            if data.get(SESSION_KEY) == str(user.id):
                session.delete()

    # @staticmethod
    # def force_logout(user):
    #     tokens = OutstandingToken.objects.filter(user=user)
    #     for token in tokens:
    #         try:
    #             BlacklistedToken.objects.get_or_create(token=token)
    #         except Exception as err:
    #             pass

    # @staticmethod
    # def get_tokens_for_user(user):
    #     refresh = RefreshToken.for_user(user)
    #
    #     return {
    #         'refresh': str(refresh),
    #         'access': str(refresh.access_token),
    #     }

    # @staticmethod
    # def block_token(refresh_token):
    #     token = RefreshToken(refresh_token)
    #     token.blacklist()

    @staticmethod
    def login_user_to_instagram(username, password, proxy: str, **kwargs):
        client = get_instagram_client()
        try:
            client.login(username, password, proxy, **kwargs)
        except Exception as exc:
            exception_mapper(exc)
        return client
