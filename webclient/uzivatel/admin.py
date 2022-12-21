import structlog
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from core.constants import ZMENA_HLAVNI_ROLE, ZMENA_UDAJU_ADMIN, UZIVATEL_RELATION_TYPE, SPOLUPRACE_NEAKTIVNI
from historie.models import Historie, HistorieVazby
from services.mailer import Mailer
from .forms import AuthUserCreationForm
from .models import User, UserNotificationType
from core.constants import ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID
from django.db import transaction, ProgrammingError
from django.db.models import Q
from django.contrib.auth.models import Group

logger_s = structlog.get_logger(__name__)


class UserNotificationTypeInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserNotificationTypeInlineForm, self).__init__(*args, **kwargs)
        self.fields['usernotificationtype'].queryset = UserNotificationType.objects.filter(
            ident_cely__in=["E-A-01", "E-A-02", "E-N-01", "E-N-02", "E-N-05", "E-K-01", "E-U-04"]
        )


class UserNotificationTypeInline(admin.TabularInline):
    model = UserNotificationType.user.through
    form = UserNotificationTypeInlineForm

    def get_queryset(self, request):
        queryset = super(UserNotificationTypeInline, self).get_queryset(request)
        queryset = queryset.filter(
            usernotificationtype__ident_cely__in=["E-A-01", "E-A-02", "E-N-01", "E-N-02", "E-N-05", "E-K-01", "E-U-04"]
        )
        return queryset

    def __init__(self, parent_model, admin_site):
        super(UserNotificationTypeInline, self).__init__(parent_model, admin_site)


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
                    "first_name",
                    "last_name",
                    "telefon",
                    "groups",
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
                    "first_name",
                    "last_name",
                    "telefon",
                    "groups",
                ),
            },
        ),
    )
    search_fields = (
    "email", "organizace__nazev_zkraceny", "ident_cely", "first_name", "last_name",
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
        user_db: User = User.objects.get(id=obj.pk)
        super().save_model(request, obj, form, change)

        form_groups = form.cleaned_data["groups"]
        groups = form_groups.filter(id__in=([ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID]))
        other_groups = form_groups.filter(~Q(id__in=([ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID,
                                                      ROLE_ADMIN_ID])))
        group_ids = groups.values_list('id', flat=True)
        max_id = max(group_ids)

        if set(user.groups.values_list('id', flat=True)) != set(form_groups.values_list('id', flat=True)):
            logger_s.debug("uzivatel.admin.save_model.role_changed", old=obj.hlavni_role,
                           new=user.groups.values_list('name', flat=True))
            Historie(
                typ_zmeny=ZMENA_HLAVNI_ROLE,
                uzivatel=user,
                poznamka="role: " + ", ".join(list(user.groups.values_list('name', flat=True))),
                vazba=obj.history_vazba,
            ).save()
            Mailer.sendEU06(user=user)
        Historie(
            typ_zmeny=ZMENA_UDAJU_ADMIN,
            uzivatel=user,
            poznamka=", ".join([f"{fieldname}: {form.cleaned_data[fieldname]}" for fieldname in form.changed_data
                                if fieldname != "groups"]),
            vazba=obj.history_vazba,
        ).save()

        logger_s.debug("uzivatel.admin.save_model.manage_user_groups", user=obj.pk,
                       user_groups=user_db.groups.values_list('id', flat=True))
        if not obj.is_active:
            logger_s("uzivatel.admin.save_model.manage_user_groups.deactivated", user=obj.pk)
            transaction.on_commit(lambda: obj.groups.set([], clear=True))
            return
        logger_s.debug("uzivatel.admin.save_model.manage_user_groups", user=obj.pk, group_count=groups.count())
        if groups.count() == 0:
            logger_s.debug("uzivatel.admin.save_model.manage_user_groups.badatel_added", user=obj.pk)
            group = Group.objects.get(pk=ROLE_BADATEL_ID)
            transaction.on_commit(lambda: obj.groups.set([group] + list(other_groups.values_list('id', flat=True)),
                                                              clear=True))
        elif groups.count() > 1:
            transaction.on_commit(lambda: obj.groups.set([max_id] + list(other_groups.values_list('id', flat=True)),
                                                              clear=True))
        logger_s.debug("uzivatel.admin.save_model.manage_user_groups.highest_groups", user=obj.pk,
                       user_groups=obj.groups.values_list('id', flat=True))
        logger_s.debug("uzivatel.admin.save_model.manage_user_groups", max_id=max_id, hlavni_role_pk=obj.hlavni_role.pk)

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
            user_count = User.objects.filter(groups__id__in=[obj.pk]).count()
            if user_count >= 1:
                return False
        return super().has_delete_permission(request)


admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
