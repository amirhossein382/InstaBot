from django.urls import path

from .views import NotificationListAPIView, CreateOrUpdatePushNotifDeviceAPIView

urlpatterns = (
    path("", NotificationListAPIView.as_view(), name="notifications"),
    path("register-or-update-device/", CreateOrUpdatePushNotifDeviceAPIView.as_view(), name="create-or-update-device"),
)
