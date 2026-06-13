import io
import json
import logging
import os
import random
import string
import zipfile

import pandas as pd
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import gettext as _
from rosetta.templatetags.rosetta import can_translate as rosetta_can_translate

from .connectors import RedisConnector
from .forms import ImportDataAdminForm
from .import_data_mappers import (
    ImportDataEmptyError,
    ImportDataError,
    ImportDataIntegrityError,
    ImportDataMissingFileError,
    ImportDataUnsupportedFileError,
    ImportDataUnsupportedFilesError,
    ImportDataValidationResult,
    ImportModelMapper,
    LookupImportField,
)
from .models import AntivirusCheckResult, Soubor
from .setting_models import CustomAdminSettings
from .utils import is_maintenance_in_progress

logger = logging.getLogger(__name__)


class AmcrCustomAdminSite(admin.AdminSite):
    """Vlastní admin site AMČR s reorganizovanou strukturou menu a správou dat."""

    def get_app_list(self, request, app_label=None):
        """
        Reorganizuje seznam aplikací v admin rozhraní do požadované struktury menu.

        :param request: HTTP požadavek.
        :param app_label: Volitelný label aplikace pro filtrování.
        :return: Vrací reorganizovaný seznam aplikací.
        """
        if app_label:
            return super().get_app_list(request, app_label)

        original_app_list = super().get_app_list(request)

        model_lookup = {}
        for app in original_app_list:
            for model in app.get("models", []):
                key = (app["app_label"], model["object_name"])
                model_lookup[key] = model

        def find_model(al, object_name):
            """Vrací model ze lookup slovníku podle aplikace a názvu objektu."""
            return model_lookup.get((al, object_name))

        def custom_link(name, url=None):
            """Vytvoří strukturu pro vlastní odkaz v admin menu."""
            return {
                "name": name,
                "object_name": name,
                "perms": {"add": False, "change": False, "delete": False, "view": True},
                "admin_url": url,
                "add_url": None,
                "view_only": True,
            }

        def make_section(name, app_label_key, models):
            """Vytvoří sekci admin menu s filtrovanými modely."""
            filtered = [m for m in models if m is not None]
            if not filtered:
                return None
            return {
                "name": name,
                "app_label": app_label_key,
                "app_url": "",
                "has_module_perms": True,
                "models": filtered,
            }

        new_app_list = []

        # 1. Systémová nastavení
        section = make_section(
            _("core.admin_site.AmcrCustomAdminSite.systemova_nastaveni"),
            "systemova_nastaveni",
            [
                find_model("core", "CustomAdminSettings"),
            ],
        )
        if section:
            new_app_list.append(section)

        # 2. Správa DB a repozitáře
        if request.user.is_superuser:
            section = make_section(
                _("core.admin_site.AmcrCustomAdminSite.sprava_db"),
                "sprava_db",
                [
                    custom_link(
                        _("core.admin_site.AmcrCustomAdminSite.aktualizovat_metadata"), reverse("admin:update_metadata")
                    ),
                    custom_link(_("core.admin_site.AmcrCustomAdminSite.aktualizovat_katastry")),
                    custom_link(_("core.admin_site.AmcrCustomAdminSite.hromadny_import"), reverse("admin:import_data")),
                    custom_link(
                        _("core.admin_site.AmcrCustomAdminSite.spravovat_doi_igsn"), reverse("admin:update_doi")
                    ),
                ],
            )
            if section:
                new_app_list.append(section)

        # 3. Správa heslářů
        section = make_section(
            _("core.admin_site.AmcrCustomAdminSite.sprava_heslaru"),
            "sprava_heslaru",
            [
                find_model("heslar", "Heslar"),
                find_model("heslar", "HeslarDatace"),
                find_model("heslar", "HeslarDokumentTypMaterialRada"),
                find_model("heslar", "HeslarHierarchie"),
                find_model("heslar", "HeslarNazev"),
                find_model("heslar", "HeslarOdkaz"),
                find_model("uzivatel", "Organizace"),
                find_model("uzivatel", "Osoba"),
                find_model("heslar", "RuianKatastr"),
                find_model("heslar", "RuianKraj"),
                find_model("heslar", "RuianOkres"),
            ],
        )
        if section:
            new_app_list.append(section)

        # 4. Správa letů
        section = make_section(
            _("core.admin_site.AmcrCustomAdminSite.sprava_letu"),
            "sprava_letu",
            [
                find_model("dokument", "Let"),
            ],
        )
        if section:
            new_app_list.append(section)

        # 5. Správa odstávek
        section = make_section(
            _("core.admin_site.AmcrCustomAdminSite.sprava_odstavek"),
            "sprava_odstavek",
            [
                find_model("core", "OdstavkaSystemu"),
            ],
        )
        if section:
            new_app_list.append(section)

        # 6. Správa oprávnění
        section = make_section(
            _("core.admin_site.AmcrCustomAdminSite.sprava_opravneni"),
            "sprava_opravneni",
            [
                find_model("core", "Permissions"),
                find_model("auth", "Group"),
                find_model("authtoken", "TokenProxy"),
                find_model("core", "PermissionsSkip"),
            ],
        )
        if section:
            new_app_list.append(section)

        # 7. Správa překladů
        if rosetta_can_translate(request.user):
            section = make_section(
                _("core.admin_site.AmcrCustomAdminSite.sprava_prekladu"),
                "sprava_prekladu",
                [
                    custom_link("Rosetta", reverse("rosetta-file-list", kwargs={"po_filter": "project"})),
                ],
            )
            if section:
                new_app_list.append(section)

        # 8. Správa periodických úloh
        section = make_section(
            _("core.admin_site.AmcrCustomAdminSite.sprava_uloh"),
            "sprava_uloh",
            [
                find_model("django_celery_beat", "ClockedSchedule"),
                find_model("django_celery_beat", "CrontabSchedule"),
                find_model("django_celery_beat", "IntervalSchedule"),
                find_model("django_celery_beat", "PeriodicTask"),
                find_model("django_celery_beat", "SolarSchedule"),
                find_model("django_celery_results", "GroupResult"),
                find_model("django_celery_results", "TaskResult"),
            ],
        )
        if section:
            new_app_list.append(section)

        # 9. Správa uživatelů
        section = make_section(
            _("core.admin_site.AmcrCustomAdminSite.sprava_uzivatelu"),
            "sprava_uzivatelu",
            [
                find_model("uzivatel", "User"),
                find_model("uzivatel", "NotificationsLog"),
            ],
        )
        if section:
            new_app_list.append(section)

        # 10. Logy API
        section = make_section(
            _("api.admin_site.AmcrCustomAdminSite.logy_api"),
            "logy_api",
            [
                find_model("api", "ApiRequestLog"),
            ],
        )
        if section:
            new_app_list.append(section)

        return new_app_list

    redis_connector = RedisConnector().get_connection_decode()

    @staticmethod
    def _read_file(uploaded_file, context):
        """
        Načte CSV/XLSX soubor se seznamem identifikátorů a převede jej na DataFrame.

        :param uploaded_file: Nahraný soubor z formuláře; podle ``content_type`` se načte jako CSV nebo Excel.
        :param context: Slovník kontextu pro šablonu; při chybě čtení nebo neplatném formátu se do něj uloží klíč ``error``.
        :return: DataFrame s jedním sloupcem ``ident_cely`` indexovaným touto hodnotou, nebo ``None`` při chybě.
        """
        sheet = None
        if uploaded_file.content_type == "text/csv":
            try:
                sheet = pd.read_csv(uploaded_file, sep=",")
            except Exception as err:
                logger.debug(
                    "core.admin_sites.AmcrCustomAdminSite.update_metadata_file_upload" ".cannot_read_file",
                    extra={"error": err},
                )
                context["error"] = _("fedora_management.admin.YourCustomAdminSite.cannot_read_file")
        else:
            try:
                sheet = pd.read_excel(uploaded_file)
            except Exception as err:
                logger.debug(
                    "core.admin_sites.AmcrCustomAdminSite.update_metadata_file_upload" ".cannot_read_file",
                    extra={"error": err},
                )
                context["error"] = _("fedora_management.admin.YourCustomAdminSite.cannot_read_file")
        if sheet is None:
            return None
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
        Zpracuje hromadnou aktualizaci DOI/IGSN podle nahraného seznamu identifikátorů.

        :param request: HTTP požadavek; u ``POST`` od superuživatele validuje formulář, připraví job v Redis a vrátí stránku průběhu.
        :return: Odpověď ``TemplateResponse`` s formulářem nebo stránkou spuštěného jobu.
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
                uploaded_file = form.cleaned_data["ident_list_file"]
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
        Zpracuje hromadnou aktualizaci metadat ve Fedora repozitáři.

        :param request: HTTP požadavek; u ``POST`` od superuživatele validuje formulář, připraví job v Redis a vrátí stránku průběhu.
        :return: Odpověď ``TemplateResponse`` s formulářem nebo stránkou spuštěného jobu.
        """
        from fedora_management.forms import UpdateMetadataFileForm

        context = {
            "app_list": self.get_app_list(request),
            **self.each_context(request),
        }
        if request.method == "POST" and request.user.is_superuser:
            form = UpdateMetadataFileForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = form.cleaned_data["ident_list_file"]
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

    IMPORT_DATA_REDIS_EXPIRATION = 6 * 60 * 60  # 6 hodin
    IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE = 1024 * 1024 * 1024  # 1024 MB

    def import_data(self, request):
        """
        Importuje datové CSV soubory ze ZIP archivu do interní importní fronty.

        :param request: HTTP požadavek; při ``POST`` od superuživatele zvaliduje vstupní formulář,
            zpracuje obsah ZIPu, provede validační kroky přes mapery a uloží připravené záznamy do Redis.
        :return: Odpověď ``TemplateResponse`` s výsledkem validace, případně s chybovou hláškou importu.
        :raises ImportDataUnsupportedFilesError: Vyvolá se, pokud ZIP obsahuje soubory mimo povolenou sadu názvů.
        :raises ImportDataUnsupportedFileError: Vyvolá se, pokud pro nalezený CSV soubor neexistuje mapper.
        """

        if not request.user.is_superuser:
            raise PermissionDenied

        def normalize_file_name(name: str) -> str:
            """
            Normalizuje název souboru ze ZIP archivu na formát pro porovnání s mapery.

            :param name: Původní cesta nebo název souboru ze ZIP archivu.
            :return: Název souboru bez adresáře, oříznutý o bílé znaky a převedený na malá písmena.
            """
            if "/" in name:
                name = name.split("/")[-1]
            return name.strip().lower()

        # Missing Redis key returns None, so bool(get(...)) is False when no import lock is held.
        import_data_running = bool(self.redis_connector.get(RedisConnector.IMPORT_DATA_LOCK_KEY))

        context = {
            "app_list": self.get_app_list(request),
            "maintenance": is_maintenance_in_progress(),
            "import_data_running": import_data_running,
            **self.each_context(request),
        }
        if not is_maintenance_in_progress() or import_data_running:
            return TemplateResponse(request, "admin/import_data/import_data.html", context)
        if request.method == "POST" and request.user.is_superuser:
            form = ImportDataAdminForm(request.POST, request.FILES)
            if form.is_valid():
                cleaned_data = form.cleaned_data
            else:
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            context["form"] = form
            performed_action = cleaned_data["performed_action"]
            try:
                data_file = cleaned_data.get("data_file")
                if not data_file:
                    raise ImportDataMissingFileError()
                file_bytes = data_file.read()
                job_id = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
                context["url"] = reverse("core:data-import-progress", args=[job_id])
                context["url_stop"] = reverse("core:data-import-stop", args=[job_id])
                validation_results = []
                records = []
                record_id = 0  # index of valid records only — used as Redis key suffix and records_count
                row_order = 0  # index of every CSV row (valid + invalid) — used as item_order in validation results
                invalid_records = []
                antivirus_result = Soubor.check_antivirus(io.BytesIO(file_bytes))
                if antivirus_result == AntivirusCheckResult.VIRUS_FOUND:
                    context["error_message"] = _("core.admin.import_data.error.import_error")
                    context["error_message_details"] = _("core.admin.import_data.error.virus_found")
                    return TemplateResponse(request, "admin/import_data/import_data.html", context)
                if antivirus_result == AntivirusCheckResult.CHECK_FAILED:
                    logger.warning("core.admin_sites.AmcrCustomAdminSite.import_data.antivirus_check_failed")
                LookupImportField.set_records(records)
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
                                Převede primární klíč importovaného záznamu na text pro validační výstup.

                                :param pk: Primární klíč z mapperu, typicky slovník složeného klíče nebo skalární hodnota.
                                :return: Textová reprezentace klíče vhodná pro zobrazení ve validační tabulce.
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
                                    records += mapper.create_records(performed_action)
                                    record["__file_name"] = file_name
                                except ImportDataIntegrityError as err:
                                    validation_results.append(
                                        ImportDataValidationResult(
                                            item_order=row_order,
                                            file_name=file_name,
                                            primary_key_import=format_primary_key(err.record_id),
                                            validation_result=str(err),
                                        )
                                    )
                                    invalid_records.append(row_order)
                                except ImportDataError as err:
                                    validation_results.append(
                                        ImportDataValidationResult(
                                            item_order=row_order,
                                            file_name=file_name,
                                            validation_result=str(err),
                                        )
                                    )
                                    invalid_records.append(row_order)
                                else:
                                    records.append(record)
                                    validation_results.append(
                                        ImportDataValidationResult(
                                            item_order=row_order,
                                            file_name=file_name,
                                            primary_key_import=format_primary_key(primary_key),
                                            validation_result=_("core.admin.import_data.record_valid"),
                                        )
                                    )
                                    self.redis_connector.set(
                                        f"import_data_{job_id}_record_{record_id}",
                                        json.dumps(record),
                                        ex=self.IMPORT_DATA_REDIS_EXPIRATION,
                                    )
                                    record_id += 1
                                row_order += 1
                            else:
                                raise ImportDataUnsupportedFileError(file_name)
                    if row_order == 0:
                        raise ImportDataEmptyError()
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
            except ImportDataEmptyError as err:
                context["error_message"] = _("core.admin.import_data.error.import_error")
                context["error_message_details"] = str(err)
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            except ImportDataMissingFileError as err:
                context["error_message"] = _("core.admin.import_data.error.import_error")
                context["error_message_details"] = str(err)
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            except Exception as err:
                logger.exception(
                    "core.admin_sites.AmcrCustomAdminSite.import_data.unexpected_error", extra={"err": err}
                )
                context["error_message"] = _("core.admin.import_data.error.import_error")
                context["error_message_details"] = _("core.admin.import_data.error.unexpected_error")
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            finally:
                LookupImportField.clear_records()
                LookupImportField.clear_cache()
            records_count = record_id
            self.redis_connector.set(f"import_data_count_{job_id}", records_count, ex=self.IMPORT_DATA_REDIS_EXPIRATION)
            self.redis_connector.set(
                f"import_performed_action_{job_id}", performed_action, ex=self.IMPORT_DATA_REDIS_EXPIRATION
            )
            self.redis_connector.set(f"import_data_progress_{job_id}", 0, ex=self.IMPORT_DATA_REDIS_EXPIRATION)
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
            self.redis_connector.set(
                f"import_data_valid_{job_id}",
                "1" if not invalid_records else "0",
                ex=self.IMPORT_DATA_REDIS_EXPIRATION,
            )
            context["records_count"] = records_count
            context["job_id"] = job_id
            context["validation_results"] = validation_results
            context["invalid_records"] = ", ".join([str(r) for r in invalid_records])
            context["performed_action"] = performed_action
            performed_action_labels = {
                ImportDataAdminForm.PERFORMED_ACTION_INSERT: _("core.forms.ImportDataAdminForm.insert"),
                ImportDataAdminForm.PERFORMED_ACTION_UPDATE: _("core.forms.ImportDataAdminForm.update"),
                ImportDataAdminForm.PERFORMED_ACTION_DELETE: _("core.forms.ImportDataAdminForm.delete"),
            }
            context["performed_action_label"] = performed_action_labels.get(performed_action, performed_action)
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
                "core.admin_sites.AmcrCustomAdminSite.import_data.end",
                extra={"job_id": job_id, "records_count": records_count, "invalid_records": invalid_records},
            )
            return TemplateResponse(request, "admin/import_data/import_data.html", context)
        else:
            context["form"] = ImportDataAdminForm()
        return TemplateResponse(request, "admin/import_data/import_data.html", context)

    def get_urls(
        self,
    ):
        """
        Vrátí vlastní URL cesty admin site pro hromadné operace.

        :return: Seznam URL vzorů rozšířený o cesty pro aktualizaci metadat,
            aktualizaci DOI/IGSN a hromadný import dat.
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
