from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import AuthUserCreationForm
from .models import User

from historie.models import Historie

from simple_history import register


class CustomUserAdmin(UserAdmin):
    add_form = AuthUserCreationForm
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
                    "telefon",
                    "groups"
                )
            },
        ),
        ("Oprávnění", {"fields": ("is_staff", "is_active", "is_superuser")}),
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
                    "is_superuser",
                    "organizace",
                    "hlavni_role",
                    "first_name",
                    "last_name",
                    "telefon",
                    "groups"
                ),
            },
        ),
    )
    search_fields = ("email", "organizace__nazev_zkraceny", "ident_cely", "hlavni_role__name", "first_name", "last_name",
                     "telefon")
    ordering = ("email",)

    def has_delete_permission(self, request, obj=None):
        if obj:
            if Historie.objects.filter(uzivatel=obj).count() > 1000:
                return False
        return True

admin.site.register(User, CustomUserAdmin)
