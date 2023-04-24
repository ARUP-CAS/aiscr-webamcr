import logging
from typing import Union


from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist

from core.constants import ZMENA_HLAVNI_ROLE, ZMENA_UDAJU_ADMIN
from historie.models import Historie
from services.mailer import Mailer
from notifikace_projekty.models import Pes
from notifikace_projekty.forms import KATASTR_CONTENT_TYPE, KRAJ_CONTENT_TYPE, OKRES_CONTENT_TYPE, create_pes_form
from .forms import AuthUserCreationForm
from .models import User, UserNotificationType
from core.constants import ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.models import Group


logger = logging.getLogger('python-logstash-logger')


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

class PesNotificationTypeInline(admin.TabularInline):
    model_type = None
    model = Pes
    form = create_pes_form(model_typ=model_type)
    
    def get_queryset(self, request):
        queryset = super(PesNotificationTypeInline, self).get_queryset(request)
        queryset = queryset.filter(
            content_type__model=self.model_type
        )
        return queryset

class PesKrajNotificationTypeInline(PesNotificationTypeInline):
    model_type = KRAJ_CONTENT_TYPE
    form = create_pes_form(model_typ=model_type)

class PesOkresNotificationTypeInline(PesNotificationTypeInline):
    model_type = OKRES_CONTENT_TYPE
    form = create_pes_form(model_typ=model_type)
    verbose_name = "Okres"
    verbose_name_plural = "Okresy"
    
class PesKatastrNotificationTypeInline(PesNotificationTypeInline):
    model_type = KATASTR_CONTENT_TYPE
    form = create_pes_form(model_typ=model_type)

class CustomUserAdmin(UserAdmin):
    add_form = AuthUserCreationForm
    model = User
    list_display = ("email", "is_active", "organizace", "ident_cely", "hlavni_role", "first_name", "last_name",
                    "telefon", "is_active", "date_joined", "last_login", "osoba")
    list_filter = ("is_active", "organizace", "groups")
    inlines = [UserNotificationTypeInline, PesKrajNotificationTypeInline, PesOkresNotificationTypeInline, PesKatastrNotificationTypeInline]
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
        logger.debug("uzivatel.admin.save_model.start",
                     extra={"user": user.pk, "obj_pk": obj.pk, "change": change, "form": form})
        try:
            user_db = User.objects.get(id=obj.pk)
        except ObjectDoesNotExist as err:
            user_db = None
        user_db: Union[User, None]
        super().save_model(request, obj, form, change)

        form_groups = form.cleaned_data["groups"]
        groups = form_groups.filter(id__in=([ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID]))
        other_groups = form_groups.filter(~Q(id__in=([ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID,
                                                      ROLE_ADMIN_ID])))
        group_ids = groups.values_list('id', flat=True)
        if group_ids.count() > 0:
            max_id = max(group_ids)
        else:
            max_id = ROLE_BADATEL_ID

        if set(user.groups.values_list('id', flat=True)) != set(form_groups.values_list('id', flat=True)):
            logger.debug("uzivatel.admin.save_model.role_changed",
                         extra={"old": obj.hlavni_role, "new": user.groups.values_list('name', flat=True)})
            Historie(
                typ_zmeny=ZMENA_HLAVNI_ROLE,
                uzivatel=user,
                poznamka="role: " + ", ".join(list(user.groups.values_list('name', flat=True))),
                vazba=obj.history_vazba,
            ).save()
        Historie(
            typ_zmeny=ZMENA_UDAJU_ADMIN,
            uzivatel=user,
            poznamka=", ".join([f"{fieldname}: {form.cleaned_data[fieldname]}" for fieldname in form.changed_data
                                if fieldname != "groups"]),
            vazba=obj.history_vazba,
        ).save()

        if user_db is not None:
            logger.debug("uzivatel.admin.save_model.manage_user_groups",
                         extra={"user": obj.pk, "user_groups": user_db.groups.values_list('id', flat=True)})
        if not obj.is_active:
            logger.debug("uzivatel.admin.save_model.manage_user_groups.deactivated", extra={"user": obj.pk})
            transaction.on_commit(lambda: obj.groups.set([], clear=True))
            return
        logger.debug("uzivatel.admin.save_model.manage_user_groups",
                     extra={"user": obj.pk, "group_count": groups.count()})
        if groups.count() == 0:
            logger.debug("uzivatel.admin.save_model.manage_user_groups.badatel_added", extra={"user": obj.pk})
            group = Group.objects.get(pk=ROLE_BADATEL_ID)
            transaction.on_commit(lambda: obj.groups.set([group] + list(other_groups.values_list('id', flat=True)),
                                                              clear=True))
            Mailer.send_eu06(user=obj, groups=[group] + list(other_groups))
        elif groups.count() > 1:
            transaction.on_commit(lambda: obj.groups.set([max_id] + list(other_groups.values_list('id', flat=True)),
                                                              clear=True))
            # Mailer.send_eu06(user=obj, groups=[groups.filter(id=max_id).first()] + list(other_groups))
        Mailer.send_eu06(user=obj, groups=[groups.filter(id=max_id).first()] + list(other_groups))
        logger.debug("uzivatel.admin.save_model.manage_user_groups.highest_groups",
                     extra={"user": obj.pk, "user_groups": obj.groups.values_list('id', flat=True)})
        logger.debug("uzivatel.admin.save_model.manage_user_groups",
                     extra={"max_id": max_id, "hlavni_role_pk": obj.hlavni_role.pk})

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
