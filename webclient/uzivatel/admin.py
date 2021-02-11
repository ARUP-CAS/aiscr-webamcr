from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import AuthUserChangeForm, AuthUserCreationForm
from .models import User


class CustomUserAdmin(UserAdmin):
    add_form = AuthUserCreationForm
    form = AuthUserChangeForm
    model = User
    list_display = ("email", "is_staff", "is_active", "organizace", "ident_cely")
    list_filter = ("is_staff", "is_active", "organizace")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "organizace",
                    "hlavni_role",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)


admin.site.register(User, CustomUserAdmin)
