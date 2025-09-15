from django.contrib import admin

from .models import Proxy


# Register your models here.
@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    list_display = ("account","temp_id","is_valid","proxy")
