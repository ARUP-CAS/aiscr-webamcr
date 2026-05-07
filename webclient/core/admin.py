import csv
import json
import logging
import os
import random
import string

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
from .forms import OdstavkaSystemuForm, PermissionImportForm, PermissionSkipImportForm
from .models import ApiRequestLog, OdstavkaSystemu, Permissions, PermissionsSkip
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


class ApiRequestLogAdmin(admin.ModelAdmin):
    """Třída admin panelu pro zobrazení logů API požadavků."""

    list_display = [
        "received_at",
        "user",
        "client_ip",
        "request_target",
        "status",
        "ident_cely",
        "filename",
        "file_size",
        "finished_at",
    ]
    list_filter = ["status", "request_target"]
    search_fields = ["user__email", "client_ip", "ident_cely"]
    readonly_fields = [
        "user",
        "client_ip",
        "received_at",
        "finished_at",
        "request_target",
        "filename",
        "file_size",
        "status",
        "ident_cely",
        "samostatny_nalez",
        "errors",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Zakáže ruční vytváření záznamů — logy se vytvářejí pouze automaticky.

        :param request: HTTP požadavek od klienta.

        :return: Vždy ``False``.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        """
        Zakáže editaci záznamů — logy jsou pouze pro čtení.

        :param request: HTTP požadavek od klienta.
        :param obj: Volitelný objekt záznamu.

        :return: Vždy ``False``.
        """
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        """
        Zakáže mazání záznamů — logy jsou auditní záznamy určené k archivaci.

        :param request: HTTP požadavek od klienta.
        :param obj: Volitelný objekt záznamu.

        :return: Vždy ``False``.
        """
        return False


admin.site.register(ApiRequestLog, ApiRequestLogAdmin)


@admin.register(PermissionsSkip)
class PermissionSkipAdmin(admin.ModelAdmin):
    """Třída admin panelu pro zobrazení a správu proskakovani oprávnení."""

    change_list_template = "core/permissions_changelist.html"
    list_display = ["user"]
    actions = ("export_as_csv",)
    search_fields = ["user"]

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
