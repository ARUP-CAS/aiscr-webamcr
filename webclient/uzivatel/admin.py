import structlog
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.constants import ZMENA_HLAVNI_ROLE, ZMENA_UDAJU_ADMIN
from .forms import AuthUserCreationForm
from .models import User

from historie.models import Historie


logger_s = structlog.get_logger(__name__)


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

    def save_model(self, request, obj: User, form, change):
        user = request.user
        user_db: User = User.objects.get(pk=obj.pk)
        logger_s.debug("uzivatel.admin.save_model.start", user=user.pk, obj_pk=obj.pk, change=change, form=form)
        if user_db.hlavni_role != obj.hlavni_role:
            Historie(
                typ_zmeny=ZMENA_HLAVNI_ROLE,
                uzivatel=user,
                poznamka=obj.hlavni_role,
                vazba=obj.history_vazba,
            ).save()
        group_ids = [x.pk for x in obj.groups.all()]
        super().save_model(request, obj, form, change)
        Historie(
            typ_zmeny=ZMENA_UDAJU_ADMIN,
            uzivatel=user,
            poznamka=f"Role: {group_ids}",
            vazba=obj.history_vazba,
        ).save()


admin.site.register(User, CustomUserAdmin)
