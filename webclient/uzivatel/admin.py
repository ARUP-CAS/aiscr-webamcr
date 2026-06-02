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
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.mail import EmailMessage, get_connection
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from django_object_actions import DjangoObjectActions
from historie.models import Historie
from notifikace_projekty.forms import (
    KATASTR_CONTENT_TYPE,
    KRAJ_CONTENT_TYPE,
    OKRES_CONTENT_TYPE,
    PES_NOTIFICATIONS,
    PesInlineFormSet,
    create_pes_form,
)
from notifikace_projekty.models import Pes
from services.mailer import Mailer

from .forms import AuthUserChangeAdminForm, AuthUserCreationForm, TestEmailForm
from .models import NotificationsLog, User, UserNotificationType

logger = logging.getLogger(__name__)


class UserNotificationTypeInlineForm(forms.ModelForm):
    """Inline form pro nastavení notifikací uživatele."""

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(UserNotificationTypeInlineForm, self).__init__(*args, **kwargs)
        self.fields["usernotificationtype"].queryset = UserNotificationType.objects.filter(
            Q(ident_cely__icontains="S-E-A")
            | Q(ident_cely__icontains="S-E-N")
            | Q(ident_cely__icontains="S-E-K")
            | Q(ident_cely="E-U-04")
            | Q(ident_cely="zpravodaj")
        )


class UserNotificationTypeInlineFormset(forms.models.BaseInlineFormSet):
    """Implementuje komponentu ``UserNotificationTypeInlineFormset`` v rámci aplikace."""

    model = UserNotificationType.user.through

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
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
    """Inline panel pro nastavení notifikací uživatele."""

    model = UserNotificationType.user.through
    form = UserNotificationTypeInlineForm
    formset = UserNotificationTypeInlineFormset
    verbose_name = _("uzivatel.admin.form.notifikace.user")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.user")

    def get_queryset(self, request):
        """
        Vrací queryset. v aplikaci.

        :param request: Parametr ``request`` předává se do volání ``get_queryset()``.

            :return: Vrací proměnná ``queryset``.
        """
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
        """
        Vrací extra. v aplikaci.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_extra``.
        :param obj: Parametr ``obj`` ovlivňuje větvení podmínek.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_extra``.

            :return: Vrací proměnná ``extra``.
        """
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
        """
        Inicializuje instanci třídy.

        :param parent_model: Parametr ``parent_model`` předává se do volání ``__init__()``.
        :param admin_site: Instance administrace předaná při registraci modelu.
        """
        super(UserNotificationTypeInline, self).__init__(parent_model, admin_site)


class PesNotificationTypeInline(admin.TabularInline):
    """Inline panel pro nastavení hlídacích psů uživatele."""

    model_type = None
    model = Pes
    form = create_pes_form(model_typ=model_type)
    form.admin_app = True
    formset = PesInlineFormSet

    def get_queryset(self, request):
        """
        Vrací queryset. v aplikaci.

        :param request: Parametr ``request`` předává se do volání ``get_queryset()``.

            :return: Vrací proměnná ``queryset``.
        """
        queryset = super(PesNotificationTypeInline, self).get_queryset(request)
        queryset = queryset.filter(content_type__model=self.model_type)
        return queryset


class PesKrajNotificationTypeInline(PesNotificationTypeInline):
    """Inline panel pro nastavení hlídacích psů uživatele pro kraj."""

    model_type = KRAJ_CONTENT_TYPE
    form = create_pes_form(model_typ=model_type)
    form.admin_app = True
    verbose_name = _("uzivatel.admin.form.notifikace.kraj")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.kraje")


class PesOkresNotificationTypeInline(PesNotificationTypeInline):
    """Inline panel pro nastavení hlídacích psů uživatele pro okres."""

    model_type = OKRES_CONTENT_TYPE
    form = create_pes_form(model_typ=model_type)
    form.admin_app = True
    verbose_name = _("uzivatel.admin.form.notifikace.okres")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.okresy")


class PesKatastrNotificationTypeInline(PesNotificationTypeInline):
    """Inline panel pro nastavení hlídacích psů uživatele pro katastr."""

    model_type = KATASTR_CONTENT_TYPE
    form = create_pes_form(model_typ=model_type)
    form.admin_app = True
    verbose_name = _("uzivatel.admin.form.notifikace.katastr")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.katastry")


class PesUserNotificationTypeInlineForm(forms.ModelForm):
    """Inline form pro nastavení notifikací uživatele."""

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(PesUserNotificationTypeInlineForm, self).__init__(*args, **kwargs)
        self.fields["usernotificationtype"].queryset = UserNotificationType.objects.filter(
            Q(ident_cely__in=PES_NOTIFICATIONS)
        )


class PesUserNotificationTypeInlineFormset(forms.models.BaseInlineFormSet):
    """Implementuje komponentu ``PesUserNotificationTypeInlineFormset`` v rámci aplikace."""

    model = UserNotificationType.user.through

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
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
    """Inline panel pro nastavení notifikací uživatele."""

    model = UserNotificationType.user.through
    form = PesUserNotificationTypeInlineForm
    formset = PesUserNotificationTypeInlineFormset
    verbose_name = _("uzivatel.admin.form.notifikace.pes")
    verbose_name_plural = _("uzivatel.admin.form.notifikace.psy")

    def get_queryset(self, request):
        """
        Vrací queryset. v aplikaci.

        :param request: Parametr ``request`` předává se do volání ``get_queryset()``.

            :return: Vrací proměnná ``queryset``.
        """
        logger.debug(self.model._default_manager)
        queryset = super(PesUserNotificationTypeInline, self).get_queryset(request)
        queryset = queryset.filter(Q(usernotificationtype__ident_cely__in=PES_NOTIFICATIONS))
        return queryset

    def get_extra(self, request, obj=None, **kwargs):
        """
        Vrací extra. v aplikaci.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_extra``.
        :param obj: Parametr ``obj`` ovlivňuje větvení podmínek.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_extra``.

            :return: Vrací proměnná ``extra``.
        """
        extra = 1  # Výchozí hodnota je 0.
        if not obj:  # pouze při vytváření nového záznamu
            extra = UserNotificationType.objects.filter(Q(ident_cely__in=PES_NOTIFICATIONS)).count()
        return extra


class CustomUserAdmin(DjangoObjectActions, UserAdmin):
    """Admin panel pro správu uživatele."""

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
    autocomplete_fields = ("osoba",)
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
        """
        Určí, zda delete permission.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_delete_permission``.
        :param obj: Parametr ``obj`` předává se do volání ``filter()``, ovlivňuje větvení podmínek.

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if obj:
            if Historie.objects.filter(uzivatel=obj)[:1001].count() > 1000:
                return False
        return True

    def save_model(self, request, obj: User, form, change):
        """
        Uloží model. v aplikaci.

        :param request: Parametr ``request`` předává se do volání ``save_model()``, pracuje se s atributy ``user``.
        :param obj: Parametr ``obj`` předává se do volání ``debug()``, ``get()``, pracuje se s atributy ``created_from_admin_panel``, ``active_transaction``, ovlivňuje větvení podmínek.
        :param form: Parametr ``form`` se předává do volání ``save_model()``, ``len()``, pracuje se s atributy ``cleaned_data``, ``changed_data``, ovlivňuje větvení podmínek.
        :param change: Parametr ``change`` se předává do volání ``debug()``, ``save_model()``.
        """
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
        """
        Provádí operaci user change password.

        :param request: Parametr ``request`` předává se do volání ``get_object()``, ``change_password_form()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param id: Identifikátor zpracovávaného záznamu.
        :param form_url: Parametr ``form_url`` se předává do volání ``user_change_password()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``user_change_password()``.
        """
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

    def get_readonly_fields(self, request, obj=None):
        """
        Vrací readonly fields.

        :param request: Parametr ``request`` předává se do volání ``get_readonly_fields()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
        :param obj: Parametr ``obj`` předává se do volání ``get_readonly_fields()``, pracuje se s atributy ``ident_cely``, ovlivňuje větvení podmínek.

            :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``fields``.
        """
        fields = super().get_readonly_fields(request, obj)
        if obj:
            if request.user.ident_cely == obj.ident_cely:
                return fields + ("is_superuser",)
        return fields

    def render_change_form(self, request, context, **kwargs):
        """
        Vyrenderuje change form.

        :param request: Parametr ``request`` předává se do volání ``render_change_form()``, pracuje se s atributy ``resolver_match``, vstupuje do návratové hodnoty.
        :param context: Parametr ``context`` se předává do volání ``render_change_form()``, pracuje se s atributy ``update``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``render_change_form()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``render_change_form()``.
        """
        object_id = request.resolver_match.kwargs.get("object_id")
        user_account_history, user_account_other_records = self.get_histore_related_records(object_id)
        context.update(
            {
                "show_delete_history_button": True,
                "object_id": object_id,
                "user_account_history_exists": (
                    user_account_history.exists() if user_account_history is not None else None
                ),
                "user_account_other_records_exists": (
                    user_account_other_records.exists() if user_account_other_records is not None else None
                ),
            }
        )
        return super().render_change_form(request, context, **kwargs)

    def get_urls(self):
        """
        Vrací urls. v aplikaci.

        :return: Vrací hodnotu podle větve zpracování.
        """
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
        """
        Vrací histore related records.

        :param object_id: Identifikátor objektu ``object``.

            :return: Vrací n-tici.
        """
        if User.objects.filter(pk=object_id).exists():
            uzivatel = User.objects.get(pk=object_id)
            history = Historie.objects.filter(uzivatel=uzivatel)
            user_account_history = history.filter(vazba=uzivatel.history_vazba)
            user_account_other_records = history.exclude(vazba=uzivatel.history_vazba)
            return user_account_history, user_account_other_records
        else:
            return None, None

    def delete_history_records(self, request, object_id, *args, **kwargs):
        """
        Odstraní history records.

        :param request: Parametr ``request`` předává se do volání ``get_object()``, ``each_context()``, pracuje se s atributy ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param object_id: Identifikátor objektu ``object``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``delete_history_records``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_history_records``.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``TemplateResponse()``, výsledek volání ``HttpResponseRedirect()``.
        """
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
        """
        Odstraní model. v aplikaci.

        :param request: Parametr ``request`` předává se do volání ``delete_model()``.
        :param obj: Parametr ``obj`` předává se do volání ``delete_model()``, pracuje se s atributy ``pes_set``.
        """
        with transaction.atomic():
            pes_set = obj.pes_set.all()
            for item in pes_set:
                item: Pes
                item.suppress_signal = True
                item.delete()
        super().delete_model(request, obj)


class CustomGroupAdmin(admin.ModelAdmin):
    """Admin panel pro správu uživatelskych skupin."""

    def has_delete_permission(self, request, obj=None):
        """
        Určí, zda delete permission.

        :param request: Parametr ``request`` předává se do volání ``has_delete_permission()``, vstupuje do návratové hodnoty.
        :param obj: Parametr ``obj`` předává se do volání ``filter()``, pracuje se s atributy ``pk``, ovlivňuje větvení podmínek.

            :return: Vrací hodnotu podle větve zpracování, typicky: bool, výsledek volání ``has_delete_permission()``.
        """
        if obj is not None:
            obj: Group
            user_count = User.objects.filter(groups__id__in=[obj.pk]).count()
            if user_count >= 1:
                return False
        return super().has_delete_permission(request)


admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)


@admin.register(NotificationsLog)
class NotificationsLogAdmin(admin.ModelAdmin):
    """
    Admin panel pro kontrolu odeslaných mailů s možností poslat testovací mail.
    """

    change_list_template = "admin/notificationslog_change_list.html"
    list_display = ("created", "notification_type", "receiver_address", "user", "status_colored")
    list_filter = ("status", "created_at")
    search_fields = ("receiver_address", "exception")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50

    def created(self, obj):
        """
        Vrátí datum a čas vytvoření záznamu ve formátu pro administraci.

        :param obj: Záznam logu notifikace.
        :return: Formátovaný datum a čas vytvoření.
        """
        return localtime(obj.created_at).strftime("%d.%m.%Y %H:%M:%S")

    created.short_description = "Created at"
    created.admin_order_field = "created_at"

    def status_colored(self, obj):
        """
        Vrátí barevně zvýrazněný stav odeslání notifikace.

        :param obj: Záznam logu notifikace.
        :return: HTML reprezentace stavu notifikace.
        """
        colors = {
            "OK": "#2e7d32",
            "ERR": "#c62828",
            "SND": "#1565c0",
        }
        color = colors.get(obj.status, "#666")
        return format_html('<b style="color:{}">{}</b>', color, obj.status or "-")

    status_colored.short_description = "Status"
    status_colored.admin_order_field = "status"

    def get_readonly_fields(self, request, obj=None):
        """
        Nastaví všechna pole modelu jako read-only v detailu záznamu.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_readonly_fields``.
        :param obj: Upravovaný záznam logu notifikace.
        :return: Seznam názvů polí určených pouze ke čtení.
        """
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        """
        Zakáže ruční vytváření záznamů v administraci.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_add_permission``.
        :return: Vždy ```False```.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Zakáže mazání záznamů logu notifikací.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``has_delete_permission``.
        :param obj: Vybraný záznam logu notifikace.
        :return: Vždy ```False```.
        """
        return False

    def get_urls(self):
        """
        Přidá vlastní URL pro odeslání testovacího emailu z administrace.

        :return: Seznam URL vzorů pro tento admin.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "test-email/",
                self.admin_site.admin_view(self.test_email_view),
                name="notificationslog_test_email",
            ),
        ]
        return custom_urls + urls

    def test_email_view(self, request):
        """
        Zobrazí a zpracuje formulář pro odeslání testovacího emailu.

        :param request: Parametr ``request`` předává se do volání ``TestEmailForm()``, ``success()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :return: Odpověď s formulářem a výsledkem odeslání.

            :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.user.has_perm('uzivatel.send_test_email')``.
        """
        if not request.user.has_perm("uzivatel.send_test_email"):
            raise PermissionDenied

        result = None
        error = None

        if request.method == "POST":
            form = TestEmailForm(request.POST)
            if form.is_valid():
                to_email = form.cleaned_data["email"]
                try:
                    connection = get_connection(fail_silently=False)
                    domain = getattr(settings, "EMAIL_SERVER_DOMAIN_NAME", "")
                    msg = EmailMessage(
                        subject="AMČR - testovací email | AMCR - testing email",
                        body=f"<p>Toto je testovací email - pokud ho čteš, odesílání funguje.</p><p>Odesláno z: {domain}</p><p>This is a test email—if you're reading this, sending is working.</p><p>Sent from: {domain}</p>",
                        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                        to=[to_email],
                        connection=connection,
                    )
                    msg.content_subtype = "html"
                    sent = msg.send(fail_silently=False)

                    result = {
                        "to": to_email,
                        "sent_count": sent,
                        "backend": getattr(settings, "EMAIL_BACKEND", ""),
                        "host": getattr(settings, "EMAIL_HOST", ""),
                        "port": getattr(settings, "EMAIL_PORT", ""),
                        "use_tls": getattr(settings, "EMAIL_USE_TLS", ""),
                        "use_ssl": getattr(settings, "EMAIL_USE_SSL", ""),
                    }
                    messages.success(
                        request, _("uzivatel.admin.NotificationsLogAdmin.test_email_view.email_sent_success")
                    )
                except Exception as e:
                    error = repr(e)
                    messages.error(request, _("uzivatel.admin.NotificationsLogAdmin.test_email_view.email_sent_failed"))
        else:
            form = TestEmailForm()

        context = {
            **self.admin_site.each_context(request),
            "title": _("uzivatel.admin.NotificationsLogAdmin.test_email_view.email_test_title"),
            "form": form,
            "result": result,
            "error": error,
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/test_email.html", context)
