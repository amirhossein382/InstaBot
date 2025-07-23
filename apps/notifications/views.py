from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response

from apps.account.models import InstagramAccount
from .serializers import NotificationSerializer
from .models import Notification
from .pagination_classes import NotificationPagination
from ..account.exceptions import base_response_with_error


class NotificationListAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationSerializer
    pagination_class = NotificationPagination

    def get_queryset(self):
        account = InstagramAccount.objects.get(user=self.request.user)
        return Notification.objects.filter(account=account)

    def get(self, request, *args, **kwargs):
        try:
            notifications = self.get_queryset()
        except InstagramAccount.DoesNotExist:
            return base_response_with_error(msg="Instagram Account Not Found", status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(notifications, many=True)
        unread_ids = notifications.filter(is_read=False).values_list("id", flat=True)
        if unread_ids:
            Notification.objects.filter(id__in=unread_ids).update(is_read=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
