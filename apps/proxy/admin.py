from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib import messages

from apps.core.paginator import CustomModelAdminPaginator
from .models import InternalProxy
from .services import ProxyService

_proxy_svc = ProxyService()


@admin.register(InternalProxy)
class InternalProxyAdmin(admin.ModelAdmin):
    paginator = CustomModelAdminPaginator
    list_display = ("is_valid", "is_active", "capacity", "used_slots")
    list_filter = ("is_valid", "is_active")

    def save_model(self, request, obj, form, change):
        proxy = obj.proxy.strip()

        if not _proxy_svc.is_valid_proxy_format(proxy):
            raise ValidationError("❌ Invalid proxy format! Example: http://127.0.0.1:8080")

        success, error = _proxy_svc.ping_proxy(proxy)
        if not success:
            raise ValidationError(f"❌ Proxy test failed: {error}")

        super().save_model(request, obj, form, change)

        messages.success(request, f"✅ Proxy {proxy} validated and saved successfully.")
