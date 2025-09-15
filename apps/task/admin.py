from django.contrib import admin

from .models import MediaTask


@admin.register(MediaTask)
class MediaTaskAdmin(admin.ModelAdmin):
    list_display = ("get_owner", "name", "state", "task_type")
    list_filter = ("state", "task_type")

    def get_owner(self, obj):
        return obj.account.username

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("account")
