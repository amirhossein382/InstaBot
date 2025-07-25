from rest_framework import views
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from apps.enums import MediaTaskTypeEnum
from apps.account.models import InstagramAccount
from .tasks import upload_media_to_instagram
from .models import MediaTask
from .serializers import MediaTaskSerializer
from ..account.exceptions import base_response_with_error


class MediaTaskListCreateView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = MediaTaskSerializer

    def get(self, request, *args, **kwargs):
        param = "task_type"
        data = self.request.GET
        try:
            account = InstagramAccount.objects.get(user=self.request.user)
        except InstagramAccount.DoesNotExist as err:
            return base_response_with_error(str(err), status.HTTP_404_NOT_FOUND)

        match data.get(param):
            case MediaTaskTypeEnum.POST:
                task = MediaTask.objects.filter(account=account, task_type=MediaTaskTypeEnum.POST)
                serializer = self.serializer_class(task, many=True)
                return Response(serializer.data)
            case MediaTaskTypeEnum.STORY:
                task = MediaTask.objects.filter(account=account, task_type=MediaTaskTypeEnum.STORY)
                serializer = self.serializer_class(task, many=True)
                return Response(serializer.data)
            case _:
                task = MediaTask.objects.filter(account=account)
                serializer = self.serializer_class(task, many=True)
                return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        data = request.POST
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        upload_media_to_instagram.apply_async((instance.id,), eta=instance.scheduled_time)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MediaTaskDetailView(views.APIView):
    serializer_class = MediaTaskSerializer

    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        try:
            task = MediaTask.objects.get(pk=pk)
        except MediaTask.DoesNotExist:
            return Response(f"Task {pk} does not exist", status=status.HTTP_404_NOT_FOUND)
        else:
            serializer = self.serializer_class(instance=task)
            return Response(serializer.data)
