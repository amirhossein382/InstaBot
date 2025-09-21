from django.contrib import admin

from apps.core.paginator import CustomModelAdminPaginator
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    paginator = CustomModelAdminPaginator
    readonly_fields = ("account",)
    list_display = ("account", "title", "type", "is_read")
