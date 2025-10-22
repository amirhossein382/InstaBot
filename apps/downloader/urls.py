from django.urls import path

from .views import DownloaderUrlResolverAPIView

urlpatterns = (
    path('<str:url>/', DownloaderUrlResolverAPIView.as_view()),
)
