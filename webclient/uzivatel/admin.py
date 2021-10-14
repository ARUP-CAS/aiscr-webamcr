from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import AuthUserCreationForm
from .models import User

from historie.models import Historie

from simple_history import register


class CustomUserAdmin(UserAdmin):
    add_form = AuthUserCreationForm
    # form = AuthUserChangeForm
    model = User
    list_display = ("email", "is_staff", "is_active", "organizace", "ident_cely", "first_name", "last_name", "telefon")
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
                    "first_name",
                    "last_name",
                    "telefon"
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
                    "first_name",
                    "last_name",
                    "telefon"
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)

    def has_delete_permission(self, request, obj=None):
        if obj:
            if Historie.objects.filter(uzivatel=obj).count() > 1000:
                return False
        return True

admin.site.register(User, CustomUserAdmin)
