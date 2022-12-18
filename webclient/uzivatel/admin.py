import structlog
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from core.constants import ZMENA_HLAVNI_ROLE, ZMENA_UDAJU_ADMIN, UZIVATEL_RELATION_TYPE
from historie.models import Historie, HistorieVazby
from services.mailer import Mailer
from .forms import AuthUserCreationForm
from .models import User, UserNotificationType

logger_s = structlog.get_logger(__name__)


class UserNotificationTypeInline(admin.TabularInline):
    model = UserNotificationType.user.through


class CustomUserAdmin(UserAdmin):
    add_form = AuthUserCreationForm
    model = User
    list_display = ("email", "is_active", "organizace", "ident_cely", "hlavni_role", "first_name", "last_name",
                    "telefon", "is_active", "date_joined", "last_login", "osoba")
    list_filter = ("is_active", "organizace", "groups")
    inlines = [UserNotificationTypeInline, ]
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
        ("Oprávnění", {"fields": ("is_active", "is_superuser")}),
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
    search_fields = (
    "email", "organizace__nazev_zkraceny", "ident_cely", "hlavni_role__name", "first_name", "last_name",
    "telefon")
    ordering = ("email",)

    def has_delete_permission(self, request, obj=None):
        if obj:
            if Historie.objects.filter(uzivatel=obj).count() > 1000:
                return False
        return True

    def save_model(self, request, obj: User, form, change):
        user = request.user
        user.created_from_admin_panel = True
        logger_s.debug("uzivatel.admin.save_model.start", user=user.pk, obj_pk=obj.pk, change=change, form=form)
        super().save_model(request, obj, form, change)
        user_db: User = User.objects.get(id=obj.pk)
        if user_db.history_vazba is None:
            historie_vazba = HistorieVazby(typ_vazby=UZIVATEL_RELATION_TYPE)
            historie_vazba.save()
            user_db.history_vazba = historie_vazba
            user_db.save()
        else:
            historie_vazba = user_db.history_vazba
        if user_db.hlavni_role != obj.hlavni_role:
            Historie(
                typ_zmeny=ZMENA_HLAVNI_ROLE,
                uzivatel=user,
                poznamka=obj.hlavni_role,
                vazba=historie_vazba,
            ).save()
            Mailer.sendEU06(user=user)
        group_ids = [str(x) for x in obj.groups.all()]
        Historie(
            typ_zmeny=ZMENA_UDAJU_ADMIN,
            uzivatel=user,
            poznamka=f"Role: {group_ids}",
            vazba=historie_vazba,
        ).save()

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            readonly_fields = ("ident_cely",)
        else:
            readonly_fields = ("ident_cely", "is_superuser")
        return readonly_fields


class CustomGroupAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            obj: Group
            if obj.uzivatele.all().count() >= 1:
                return False
        return super().has_delete_permission(request)


admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
