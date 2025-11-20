from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.validators import UnicodeUsernameValidator

from apps.core.models import BaseTimeStampedModel
from .managers import SuperUserManager, AdminUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user class.

    username and password are required. Other fields are optional.
    """

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_("email address"), blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class SuperUser(CustomUser):
    objects = SuperUserManager()

    class Meta:
        proxy = True
        verbose_name = "Super User"
        verbose_name_plural = "Super Users"


class AdminUser(CustomUser):
    objects = AdminUserManager()

    class Meta:
        proxy = True
        verbose_name = "Admin User"
        verbose_name_plural = "Admin Users"


class InstagramAccount(BaseTimeStampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="instagram_account")
    client_pk = models.BigIntegerField(unique=True)
    client_settings = models.TextField()
    internal_proxy = models.ForeignKey(
        "proxy.InternalProxy", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="instagram_accounts",
    )
    is_initialized = models.BooleanField(default=False)
    is_analyses_paused = models.BooleanField(default=False, editable=False)
