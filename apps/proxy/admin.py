from django.contrib import admin

from apps.core.paginator import CustomModelAdminPaginator
from .models import Proxy


# Register your models here.
@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    paginator = CustomModelAdminPaginator
    readonly_fields = ("account",)
    list_display = ("account", "temp_id", "is_valid", "proxy")
