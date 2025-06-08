from django.urls import path

from .views import MediaTaskListCreateView, MediaTaskDetailView

urlpatterns = [
    path("", MediaTaskListCreateView.as_view(), name="media_tasks"),
    path("<int:pk>/", MediaTaskDetailView.as_view(), name="media_task_detail"),
]
