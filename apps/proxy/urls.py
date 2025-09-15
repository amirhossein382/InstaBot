from django.urls import path

from .views import ProxyCreateAPIView, ProxyListAPIView

urlpatterns = [
    path('', ProxyListAPIView.as_view()),
    path('create/', ProxyCreateAPIView.as_view(), name="proxy_create"),
]
