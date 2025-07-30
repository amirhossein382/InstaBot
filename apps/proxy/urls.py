from django.urls import path

from .views import CreateProxyAPIView

urlpatterns = [
    path('proxy/', CreateProxyAPIView.as_view(), name='proxy'),
]
