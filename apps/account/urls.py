from django.urls import path

from .views import LoginView, LogoutView, AccountInitialView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("initial/", AccountInitialView.as_view(), name="initial"),
]
