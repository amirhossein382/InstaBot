from django.urls import path

from .views import LoginAPIView, LogoutAPIView, AccountInitialAPIView

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("initial/", AccountInitialAPIView.as_view(), name="initial"),
]
