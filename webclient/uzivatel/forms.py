from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class AuthUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ("email", "organizace", "jazyk")


class AuthUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "organizace", "jazyk")
