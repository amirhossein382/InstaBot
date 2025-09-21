from django.contrib.auth.forms import UserChangeForm, UserCreationForm, SetUnusablePasswordMixin, UsernameField

from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = UserChangeForm.Meta.fields
        field_classes = UserChangeForm.Meta.field_classes


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ("email",)


class CustomAdminUserCreationForm(SetUnusablePasswordMixin, CustomUserCreationForm):
    usable_password = SetUnusablePasswordMixin.create_usable_password_field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].required = False
        self.fields["password2"].required = False
