import logging
from typing import Union

from cacheops import invalidate_model
from django import forms
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin, sensitive_post_parameters_m
from django.core.exceptions import ObjectDoesNotExist
from django.http import StreamingHttpResponse
from django_object_actions import DjangoObjectActions, action

from core.constants import ZMENA_HLAVNI_ROLE, ZMENA_UDAJU_ADMIN, ZMENA_HESLA_ADMIN
from core.repository_connector import FedoraTransaction
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
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


class UserNotificationTypeInlineForm(forms.ModelForm):
    """
    Inline form pro nastavení notifikací uživatele.
    """
    def __init__(self, *args, **kwargs):
        super(UserNotificationTypeInlineForm, self).__init__(*args, **kwargs)
        self.fields['usernotificationtype'].queryset = UserNotificationType.objects.filter(
            Q(ident_cely__icontains='S-E-')
            |Q(ident_cely='E-U-04')
        )

class UserNotificationTypeInlineFormset(forms.models.BaseInlineFormSet):
    model = UserNotificationType.user.through

    def __init__(self, *args, **kwargs):
        super(UserNotificationTypeInlineFormset, self).__init__(*args, **kwargs)
        logger.debug(self.data)
        if not self.instance.pk and not self.data: 
            notification_ids = UserNotificationType.objects.filter(
                Q(ident_cely__icontains='S-E-')
            ).values_list('id', flat=True)
            logger.debug(self.initial)
            self.initial = []
            for id in notification_ids:
                self.initial.append({'usernotificationtype': id, })


class UserNotificationTypeInline(admin.TabularInline):
    """
    Inline panel pro nastavení notifikací uživatele.
    """
    model = UserNotificationType.user.through
    form = UserNotificationTypeInlineForm
    formset = UserNotificationTypeInlineFormset

    def get_queryset(self, request):
        logger.debug(self.model._default_manager)
        queryset = super(UserNotificationTypeInline, self).get_queryset(request)
        queryset = queryset.filter(
            Q(usernotificationtype__ident_cely__icontains='S-E-')
            |Q(usernotificationtype__ident_cely='E-U-04')
        )
        return queryset
    
    def get_extra(self, request, obj=None, **kwargs):
        extra = 1  #default 0
        if not obj: #new create only
            extra = UserNotificationType.objects.filter(
                Q(ident_cely__icontains='S-E-')
            ).count()
        return extra

    def __init__(self, parent_model, admin_site):
        super(UserNotificationTypeInline, self).__init__(parent_model, admin_site)


class PesNotificationTypeInline(admin.TabularInline):
    """
    Inline panel pro nastavení hlídacích psů uživatele.
    """
    model_type = None
    model = Pes
    form = create_pes_form(model_typ=model_type)
    form.admin_app = True

    def get_queryset(self, request):
        queryset = super(PesNotificationTypeInline, self).get_queryset(request)
        queryset = queryset.filter(
            content_type__model=self.model_type
        )
        return queryset


class PesKrajNotificationTypeInline(PesNotificationTypeInline):
    """
    Inline panel pro nastavení hlídacích psů uživatele pro kraj.
    """
    model_type = KRAJ_CONTENT_TYPE
    form = create_pes_form(model_typ=model_type)
    form.admin_app = True
    verbose_name = _("uzivatel.admin.form.notifikace.kraj")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.kraje")


class PesOkresNotificationTypeInline(PesNotificationTypeInline):
    """
    Inline panel pro nastavení hlídacích psů uživatele pro okres.
    """
    model_type = OKRES_CONTENT_TYPE
    form = create_pes_form(model_typ=model_type)
    form.admin_app = True
    verbose_name = _("uzivatel.admin.form.notifikace.okres")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.okresy")


class PesKatastrNotificationTypeInline(PesNotificationTypeInline):
    """
    Inline panel pro nastavení hlídacích psů uživatele pro katastr.
    """
    model_type = KATASTR_CONTENT_TYPE
    form = create_pes_form(model_typ=model_type)
    form.admin_app = True
    verbose_name = _("uzivatel.admin.form.notifikace.katastr")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.katastry")


class CustomUserAdmin(DjangoObjectActions, UserAdmin):
    """
    Admin panel pro správu uživatele.
    """
    add_form = AuthUserCreationForm
    model = User
    list_display = ("ident_cely", "email", "is_active", "organizace", "hlavni_role", "first_name", "last_name",
                    "telefon", "date_joined", "last_login", "osoba", "is_superuser")
    list_filter = ("is_active", "organizace", "groups", "is_superuser")
    readonly_fields = ("ident_cely",)
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
    change_actions = ("metadata",)

    @action(label="Metadata", description="Download of metadata")
    def metadata(self, request, obj):
        metadata = obj.metadata

        def context_processor(content):
            yield content

        response = StreamingHttpResponse(context_processor(metadata), content_type="text/xml")
        response['Content-Disposition'] = 'attachment; filename="metadata.xml"'
        return response

    def has_delete_permission(self, request, obj=None):
        if obj:
            if Historie.objects.filter(uzivatel=obj).count() > 1000:
                return False
        return True

    def save_model(self, request, obj: User, form, change):
        fedora_transaction = FedoraTransaction()
        user = request.user
        obj.created_from_admin_panel = True
        obj.active_transaction = fedora_transaction
        invalidate_model(User)
        invalidate_model(Historie)
        logger.debug("uzivatel.admin.save_model.start",
                     extra={"user": user.pk, "obj_pk": obj.pk, "change": change, "form": form,
                            "transaction": fedora_transaction.uid})
        basic_groups_ids_list = [ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID]
        try:
            user_db = User.objects.get(id=obj.pk)
            user_db_group_ids = set(user_db.groups.values_list('id', flat=True))
        except ObjectDoesNotExist as err:
            user_db = None
            user_db_group_ids = set()
        user_db: Union[User, None]
        form_groups = form.cleaned_data["groups"]
        if obj.is_active:
            if "is_superuser" in form.cleaned_data.keys():
                if form.cleaned_data["is_superuser"]:
                    obj.is_superuser = True
                else:
                    obj.is_superuser = False
            if form_groups.filter(id=ROLE_ADMIN_ID).count() == 1:
                obj.is_staff = True
            else:
                obj.is_staff = False
        else:
            obj.is_superuser = False
            obj.is_staff = False
        super().save_model(request, obj, form, change)

        groups = form_groups.filter(id__in=basic_groups_ids_list)
        other_groups = form_groups.filter(~Q(id__in=basic_groups_ids_list))
        group_ids = groups.values_list('id', flat=True)
        all_groups_ids = form_groups.values_list('id', flat=True)
        if group_ids.count() > 0:
            max_id = max(group_ids)
        else:
            max_id = ROLE_BADATEL_ID
        main_group = Group.objects.get(pk=max_id)

        if (user_db is None
                or (set(user.groups.values_list('id', flat=True)) != set(form_groups.values_list('id', flat=True)))):
            logger.debug("uzivatel.admin.save_model.role_changed",
                         extra={"old": obj.hlavni_role, "new": form_groups.values_list('name', flat=True)})
            Historie(
                typ_zmeny=ZMENA_HLAVNI_ROLE,
                uzivatel=user,
                poznamka="role: " + ", ".join(list(form_groups.values_list('name', flat=True))),
                vazba=obj.history_vazba,
            ).save()
        changed_data_without_groups = [fieldname for fieldname in form.changed_data if fieldname != "groups"]
        if form.changed_data is not None and len([form.changed_data]) > 0:
            poznamka = ", ".join([f"{fieldname}: {form.cleaned_data[fieldname]}" for fieldname in
                                  changed_data_without_groups if "password" not in fieldname])
            if len(poznamka) > 0:
                Historie(
                    typ_zmeny=ZMENA_UDAJU_ADMIN,
                    uzivatel=user,
                    poznamka=poznamka,
                    vazba=obj.history_vazba,
                ).save()

        if user_db is not None:
            logger.debug("uzivatel.admin.save_model.manage_user_groups",
                         extra={"user": obj.pk, "user_groups": user_db.groups.values_list('id', flat=True),
                                "transaction": fedora_transaction.uid})
        if not obj.is_active:
            logger.debug("uzivatel.admin.save_model.manage_user_groups.deactivated",
                         extra={"user": obj.pk, "transaction": fedora_transaction.uid})
            transaction.on_commit(lambda: obj.groups.set([], clear=True))
            obj.save()
            fedora_transaction.mark_transaction_as_closed()
            return
        logger.debug("uzivatel.admin.save_model.manage_user_groups",
                     extra={"user": obj.pk, "group_count": groups.count(), "transaction": fedora_transaction.uid})
        if groups.count() == 0:
            logger.debug("uzivatel.admin.save_model.manage_user_groups.badatel_added",
                         extra={"user": obj.pk, "transaction": fedora_transaction.uid})
            group = Group.objects.filter(pk=ROLE_BADATEL_ID)
            transaction.on_commit(lambda: obj.groups.set([group.first()] + list(other_groups.values_list('id', flat=True)),
                                  clear=True))
            all_groups_ids = all_groups_ids.union(group.values_list('id', flat=True))
        elif groups.count() > 1:
            transaction.on_commit(lambda: obj.groups.set([max_id] + list(other_groups.values_list('id', flat=True)),
                                  clear=True))
        if user_db_group_ids != set(all_groups_ids):
            logger.debug("send activate email or change email")
            Mailer.send_eu06(user=obj, groups=[main_group] + list(other_groups))
        logger.debug("uzivatel.admin.save_model.manage_user_groups.highest_groups",
                     extra={"user": obj.pk, "user_groups": obj.groups.values_list('id', flat=True),
                            "transaction": fedora_transaction.uid})
        logger.debug("uzivatel.admin.save_model.manage_user_groups",
                     extra={"max_id": max_id, "hlavni_role_pk": obj.hlavni_role.pk,
                            "transaction": fedora_transaction.uid})
        obj.close_active_transaction_when_finished = True
        obj.save()

    def user_change_password(self, request, id, form_url=""):
        if request.method == "POST":
            user = self.get_object(request, unquote(id))
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                Historie(
                    typ_zmeny=ZMENA_HESLA_ADMIN,
                    uzivatel=user,
                    vazba=user.history_vazba,
                ).save()
        return super(CustomUserAdmin, self).user_change_password(request, id, form_url=form_url)

    def log_deletion(self, request, object, object_repr):
        object.deleted_by_user = request.user
        super().log_deletion(request, object, object_repr)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request,obj)
        if obj:
            if request.user.ident_cely == obj.ident_cely:
                return fields+("is_superuser",)
        return fields


class CustomGroupAdmin(admin.ModelAdmin):
    """
    Admin panel pro správu uživatelskych skupin.
    """
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
