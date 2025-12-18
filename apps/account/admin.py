from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.profiles.admin import ProfileAdmin
from apps.core.paginator import CustomModelAdminPaginator
from .forms import CustomUserChangeForm, CustomAdminUserCreationForm
from .models import InstagramAccount, SuperUser, AdminUser

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    paginator = CustomModelAdminPaginator
    form = CustomUserChangeForm
    add_form = CustomAdminUserCreationForm
    list_display = ("username", "email", "is_superuser")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("email",)}),
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
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ["email"]}),)


@admin.register(AdminUser)
class AdminUserAdmin(CustomUserAdmin):
    list_display = ("username", "email", "is_active")
    list_filter = ("is_active",)


@admin.register(SuperUser)
class SuperUserAdmin(CustomUserAdmin):
    list_display = ("username", "email", "is_active")
    list_filter = ("is_active",)


@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    paginator = CustomModelAdminPaginator
    show_full_result_count = True
    search_fields = ("username",)
    exclude = ("client_settings",)
    list_display = ("username", "is_initialized", "is_analyses_paused")
    list_filter = ("is_initialized", "is_analyses_paused")
    readonly_fields = ("user",)
    inlines = (ProfileAdmin,)

    def username(self, obj):
        return obj.user.username

    def get_queryset(self, request):
        default_qs = super().get_queryset(request)
        return default_qs.select_related("user")
