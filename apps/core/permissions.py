from django.contrib.auth import logout
from rest_framework.permissions import BasePermission

from apps.account.models import InstagramAccount
from apps.account.services import AccountService
from apps.account.exceptions import ClientUnauthorizedError

account_svc = AccountService()


class IsInstaSessionValid(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        account = InstagramAccount.objects.get(user=user)
        client = account_svc.get_client_by_user_id(account.pk)
        try:
            client.get_timeline_feed()
        except ClientUnauthorizedError:
            logout(request=request)
            return False
        else:
            return True
