import json
import re
import logging
from django.http import HttpResponse
from django.http.request import HttpRequest
import pandas as pd
import os
import io
from bs4 import BeautifulSoup
from polib import pofile
import csv
from cacheops import invalidate_model

from django.contrib import admin
from django.shortcuts import redirect
from django.core.cache.utils import make_template_fragment_key
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _
from django.contrib import messages
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth.models import Group
from django.urls import path, reverse
from django.core.cache import cache

from uzivatel.models import User

from .models import OdstavkaSystemu, Permissions, CustomAdminSettings, PermissionsSkip
from .exceptions import WrongCSVError, WrongSheetError
from .forms import OdstavkaSystemuForm, PermissionImportForm, PermissionSkipImportForm
from .constants import (
    ROLE_NASTAVENI_ODSTAVKY,
    PERMISSIONS_IMPORT_SHEET,
    PERMISSIONS_SHEET_ZAKLADNI_NAME,
    PERMISSIONS_SHEET_PRISTUPNOST_NAME,
    PERMISSIONS_SHEET_STAV_NAME,
    PERMISSIONS_SHEET_VLASTNICTVI_NAME,
    PERMISSIONS_SHEET_APP_NAME,
    PERMISSIONS_SHEET_URL_NAME,
    PERMISSIONS_SHEET_ACTION_NAME,
)

logger = logging.getLogger(__name__)


class OdstavkaSystemuAdmin(admin.ModelAdmin):
    """
    Třída admin panelu pro zobrazení odstávek systému.
    Pomocí ní se zobrazuje tabulka s odstávkami, detail a jednotlivé akce.
    """
    change_list_template = 'core/odstavky_changelist.html'
    list_display = (
        "info_od",
        "datum_odstavky",
        "cas_odstavky",
        "status",
    )
    form = OdstavkaSystemuForm

    def save_model(self, request, obj, form, change):
        """
        Metóda na uložení modelu odstávky.
        Jednotlivé texty z modelu se ukladají do textú prekladů a template.
        Po uložení se restartuje wsgi pro načítaní nových prekladů.
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
        cache.delete("last_maintenance")
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
                logger.debug(
                    "core.admin.OdstavkaSystemuAdmin.exception", extra={"exception": e}
                )
                pass  # we may not be running under uwsgi :P
        super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        """
        Metóda pro určení práv na modul odstávky.
        """
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_view_permission(self, request, obj=None, *args):
        """
        Metóda pro určení práv na videní odstávky.
        """
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_add_permission(self, request, *args):
        """
        Metóda pro určení práv na přidání odstávky. Není možné přidat více než jednu odstávku.
        """
        if OdstavkaSystemu.objects.count() > 0:
            return False
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def has_change_permission(self, request, obj=None, *args):
        """
        Metóda pro určení práv pro úpravu odstávky.
        """
        return request.user.groups.filter(id=ROLE_NASTAVENI_ODSTAVKY).count() > 0

    def file_handler(self, language, form):
        """
        Pomocní metóda pro úpravu template zobrazených počas odstávky.
        """
        with open("/vol/web/nginx/data/" + language + "/custom_50x.html") as fp:
            soup = BeautifulSoup(fp, "html.parser")
            soup.find("h1").string.replace_with(
                form.cleaned_data["error_text_" + language]
            )
        with open("/vol/web/nginx/data/" + language + "/custom_50x.html", "w") as fp:
            fp.write(str(soup))
        with open(
            "/vol/web/nginx/data/" + language + "/oznameni/custom_50x.html"
        ) as fp:
            soup = BeautifulSoup(fp, "html.parser")
            soup.find("h1").string.replace_with(
                form.cleaned_data["error_text_oznam_" + language]
            )
        with open(
            "/vol/web/nginx/data/" + language + "/oznameni/custom_50x.html", "w"
        ) as fp:
            fp.write(str(soup))


admin.site.register(OdstavkaSystemu, OdstavkaSystemuAdmin)

class CustomAdminSettingsAdmin(admin.ModelAdmin):
    """
    Admin panel pro vlastních nastavení.
    """
    model = CustomAdminSettings
    list_display = ("item_id", "item_group")


admin.site.register(CustomAdminSettings, CustomAdminSettingsAdmin)

@admin.register(Permissions)
class PermissionAdmin(admin.ModelAdmin):
    """
    Třída admin panelu pro zobrazení a správu oprávnení.
    """

    change_list_template = "core/permissions_changelist.html"
    list_display = [
        "address_in_app", "main_role", "action", "base", "status", "ownership", "accessibility"
    ]
    list_filter = ["main_role"]
    search_fields = ["address_in_app", "action"]

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, str] | None = ...) -> TemplateResponse:
        return super().changelist_view(request, {"import_list":True})

    def get_urls(self):
        """
        Metóda pri definici dodatečných url.
        """
        urls = super().get_urls()
        my_urls = [
            path("import_file/", self.import_file, name="import_permissions"),
            path(
                "import_success/",
                self.import_success,
                name="import_success",
            ),
        ]
        return my_urls + urls

    def import_file(self, request):
        """
        Metóda view pro zobrazení formuláře a samtotný import oprávnení z excelu.
        """
        model = self.model
        opts = model._meta
        app_label = "core"
        if request.method == "POST":
            docfile = request.FILES["file"]
            try:
                sheet = pd.read_excel(docfile, PERMISSIONS_IMPORT_SHEET)
            except ValueError as e:
                logger.debug(e)
                self.message_user(
                    request,
                    _("core.admin.permissionAdmin.wrongSheet.error"),
                    messages.ERROR,
                )
                return redirect(reverse("admin:core_permissions_changelist"))
            try:
                sheet = self.validate_and_prepare_sheet(sheet)
            except WrongSheetError as e:
                logger.debug(e)
                self.message_user(
                    request,
                    _("core.admin.permissionAdmin.wrongSheetConfiguration.error"),
                    messages.ERROR,
                )
                return redirect(reverse("admin:core_permissions_changelist"))
            Permissions.objects.all().delete()
            sheet["result"] = sheet.apply(self.check_save_row, axis=1)
            sheet.drop(sheet.iloc[:, 3:22], axis=1, inplace=True)
            sheet = sheet.reset_index(drop=True)
            logger.debug(sheet.info())
            json_sheet = sheet.to_json(orient="records")
            cache.set("import_json_results",json_sheet,120)
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
        invalidate_model(Permissions)
        return TemplateResponse(
            request,
            "core/permission_import_form.html",
            payload,
        )

    def validate_and_prepare_sheet(self, sheet):
        """
        Metóda pro validaci importovaného excelu a jeho úpravu.
        """
        if (
            not sheet.columns[3] == PERMISSIONS_SHEET_ZAKLADNI_NAME
            or not sheet.columns[8] == PERMISSIONS_SHEET_STAV_NAME
            or not sheet.columns[12] == PERMISSIONS_SHEET_VLASTNICTVI_NAME
            or not sheet.columns[16] == PERMISSIONS_SHEET_PRISTUPNOST_NAME
        ):
            raise WrongSheetError
        sheet.columns = sheet.iloc[0]
        sheet = sheet[1:]
        sheet = sheet.reset_index(drop=True)
        if (
            not sheet.columns[0] == PERMISSIONS_SHEET_APP_NAME
            or not sheet.columns[1] == PERMISSIONS_SHEET_URL_NAME
            or not sheet.columns[2] == PERMISSIONS_SHEET_ACTION_NAME
            or not sheet.columns[3] == "A"
        ):
            raise WrongSheetError
        i = 4
        while i < 20:
            if (
                not sheet.columns[i] == "B"
                or not sheet.columns[i + 1] == "C"
                or not sheet.columns[i + 2] == "D"
                or not sheet.columns[i + 3] == "E"
            ):
                raise WrongSheetError
            i = i + 4

        return sheet

    def check_save_row(self, row):
        """
        Metóda pro kontrolu řádku excelu.
        """
        number_to_role = ["B", "C", "D", "E"]
        if row.iloc[1]=="/":
            row.iloc[1] = ""
        with io.StringIO() as out:
            call_command("show_urls", "--format", "json", stdout=out)
            url_list = pd.read_json(io.StringIO(out.getvalue()))
        url = "/" + str(row.iloc[0]) + "/" + str(row.iloc[1]) if row.iloc[0]!="core" else "/" + str(row.iloc[1])
        if url_list["url"].eq(url).any():
            if pd.isna(row.iloc[2]) or row.iloc[2] in Permissions.actionChoices.values:
                i = 0
                row_result = list()
                while i < 4:
                    row_result.append(self.save_permission(row, i))
                    i += 1
                if all(i == True for i in row_result):
                    return "ALL OK"
                else:
                    results = []
                    for idx, i in enumerate(row_result):
                        if i == True:
                            results.append(str(number_to_role[idx] + " OK"))
                        else:
                            results.append(str(number_to_role[idx] + " NOK"))
                return results
            else:
                return "NOK action"
        else:
            return "NOK address"

    def save_permission(self, row, i):
        """
        Metóda pro kontrolu a uložení jednotlivého oprávnení z řádku excelu.
        """
        if row.iloc[0]!="core":
            address = str(row.iloc[0]) + "/" + str(row.iloc[1])
        else:
            address =  str(row.iloc[1])
        if row.iloc[4 + i] == "X":
            Permissions.objects.create(
                address_in_app=address,
                base=False,
                main_role=Group.objects.get(id=i + 1),
                action=None if pd.isna(row.iloc[2]) else row.iloc[2]
            )
            return True
        elif row.iloc[4 + i] == "*":
            base = True
        else:
            return False
        if "|" in row.iloc[8 + i]:
            n = 0
            results = list()
            for n, value in enumerate(row.iloc[8 + i].split("|")):
                new_row = row.copy()
                new_row.iloc[8 + i] = row.iloc[8 + i].split("|")[n].strip()
                if len(row.iloc[12 + i].split("|")) > 1:
                    new_row.iloc[12 + i] = row.iloc[12 + i].split("|")[n].strip()
                else:
                    new_row.iloc[12 + i] = row.iloc[12 + i]
                if len(row.iloc[16 + i].split("|")) > 1:
                    new_row.iloc[16 + i] = row.iloc[16 + i].split("|")[n].strip()
                else:
                    new_row.iloc[16 + i] = row.iloc[16 + i]
                results.append(self.save_permission(new_row, i))
            if all(a == True for a in results):
                return True
            else:
                return False
        else:
            if row.iloc[8 + i] == "*":
                status = None
            elif self.check_status_regex(row.iloc[8 + i]):
                status = row.iloc[8 + i]
            else:
                logger.debug("core.admin.PermissionAdmin.status_NOK")
                return False
        if row.iloc[12 + i] == "*":
            ownership = None
        elif row.iloc[12 + i].endswith(".my"):
            ownership = Permissions.ownershipChoices.my
        elif row.iloc[12 + i].endswith(".ours"):
            ownership = Permissions.ownershipChoices.our
        else:
            logger.debug("core.admin.PermissionAdmin.ownership_NOK")
            return False
        if row.iloc[16 + i] == "*":
            accessibility = None
        elif row.iloc[16 + i].endswith("(my)"):
            accessibility = Permissions.ownershipChoices.my
        elif row.iloc[16 + i].endswith("(ours)"):
            accessibility = Permissions.ownershipChoices.our
        else:
            logger.debug("core.admin.PermissionAdmin.accessibility_NOK")
            return False
        if not (
            base == True
            and status is None
            and ownership is None
            and accessibility is None
        ):
            Permissions.objects.create(
                address_in_app=address,
                base=base,
                main_role=Group.objects.get(id=i + 1),
                status=status,
                ownership=ownership,
                accessibility=accessibility,
                action=None if pd.isna(row.iloc[2]) else row.iloc[2]
            )
        return True

    def check_status_regex(self, cell):
        """
        Metóda pro kontrolu správneho zadáni statusu v excelu.
        """
        if re.fullmatch(r"(<|>|)[A-Z]{1,2}\d{1}", cell) or re.fullmatch(
            r"\D{1,2}\d{1}-\D{1,2}\d{1}", cell
        ):
            return True
        else:
            return False

    def import_success(self, request):
        """
        Metóda view pro zobrazení tabulky s výsledkom importu.
        """
        json_table = cache.get("import_json_results")
        cache.delete("import_json_results")
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
    """
    Třída admin panelu pro zobrazení a správu proskakovani oprávnení.
    """

    change_list_template = "core/permissions_changelist.html"
    list_display = [
        "user"
    ]
    actions = ("export_as_csv",)
    search_fields = ["user"]

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, str] | None = ...) -> TemplateResponse:
        return super().changelist_view(request, {"import_skip_list":True})

    def get_urls(self):
        """
        Metóda pri definici dodatečných url.
        """
        urls = super().get_urls()
        my_urls = [
            path("import_skip_file/", self.import_skip_file, name="import_permissions_skip"),
            path(
                "import_skip_success/",
                self.import_skip_success,
                name="import_skip_success",
            ),
        ]
        return my_urls + urls
    
    def validate_sheet(self, sheet):
        """
        Metóda pro validaci importovaného excelu a jeho úpravu.
        """
        if (
            not sheet.columns[0] == "IDENT_CELY"
            or not sheet.columns[1] == "IDENT_LIST"
        ):
            raise WrongCSVError
        return True

    def import_skip_file(self, request):
        """
        Metóda view pro zobrazení formuláře a samtotný import oprávnení z excelu.
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
            cache.set("import_json_results",json_sheet,120)
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
        Metóda view pro zobrazení tabulky s výsledkom importu.
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
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=opravneni_override.csv'
        writer = csv.writer(response,delimiter=";")
        writer.writerow(["IDENT_CELY","IDENT_LIST"])
        for obj in queryset:
            writer.writerow([obj.user.ident_cely,obj.ident_list])
        return response
    
    export_as_csv.short_description = _("core.admin.permissionSkipAdmin.downloadAction_label")
