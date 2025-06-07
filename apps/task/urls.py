from django.urls import path

from .views import MediaTaskListView, MediaTaskDetailView

urlpatterns = [
    path("", MediaTaskListView.as_view(), name="media_tasks"),
    path("<int:pk>/", MediaTaskDetailView.as_view(), name="media_task_detail"),
]
