import logging
from typing import Union

from core.constants import (
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    ROLE_BADATEL_ID,
    ZMENA_HESLA_ADMIN,
    ZMENA_HLAVNI_ROLE,
    ZMENA_UDAJU_ADMIN,
)
from core.repository_connector import FedoraTransaction
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django_object_actions import DjangoObjectActions
from historie.models import Historie
from notifikace_projekty.forms import (
    KATASTR_CONTENT_TYPE,
    KRAJ_CONTENT_TYPE,
    OKRES_CONTENT_TYPE,
    PES_NOTIFICATIONS,
    create_pes_form,
)
from notifikace_projekty.models import Pes
from services.mailer import Mailer

from .forms import AuthUserChangeAdminForm, AuthUserCreationForm
from .models import User, UserNotificationType

logger = logging.getLogger(__name__)


class UserNotificationTypeInlineForm(forms.ModelForm):
    """
    Inline form pro nastavení notifikací uživatele.
    """

    def __init__(self, *args, **kwargs):
        super(UserNotificationTypeInlineForm, self).__init__(*args, **kwargs)
        self.fields["usernotificationtype"].queryset = UserNotificationType.objects.filter(
            Q(ident_cely__icontains="S-E-A")
            | Q(ident_cely__icontains="S-E-N")
            | Q(ident_cely__icontains="S-E-K")
            | Q(ident_cely="E-U-04")
            | Q(ident_cely="zpravodaj")
        )


class UserNotificationTypeInlineFormset(forms.models.BaseInlineFormSet):
    model = UserNotificationType.user.through

    def __init__(self, *args, **kwargs):
        super(UserNotificationTypeInlineFormset, self).__init__(*args, **kwargs)
        if not self.instance.pk and not self.data:
            notification_ids = UserNotificationType.objects.filter(
                Q(ident_cely__icontains="S-E-A")
                | Q(ident_cely__icontains="S-E-N")
                | Q(ident_cely__icontains="S-E-K")
                | Q(ident_cely="zpravodaj")
            ).values_list("id", flat=True)
            self.initial = []
            for id in notification_ids:
                self.initial.append(
                    {
                        "usernotificationtype": id,
                    }
                )


class UserNotificationTypeInline(admin.TabularInline):
    """
    Inline panel pro nastavení notifikací uživatele.
    """

    model = UserNotificationType.user.through
    form = UserNotificationTypeInlineForm
    formset = UserNotificationTypeInlineFormset
    verbose_name = _("uzivatel.admin.form.notifikace.user")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.user")

    def get_queryset(self, request):
        logger.debug(self.model._default_manager)
        queryset = super(UserNotificationTypeInline, self).get_queryset(request)
        queryset = queryset.filter(
            Q(usernotificationtype__ident_cely__icontains="S-E-A")
            | Q(usernotificationtype__ident_cely__icontains="S-E-N")
            | Q(usernotificationtype__ident_cely__icontains="S-E-K")
            | Q(usernotificationtype__ident_cely="E-U-04")
            | Q(usernotificationtype__ident_cely="zpravodaj")
        )
        return queryset

    def get_extra(self, request, obj=None, **kwargs):
        extra = 1  # Výchozí hodnota je 0.
        if not obj:  # pouze při vytváření nového záznamu
            extra = UserNotificationType.objects.filter(
                Q(ident_cely__icontains="S-E-A")
                | Q(ident_cely__icontains="S-E-N")
                | Q(ident_cely__icontains="S-E-K")
                | Q(ident_cely="zpravodaj")
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
        queryset = queryset.filter(content_type__model=self.model_type)
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


class PesUserNotificationTypeInlineForm(forms.ModelForm):
    """
    Inline form pro nastavení notifikací uživatele.
    """

    def __init__(self, *args, **kwargs):
        super(PesUserNotificationTypeInlineForm, self).__init__(*args, **kwargs)
        self.fields["usernotificationtype"].queryset = UserNotificationType.objects.filter(
            Q(ident_cely__in=PES_NOTIFICATIONS)
        )


class PesUserNotificationTypeInlineFormset(forms.models.BaseInlineFormSet):
    model = UserNotificationType.user.through

    def __init__(self, *args, **kwargs):
        super(PesUserNotificationTypeInlineFormset, self).__init__(*args, **kwargs)
        if not self.instance.pk and not self.data:
            notification_ids = UserNotificationType.objects.filter(Q(ident_cely__in=PES_NOTIFICATIONS)).values_list(
                "id", flat=True
            )
            self.initial = []
            for id in notification_ids:
                self.initial.append(
                    {
                        "usernotificationtype": id,
                    }
                )


class PesUserNotificationTypeInline(admin.TabularInline):
    """
    Inline panel pro nastavení notifikací uživatele.
    """

    model = UserNotificationType.user.through
    form = PesUserNotificationTypeInlineForm
    formset = PesUserNotificationTypeInlineFormset
    verbose_name = _("uzivatel.admin.form.notifikace.pes")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.psy")

    def get_queryset(self, request):
        logger.debug(self.model._default_manager)
        queryset = super(PesUserNotificationTypeInline, self).get_queryset(request)
        queryset = queryset.filter(Q(usernotificationtype__ident_cely__in=PES_NOTIFICATIONS))
        return queryset

    def get_extra(self, request, obj=None, **kwargs):
        extra = 1  # Výchozí hodnota je 0.
        if not obj:  # pouze při vytváření nového záznamu
            extra = UserNotificationType.objects.filter(Q(ident_cely__in=PES_NOTIFICATIONS)).count()
        return extra


class CustomUserAdmin(DjangoObjectActions, UserAdmin):
    """
    Admin panel pro správu uživatele.
    """

    add_form = AuthUserCreationForm
    form = AuthUserChangeAdminForm
    model = User
    list_display = (
        "ident_cely",
        "email",
        "is_active",
        "organizace",
        "hlavni_role",
        "first_name",
        "last_name",
        "telefon",
        "date_joined",
        "last_login",
        "osoba",
        "is_superuser",
    )
    list_filter = ("is_active", "organizace", "groups", "is_superuser")
    readonly_fields = ("ident_cely",)
    inlines = [
        UserNotificationTypeInline,
        PesUserNotificationTypeInline,
        PesKrajNotificationTypeInline,
        PesOkresNotificationTypeInline,
        PesKatastrNotificationTypeInline,
    ]
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
                    "osoba",
                    "orcid",
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
                    "osoba",
                    "orcid",
                    "groups",
                ),
            },
        ),
    )
    search_fields = (
        "email",
        "organizace__nazev_zkraceny",
        "ident_cely",
        "first_name",
        "last_name",
        "telefon",
        "orcid",
    )
    ordering = ("email",)
    change_form_template = "admin/admin_user_change.html"

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
        logger.debug(
            "uzivatel.admin.save_model.start",
            extra={
                "number": user.pk,
                "pk": obj.pk,
                "change": change,
                "transaction": fedora_transaction.uid,
            },
        )
        basic_groups_ids_list = [ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID]
        try:
            user_db = User.objects.get(id=obj.pk)
            user_db_group_ids = set(user_db.groups.values_list("id", flat=True))
        except ObjectDoesNotExist:
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
        group_ids = groups.values_list("id", flat=True)
        all_groups_ids = form_groups.values_list("id", flat=True)
        if group_ids.count() > 0:
            max_id = max(group_ids)
        else:
            max_id = ROLE_BADATEL_ID
        main_group = Group.objects.get(pk=max_id)

        if user_db is None or (
            set(user.groups.values_list("id", flat=True)) != set(form_groups.values_list("id", flat=True))
        ):
            logger.debug(
                "uzivatel.admin.save_model.role_changed",
                extra={"old": obj.hlavni_role, "new": form_groups.values_list("name", flat=True)},
            )
            Historie(
                typ_zmeny=ZMENA_HLAVNI_ROLE,
                uzivatel=user,
                poznamka="role: " + ", ".join(list(form_groups.values_list("name", flat=True))),
                vazba=obj.history_vazba,
            ).save()
        changed_data_without_groups = [fieldname for fieldname in form.changed_data if fieldname != "groups"]
        if form.changed_data is not None and len([form.changed_data]) > 0:
            poznamka = ", ".join(
                [
                    f"{fieldname}: {form.cleaned_data[fieldname]}"
                    for fieldname in changed_data_without_groups
                    if "password" not in fieldname
                ]
            )
            if len(poznamka) > 0:
                Historie(
                    typ_zmeny=ZMENA_UDAJU_ADMIN,
                    uzivatel=user,
                    poznamka=poznamka,
                    vazba=obj.history_vazba,
                ).save()

        if user_db is not None:
            logger.debug(
                "uzivatel.admin.save_model.manage_user_groups",
                extra={
                    "pk": obj.pk,
                    "value": user_db.groups.values_list("id", flat=True),
                    "transaction": fedora_transaction.uid,
                },
            )
        if not obj.is_active:
            logger.debug(
                "uzivatel.admin.save_model.manage_user_groups.deactivated",
                extra={"pk": obj.pk, "transaction": fedora_transaction.uid},
            )
            group = Group.objects.get(pk=ROLE_BADATEL_ID)
            transaction.on_commit(lambda: obj.groups.set([group], clear=True))
            obj.save()
            fedora_transaction.mark_transaction_as_closed()
            return
        logger.debug(
            "uzivatel.admin.save_model.manage_user_groups",
            extra={"pk": obj.pk, "count": groups.count(), "transaction": fedora_transaction.uid},
        )
        if groups.count() == 0:
            logger.debug(
                "uzivatel.admin.save_model.manage_user_groups.badatel_added",
                extra={"pk": obj.pk, "transaction": fedora_transaction.uid},
            )
            group = Group.objects.filter(pk=ROLE_BADATEL_ID)
            transaction.on_commit(
                lambda: obj.groups.set([group.first()] + list(other_groups.values_list("id", flat=True)), clear=True)
            )
            all_groups_ids = all_groups_ids.union(group.values_list("id", flat=True))
        elif groups.count() > 1:
            transaction.on_commit(
                lambda: obj.groups.set([max_id] + list(other_groups.values_list("id", flat=True)), clear=True)
            )
        if (user_db_group_ids != set(all_groups_ids) or user_db.is_active != obj.is_active) and obj.is_active:
            logger.debug("uzivatel.admin.save_model.send_activation_email", extra={"pk": obj.pk})
            Mailer.send_eu06(user=obj, groups=[main_group] + list(other_groups))
        logger.debug(
            "uzivatel.admin.save_model.manage_user_groups.highest_groups",
            extra={
                "pk": obj.pk,
                "value": obj.groups.values_list("id", flat=True),
                "transaction": fedora_transaction.uid,
            },
        )
        logger.debug(
            "uzivatel.admin.save_model.manage_user_groups",
            extra={"count": max_id, "pk": obj.hlavni_role.pk, "transaction": fedora_transaction.uid},
        )
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
        fields = super().get_readonly_fields(request, obj)
        if obj:
            if request.user.ident_cely == obj.ident_cely:
                return fields + ("is_superuser",)
        return fields

    def render_change_form(self, request, context, **kwargs):
        object_id = request.resolver_match.kwargs.get("object_id")
        user_account_history, user_account_other_records = self.get_histore_related_records(object_id)
        context.update(
            {
                "show_delete_history_button": True,
                "object_id": object_id,
                "user_account_history_exists": user_account_history.exists() if user_account_history else None,
                "user_account_other_records_exists": (
                    user_account_other_records.exists() if user_account_other_records else None
                ),
            }
        )
        return super().render_change_form(request, context, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/delete-history-records",
                self.admin_site.admin_view(self.delete_history_records),
                name="delete_history_records",
            ),
        ]
        return custom_urls + urls

    def get_histore_related_records(self, object_id):
        if User.objects.filter(pk=object_id).exists():
            uzivatel = User.objects.get(pk=object_id)
            history = Historie.objects.filter(uzivatel=uzivatel)
            user_account_history = history.filter(vazba=uzivatel.history_vazba)
            user_account_other_records = history.filter(~Q(id__in=(user_account_history.values_list("id", flat=True))))
            return user_account_history, user_account_other_records
        else:
            return None, None

    def delete_history_records(self, request, object_id, *args, **kwargs):
        user_account_history, user_account_other_records = self.get_histore_related_records(object_id)
        obj: User = self.get_object(request, object_id)
        if request.method == "GET":
            context = {
                **self.admin_site.each_context(request),
                "opts": self.model._meta,
                "object": obj,
                "user_account_history": user_account_history,
                "user_account_other_records": user_account_other_records,
            }
            return TemplateResponse(request, "admin/admin_user_change_delete_history_records.html", context)
        else:
            if user_account_history is not None and user_account_other_records is not None:
                if user_account_other_records.exists():
                    self.message_user(
                        request,
                        _("uzivatel.admin.CustomUserAdmin.delete_history_records.cannot_delete"),
                        messages.ERROR,
                    )
                else:
                    obj.active_transaction = FedoraTransaction()
                    user_account_history.delete()
                    obj.close_active_transaction_when_finished = True
                    obj.save()
                    self.message_user(
                        request, _("uzivatel.admin.CustomUserAdmin.delete_history_records.success"), messages.SUCCESS
                    )
            change_url = reverse("admin:uzivatel_user_change", args=[object_id])
            return HttpResponseRedirect(change_url)

    def delete_model(self, request, obj):
        with transaction.atomic():
            pes_set = obj.pes_set.all()
            for item in pes_set:
                item: Pes
                item.suppress_signal = True
                item.delete()
        super().delete_model(request, obj)


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
