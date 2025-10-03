from django.urls import path

from .views import MediaTaskListCreateAPIView, MediaTaskDetailAPIView

urlpatterns = [
    path("", MediaTaskListCreateAPIView.as_view(), name="media_tasks"),
    path("<int:pk>/", MediaTaskDetailAPIView.as_view(), name="media_task_detail"),
]
