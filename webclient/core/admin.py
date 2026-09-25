import csv
import json
import logging
import random
import string

import pandas as pd
from bs4 import BeautifulSoup
from core.services import PermissionService
from django.conf import settings
from django.contrib import admin, messages
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import gettext as _
from uzivatel.models import User

from .connectors import RedisConnector
from .constants import ROLE_NASTAVENI_ODSTAVKY
from .exceptions import WrongCSVError, WrongSheetError
from .forms import OdstavkaSystemuForm, PermissionImportForm, PermissionSkipImportForm
from .import_maintenance import (
    MaintenanceImportConflict,
    ensure_maintenance_change_allowed,
    import_is_protected,
    lock_maintenance_configuration,
)
from .models import OdstavkaSystemu, Permissions, PermissionsSkip
from .setting_models import CustomAdminSettings

logger = logging.getLogger(__name__)


class OdstavkaSystemuAdmin(admin.ModelAdmin):
    """
    Třída admin panelu pro zobrazení odstávek systému.

    Pomocí ní se zobrazuje tabulka s odstávkami, detail a jednotlivé akce.
    """

    change_list_template = "core/odstavky_changelist.html"
    list_display = (
        "info_od",
        "datum_odstavky",
        "cas_odstavky",
        "status",
    )
    form = OdstavkaSystemuForm

    def _maintenance_conflict_response(self, request, exc):
        """Zobrazí chybu konfliktu odstávky s importem a vrátí přesměrování.

        :param request: HTTP požadavek administrace.
        :param exc: Výjimka oznamující konflikt odstávky s importem.
        :return: Přesměrování zpět na aktuální stránku administrace.
        """
        self.message_user(request, str(exc), messages.ERROR)
        return redirect(request.path)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Zobrazí odmítnutí ukončení odstávky jako zprávu administrátorovi.

        :param request: HTTP požadavek administrace.
        :param object_id: Identifikátor upravované odstávky.
        :param form_url: Cílová URL formuláře.
        :param extra_context: Dodatečný kontext šablony.
        :return: Formulář nebo přesměrování se zprávou po odmítnuté změně.
        """
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except MaintenanceImportConflict as exc:
            return self._maintenance_conflict_response(request, exc)

    def delete_view(self, request, object_id, extra_context=None):
        """Zobrazí důvod odmítnutého smazání odstávky.

        :param request: HTTP požadavek administrace.
        :param object_id: Identifikátor mazané odstávky.
        :param extra_context: Dodatečný kontext šablony.
        :return: Potvrzení smazání nebo přesměrování se zprávou.
        """
        try:
            return super().delete_view(request, object_id, extra_context)
        except MaintenanceImportConflict as exc:
            return self._maintenance_conflict_response(request, exc)

    def response_action(self, request, queryset):
        """Zobrazí důvod odmítnutého hromadného smazání odstávek.

        :param request: HTTP požadavek administrace.
        :param queryset: Řádky vybrané pro akci.
        :return: Odpověď akce nebo přesměrování se zprávou.
        """
        try:
            with transaction.atomic():
                return super().response_action(request, queryset)
        except MaintenanceImportConflict as exc:
            return self._maintenance_conflict_response(request, exc)

    @transaction.atomic
    def delete_model(self, request, obj):
        """Smaže odstávku pouze po ověření, že nechrání běžící import.

        :param request: HTTP požadavek administrace.
        :param obj: Odstávka určená ke smazání.
        :raises MaintenanceImportConflict: Odstávka chrání import.
        """
        import_protected = import_is_protected()
        for current in lock_maintenance_configuration():
            if current.pk == obj.pk:
                ensure_maintenance_change_allowed(current, import_protected=import_protected)
        super().delete_model(request, obj)
        transaction.on_commit(lambda: cache.delete("maintenance"))

    @transaction.atomic
    def delete_queryset(self, request, queryset):
        """Ověří všechny odstávky před hromadným smazáním.

        :param request: HTTP požadavek administrace.
        :param queryset: Odstávky vybrané ke smazání.
        :raises MaintenanceImportConflict: Některá odstávka chrání import.
        """
        import_protected = import_is_protected()
        configurations = lock_maintenance_configuration()
        selected_ids = set(queryset.values_list("pk", flat=True))
        for current in configurations:
            if current.pk in selected_ids:
                ensure_maintenance_change_allowed(current, import_protected=import_protected)
        super().delete_queryset(request, queryset)
        transaction.on_commit(lambda: cache.delete("maintenance"))

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """
        Metoda na uložení modelu odstávky.

        Texty odstávky se uloží do modelu a texty chybových stránek se zapíší
        do příslušných šablon proxy.

        :param request: Parametr ``request`` se předává do volání ``int()``, ``utime()``, pracuje se s atributy ``environ``.
        :param obj: Parametr ``obj`` předává se do volání ``save_model()``.
        :param form: Parametr ``form`` se předává do volání ``file_handler()``, ``save_model()``, pracuje se s atributy ``cleaned_data``.
        :param change: Parametr ``change`` se předává do volání ``save_model()``.
        """
        import_protected = import_is_protected()
        for current in lock_maintenance_configuration():
            if current.pk == obj.pk:
                ensure_maintenance_change_allowed(current, obj, import_protected)
        for code, language_code in settings.LANGUAGES:
            self.file_handler(code, form)
        cache.delete("maintenance")
        super().save_model(request, obj, form, change)
        transaction.on_commit(lambda: cache.delete("maintenance"))

    def has_module_permission(self, request):
        """
        Metoda pro určení práv na modul oSdstávky.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_view_permission(self, request, obj=None, *args):
        """
        Metoda pro určení práv na videní odstávky.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
        :param obj: Volitelný objekt modelu, na který se oprávnění vztahuje (není využit).
        :param args: Další poziční argumenty (nejsou využity).

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_add_permission(self, request, *args):
        """
        Metoda pro určení práv na přidání odstávky. Není možné přidat více než jednu odstávku.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
        :param args: Další poziční argumenty (nejsou využity).

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if OdstavkaSystemu.objects.count() > 0:
            return False
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_change_permission(self, request, obj=None, *args):
        """
        Metoda pro určení práv pro úpravu odstávky.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
        :param obj: Volitelný objekt modelu, na který se oprávnění vztahuje (není využit).
        :param args: Další poziční argumenty (nejsou využity).

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def file_handler(self, language, form):
        """
        Pomocní metoda pro úpravu template zobrazených během odstávky.

        :param language: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.
        :param form: Parametr ``form`` se předává do volání ``replace_with()``, pracuje se s atributy ``cleaned_data``.
        """
        with open("/vol/web/nginx/data/" + language + "/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
            p_tag = soup.find("p")
            if p_tag:
                p_tag.string = form.cleaned_data["error_text_" + language]
        with open("/vol/web/nginx/data/" + language + "/custom_503.html", "w") as fp:
            fp.write(str(soup))
        with open("/vol/web/nginx/data/" + language + "/oznameni/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
            p_tag = soup.find("p")
            if p_tag:
                p_tag.string = form.cleaned_data["error_text_oznam_" + language]
        with open("/vol/web/nginx/data/" + language + "/oznameni/custom_503.html", "w") as fp:
            fp.write(str(soup))


admin.site.register(OdstavkaSystemu, OdstavkaSystemuAdmin)


class CustomAdminSettingsAdmin(admin.ModelAdmin):
    """Admin panel pro vlastních nastavení."""

    change_list_template = "core/custom_settings_changelist.html"
    model = CustomAdminSettings
    list_display = ("item_id", "item_group")


admin.site.register(CustomAdminSettings, CustomAdminSettingsAdmin)


@admin.register(Permissions)
class PermissionAdmin(admin.ModelAdmin):
    """Třída admin panelu pro zobrazení a správu oprávnení."""

    change_list_template = "core/permissions_changelist.html"
    list_display = ["address_in_app", "main_role", "action", "base", "status", "ownership", "accessibility"]
    list_filter = ["main_role"]
    search_fields = ["address_in_app", "action"]

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, str] | None = None) -> HttpResponse:
        """
        Zobrazí přehledovou stránku oprávnění s přidaným příznakem pro zobrazení tlačítka importu.

        :param request: HTTP požadavek od klienta.
        :param extra_context: Volitelný slovník s dalším kontextem předaným do šablony.

        :return: HTTP odpověď s vyrenderovanou šablonou přehledové stránky.
        """
        return super().changelist_view(request, {"import_list": True})

    def get_urls(self):
        """
        Metoda pri definici dodatečných url.

        :return: Vrací hodnotu podle větve zpracování.
        """
        urls = super().get_urls()
        my_urls = [
            path("import_file/", self.admin_site.admin_view(self.import_file), name="import_permissions"),
            path(
                "import_success/",
                self.admin_site.admin_view(self.import_success),
                name="import_success",
            ),
            path(
                "reload_permissions/",
                self.admin_site.admin_view(self.reload_permissions),
                name="reload_permissions",
            ),
        ]
        return my_urls + urls

    def import_file(self, request):
        """
        Metoda view pro zobrazení formuláře a samtotný import oprávnení z excelu.

        :param request: Parametr ``request`` se předává do volání ``message_user()``, ``each_context()``, pracuje se s atributy ``method``, ``FILES``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.
        """
        model = self.model
        opts = model._meta
        app_label = "core"
        if request.method == "POST":
            docfile = request.FILES["file"]
            try:
                sheet, missing = PermissionService().run(docfile)
            except WrongCSVError as err:
                logger.error("core.admin.permissionAdmin.wrongCSVConfiguration.error", extra={"error": err})
                self.message_user(
                    request,
                    _("core.admin.permissionAdmin.wrongCSVConfiguration.error"),
                    messages.ERROR,
                )
                return redirect(reverse("admin:core_permissions_changelist"))
            except WrongSheetError as err:
                logger.error("core.admin.permissionAdmin.wrongSheetConfiguration.error", extra={"error": err})
                self.message_user(
                    request,
                    _("core.admin.permissionAdmin.wrongSheetConfiguration.error"),
                    messages.ERROR,
                )
                return redirect(reverse("admin:core_permissions_changelist"))
            except ValueError as err:
                logger.error("core.admin.permissionAdmin.ValueError.error", extra={"error": err})
                self.message_user(
                    request,
                    _("core.admin.permissionAdmin.wrongSheet.error"),
                    messages.ERROR,
                )
                return redirect(reverse("admin:core_permissions_changelist"))
            cache.set("import_missing_results", missing, 120)
            json_sheet = sheet.to_json(orient="records")
            cache.set("import_json_results", json_sheet, 120)
            return redirect(reverse("admin:import_success"))
        form = PermissionImportForm()
        media = self.media
        payload = {
            **self.admin_site.each_context(request),
            "title": _("core.admin.permissionAdmin.title"),
            "form": form,
            "media": media,
        }
        payload.update(
            {
                "app_label": app_label,
                "opts": opts,
            }
        )
        return TemplateResponse(
            request,
            "core/permission_import_form.html",
            payload,
        )

    def import_success(self, request):
        """
        Metoda view pro zobrazení tabulky s výsledkom importu.

        :param request: Parametr ``request`` se předává do volání ``each_context()``, ``message_user()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.
        """
        json_table = cache.get("import_json_results")
        missing_urls = cache.get("import_missing_results")
        cache.delete("import_json_results")
        cache.delete("import_missing_results")
        if not json_table:
            return redirect(reverse("admin:core_permissions_changelist"))
        table = json.loads(json_table)
        model = self.model
        opts = model._meta
        app_label = "core"
        media = self.media
        payload = {
            **self.admin_site.each_context(request),
            "title": _("core.admin.permissionAdmin.title.success"),
            "table": table,
            "media": media,
            "missing_urls": missing_urls,
        }
        payload.update(
            {
                "app_label": app_label,
                "opts": opts,
            }
        )
        self.message_user(request, _("core.admin.permissionAdmin.uploadSucces"))
        return TemplateResponse(
            request,
            "core/permission_import_success.html",
            payload,
        )

    def reload_permissions(self, request):
        """
        Metoda view pro automatický import oprávnění z csv v gitu a zobrazení výsledků importu.

        :param request: Parametr ``request`` se předává do volání ``message_user()``, ``each_context()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.
        """
        with open("core/resources/uzivatelska_prava.csv", "rb") as f:
            permission_file = SimpleUploadedFile(
                name="uzivatelska_prava.csv",
                content=f.read(),
                content_type="application/csv",
            )
        try:
            sheet, missing_urls = PermissionService().run(permission_file)
        except WrongCSVError as err:
            logger.error("core.admin.permissionAdmin.wrongCSVConfiguration.error", extra={"error": err})
            self.message_user(
                request,
                _("core.admin.permissionAdmin.wrongCSVConfiguration.error"),
                messages.ERROR,
            )
            return redirect(reverse("admin:core_permissions_changelist"))
        table = sheet.to_dict(orient="records")
        model = self.model
        opts = model._meta
        app_label = "core"
        media = self.media
        payload = {
            **self.admin_site.each_context(request),
            "title": _("core.admin.permissionAdmin.title.success"),
            "table": table,
            "media": media,
            "missing_urls": missing_urls,
        }
        payload.update(
            {
                "app_label": app_label,
                "opts": opts,
            }
        )
        self.message_user(request, _("core.admin.permissionAdmin.uploadSucces"))
        return TemplateResponse(
            request,
            "core/permission_import_success.html",
            payload,
        )


@admin.register(PermissionsSkip)
class PermissionSkipAdmin(admin.ModelAdmin):
    """Třída admin panelu pro zobrazení a správu proskakovani oprávnení."""

    change_list_template = "core/permissions_changelist.html"
    list_display = ["user"]
    actions = ("export_as_csv",)
    search_fields = ["user__ident_cely", "user__last_name", "user__first_name"]
    autocomplete_fields = ["user"]

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, str] | None = None) -> HttpResponse:
        """
        Zobrazí přehledovou stránku výjimek oprávnění s přidaným příznakem pro zobrazení tlačítka importu.

        :param request: HTTP požadavek od klienta.
        :param extra_context: Volitelný slovník s dalším kontextem předaným do šablony.

        :return: HTTP odpověď s vyrenderovanou šablonou přehledové stránky.
        """
        return super().changelist_view(request, {"import_skip_list": True})

    def get_urls(self):
        """
        Metoda pri definici dodatečných url.

        :return: Vrací hodnotu podle větve zpracování.
        """
        urls = super().get_urls()
        my_urls = [
            path(
                "import_skip_file/", self.admin_site.admin_view(self.import_skip_file), name="import_permissions_skip"
            ),
            path(
                "import_skip_success/",
                self.admin_site.admin_view(self.import_skip_success),
                name="import_skip_success",
            ),
        ]
        return my_urls + urls

    def validate_sheet(self, sheet):
        """
        Metoda pro validaci importovaného excelu a jeho úpravu.

        :param sheet: Parametr ``sheet`` pracuje se s atributy ``columns``, ovlivňuje větvení podmínek.

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
            :raises WrongCSVError: Vyvolá se při splnění podmínky ``not sheet.columns[0] == 'IDENT_CELY' or not sheet.columns[1] == 'IDENT_LIST'``.
        """
        if not sheet.columns[0] == "IDENT_CELY" or not sheet.columns[1] == "IDENT_LIST":
            raise WrongCSVError
        return True

    def import_skip_file(self, request):
        """
        Metoda view pro zobrazení formuláře a samtotný import oprávnení z excelu.

        :param request: Parametr ``request`` se předává do volání ``message_user()``, ``each_context()``, pracuje se s atributy ``method``, ``FILES``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.
        """
        model = self.model
        opts = model._meta
        app_label = "core"
        if request.method == "POST":
            docfile = request.FILES["file"]
            try:
                sheet = pd.read_csv(docfile, sep=";")
            except ValueError as e:
                logger.debug(e)
                self.message_user(
                    request,
                    _("core.admin.permissionSkipAdmin.wrongDoc.error"),
                    messages.ERROR,
                )
                return redirect(reverse("admin:core_permissionsskip_changelist"))
            try:
                self.validate_sheet(sheet)
            except WrongCSVError as e:
                logger.debug(e)
                self.message_user(
                    request,
                    _("core.admin.permissionSkipAdmin.wrongCsvConfiguration.error"),
                    messages.ERROR,
                )
                return redirect(reverse("admin:core_permissionsskip_changelist"))
            PermissionsSkip.objects.all().delete()
            sheet["result"] = sheet.apply(self.check_save_row, axis=1)
            sheet.drop(sheet.iloc[:, 1:2], axis=1, inplace=True)
            sheet = sheet.reset_index(drop=True)
            logger.debug(sheet.info())
            json_sheet = sheet.to_json(orient="records")
            cache.set("import_json_results", json_sheet, 120)
            return redirect(reverse("admin:import_skip_success"))
        form = PermissionSkipImportForm()
        media = self.media
        payload = {
            **self.admin_site.each_context(request),
            "title": _("core.admin.permissionSkipAdmin.title.error"),
            "form": form,
            "media": media,
        }
        payload.update(
            {
                "app_label": app_label,
                "opts": opts,
            }
        )
        return TemplateResponse(
            request,
            "core/permission_import_form.html",
            payload,
        )

    def check_save_row(self, row):
        """
        Ověří save row.

        :param row: Parametr ``row`` předává se do volání ``create()``, ``get()``, pracuje se s atributy ``iloc``.

            :return: Vrací str.
        """
        try:
            PermissionsSkip.objects.create(
                user=User.objects.get(ident_cely=row.iloc[0]),
                ident_list=row.iloc[1],
            )
            return "OK"
        except Exception as e:
            logger.error(e)
            return "NOK"

    def import_skip_success(self, request):
        """
        Metoda view pro zobrazení tabulky s výsledkom importu.

        :param request: Parametr ``request`` se předává do volání ``each_context()``, ``message_user()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.
        """
        json_table = cache.get("import_json_results")
        cache.delete("import_json_results")
        if not json_table:
            return redirect(reverse("admin:core_permissions_skip_changelist"))
        table = json.loads(json_table)
        model = self.model
        opts = model._meta
        app_label = "core"
        media = self.media
        payload = {
            **self.admin_site.each_context(request),
            "title": _("core.admin.permissionSkipAdmin.title.success"),
            "table": table,
            "media": media,
        }
        payload.update(
            {
                "app_label": app_label,
                "opts": opts,
            }
        )
        self.message_user(request, _("core.admin.permissionSkipAdmin.uploadSucces"))
        return TemplateResponse(
            request,
            "core/permission_import_success.html",
            payload,
        )

    def export_as_csv(self, request, queryset):
        """
        Exportuje vybrané záznamy PermissionsSkip do CSV souboru ke stažení.

        :param request: HTTP požadavek od klienta.
        :param queryset: Queryset vybraných záznamů PermissionsSkip určených k exportu.

        :return: HTTP odpověď s CSV souborem ke stažení.
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=opravneni_override.csv"
        writer = csv.writer(response, delimiter=";")
        writer.writerow(["IDENT_CELY", "IDENT_LIST"])
        for obj in queryset:
            writer.writerow([obj.user.ident_cely, obj.ident_list])
        return response

    export_as_csv.short_description = _("core.admin.permissionSkipAdmin.downloadAction_label")


class FedoraCustomAdminSite(admin.AdminSite):
    """Implementuje komponentu ``FedoraCustomAdminSite`` v rámci aplikace."""

    redis_connector = RedisConnector().get_connection_decode()

    @staticmethod
    def _read_file(uploaded_file, context):
        """
        Načte file.

        :param uploaded_file: Parametr ``uploaded_file`` se předává do volání ``read_csv()``, ``read_excel()``, pracuje se s atributy ``content_type``, ovlivňuje větvení podmínek.
        :param context: Parametr ``context`` slouží jako vstup pro logiku funkce ``_read_file``.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        sheet = None
        if uploaded_file.content_type == "text/csv":
            try:
                sheet = pd.read_csv(uploaded_file, sep=",")
            except Exception as err:
                logger.debug(
                    "fedora_management.admin.FedoraCustomAdminSite.update_metadata_file_upload" ".cannot_read_file",
                    extra={"error": err},
                )
                context["error"] = _("fedora_management.admin.YourCustomAdminSite.cannot_read_file")
        else:
            try:
                sheet = pd.read_excel(uploaded_file)
            except Exception as err:
                logger.debug(
                    "fedora_management.admin.FedoraCustomAdminSite.update_metadata_file_upload" ".cannot_read_file",
                    extra={"error": err},
                )
                context["error"] = _("fedora_management.admin.YourCustomAdminSite.cannot_read_file")
        if not isinstance(sheet, pd.DataFrame):
            return None
        if sheet.shape[1] != 1:
            context["error"] = _("fedora_management.admin.YourCustomAdminSite.too_many_columns")
            return None
        sheet.columns = [
            "ident_cely",
        ]
        sheet["ident_cely"] = sheet["ident_cely"].astype(str).str.strip()
        sheet = sheet[sheet["ident_cely"] != ""]
        sheet = sheet.set_index("ident_cely")
        return sheet

    def update_doi(self, request):
        """
        Aktualizuje doi. v aplikaci.

        :param request: Parametr ``request`` předává se do volání ``get_app_list()``, ``each_context()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací výsledek volání ``TemplateResponse()``.
        """
        from pid.forms import UpdateDocumentObjectIdentifierFileForm

        context = {
            "app_list": self.get_app_list(request),
            **self.each_context(request),
        }
        if request.method == "POST" and request.user.is_superuser:
            form = UpdateDocumentObjectIdentifierFileForm(request.POST, request.FILES)
            context["form"] = form
            if form.is_valid():
                uploaded_file = request.FILES["ident_list_file"]
                sheet = self._read_file(uploaded_file, context)
                if isinstance(sheet, pd.DataFrame):
                    job_id = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
                    job_id = f"update_pid_{job_id}"
                    self.redis_connector.set(job_id, "0;" + ";".join(sheet.index.unique().tolist()))
                    performed_action = form.cleaned_data["performed_action"]
                    context["url"] = reverse("pid:continue-processing", args=[job_id, performed_action])
            return TemplateResponse(request, "admin/update_running_job.html", context)
        else:
            context["form"] = UpdateDocumentObjectIdentifierFileForm()
        return TemplateResponse(request, "admin/doi_management/update_doi.html", context)

    def update_metadata_file_upload(self, request):
        """
        Aktualizuje metadata file upload.

        :param request: Parametr ``request`` předává se do volání ``get_app_list()``, ``each_context()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací výsledek volání ``TemplateResponse()``.
        """
        from fedora_management.forms import UpdateMetadataFileForm

        context = {
            "app_list": self.get_app_list(request),
            **self.each_context(request),
        }
        if request.method == "POST" and request.user.is_superuser:
            form = UpdateMetadataFileForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = request.FILES["ident_list_file"]
                sheet = self._read_file(uploaded_file, context)
                if isinstance(sheet, pd.DataFrame):
                    job_id = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
                    job_id = f"update_metadata_{job_id}"
                    self.redis_connector.set(job_id, "0;" + ";".join(sheet.index.unique().tolist()))
                    context["url"] = reverse("fedora:continue-processing", args=[job_id])
            return TemplateResponse(request, "admin/update_running_job.html", context)
        else:
            context["form"] = UpdateMetadataFileForm()
        return TemplateResponse(request, "admin/fedora_management/update_metadata.html", context)

    def get_urls(
        self,
    ):
        """Vrací urls. v aplikaci.

        :return: Vrací hodnotu podle větve zpracování.
        """
        return [
            path(
                "update-metadata/",
                self.admin_view(self.update_metadata_file_upload),
                name="update_metadata",
            ),
            path(
                "update-doi/",
                self.admin_view(self.update_doi),
                name="update_doi",
            ),
        ] + super().get_urls()
