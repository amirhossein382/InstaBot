from django.urls import path

from .views import CreateProxyAPIView

urlpatterns = [
    path('', CreateProxyAPIView.as_view(), name='proxy'),
]
