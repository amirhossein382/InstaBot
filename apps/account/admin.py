from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import InstagramAccount, SuperUser, AdminUser

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    model = User
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ("username", "email", "is_superuser")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "usable_password", "password1", "password2"),
            },
        ),
    )


admin.site.register(User, CustomUserAdmin)


@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    search_fields = ("username",)
    list_display = ("username", "client_pk")

    def username(self, obj):
        return obj.user.username

    def get_queryset(self, request):
        default_qs = super().get_queryset(request)
        return default_qs.select_related("user")


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("email",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)


@admin.register(SuperUser)
class SuperUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("email",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_superuser=True)
