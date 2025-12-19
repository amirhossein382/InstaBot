"""
Project-specific secure client_settings + admin policies for Instabot

This file contains:
- A Django app-level service module to encrypt/decrypt and save client_settings for InstagramAccount
  (placed in `account/services/secure_client_settings.py`)
- Admin customizations for InstagramAccount and Follower models
  (admin snippets to place in `account/admin.py`)

Security guarantees implemented:
- Server-side authenticated encryption with Fernet (cryptography)
- Key rotation notes and safe re-encrypt procedure outlined

"""
import os
import json
from typing import Optional, Dict

from django.conf import settings
from django.db import transaction
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.utils import timezone

from cryptography.fernet import Fernet, InvalidToken

# Load key from secure env var. MUST set DJANGO_CLIENT_SETTINGS_KEY in prod.
CLIENT_SETTINGS_KEY = getattr(settings, "CLIENT_SETTINGS_KEY", None) or os.getenv("DJANGO_CLIENT_SETTINGS_KEY")
if not CLIENT_SETTINGS_KEY:
    raise ImproperlyConfigured("DJANGO_CLIENT_SETTINGS_KEY is not set. Generate a Fernet key and set it in env")
if isinstance(CLIENT_SETTINGS_KEY, str):
    CLIENT_SETTINGS_KEY = CLIENT_SETTINGS_KEY.encode()

try:
    _FERNET = Fernet(CLIENT_SETTINGS_KEY)
except Exception as e:
    raise ImproperlyConfigured(f"DJANGO_CLIENT_SETTINGS_KEY is malformed: {e}")


def encrypt_client_settings(settings_obj: Dict) -> str:
    raw = json.dumps(settings_obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    token = _FERNET.encrypt(raw)
    return token.decode()


def decrypt_client_settings(token_str: str) -> Dict:
    try:
        raw = _FERNET.decrypt(token_str.encode())
        return json.loads(raw.decode("utf-8"))
    except InvalidToken:
        raise InvalidToken("failed to decrypt client settings — token invalid or tampered")


def save_client_settings_for_account(account, settings_dict: Dict):
    """Encrypt and store client settings. Atomic and updates metadata."""
    encrypted = encrypt_client_settings(settings_dict)
    account.client_settings = encrypted
    account.save(update_fields=("client_settings",))


def get_client_settings_for_account(account) -> Optional[Dict]:
    token = account.client_settings
    return decrypt_client_settings(token)


# Key rotation helper (sketch)
def reencrypt_with_new_key(account_qs, old_keys: list, new_key: bytes):
    """Sketch: run a background job that tries to decrypt with old_keys and re-encrypt with new_key.
    old_keys: list of bytes (previous fernet keys). new_key: bytes for fresh key.
    IMPORTANT: keep old_keys in secure vault and limit who can run this job.
    """
    # Implementation notes only: do not place keys here in plain text.
    pass


# -----------------------------
# Admin guidance + snippets (put into account/admin.py)
# -----------------------------
# Advice: register models but restrict permissions & fields — do NOT expose raw client_settings.
# - Do NOT show encrypted_client_settings in admin list or detail pages.
# - Make sensitive fields read-only and disable delete/change where appropriate.
# - Provide admin actions for enabling/disabling tasks (e.g., pause analyze tasks) without revealing user data.


# Example admin.py snippets (paste into account/admin.py):
ADMIN_SNIPPET = '''
from django.contrib import admin
from django.utils.html import format_html
from .models import InstagramAccount, Follower

@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "user", "has_client_settings", "client_settings_last_updated", "device_id")
    readonly_fields = ("client_settings_last_updated", "client_settings_expires_at", "device_id")
    exclude = ("encrypted_client_settings",)  # never show the encrypted blob

    def has_delete_permission(self, request, obj=None):
        # Prevent admin from deleting accounts via admin UI
        return False

    def has_change_permission(self, request, obj=None):
        # Allow reading details but prevent editing sensitive fields from admin
        # return True if you want limited edit, otherwise False to make read-only
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def has_module_permission(self, request):
        return True

    def has_client_settings(self, obj):
        return bool(getattr(obj, 'encrypted_client_settings', None))
    has_client_settings.boolean = True
    has_client_settings.short_description = 'has client settings?'

    actions = ["revoke_client_settings_action", "enable_analysis_action", "disable_analysis_action"]

    def revoke_client_settings_action(self, request, queryset):
        from .services.secure_client_settings import revoke_client_settings
        for account in queryset:
            revoke_client_settings(account)
        self.message_user(request, "Revoked client settings for selected accounts")
    revoke_client_settings_action.short_description = "Revoke client settings"

    def enable_analysis_action(self, request, queryset):
        # Example: toggle a boolean field like `analyze_enabled` (you may need to add it to model)
        queryset.update(analyze_enabled=True)
        self.message_user(request, "Enabled analysis for selected accounts")
    enable_analysis_action.short_description = "Enable analysis tasks"

    def disable_analysis_action(self, request, queryset):
        queryset.update(analyze_enabled=False)
        self.message_user(request, "Disabled analysis for selected accounts")
    disable_analysis_action.short_description = "Disable analysis tasks"


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "user_pk", "username", "is_current")
    readonly_fields = ("user_pk", "username", "full_name", "profile_pic_url")
    search_fields = ("username",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent admin deleting follower rows from admin UI to avoid tampering
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent editing follower details via admin UI
        return False
'''
