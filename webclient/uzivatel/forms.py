from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import AuthUser


class AuthUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = AuthUser
        fields = ("email",)


class AuthUserChangeForm(UserChangeForm):
    class Meta:
        model = AuthUser
        fields = ("email",)
