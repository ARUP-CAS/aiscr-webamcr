import json
import logging
import os
import random
import secrets
import string

import pandas as pd
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import gettext as _
from rosetta.templatetags.rosetta import can_translate as rosetta_can_translate

from .connectors import RedisConnector
from .forms import ImportDataAdminForm
from .import_data_mappers import ImportDataMissingFileError
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
                sheet = pd.read_csv(uploaded_file, sep=",", dtype=str)
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
    # Velikost chunku komprimovaného ZIPu ve stagingu do Redis (§3.3). Zdrojová konstanta,
    # neladí se za běhu; drží každý SET/GET v řádu desítek ms a hodnotu pod proto-max-bulk-len.
    IMPORT_DATA_REDIS_CHUNK_SIZE = 64 * 1024 * 1024  # 64 MiB

    def _import_performed_action_labels(self):
        """
        Vrátí mapu kódů akcí importu na jejich lidsky čitelné popisky.

        :return: Slovník ``{kód akce: přeložený popisek}`` pro zobrazení ve stavu importu.
        """
        return {
            ImportDataAdminForm.PERFORMED_ACTION_INSERT: _("core.forms.ImportDataAdminForm.insert"),
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE: _("core.forms.ImportDataAdminForm.update"),
            ImportDataAdminForm.PERFORMED_ACTION_DELETE: _("core.forms.ImportDataAdminForm.delete"),
        }

    def _import_directory_configured(self):
        """
        Zjistí, zda je nakonfigurovaný a dostupný adresář pro import binárních souborů.

        :return: ``True``, pokud je ``DIRECTORY_PATH`` nastavený a ukazuje na existující adresář.
        """
        try:
            import_directory_settings_obj = CustomAdminSettings.objects.get(item_id="import_directory_settings")
            import_directory_settings = json.loads(import_directory_settings_obj.value)
            import_directory_path = import_directory_settings.get("DIRECTORY_PATH")
            return bool(import_directory_path and os.path.isdir(import_directory_path))
        except (CustomAdminSettings.DoesNotExist, json.JSONDecodeError, ValueError, KeyError):
            return False

    def _render_lock_busy(self, request, context):
        """
        Vykreslí stránku s hláškou ``import_is_running`` — globální lock drží jiný admin.

        Symetrický protějšek k ``_render_import_polling_ui`` pro větev „jiný admin má lock“
        (§4.1 krok 4 / Invariant B). Kontext se nedotýká dat importu ani validace.

        :param request: HTTP požadavek.
        :param context: Základní kontext šablony (``app_list``, ``maintenance`` …).
        :return: ``TemplateResponse`` s hláškou o běžícím importu jiného admina.
        """
        context = dict(context)
        context["import_data_running"] = True
        # No-arg reset: the blocked admin does not know the running job's id, so the endpoint
        # resolves it from IMPORT_DATA_ACTIVE_JOB_KEY.
        context["url_reset"] = reverse("core:data-import-reset-active")
        return TemplateResponse(request, "admin/import_data/import_data.html", context)

    def _render_import_polling_ui(self, request, context, job_id):
        """
        Vykreslí polling UI navázané na běžící nebo terminální importní úlohu ``job_id``.

        Do kontextu vkládá pouze ne-datové položky (URL, popisek akce, konfigurace adresáře);
        veškerá importní a validační data si stránka tahá z progress endpointu (požadavek 3, §4.1).

        :param request: HTTP požadavek.
        :param context: Základní kontext šablony (``app_list``, ``maintenance`` …).
        :param job_id: Identifikátor importní úlohy, na kterou se stránka naváže.
        :return: ``TemplateResponse`` s polling UI bez validačních dat v kontextu.
        """
        performed_action = self.redis_connector.get(f"import_performed_action_{job_id}") or None
        context = dict(context)
        context["job_id"] = job_id
        context["url"] = reverse("core:data-import-progress", args=[job_id])
        context["url_stop"] = reverse("core:data-import-stop", args=[job_id])
        context["url_start"] = reverse("core:data-import-start", args=[job_id])
        context["url_cancel"] = reverse("core:data-import-cancel", args=[job_id])
        context["url_reset"] = reverse("core:data-import-reset", args=[job_id])
        context["performed_action"] = performed_action
        context["performed_action_label"] = self._import_performed_action_labels().get(
            performed_action, performed_action
        )
        context["import_directory_configured"] = self._import_directory_configured()
        return TemplateResponse(request, "admin/import_data/import_data.html", context)

    def import_data(self, request):
        """
        Přijme nahraný ZIP hromadného importu a zařadí jeho validaci do fronty (accept-and-enqueue).

        Validace ani import už neběží v HTTP požadavku (viz #391): POST komprimovaný ZIP nastageuje
        do Redis po chuncích, získá globální importní lock, nastaví fázi ``validating`` a dispatchne
        ``cron.tasks.run_data_import_validation``. Stránka pak jen pollује progress endpoint —
        žádná importní ani validační data se nevykreslují z kontextu POSTu (požadavek 3).

        Znovuotevření stránky (GET) se naváže na běžící úlohu daného uživatele přes
        ``import_data_current_job_{user_id}`` (požadavek 2).

        Paměťová charakteristika (§8): ``data_file.read()`` načte celý komprimovaný upload
        (~200-330 MB pro max. úlohu) najednou do RAM web workeru a slicing chunků drží druhou
        referenci — přechodný špičkový nárůst ~250-500 MB na jeden upload. Globální lock serializuje
        uploady, takže špičkuje jen jeden uWSGI worker; buffery se uvolní návratem požadavku.

        :param request: HTTP požadavek; při ``POST`` od superuživatele zvaliduje formulář a zařadí
            validaci do fronty.
        :return: ``TemplateResponse`` s polling UI, upload formulářem nebo chybovou hláškou.
        :raises PermissionDenied: Pokud přihlášený uživatel není superuživatel.
        """
        if not request.user.is_superuser:
            raise PermissionDenied

        from cron import tasks

        maintenance = is_maintenance_in_progress()
        # Missing Redis key returns None, so bool(get(...)) is False when no import lock is held.
        import_data_running = bool(self.redis_connector.get(RedisConnector.IMPORT_DATA_LOCK_KEY))

        context = {
            "app_list": self.get_app_list(request),
            "maintenance": maintenance,
            "import_data_running": import_data_running,
            **self.each_context(request),
        }

        # Own-job gate (§4.1 step 3 / GET branch): if the requesting admin already has a non-terminal
        # job, always bind the page to it and never accept a new upload. This gate is advisory and not
        # atomic — the real serialization is the global lock acquire below (§4.1 step 7).
        current_job_id = self.redis_connector.get(f"import_data_current_job_{request.user.id}") or None
        if current_job_id:
            phase = self.redis_connector.get(f"import_data_phase_{current_job_id}")
            if phase in (
                tasks.IMPORT_PHASE_VALIDATING,
                tasks.IMPORT_PHASE_AWAITING_APPROVAL,
                tasks.IMPORT_PHASE_IMPORTING,
            ):
                return self._render_import_polling_ui(request, context, current_job_id)

        # Maintenance gate (§4.1 step 2 / Invariant A): reject uploads outside maintenance mode.
        if not maintenance:
            context["form"] = ImportDataAdminForm()
            return TemplateResponse(request, "admin/import_data/import_data.html", context)

        # Global-lock-busy gate (§4.1 step 4 / Invariant B): another admin's pipeline holds the lock.
        if import_data_running:
            return self._render_lock_busy(request, context)

        if request.method == "POST":
            form = ImportDataAdminForm(request.POST, request.FILES)
            if not form.is_valid():
                context["form"] = form
                return TemplateResponse(request, "admin/import_data/import_data.html", context)
            context["form"] = form
            performed_action = form.cleaned_data["performed_action"]
            data_file = form.cleaned_data.get("data_file")
            if not data_file:
                context["error_message"] = _("core.admin.import_data.error.import_error")
                context["error_message_details"] = str(ImportDataMissingFileError())
                return TemplateResponse(request, "admin/import_data/import_data.html", context)

            job_id = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
            lock_token = secrets.token_hex(16)

            # Atomic acquire is the real serialization guarantee (§4.1 step 7); on a TOCTOU race with
            # another upload, fall back to the import_is_running page.
            if not RedisConnector.acquire_import_lock(
                self.redis_connector, lock_token, tasks.IMPORT_DATA_RUNNING_TTL_SECONDS
            ):
                return self._render_lock_busy(request, context)

            chunk_count = 0
            try:
                # Stage the compressed ZIP in Redis, chunked (§3.3 / §4.1 step 8). Binary chunks are
                # written through the bytes connection so they are not utf-8 mangled.
                file_bytes = data_file.read()
                chunk_size = self.IMPORT_DATA_REDIS_CHUNK_SIZE
                chunk_count = (len(file_bytes) + chunk_size - 1) // chunk_size
                bytes_connector = RedisConnector.get_connection()
                pipe = bytes_connector.pipeline()
                for i in range(chunk_count):
                    pipe.set(
                        f"import_data_file_{job_id}_{i}",
                        file_bytes[i * chunk_size : (i + 1) * chunk_size],
                        ex=tasks.IMPORT_DATA_RUNNING_TTL_SECONDS,
                    )
                pipe.execute()

                ttl = tasks.IMPORT_DATA_RUNNING_TTL_SECONDS
                self.redis_connector.set(f"import_data_file_chunks_{job_id}", chunk_count, ex=ttl)
                self.redis_connector.set(f"import_data_current_job_{request.user.id}", job_id, ex=ttl)
                # Lock → job back-reference so a superuser can manually reset this job from anywhere.
                self.redis_connector.set(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, job_id, ex=ttl)
                self.redis_connector.set(f"import_data_phase_{job_id}", tasks.IMPORT_PHASE_VALIDATING, ex=ttl)
                self.redis_connector.set(
                    f"import_data_status_message_tr_{job_id}",
                    tasks.translation_value("cron.tasks.run_data_import.validating"),
                    ex=ttl,
                )
                self.redis_connector.set(f"import_performed_action_{job_id}", performed_action, ex=ttl)
                self.redis_connector.set(f"import_data_user_{job_id}", request.user.id, ex=ttl)
                self.redis_connector.set(f"import_data_lock_token_{job_id}", lock_token, ex=ttl)
                self.redis_connector.set(f"import_data_validation_total_{job_id}", 0, ex=ttl)
                self.redis_connector.set(f"import_data_validation_progress_{job_id}", 0, ex=ttl)
                self.redis_connector.set(f"import_data_validation_results_{job_id}", json.dumps([]), ex=ttl)
                self.redis_connector.set(f"import_data_valid_{job_id}", "0", ex=ttl)

                tasks.run_data_import_validation.delay(job_id, request.user.id, lock_token, performed_action)
            except Exception as err:
                logger.exception("core.admin_sites.AmcrCustomAdminSite.import_data.dispatch_failed", extra={"err": err})
                # On dispatch failure release the lock and delete every staged chunk key plus the
                # count and the per-user pointer (§4.1 step 10).
                RedisConnector.release_import_lock(self.redis_connector, lock_token)
                stray_keys = [f"import_data_file_{job_id}_{i}" for i in range(chunk_count)]
                stray_keys.append(f"import_data_file_chunks_{job_id}")
                self.redis_connector.delete(*stray_keys)
                self.redis_connector.delete(f"import_data_current_job_{request.user.id}")
                self.redis_connector.delete(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY)
                context["error_message"] = _("core.admin.import_data.error.import_error")
                context["error_message_details"] = _("core.admin.import_data.error.unexpected_error")
                return TemplateResponse(request, "admin/import_data/import_data.html", context)

            logger.debug(
                "core.admin_sites.AmcrCustomAdminSite.import_data.enqueued",
                extra={"job_id": job_id, "chunk_count": chunk_count},
            )
            return self._render_import_polling_ui(request, context, job_id)

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
