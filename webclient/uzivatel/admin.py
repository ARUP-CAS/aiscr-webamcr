from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import AuthUserCreationForm
from .models import User

from simple_history import register


class CustomUserAdmin(UserAdmin):
    add_form = AuthUserCreationForm
    # form = AuthUserChangeForm
    model = User
    list_display = ("email", "is_staff", "is_active", "organizace", "ident_cely")
    list_filter = ("is_staff", "is_active", "organizace")
    readonly_fields = ("ident_cely", )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                    "organizace",
                    "ident_cely",
                    "hlavni_role",
                )
            },
        ),
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
