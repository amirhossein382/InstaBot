from django.contrib import admin

from .models import MediaTask


@admin.register(MediaTask)
class MediaTaskAdmin(admin.ModelAdmin):
    list_display = ("owner", "name", "state", "task_type")
    list_filter = ("owner", "state", "task_type")

    def owner(self, obj):
        return obj.account.username

    def get_queryset(self, request):
        return super().get_queryset(request).select_releated("account")
