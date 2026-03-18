import csv
import io
import json
import logging
import os
import random
import string
import zipfile

import pandas as pd
from bs4 import BeautifulSoup
from core.services import PermissionService
from django.conf import settings
from django.contrib import admin, messages
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import gettext as _
from polib import pofile
from uzivatel.models import User

from .connectors import RedisConnector
from .constants import ROLE_NASTAVENI_ODSTAVKY
from .exceptions import WrongCSVError, WrongSheetError
from .forms import ImportDataAdminForm, OdstavkaSystemuForm, PermissionImportForm, PermissionSkipImportForm
from .import_data_mappers import (
    ImportDataError,
    ImportDataIntegrityError,
    ImportDataUnsupportedFileError,
    ImportDataUnsupportedFilesError,
    ImportDataValidationResult,
    ImportModelMapper,
    LookupImportField,
)
from .models import OdstavkaSystemu, Permissions, PermissionsSkip
from .setting_models import CustomAdminSettings
from .utils import is_maintenance_in_progress

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

    def save_model(self, request, obj, form, change):
        """
        Metoda na uložení modelu odstávky.

        Jednotlivé texty z modelu se ukladají do textú prekladů a template.
        Po uložení se restartuje wsgi pro načítaní nových prekladů.

        :param request: Parametr ``request`` se předává do volání ``int()``, ``utime()``, pracuje se s atributy ``environ``.
        :param obj: Parametr ``obj`` předává se do volání ``save_model()``.
        :param form: Parametr ``form`` se předává do volání ``file_handler()``, ``save_model()``, pracuje se s atributy ``cleaned_data``.
        :param change: Parametr ``change`` se předává do volání ``save_model()``.
        """
        locale_path = settings.LOCALE_PATHS[0]
        languages = settings.LANGUAGES
        for code, lang in languages:
            path = locale_path + "/" + code + "/LC_MESSAGES/django.po"
            po_file = pofile(path)
            entry = po_file.find("base.odstavka.text")
            text = "text_" + code
            entry.msgstr = form.cleaned_data[text]
            po_file.save()
            po_filepath, ext = os.path.splitext(path)
            po_file.save_as_mofile(po_filepath + ".mo")
            self.file_handler(code, form)
        cache.delete("maintenance")
        should_try_wsgi_reload = (
            settings.ROSETTA_WSGI_AUTO_RELOAD
            and "mod_wsgi.process_group" in request.environ
            and request.environ.get("mod_wsgi.process_group", None)
            and "SCRIPT_FILENAME" in request.environ
            and int(request.environ.get("mod_wsgi.script_reloading", 0))
        )
        if should_try_wsgi_reload:
            try:
                os.utime(request.environ.get("SCRIPT_FILENAME"), None)
            except OSError:
                pass
        # Try auto-reloading via uwsgi daemon reload mechanism
        if settings.ROSETTA_UWSGI_AUTO_RELOAD:
            try:
                import uwsgi

                uwsgi.reload()  # pretty easy right?
            except Exception as e:
                logger.debug("core.admin.OdstavkaSystemuAdmin.exception", extra={"exception": e})
                pass  # aplikace nemusí běžet pod uWSGI.
        super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        """
        Metoda pro určení práv na modul odstávky.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_view_permission(self, request, obj=None, *args):
        """
        Metoda pro určení práv na videní odstávky.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
        :param obj: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_view_permission``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``has_view_permission``.

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_add_permission(self, request, *args):
        """
        Metoda pro určení práv na přidání odstávky. Není možné přidat více než jednu odstávku.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``has_add_permission``.

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if OdstavkaSystemu.objects.count() > 0:
            return False
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_change_permission(self, request, obj=None, *args):
        """
        Metoda pro určení práv pro úpravu odstávky.

        :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
        :param obj: Parametr ``obj`` slouží jako vstup pro logiku funkce ``has_change_permission``.
        :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``has_change_permission``.

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
            soup.find("h1").string.replace_with(form.cleaned_data["error_text_" + language])
        with open("/vol/web/nginx/data/" + language + "/custom_503.html", "w") as fp:
            fp.write(str(soup))
        with open("/vol/web/nginx/data/" + language + "/oznameni/custom_503.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
            soup.find("h1").string.replace_with(form.cleaned_data["error_text_oznam_" + language])
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
               Provádí operaci changelist view.

               :param request: Parametr ``request`` předává se do volání ``changelist_view()``, vstupuje do návratové hodnoty.
               :param extra_context: Kolekce ``extra_context`` zpracovávaná touto funkcí.
        :return: Výstup funkce odpovídající implementované logice.
        """
        return super().changelist_view(request, {"import_list": True})

    def get_urls(self):
        """Metoda pri definici dodatečných url.

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
    search_fields = ["user"]

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, str] | None = None) -> HttpResponse:
        """
               Provádí operaci changelist view.

               :param request: Parametr ``request`` předává se do volání ``changelist_view()``, vstupuje do návratové hodnoty.
               :param extra_context: Kolekce ``extra_context`` zpracovávaná touto funkcí.
        :return: Výstup funkce odpovídající implementované logice.
        """
        return super().changelist_view(request, {"import_skip_list": True})

    def get_urls(self):
        """Metoda pri definici dodatečných url.

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
        Exportuje as csv.

        :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``export_as_csv``.
        :param queryset: Parametr ``queryset`` slouží jako vstup pro logiku funkce ``export_as_csv``.

            :return: Vrací proměnná ``response``.
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

    IMPORT_DATA_REDIS_EXPIRATION = 6 * 60**2
    IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE = 2**30

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
        if sheet.shape[1] != 1:
            context["error"] = _("fedora_management.admin.YourCustomAdminSite.too_many_columns")
            sheet = None
        if isinstance(sheet, pd.DataFrame):
            sheet.columns = [
                "ident_cely",
            ]
            sheet["ident_cely"] = sheet["ident_cely"].str.strip()
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

    def import_data(self, request):
        """
        Creates a view for importing data from a zip file.

        :param request: Parametr ``request`` se předává do volání ``get_app_list()``, ``each_context()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``TemplateResponse()``.
            :raises ImportDataUnsupportedFilesError: Vyvolá se při splnění podmínky ``not normalized_imported_file_names.issubset(allowed_file_names)``.
            :raises ImportDataUnsupportedFileError: Vyvolá se při splnění podmínky ``mapper_class``.
        """

        def normalize_file_name(name: str) -> str:
            """
                       Provádí operaci normalize file name.

                       :param name: Parametr ``name`` pracuje se s atributy ``split``, ``strip``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
            :return: Výstup funkce odpovídající implementované logice.
            """
            if "/" in name:
                name = name.split("/")[-1]
            return name.strip().lower()

        import_data_running_value = self.redis_connector.get("import_data_running")
        import_data_running = import_data_running_value == "true"

        context = {
            "app_list": self.get_app_list(request),
            "maintenance": is_maintenance_in_progress(),
            "import_data_running": import_data_running,
            **self.each_context(request),
        }
        if not is_maintenance_in_progress() or import_data_running:
            return TemplateResponse(request, "admin/import_data/import_data.html", context)
        if request.method == "POST" and request.user.is_superuser:
            data_file = request.FILES["data_file"]
            form = ImportDataAdminForm(request.POST, request.FILES)
            if form.is_valid():
                cleaned_data = form.cleaned_data
            else:
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            context["form"] = form
            file_bytes = data_file.read()
            job_id = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
            context["url"] = reverse("core:data-import-progress", args=[job_id])
            context["url_stop"] = reverse("core:data-import-stop", args=[job_id])
            validation_results = []
            records = []
            LookupImportField.records = records
            LookupImportField.clear_cache()
            record_id = 0
            invalid_records = []
            performed_action = cleaned_data["performed_action"]
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                    file_names = [
                        name for name in zf.namelist() if not name.startswith("__MACOSX") and not name.endswith("/")
                    ]
                    mapper_dict = ImportModelMapper.get_import_data_mapper_dict()
                    mapper_key_order = {f"{name}.csv": i for i, name in enumerate(mapper_dict.keys())}
                    allowed_file_names = set(
                        [
                            f"{name}.csv".lower()
                            for name, mapper in mapper_dict.items()
                            if performed_action != ImportDataAdminForm.PERFORMED_ACTION_UPDATE or mapper.allow_update
                        ]
                    )
                    normalized_imported_file_names = set([normalize_file_name(file_name) for file_name in file_names])
                    if not normalized_imported_file_names.issubset(allowed_file_names):
                        raise ImportDataUnsupportedFilesError(normalized_imported_file_names - allowed_file_names)
                    file_names.sort(key=lambda fn: mapper_key_order.get(normalize_file_name(fn), len(mapper_key_order)))
                    total_uncompressed_size = sum(zf.getinfo(fn).file_size for fn in file_names)
                    if total_uncompressed_size > self.IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE:
                        raise ValueError(_("core.admin.import_data.error.zip_too_large"))
                    for file_name in file_names:
                        with zf.open(file_name) as file:
                            sheet = pd.read_csv(file)
                        file_name = normalize_file_name(file_name)
                        mapper_class = ImportModelMapper.get_import_data_mapper(file_name)
                        for idx, row in sheet.iterrows():

                            def format_primary_key(pk):
                                """
                                                               Provádí operaci format primary key.

                                                               :param pk: Primární klíč zpracovávaného záznamu.
                                Zpracovaná hodnota po validaci nebo transformaci.

                                    :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``join()``, výsledek volání ``str()``.
                                """
                                if isinstance(pk, dict):
                                    return ", ".join("{}: {}".format(k, v) for k, v in pk.items())
                                return str(pk)

                            if mapper_class:
                                try:
                                    mapper = mapper_class(row.to_dict())
                                    record = mapper.map(performed_action, serialize=True, include_primary_key=True)
                                    mapper.check_required_fields(performed_action)
                                    primary_key = mapper.import_validation(performed_action, request.user.pk)
                                    LookupImportField.records += mapper.create_records(performed_action)
                                    record["__file_name"] = file_name
                                except ImportDataIntegrityError as err:
                                    validation_results.append(
                                        ImportDataValidationResult(
                                            item_order=record_id,
                                            file_name=file_name,
                                            primary_key_import=format_primary_key(err.record_id),
                                            validation_result=str(err),
                                        )
                                    )
                                    invalid_records.append(record_id)
                                except ImportDataError as err:
                                    validation_results.append(
                                        ImportDataValidationResult(
                                            item_order=record_id,
                                            file_name=file_name,
                                            validation_result=str(err),
                                        )
                                    )
                                    invalid_records.append(record_id)
                                else:
                                    records.append(record)
                                    validation_results.append(
                                        ImportDataValidationResult(
                                            item_order=record_id,
                                            file_name=file_name,
                                            primary_key_import=format_primary_key(primary_key),
                                            validation_result=_("core.admin.import_data.record_valid"),
                                        )
                                    )
                                    self.redis_connector.set(
                                        f"import_data_{job_id}_record_{record_id}", json.dumps(record)
                                    )
                                record_id += 1
                            else:
                                raise ImportDataUnsupportedFileError(file_name)
            except zipfile.BadZipFile:
                context["error_message"] = _("core.admin.import_data.error.import_error")
                context["error_message_details"] = _("core.admin.import_data.error.bad_zip_file")
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            except ImportDataUnsupportedFilesError as err:
                context["error_message"] = _("core.admin.import_data.error.import_error")
                context["error_message_details"] = str(err)
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            except ImportDataUnsupportedFileError as err:
                context["error_message"] = _("core.admin.import_data.error.import_error")
                context["error_message_details"] = str(err)
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            except Exception as err:
                logger.exception("core.admin.FedoraCustomAdminSite.import_data.unexpected_error", extra={"err": err})
                context["error_message"] = _("core.admin.import_data.error.import_error")
                context["error_message_details"] = _("core.admin.import_data.error.unexpected_error")
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            finally:
                LookupImportField.records = []
                LookupImportField.clear_cache()
            records_count = record_id
            self.redis_connector.set(f"import_data_count_{job_id}", records_count, ex=self.IMPORT_DATA_REDIS_EXPIRATION)
            self.redis_connector.set(
                f"import_performed_action_{job_id}", performed_action, ex=self.IMPORT_DATA_REDIS_EXPIRATION
            )
            self.redis_connector.set(
                f"import_data_progress_{job_id}", json.dumps({}), ex=self.IMPORT_DATA_REDIS_EXPIRATION
            )
            self.redis_connector.set(
                f"import_data_primary_keys_{job_id}", json.dumps({}), ex=self.IMPORT_DATA_REDIS_EXPIRATION
            )
            self.redis_connector.set(
                f"import_data_files_{job_id}", json.dumps([]), ex=self.IMPORT_DATA_REDIS_EXPIRATION
            )
            self.redis_connector.set(f"import_data_progress_files_{job_id}", 0, ex=self.IMPORT_DATA_REDIS_EXPIRATION)
            self.redis_connector.set(
                f"import_data_status_message_{job_id}",
                _("core.templates.admin.import_data.starting"),
                ex=self.IMPORT_DATA_REDIS_EXPIRATION,
            )
            self.redis_connector.set(
                f"import_data_validation_results_{job_id}",
                json.dumps([r.to_dict() for r in validation_results]),
                ex=self.IMPORT_DATA_REDIS_EXPIRATION,
            )
            context["records_count"] = records_count
            context["job_id"] = job_id
            context["validation_results"] = validation_results
            context["invalid_records"] = ", ".join([str(r) for r in invalid_records])
            try:
                import_directory_settings_obj = CustomAdminSettings.objects.get(item_id="import_directory_settings")
                import_directory_settings = json.loads(import_directory_settings_obj.value)
                import_directory_path = import_directory_settings.get("DIRECTORY_PATH")
                context["import_directory_configured"] = bool(
                    import_directory_path and os.path.isdir(import_directory_path)
                )
            except (CustomAdminSettings.DoesNotExist, json.JSONDecodeError, ValueError, KeyError):
                context["import_directory_configured"] = False
            context["url_start"] = reverse("core:data-import-start", args=[job_id])
            if not invalid_records:
                context["stop_request"] = False
            else:
                context["stop_request"] = True
            logger.debug(
                "core.admin.FedoraCustomAdminSite.import_data.end",
                extra={"job_id": job_id, "records_count": records_count, "invalid_records": invalid_records},
            )
            return TemplateResponse(request, "admin/import_data/import_data.html", context)
        else:
            context["form"] = ImportDataAdminForm()
        return TemplateResponse(request, "admin/import_data/import_data.html", context)

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
            path(
                "import-data/",
                self.admin_view(self.import_data),
                name="import_data",
            ),
        ] + super().get_urls()


admin.site.__class__ = FedoraCustomAdminSite
