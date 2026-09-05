import datetime
import io
import json
import logging
import os
import traceback
import zipfile
from collections import defaultdict
from io import BytesIO

import pandas as pd
import requests
from arch_z.models import Akce
from cacheops import invalidate_model
from celery import shared_task
from core.connectors import RedisConnector
from core.constants import (
    IMPORT,
    OBLAST_CECHY,
    PRISTUPNOST_MIN_RAZENI,
    PROJEKT_STAV_VYTVORENY,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
    RUSENI_PROJ,
    RUSENI_STARE_PROJ,
    SCHVALENI_OZNAMENI_PROJ,
    STARY_PROJEKT_ZRUSEN,
    UDAJ_ODSTRANEN,
    ZAPSANI_PROJ,
)
from core.forms import ImportDataAdminForm
from core.ident_cely import get_record_from_ident
from core.import_data_mappers import (
    ImportDataBatchOrderingError,
    ImportDataEmptyError,
    ImportDataError,
    ImportDataIntegrityError,
    ImportDataMissingFileError,
    ImportDataUnsupportedFileError,
    ImportDataUnsupportedFilesError,
    ImportDataValidationResult,
    ImportModelMapper,
    LookupImportField,
    SouborMapper,
    UzivatelNotifikaceMapper,
    UzivatelOpravneniMapper,
)
from core.models import AntivirusCheckResult, Soubor, SouborVazby
from core.repository_connector import (
    DryRunFedoraTransaction,
    FedoraDeletionOnlyTransaction,
    FedoraError,
    FedoraRepositoryConnector,
    FedoraTransaction,
)
from core.utils import check_import_report_directory, upsert_import_report_index_entry
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import connection, transaction
from django.db.models import F, Min, Model, Prefetch, Q
from django.db.models.functions import Coalesce, Upper
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.translation import gettext as _
from dokument.models import Dokument
from ez.models import ExterniZdroj
from heslar import hesla_dynamicka
from heslar.hesla import HESLAR_PRISTUPNOST
from heslar.hesla_dynamicka import DOKUMENT_LICENCE_NEZNAMA, TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar
from historie.models import Historie
from lokalita.models import Lokalita
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from projekt.models import Projekt
from services.mailer import Mailer
from uzivatel.models import Osoba, User, UserNotificationType
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)

IMPORT_DATA_EXPIRATION_SECONDS = 6 * 60 * 60  # 6 hodin — retence reportu po ukončení úlohy
IMPORT_DATA_RUNNING_TTL_SECONDS = 48 * 60 * 60  # 48 hodin — maximální očekávaná délka importu

# Procentuální checkpointy sjednoceného progress baru importu (po dokončení dané fáze).
IMPORT_PROGRESS_PHASE_FAILED = 0
IMPORT_PROGRESS_PHASE_DATA_DONE = 25
IMPORT_PROGRESS_PHASE_HISTORY_DONE = 50
IMPORT_PROGRESS_PHASE_FEDORA_DONE = 75
IMPORT_PROGRESS_PHASE_FINISHED = 100

# Fáze životního cyklu importní úlohy (klíč ``import_data_phase_{job_id}``).
IMPORT_PHASE_VALIDATING = "validating"
IMPORT_PHASE_AWAITING_APPROVAL = "awaiting_approval"
IMPORT_PHASE_IMPORTING = "importing"
IMPORT_PHASE_FINISHED = "finished"
IMPORT_PHASE_STOPPED = "stopped"
IMPORT_PHASE_CANCELED = "canceled"
IMPORT_PHASE_FAILED = "failed"

# Diskriminátor terminální fáze ``failed`` (klíč ``import_data_failure_reason_{job_id}``).
IMPORT_FAILURE_REASON_VALIDATION_REJECTED = "validation_rejected"
IMPORT_FAILURE_REASON_ERROR = "error"

# Záznam nemá Fedora cíl vůbec (na rozdíl od ``fedora_waiting_data_import`` — ten na cíl jen čeká).
# Sdíleno mezi hlavním per-záznamovým listem a listem ``Fedora`` (řádky bez skutečného pokusu
# o aktualizaci — zákaznický požadavek, transaction_uid zůstává prázdné).
FEDORA_SKIPPED_ID = "cron.tasks.run_data_import.fedora_skipped"

# Suffixy per-job datových klíčů importní úlohy (bez sufixu ``_{job_id}``). Jedinný zdroj pravdy
# sdílený validačním taskem (persist/expire), importním taskem (terminální finally) a view
# (``_expire_import_data_keys``). Nový per-job klíč se přidává pouze sem.
IMPORT_DATA_JOB_KEY_SUFFIXES = (
    "import_data_validation_results",
    "import_data_validation_details",
    "import_data_validation_ids",
    "import_data_validation_progress",
    "import_data_validation_total",
    "import_data_invalid_records",
    "import_data_failure_reason",
    "import_data_count",
    "import_data_valid",
    "import_data_phase",
    "import_data_primary_keys",
    "import_data_files",
    "import_data_history_record_result_tr",
    "import_fedora_result_tr",
    "import_fedora_target_results_tr",
    "import_data_progress",
    "import_data_progress_details_tr",
    "import_data_progress_ids",
    "import_data_history_progress",
    "import_data_history_total",
    "import_data_fedora_progress",
    "import_data_fedora_total",
    "import_data_files_progress",
    "import_data_files_total",
    "import_data_status_message_tr",
    "import_performed_action",
    "import_data_user",
    "import_data_lock_token",
    "import_data_stop",
)

# Jak často validační task zapisuje JSON snapshot ``import_data_validation_results_{job_id}`` pro report
# (živý seznam ``import_data_validation_details`` se plní ``rpush`` každý řádek). Zrcadlí
# ``HISTORY_REDIS_UPDATE_INTERVAL``.
VALIDATION_REDIS_UPDATE_INTERVAL = 50

# Standardizační pravidlo: do Redis se ukládají pouze ID překladových řetězců (nikoli přeložené
# texty); překlad se provádí až na straně čtenáře (``DataImportProgress`` /
# ``DataImportProgressReportView``) v locale přihlášeného admina. Klíče, které drží překladové
# ID (případně obálku ``{id, params}`` pro parametrizované zprávy), mají suffix ``_tr``, takže je
# z názvu klíče poznat, že hodnotu je třeba před zobrazením přeložit.

# Suffix pro Redis klíče, jejichž hodnota je překladové ID nebo obálka ``{id, params}``.
TRANSLATABLE_KEY_SUFFIX = "_tr"


def translation_value(message_id: str, raw: bool = False, **params) -> str:
    """Zabalí překladové ID (a případné parametry) pro uložení do Redis.

    Pro zprávy bez parametrů vrací přímo ID (plain string) — běžný případ. Pro parametrizované
    zprávy vrací JSON obálku ``{"id": <id>, "params": {...}}``, kterou čtenář rozbalí a interpoluje
    po překladu. Nikdy nevolá ``_()`` — překlad probíhá až na straně čtenáře.

    Pro výjimky, jejichž zpráva je složena za běhu (např. ``str(err)`` z mapperů), použijte
    ``raw=True``: obálka ``{"id": "cron.tasks.run_data_import.error.raw", "params": {"message": ...},
    "raw": true}`` se na čtenáři vrátí doslova bez překladu. ``raw`` je zde samostatný keyword
    argument (ne součást ``params``), aby v obálce skončil na nejvyšší úrovni, kde ho čtenář hledá.

    :param message_id: ID překladového řetězce (dotted key, např.
        ``cron.tasks.run_data_import.finished``).
    :param raw: Pokud ``True``, obálka nese příznak ``raw`` na nejvyšší úrovni a čtenář zprávu
        vrátí doslova (``params["message"]``) bez volání ``_()``.
    :param params: Parametry pro interpolaci přeloženého řetězce (např. ``n``, ``total``). Pro
        výjimku použijte ``raw=True`` a ``message=<str(err)>``.
    :return: Hodnota připravená k zápisu do Redis (ID nebo JSON obálka).
    """
    if raw:
        return json.dumps({"id": message_id, "params": params, "raw": True})
    if not params:
        return message_id
    return json.dumps({"id": message_id, "params": params})


# Registry všech překladových ID, která se ukládají do Redis (přes ``translation_value`` nebo jako
# bare ID do ``_tr`` klíčů / ``validation_result`` / ``additional_info_tr``). Každé ID je zabaleno
# do ``_()``, aby ho ``makemessages``/``xgettext`` extrahoval do .po souborů — hodnoty se nepoužívají
# za běhu (Redis stále dostává pouze bare ID přes ``translation_value``), slouží výhradně jako zdroj
# pro extrakci překladů. Při přidání nového překladového ID ho přidejte do ``TRANSLATABLE_MESSAGE_IDS``,
# jinak zůstane nepřeloženo (``_translate_status_value`` vrátí na čtenáři neaplikovaný key doslova).
TRANSLATABLE_MESSAGE_IDS = (
    _("cron.tasks.run_data_import.validating"),
    _("cron.tasks.run_data_import.stopped_by_user"),
    _("cron.tasks.run_data_import.failed_lock_lost"),
    _("cron.tasks.run_data_import.failed_lock_acquisition"),
    _("cron.tasks.run_data_import.failed_during_data_import"),
    _("cron.tasks.run_data_import.importing_record_data"),
    _("cron.tasks.run_data_import.success"),
    _("cron.tasks.run_data_import.file"),
    _("cron.tasks.run_data_import.rolled_back"),
    _("cron.tasks.run_data_import.creating_history_records"),
    _("cron.tasks.run_data_import.history_record_skipped"),
    _("cron.tasks.run_data_import.history_record_created"),
    _("cron.tasks.run_data_import.failed_during_history"),
    _("cron.tasks.run_data_import.history_record_error"),
    _("cron.tasks.run_data_import.updating_fedora_records"),
    _("cron.tasks.run_data_import.fedora_skipped"),
    _("cron.tasks.run_data_import.fedora_waiting_data_import"),
    _("cron.tasks.run_data_import.fedora_record"),
    _("cron.tasks.run_data_import.fedora_error"),
    _("cron.tasks.run_data_import.fedora_delete_commit_failed"),
    _("cron.tasks.run_data_import.fedora_target_success"),
    _("cron.tasks.run_data_import.fedora_target_error"),
    _("cron.tasks.run_data_import.fedora_target_skipped"),
    _("cron.tasks.run_data_import.fedora_target_unattempted"),
    _("cron.tasks.run_data_import.failed_during_fedora"),
    _("cron.tasks.run_data_import.finalizing"),
    _("cron.tasks.run_data_import.file_import.validating_directory_settings"),
    _("cron.tasks.run_data_import.import_directory_not_configured"),
    _("cron.tasks.run_data_import.file_import.connected"),
    _("cron.tasks.run_data_import.already_exists"),
    _("cron.tasks.run_data_import.file_not_found_in_directory"),
    _("cron.tasks.run_data_import.cannot_read_from_directory"),
    _("cron.tasks.run_data_import.importing_file"),
    _("cron.tasks.run_data_import.file_mime_type"),
    _("cron.tasks.run_data_import.failed_missing_repository_uuid"),
    _("cron.tasks.run_data_import.failed_mime_unsupported"),
    _("cron.tasks.run_data_import.failed_mime_extension_mismatch"),
    _("cron.tasks.run_data_import.failed_mime_not_allowed"),
    _("cron.tasks.run_data_import.finished"),
    _("cron.tasks.run_data_import.cancelled"),
    _("cron.tasks.run_data_import.validation_rejected"),
    _("cron.tasks.run_data_import.validation_done"),
    _("cron.tasks.run_data_import.reset_by_admin"),
    _("core.admin.import_data.record_valid"),
)


class SouborMissingRepositoryUuidError(RuntimeError):
    """Vyvoláno při pokusu o UPDATE binárního souboru, jehož ``repository_uuid`` je None.

    Indikuje poškozená data: záznam ``Soubor`` existuje v DB, ale nemá přiřazený
    Fedora UUID, tedy binární soubor v repositáři neexistuje nebo nebyl nikdy nahrán.
    """

    def __init__(self, soubor_pk, nazev):
        """
        Inicializuje instanci třídy.

        :param soubor_pk: Primární klíč záznamu ``Soubor`` s chybějícím ``repository_uuid``.
        :param nazev: Název souboru, u nějž chybí ``repository_uuid``.
        """
        self.soubor_pk = soubor_pk
        self.nazev = nazev
        super().__init__(
            "Soubor pk={} nazev={!r} has no repository_uuid — record is corrupted".format(soubor_pk, nazev)
        )


class SouborMimeUnsupportedError(RuntimeError):
    """Vyvoláno při importu souboru, jehož detekovaný MIME typ aplikace nepodporuje.

    Indikuje MIME typ mimo mapu podporovaných formátů ``Soubor.MIME_TO_EXTENSIONS``.
    """

    def __init__(self, nazev, mime_type):
        """
        Inicializuje instanci třídy.

        :param nazev: Název importovaného souboru.
        :param mime_type: MIME typ detekovaný z obsahu souboru.
        """
        self.nazev = nazev
        self.mime_type = mime_type
        super().__init__("Soubor nazev={!r}: detected mime type {!r} is not supported".format(nazev, mime_type))


class SouborMimeExtensionMismatchError(RuntimeError):
    """Vyvoláno při importu souboru, jehož přípona neodpovídá MIME typu detekovanému z obsahu.

    Indikuje přejmenovaný soubor (např. JPEG uložený s příponou ``.tif``), jehož import
    by vedl k nekonzistenci mezi názvem a skutečným obsahem souboru.
    """

    def __init__(self, nazev, extension, mime_type):
        """
        Inicializuje instanci třídy.

        :param nazev: Název souboru, u nějž byla zjištěna neshoda.
        :param extension: Přípona odvozená z názvu souboru.
        :param mime_type: MIME typ detekovaný z obsahu souboru.
        """
        self.nazev = nazev
        self.extension = extension
        self.mime_type = mime_type
        super().__init__(
            "Soubor nazev={!r}: extension {!r} does not match detected mime type {!r}".format(
                nazev, extension, mime_type
            )
        )


class SouborMimeNotAllowedError(RuntimeError):
    """Vyvoláno při importu souboru, jehož MIME typ není povolen pro typ navázaného záznamu.

    Whitelisty povolených MIME typů odpovídají kontrole ``Soubor.check_mime_for_url``
    používané při uživatelském uploadu.
    """

    def __init__(self, nazev, mime_type, navazany_ident_cely):
        """
        Inicializuje instanci třídy.

        :param nazev: Název importovaného souboru.
        :param mime_type: MIME typ detekovaný z obsahu souboru.
        :param navazany_ident_cely: Identifikátor navázaného záznamu, pro který MIME typ není povolen.
        """
        self.nazev = nazev
        self.mime_type = mime_type
        self.navazany_ident_cely = navazany_ident_cely
        super().__init__(
            "Soubor nazev={!r}: mime type {!r} is not allowed for record {!r}".format(
                nazev, mime_type, navazany_ident_cely
            )
        )


class ImportLockLostError(RuntimeError):
    """Vyvoláno, když ``refresh_import_lock`` zjistí, že importní lock byl ztracen.

    Použito jako sentinel, aby vnější ``except Exception`` v ``run_data_import`` mohl
    rozlišit ztrátu zámku od ostatních selhání během importu dat a nepřepsal
    konkrétní status message ``failed_lock_lost``.
    """


@shared_task
def send_notifications_enz():
    """
    Každý den zkontrolovat a případně odeslat upozornění uživatelům na základě pole projekt.datum_odevzdani_NZ,

    pokud je projekt ve stavu <P5 a zároveň:
    -- pokud [dnes] + 90 dní = datum_odevzdani_NZ => email E-NZ-01
    -- pokud [dnes] - 1 den = datum_odevzdani_NZ => email E-NZ-02
    """
    try:
        logger.debug("cron.tasks.send_notifications_enz.do.start")
        Mailer.send_enz01()
        logger.debug("cron.tasks.send_notifications.do.send_enz_01.end")
        Mailer.send_enz02()
        logger.debug("cron.tasks.send_notifications_enz.do.end")
    except Exception as err:
        logger.error(
            "cron.tasks.send_notifications_enz.do.error", extra={"error": str(err), "traceback": traceback.format_exc()}
        )


@shared_task
def send_notification_enz03():
    """
    Kontrola a odeslání emailů E-NZ-03 pro akce čekající na archivaci déle než 90 dní.
    """
    try:
        logger.debug("cron.tasks.send_notification_enz03.do.start")
        Mailer.send_enz03()
        logger.debug("cron.tasks.send_notification_enz03.do.end")
    except Exception as err:
        logger.error(
            "cron.tasks.send_notification_enz03.do.error",
            extra={"error": str(err), "traceback": traceback.format_exc()},
        )


@shared_task
def send_notifications_en():
    """Každý den kontrola a odeslání emailů E-N-01 a E-N-02"""
    try:
        logger.debug("cron.tasks.send_notifications_en.do.start")
        dataEn01 = Mailer.get_en01_data()
        for email, projekt_ident_list in dataEn01.items():
            Mailer.send_en01(email, projekt_ident_list)
        dataEn02 = Mailer.get_en02_data()
        for email, projekt_ident_list in dataEn02.items():
            Mailer.send_en02(email, projekt_ident_list)
        logger.debug("cron.tasks.send_notifications_en.do.end")
    except Exception as err:
        logger.error(
            "cron.tasks.send_notifications_en.do.error", extra={"error": str(err), "traceback": traceback.format_exc()}
        )


@shared_task
def delete_personal_data_canceled_projects():
    """
    Rok po zrušení projektu nahradit související údaje v tabulce oznamovatel řetězcem “RRRR-MM-DD: údaj odstraněn”,

    kromě pole projekt.oznamovatel + odstranit projektovou dokumentaci a vytvořit log (jako při archivaci projektu).
    """
    try:
        logger.debug("core.cron.delete_personal_data_canceled_projects.do.start")
        deleted_string = UDAJ_ODSTRANEN
        today = datetime.datetime.now().date()
        year_ago = today - datetime.timedelta(days=365)
        projects = (
            Projekt.objects.filter(stav=PROJEKT_STAV_ZRUSENY)
            .filter(~Q(oznamovatel__email__icontains=deleted_string))
            .filter(
                Q(historie__historie__typ_zmeny__in=(RUSENI_PROJ, RUSENI_STARE_PROJ))
                & Q(historie__historie__datum_zmeny__lt=year_ago)
            )
            .distinct()
        )
        for item in projects:
            item: Projekt
            if item.has_oznamovatel():
                item.active_transaction = FedoraTransaction()
                logger.debug(
                    "core.cron.delete_personal_data_canceled_projects.do.project", extra={"projekt": item.ident_cely}
                )
                item.oznamovatel.email = f"{today.strftime('%Y-%m-%d')}: {deleted_string}"
                item.oznamovatel.adresa = f"{today.strftime('%Y-%m-%d')}: {deleted_string}"
                item.oznamovatel.odpovedna_osoba = f"{today.strftime('%Y-%m-%d')}: {deleted_string}"
                item.oznamovatel.telefon = f"{today.strftime('%Y-%m-%d')}: {deleted_string}"
                item.oznamovatel.poznamka = f"{today.strftime('%Y-%m-%d')}: {deleted_string}"
                item.oznamovatel.save()
                item.archive_project_documentation()
                item.close_active_transaction_when_finished = True
                item.save()
        logger.debug("core.cron.delete_personal_data_canceled_projects.do.end")
    except Exception as err:
        logger.error("core.cron.delete_personal_data_canceled_projects.do.error", extra={"error": err})


@shared_task
def delete_reporter_data_ten_years():
    """
    Deset let po zápisu projektu smazat související záznam z tabulky oznamovatel + odstranit projektovou dokumentaci

    a vytvořit log (jako při archivaci projektu).
    """
    logger.debug("core.cron.delete_reporter_data_canceled_projects.do.start")
    today = datetime.datetime.now().date()
    ten_years_ago = today - datetime.timedelta(days=365 * 10)
    projects = (
        Projekt.objects.filter(oznamovatel__isnull=False)
        .filter(typ_projektu=TYP_PROJEKTU_ZACHRANNY_ID)
        .filter(
            Q(historie__historie__typ_zmeny__in=(ZAPSANI_PROJ, SCHVALENI_OZNAMENI_PROJ))
            & Q(historie__historie__datum_zmeny__lt=ten_years_ago)
        )
        .distinct()
    )
    for item in projects:
        try:
            item.active_transaction = FedoraTransaction()
            logger.debug(
                "core.cron.delete_reporter_data_canceled_projects.do.project.start",
                extra={"ident_cely": item.ident_cely, "transaction": item.active_transaction.uid},
            )
            item.oznamovatel.delete()
            item.archive_project_documentation()
            item.oznamovatel = None
            item.save()
            item.close_active_transaction_when_finished = True
            item.save()
            logger.debug(
                "core.cron.delete_reporter_data_canceled_projects.do.end",
                extra={"ident_cely": item.ident_cely, "transaction": item.active_transaction.uid},
            )
        except Exception as err:
            logger.error("core.cron.delete_reporter_data_canceled_projects.do.error", extra={"error": err})
    logger.debug("core.cron.delete_reporter_data_canceled_projects.do.end")


@shared_task
def change_document_accessibility():
    """
    Každý den změnit přístupnost dokumentů, u kterých datum_zverejneni<=[dnes], a to na přístupnost stanovenou

    v hesláři organizace (podle vazby dokument.organizace), ale nikdy ne na vyšší přístupnost, než má nejlépe
    přístupný připojený archeologický záznam (tj. když mají připojené AZ C a D, bude mít dokument nejvýše C).
    """
    invalidate_model(Dokument)
    invalidate_model(Akce)

    try:
        logger.debug("core.cron.change_document_accessibility.do.start")
        documents = (
            Dokument.objects.filter(datum_zverejneni__lte=datetime.datetime.now().date())
            .annotate(
                min_pristupnost_razeni=Coalesce(
                    Min(F("casti__archeologicky_zaznam__pristupnost__razeni")), PRISTUPNOST_MIN_RAZENI
                )
            )
            .filter(
                Q(pristupnost__razeni__gt=F("min_pristupnost_razeni"))
                & Q(pristupnost__razeni__gt=F("organizace__zverejneni_pristupnost__razeni"))
            )
            .distinct()
        )
        for item in documents:
            item: Dokument
            pristupnost_razeni = item.organizace.zverejneni_pristupnost.razeni
            pristupnost_az = [
                x.archeologicky_zaznam.pristupnost.razeni
                for x in item.casti.all()
                if x.archeologicky_zaznam is not None
            ]
            if pristupnost_az:
                az_pristupnost_razeni = min(pristupnost_az)
                if pristupnost_razeni < az_pristupnost_razeni:
                    pristupnost_razeni = az_pristupnost_razeni
            pristupnost = (
                Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST).filter(razeni=pristupnost_razeni).first()
            )
            save = False
            if item.pristupnost != pristupnost:
                item.pristupnost = pristupnost
                save = True
            if item.licence_id == DOKUMENT_LICENCE_NEZNAMA:
                item.licence = item.organizace.licence
                save = True
            if save:
                item.active_transaction = FedoraTransaction()
                item.close_active_transaction_when_finished = True
                item.save()
                logger.debug(
                    "core.cron.change_document_accessibility.do.dokument", extra={"ident_cely": item.ident_cely}
                )
        logger.debug("core.cron.change_document_accessibility.do.end")
    except Exception as err:
        logger.error("core.cron.change_document_accessibility.do.error", extra={"error": err})


@shared_task
def delete_unsubmited_projects():
    """Každý den smazat projekty ve stavu -1, které vznikly před více než 12 hodinami."""
    logger.debug("core.cron.delete_unsubmited_projects.do.start")
    now_minus_12_hours = timezone.now() - datetime.timedelta(hours=12)
    projekt_query = (
        Projekt.objects.filter(stav=PROJEKT_STAV_VYTVORENY)
        .filter(historie__historie__datum_zmeny__lt=now_minus_12_hours)
        .distinct("id")
    )
    admin_user = User.objects.filter(pk=hesla_dynamicka.ADMIN_USER).first()
    for item in projekt_query:
        item: Projekt
        logger.debug("core.cron.delete_unsubmited_projects.delete_projekt", extra={"ident_cely": item.ident_cely})
        fedora_transaction = FedoraTransaction(main_record=item, transaction_user=admin_user, suppress_message=True)
        item.active_transaction = fedora_transaction
        item.deleted_by_user = admin_user
        try:
            con = FedoraRepositoryConnector(item, fedora_transaction)
            if con.container_exists():
                # Vytvoří proxy /model/deleted/member/X-... ukazující na record/X-...
                con.record_deletion()
                # Tombstone record/X-...; /model/projekt/member/X-... zůstává nedotčen.
                con.delete_container(delete_tombstone=False, delete_link=False)
            if isinstance(item.soubory, SouborVazby):
                for item_file in item.soubory.soubory.all():
                    item_file.suppress_signal = True
                    item_file.delete()
                item.soubory.delete()
                item.soubory = None
            item.suppress_signal = True
            item.delete()
            fedora_transaction.mark_transaction_as_closed()
        except Exception as err:
            fedora_transaction.rollback_transaction()
            logger.error("core.cron.delete_unsubmited_projects.do.error", extra={"error": err})
    logger.debug("core.cron.delete_unsubmited_projects.do.end")


@shared_task
def cancel_old_projects():
    """
    Každý den převést na P8 projekty v P1 starší tří let, které mají plánované datum zahájení více než rok

    v minulosti. Do poznámky ke zrušení uvést “Automatické zrušení projektů starších tří let, u kterých již
    nelze očekávat zahájení.”
    """
    try:
        logger.debug("core.cron.cancel_old_projects.do.start")
        today_minus_3_years = timezone.now() - datetime.timedelta(days=365 * 3)
        today_minus_1_year = timezone.now() - datetime.timedelta(days=365)
        projects = (
            Projekt.objects.filter(stav=PROJEKT_STAV_ZAPSANY)
            .filter(typ_projektu=TYP_PROJEKTU_ZACHRANNY_ID)
            .filter(
                Q(historie__historie__typ_zmeny__in=(ZAPSANI_PROJ, SCHVALENI_OZNAMENI_PROJ))
                & Q(historie__historie__datum_zmeny__lt=today_minus_3_years)
            )
            .annotate(upper=Upper("planovane_zahajeni"))
            .filter(upper__lte=today_minus_1_year)
            .distinct()
        )
        cancelled_string = STARY_PROJEKT_ZRUSEN
        for project in projects:
            project: Projekt
            project.active_transaction = FedoraTransaction()
            project.set_zruseny(User.objects.get(pk=hesla_dynamicka.ADMIN_USER), cancelled_string, RUSENI_STARE_PROJ)
            if project.typ_projektu.pk == TYP_PROJEKTU_ZACHRANNY_ID and project.has_oznamovatel():
                rep_bin_file = project.create_cancel_confirmation_document(
                    User.objects.get(pk=hesla_dynamicka.ADMIN_USER)
                )
            else:
                rep_bin_file = None
            project.close_active_transaction_when_finished = True
            project.save()
            reason = STARY_PROJEKT_ZRUSEN
            if project.ident_cely[0] == OBLAST_CECHY:
                Mailer.send_ep06a(project=project, reason=reason, rep_bin_file=rep_bin_file)
            else:
                Mailer.send_ep06b(project=project, reason=reason, rep_bin_file=rep_bin_file)
            logger.debug("core.cron.cancel_old_projects.do.project", extra={"ident_cely": project.ident_cely})
        logger.debug("core.cron.cancel_old_projects.do.end")
    except Exception as err:
        logger.error("core.cron.cancel_old_projects.do.error", extra={"error": err})


@shared_task
def update_snapshot_fields():
    """Aktualizuje snapshot fields."""
    try:
        logger.debug("core.cron.update_snapshot_fields.do.start")
        for item in ExterniZdroj.objects.filter(
            (Q(autori_snapshot__isnull=True) & Q(externizdrojautor__isnull=False))
            | (Q(editori_snapshot__isnull=True) & Q(externizdrojeditor__isnull=False))
        ):
            item.suppress_signal = True
            item.save()
        for item in Dokument.objects.filter(
            (Q(autori_snapshot__isnull=True) & Q(dokumentautor__isnull=False))
            | (Q(osoby_snapshot__isnull=True) & Q(dokumentosoba__isnull=False))
        ):
            item: Dokument
            item.suppress_signal = True
            item.save()
        for item in Lokalita.objects.filter(
            Q(dalsi_katastry_snapshot__isnull=True) & Q(archeologicky_zaznam__katastry__isnull=False)
        ):
            item: Lokalita
            item.suppress_signal = True
            item.save()
        for item in Akce.objects.filter(Q(vedouci_snapshot__isnull=True) & Q(akcevedouci__isnull=False)):
            item: Akce
            item.suppress_signal = True
            item.set_snapshots()
        for item in Historie.objects.filter(organizace_snapshot__isnull=True):
            item: Historie
            item.suppress_signal = True
            item.save()
        logger.debug("core.cron.update_snapshot_fields.do.end")
    except Exception as err:
        logger.error("core.cron.update_snapshot_fields.do.error", extra={"error": err})


@shared_task
def update_all_redis_snapshots(rewrite_existing=False, classes=None):
    """
    Aktualizuje Redis snapshots pro všechny nebo vybrané třídy modelů.

    :param rewrite_existing: Pokud je ``True``, přepíše i existující záznamy v Redis. Výchozí hodnota je ``False``.
    :param classes: Volitelný seznam tříd modelů, pro které se mají Redis snapshot záznamy aktualizovat.
        Pokud není zadán, použijí se výchozí třídy
        (Akce, Projekt, Dokument, Lokalita, ExterniZdroj, UzivatelSpoluprace, SamostatnyNalez).
    """
    logger.debug("cron.tasks.update_all_redis_snapshots.start")
    r = RedisConnector.get_connection()
    default_classes = (Akce, Projekt, Dokument, Lokalita, ExterniZdroj, UzivatelSpoluprace, SamostatnyNalez)
    classes_list = classes if classes is not None else default_classes
    for current_class in classes_list:
        logger.debug("cron.tasks.update_all_redis_snapshots.class_start", extra={"class_name": current_class.__name__})
        pipe = r.pipeline()
        query = current_class.objects.all()
        if current_class == Dokument:
            query = query.prefetch_related(
                Prefetch(
                    "autori",
                    queryset=Osoba.objects.all().order_by("dokumentautor__poradi"),
                    to_attr="ordered_autors",
                )
            )
        i = 0
        change_items = 0
        for item in query.iterator(chunk_size=1000):
            if rewrite_existing or not r.exists(item.redis_snapshot_id):
                key, value = item.generate_redis_snapshot()
                if key and value:
                    if rewrite_existing:
                        pipe.delete(key)
                    pipe.hset(key, mapping=value)
                    change_items = change_items + 1
                    if (change_items % 1000) == 0:
                        pipe.execute()

            i = i + 1
            if (i % 1000) == 0:
                print(f"\r{i}", end="")
        pipe.execute()
        logger.debug("cron.tasks.update_all_redis_snapshots.class_end", extra={"class_name": current_class.__name__})
    logger.debug("cron.tasks.update_all_redis_snapshots.end")


@shared_task
def update_single_redis_snapshot(class_name: str, record_pk):
    """
    Aktualizuje single redis snapshot.

    :param class_name: Parametr ``class_name`` předává se do volání ``error()``, ovlivňuje větvení podmínek.
    :param record_pk: Identifikátor ``record_pk`` používaný pro dohledání cílového záznamu.
    """
    r = RedisConnector.get_connection()
    if class_name == "Akce":
        item = Akce.objects.get(pk=record_pk)
    elif class_name == "Projekt":
        item = Projekt.objects.get(pk=record_pk)
    elif class_name == "Dokument":
        item = Dokument.objects.get(pk=record_pk)
    elif class_name == "Lokalita":
        item = Lokalita.objects.get(pk=record_pk)
    elif class_name == "ExterniZdroj":
        item = ExterniZdroj.objects.get(pk=record_pk)
    elif class_name == "UzivatelSpoluprace":
        item = UzivatelSpoluprace.objects.get(pk=record_pk)
    elif class_name == "SamostatnyNalez":
        item = SamostatnyNalez.objects.get(pk=record_pk)
    else:
        logger.error("cron.tasks.update_single_redis_snapshot.unsupported_class_name", extra={"class_name": class_name})
        return
    key, value = item.generate_redis_snapshot()
    if key and value:
        r.hset(key, mapping=value)


@shared_task
def update_materialized_views():
    """Aktualizuje materialized views."""
    logger.debug("cron.tasks.update_materialized_views.start")

    query = (
        "REFRESH MATERIALIZED VIEW amcr_heat_pas_l1;"
        "REFRESH MATERIALIZED VIEW amcr_heat_pas_l2;"
        "REFRESH MATERIALIZED VIEW amcr_heat_pas_lx1;"
        "REFRESH MATERIALIZED VIEW amcr_heat_pas_lx2;"
        "REFRESH MATERIALIZED VIEW amcr_heat_pian_l1;"
        "REFRESH MATERIALIZED VIEW amcr_heat_pian_l2;"
        "REFRESH MATERIALIZED VIEW amcr_heat_pian_lx1;"
        "REFRESH MATERIALIZED VIEW amcr_heat_pian_lx2;"
        "REFRESH MATERIALIZED VIEW amcr_heat_projekt_l1;"
        "REFRESH MATERIALIZED VIEW amcr_heat_projekt_l2;"
        "REFRESH MATERIALIZED VIEW amcr_heat_projekt_lx1;"
        "REFRESH MATERIALIZED VIEW amcr_heat_projekt_lx2;"
    )
    cursor = connection.cursor()
    cursor.execute(query)
    logger.debug("cron.tasks.update_materialized_views.end")


@shared_task
def write_value_to_redis(key, value):
    """
    Zapíše value to redis.

    :param key: Textový název nebo klíč ``key`` používaný v rámci operace.
    :param value: Parametr ``value`` předává se do volání ``set()``, vstupuje do návratové hodnoty.

        :return: Vrací n-tici.
    """
    redis_connection = RedisConnector.get_connection()
    redis_connection.set(key, value)
    return key, value


@shared_task
def call_digiarchiv_update_task():
    """Zavolá URL digiarchívu pro spuštění aktualizace dat."""
    logger.debug("cron.tasks.call_digiarchiv_update_task.start")
    url = settings.DIGIARCHIV_UPDATE
    requests.get(url, timeout=10)
    logger.debug("cron.tasks.call_digiarchiv_update_task.end")


def _normalize_import_file_name(name: str) -> str:
    """
    Normalizuje název souboru ze ZIP archivu na formát pro porovnání s mapery.

    :param name: Původní cesta nebo název souboru ze ZIP archivu.
    :return: Název souboru bez adresáře, oříznutý o bílé znaky a převedený na malá písmena.
    """
    if "/" in name:
        name = name.split("/")[-1]
    return name.strip().lower()


def _format_import_primary_key(pk):
    """
    Převede primární klíč importovaného záznamu na text pro validační výstup.

    :param pk: Primární klíč z mapperu, typicky slovník složeného klíče nebo skalární hodnota.
    :return: Textová reprezentace klíče vhodná pro zobrazení ve validační tabulce.
    """
    if isinstance(pk, dict):
        return ", ".join("{}: {}".format(k, v) for k, v in pk.items())
    return str(pk)


def reset_import_job(redis_connector, job_id):
    """Ruční superuživatelský reset zaseklé importní úlohy: uvolní globální lock a úlohu ukončí.

    Určeno pro případ, kdy worker validační/importní úlohy zemřel (OOM/SIGKILL) a lock zůstal
    držený — jediná povolená obnova je tato ruční akce administrátora (žádný automatický reaper).
    Uvolnění locku je token-checked: pokud lock mezitím legitimně získala jiná úloha, je release
    no-op a cizí lock zůstane nedotčen. Postup zrcadlí terminální ``finally`` importních tasků:
    nastaví stop sentinel (případný živý zombie task se zastaví při nejbližší kontrole a sám
    zruší svou právě otevřenou DB transakci), fázi ``failed`` s důvodem ``error``, vyčistí
    ukazatel běžící úlohy uživatele i zpětný odkaz ``IMPORT_DATA_ACTIVE_JOB_KEY``, uvolní případný
    nastagovaný ZIP a per-job datové klíče pouze expiruje (report zůstane stažitelný).

    :param redis_connector: Dekódující Redis spojení.
    :param job_id: Identifikátor resetované importní úlohy.
    """
    logger.warning("cron.tasks.reset_import_job.start", extra={"job_id": job_id})

    def job_key(key):
        return "{}_{}".format(key, job_id)

    def to_str(value):
        return value.decode("utf-8") if isinstance(value, bytes) else value

    # Halt any still-alive task first, then token-checked release so a re-acquired lock is untouched.
    redis_connector.set(job_key("import_data_stop"), 1, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
    lock_token = to_str(redis_connector.get(job_key("import_data_lock_token")))
    if lock_token:
        RedisConnector.release_import_lock(redis_connector, lock_token)

    redis_connector.set(job_key("import_data_phase"), IMPORT_PHASE_FAILED, ex=IMPORT_DATA_EXPIRATION_SECONDS)
    redis_connector.set(
        job_key("import_data_failure_reason"), IMPORT_FAILURE_REASON_ERROR, ex=IMPORT_DATA_EXPIRATION_SECONDS
    )
    redis_connector.set(
        job_key("import_data_status_message_tr"),
        translation_value("cron.tasks.run_data_import.reset_by_admin"),
        ex=IMPORT_DATA_EXPIRATION_SECONDS,
    )

    job_user = to_str(redis_connector.get(job_key("import_data_user")))
    if job_user is not None:
        # Compare-then-delete: only clear the pointer if it still points at this job — a
        # replacement job may have already claimed it.
        RedisConnector.delete_if_value_matches(redis_connector, "import_data_current_job_{}".format(job_user), job_id)
    RedisConnector.delete_if_value_matches(redis_connector, RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, job_id)

    # Free any staged ZIP chunks the dead task never cleaned up (can be hundreds of MB).
    leftover_chunks_raw = redis_connector.get(job_key("import_data_file_chunks"))
    if leftover_chunks_raw:
        try:
            leftover_count = int(leftover_chunks_raw)
        except (TypeError, ValueError):
            leftover_count = 0
        stray_keys = ["import_data_file_{}_{}".format(job_id, i) for i in range(leftover_count)]
        stray_keys.append(job_key("import_data_file_chunks"))
        redis_connector.delete(*stray_keys)

    # Expire (not delete) the per-job data keys so the report stays downloadable during retention.
    count_raw = redis_connector.get(job_key("import_data_count"))
    try:
        count = int(count_raw) if count_raw else 0
    except (TypeError, ValueError):
        count = 0
    pipe = redis_connector.pipeline()
    for suffix in IMPORT_DATA_JOB_KEY_SUFFIXES:
        pipe.expire(job_key(suffix), IMPORT_DATA_EXPIRATION_SECONDS)
    for i in range(count):
        pipe.expire("import_data_{}_record_{}".format(job_id, i), IMPORT_DATA_EXPIRATION_SECONDS)
    pipe.execute()
    logger.warning("cron.tasks.reset_import_job.done", extra={"job_id": job_id, "job_user": job_user})


def _translate_status_value_for_report(raw):
    """Přeloží hodnotu z Redis (ID nebo obálka ``{id, params}``) do aktivního jazyka.

    Zrcadlí ``core.views._translate_status_value`` — nedovolat odtud, aby ``cron.tasks`` (načítaný
    při startu Celery workeru) nezávisel na ``core.views`` na úrovni modulu.

    :param raw: Hodnota z Redis — ``None``, plain ID (str), nebo JSON obálka (str) s ``id`` a
        ``params``.
    :return: Přeložený řetězec, nebo ``None``, pokud je vstup ``None``.
    """
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        obj = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return _(raw)
    if isinstance(obj, dict) and "id" in obj:
        params = obj.get("params") or {}
        if obj.get("raw"):
            return params.get("message", "")
        try:
            return _(obj["id"]).format(**params)
        except (KeyError, IndexError, ValueError):
            return _(obj["id"])
    return _(raw)


def get_or_create_import_report_path(job_id, redis_connector, reports_directory_path):
    """Vrátí cestu k XLSX reportu importní úlohy, poprvé ji odvodí a uloží do Redis.

    Report je vázaný na okamžik prvního volání (typicky začátek validace) — jméno souboru nese
    tento časový otisk plus ``job_id`` pro jednoznačnost. Cesta se persistuje do Redis, aby ji
    validace i navazující import (dvě samostatné Celery úlohy) použily shodně a psaly do stejného
    souboru (zákaznický požadavek: jeden XLSX report na import, dohledatelný podle času startu).

    :param job_id: Identifikátor importní úlohy.
    :param redis_connector: Redis spojení, přes které se cesta persistuje.
    :param reports_directory_path: Adresář, kam se report ukládá (podadresář ``reports``).
    :return: Absolutní cesta k XLSX souboru reportu této úlohy.
    """
    key = "import_data_report_path_{}".format(job_id)
    existing = redis_connector.get(key)
    reports_directory_path = os.path.realpath(reports_directory_path)
    if existing:
        existing = existing.decode("utf-8") if isinstance(existing, bytes) else existing
        if os.path.commonpath((reports_directory_path, os.path.realpath(existing))) == reports_directory_path:
            return existing
        raise ValueError(_("cron.tasks.get_or_create_import_report_path.persisted_path_outside_reports_directory"))
    started_at = timezone.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(reports_directory_path, "import_report_{}_{}.xlsx".format(started_at, job_id))
    if os.path.commonpath((reports_directory_path, os.path.realpath(report_path))) != reports_directory_path:
        raise ValueError(_("cron.tasks.get_or_create_import_report_path.generated_path_outside_reports_directory"))
    redis_connector.set(key, report_path, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
    return report_path


def build_import_report_dataframe(job_id, redis_connector):
    """Sestaví DataFrame reportu importní úlohy z aktuálního stavu v Redis.

    Sdílený mechanismus mezi periodickým ukládáním na disk (``save_import_report_to_disk``,
    volané z ``run_data_import_validation``/``run_data_import``) a stahováním přes
    ``DataImportProgressReportView`` — obě strany čtou stejná Redis data stejným způsobem, takže
    stažený a na disk uložený report si vždy odpovídají.

    :param job_id: Identifikátor importní úlohy.
    :param redis_connector: Dekódující Redis spojení (klíče i hodnoty jako ``str``).
    :return: Dvojice ``(DataFrame, fáze)`` — ``fáze`` je aktuální ``import_data_phase_{job_id}``.
    """
    # cron.tasks callers pass RedisConnector.get_connection() (bytes mode, unlike the decode
    # connection core.views uses) — normalize phase/progress_ids to str so the "0"/"1"/... lookups
    # below match regardless of which connector mode the caller used.
    phase_raw = redis_connector.get("import_data_phase_{}".format(job_id)) or "unknown"
    phase = phase_raw.decode("utf-8") if isinstance(phase_raw, bytes) else phase_raw
    validation_results_raw = json.loads(redis_connector.get("import_data_validation_results_{}".format(job_id)) or "[]")
    validation_results = [
        {**item, "validation_result": _translate_status_value_for_report(item.get("validation_result", ""))}
        for item in validation_results_raw
    ]
    primary_keys = json.loads(redis_connector.get("import_data_primary_keys_{}".format(job_id)) or "{}")
    progress_ids = [
        pid.decode("utf-8") if isinstance(pid, bytes) else pid
        for pid in redis_connector.lrange("import_data_progress_ids_{}".format(job_id), 0, -1)
    ]
    progress_details = redis_connector.lrange("import_data_progress_details_tr_{}".format(job_id), 0, -1)
    serialized_results = {
        rid: _translate_status_value_for_report(detail) for rid, detail in zip(progress_ids, progress_details)
    }
    history_record_result = {
        rid: _translate_status_value_for_report(value)
        for rid, value in json.loads(
            redis_connector.get("import_data_history_record_result_tr_{}".format(job_id)) or "{}"
        ).items()
    }
    fedora_update_result = {
        rid: [_translate_status_value_for_report(item) for item in items]
        for rid, items in json.loads(redis_connector.get("import_fedora_result_tr_{}".format(job_id)) or "{}").items()
    }

    def build_row(item):
        i = item["item_order"]
        return {
            _("core.templates.admin.import_data.import_order"): i + 1,
            _("core.templates.admin.import_data.fila_name"): item.get("file_name", ""),
            _("core.templates.admin.import_data.primary_key_import"): item.get("primary_key_import", ""),
            _("core.templates.admin.import_data.primary_key_database"): primary_keys.get(str(i), ""),
            _("core.templates.admin.validation_result"): item.get("validation_result", ""),
            _("core.templates.admin.status"): serialized_results.get(str(i), ""),
            _("core.templates.admin.import_data.history_record_result"): history_record_result.get(str(i), ""),
            _("core.templates.admin.import_data.fedora_update_result"): ", ".join(fedora_update_result.get(str(i), [])),
        }

    rows = [build_row(item) for item in validation_results]
    if phase in (IMPORT_PHASE_VALIDATING, IMPORT_PHASE_IMPORTING):
        rows = [
            {
                _("core.templates.admin.import_data.import_order"): _(
                    "core.templates.admin.import_data.partial_report_banner"
                )
            }
        ] + rows
    return pd.DataFrame(rows), phase


def build_import_fedora_target_dataframe(job_id, redis_connector):
    """Sestaví DataFrame druhého listu reportu s výsledky Fedora aktualizací po cílech.

    Na rozdíl od hlavního listu (jeden řádek na importovaný záznam) obsahuje jeden řádek na
    skutečně provedenou aktualizaci Fedora metadat nad deduplikovanými cíli z
    ``fedora_update_targets_dict`` — víc importovaných záznamů může sdílet jeden Fedora cíl
    (zákaznický požadavek na list ``Fedora``). Navíc obsahuje řádek pro každý záznam, který žádný
    Fedora cíl neměl (``FEDORA_SKIPPED_ID``) — nový unikátní placeholder výsledku importu, ID
    transakce zůstává prázdné (zákaznický požadavek).

    :param job_id: Identifikátor importní úlohy.
    :param redis_connector: Dekódující Redis spojení.
    :return: DataFrame se sloupci ``ident_cely``, ID transakce Fedora a přeložený výsledek.
    """
    targets_raw = json.loads(redis_connector.get("import_fedora_target_results_tr_{}".format(job_id)) or "[]")
    fedora_result_raw = json.loads(redis_connector.get("import_fedora_result_tr_{}".format(job_id)) or "{}")
    validation_results_raw = json.loads(redis_connector.get("import_data_validation_results_{}".format(job_id)) or "[]")
    skipped_identity_by_record_id = {
        str(item["item_order"]): item.get("primary_key_import", "") for item in validation_results_raw
    }
    columns = [
        _("core.templates.admin.import_data.fedora_target.ident_cely"),
        _("core.templates.admin.import_data.fedora_target.transaction_uid"),
        _("core.templates.admin.import_data.fedora_target.affected_records"),
        _("core.templates.admin.import_data.fedora_target.result"),
    ]

    def build_row(ident_cely, transaction_uid, record_ids, result_id):
        return {
            columns[0]: ident_cely or "",
            columns[1]: transaction_uid or "",
            columns[2]: ", ".join(str(record_id + 1) for record_id in record_ids or []),
            columns[3]: _translate_status_value_for_report(result_id),
        }

    rows = [
        build_row(
            item.get("ident_cely"), item.get("transaction_uid"), item.get("record_ids", []), item.get("result", "")
        )
        for item in targets_raw
    ]
    for record_id, items in fedora_result_raw.items():
        if items == [FEDORA_SKIPPED_ID]:
            rows.append(
                build_row(
                    skipped_identity_by_record_id.get(record_id, ""),
                    None,
                    [int(record_id)],
                    _("cron.tasks.run_data_import.fedora_target_skipped"),
                )
            )
    return pd.DataFrame(rows, columns=columns)


def save_import_report_to_disk(job_id, redis_connector, reports_directory_path):
    """Uloží aktuální stav reportu importní úlohy jako XLSX do adresáře reportů.

    Volá se na začátku validace/importu a po každé fázové tranzici i v except/finally větvích
    (zákaznický požadavek — report musí přežít TTL Redis klíčů). Zápis je
    atomický (dočasný soubor + ``os.replace``), takže souběžné čtení nikdy neuvidí částečně
    zapsaný XLSX. Chyba zápisu se loguje a vrací se ``None``; úvodní snapshot validačního či
    importního tasku tuto hodnotu používá jako fail-closed bránu před další prací.

    :param job_id: Identifikátor importní úlohy.
    :param redis_connector: Dekódující Redis spojení.
    :param reports_directory_path: Adresář reportů (z ``check_import_report_directory``).
    :return: Cesta k uloženému souboru při úspěchu, jinak ``None``.
    """
    report_path = None
    try:
        report_path = get_or_create_import_report_path(job_id, redis_connector, reports_directory_path)
        df, phase = build_import_report_dataframe(job_id, redis_connector)
        fedora_df = build_import_fedora_target_dataframe(job_id, redis_connector)
        # openpyxl's ExcelWriter validates the file extension against the engine, so the temp file
        # must still end in .xlsx (a plain ".tmp" suffix raises ValueError before anything is written).
        base_path, ext = os.path.splitext(report_path)
        tmp_path = "{}.tmp{}".format(base_path, ext)
        with pd.ExcelWriter(tmp_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Import")
            fedora_df.to_excel(writer, index=False, sheet_name="Fedora")
        os.replace(tmp_path, report_path)
        # Both the file and the index are derived from the validated directory, never a Redis path.
        upsert_import_report_index_entry(os.path.dirname(report_path), job_id, os.path.basename(report_path), phase)
        redis_connector.set(
            "import_data_report_saved_path_{}".format(job_id), report_path, ex=IMPORT_DATA_RUNNING_TTL_SECONDS
        )
        return report_path
    except Exception as err:
        logger.error(
            "cron.tasks.save_import_report_to_disk.error",
            extra={"job_id": job_id, "report_path": report_path, "error": str(err)},
        )
        return None


@shared_task
def run_data_import_validation(job_id, user_id, lock_token, performed_action):
    """
    Asynchronně zvaliduje nahraný ZIP archiv hromadného importu.

    Task převezme staged ZIP z Redis (chunky ``import_data_file_{job_id}_{i}``), projde
    všechny CSV řádky přes mappery (``map`` / ``check_required_fields`` / ``import_validation`` /
    ``create_records``) a inkrementálně zapisuje výsledky do Redis, aby je stránka mohla pollovat.
    Samotný import neprovádí — po úspěšné validaci nechává lock držený a přechází do fáze
    ``awaiting_approval``; při chybě nebo zastavení lock uvolní.

    Kontrakt read-only: ``create_records`` se během validace volá pouze pro serializaci a musí
    zůstat read-only — nesmí volat ``save()``/``delete()`` ani jinak měnit databázi.

    Paměťová charakteristika: reassembled komprimovaný blob (~250 MB pro maximální úlohu)
    NENÍ high-water mark workeru. Validační průchod (object-dtype DataFrame + kopie z ``to_dict`` +
    akumulující se seznam ``records``) dosahuje několika GB pro maximální úlohu — worker musí být
    dimenzován na tento peak, ne na ~250 MB komprimovaného blobu.

    :param job_id: Identifikátor importní úlohy (sufix všech per-job Redis klíčů).
    :param user_id: Identifikátor uživatele, který import spustil.
    :param lock_token: Token vlastnictví importního locku, obnovovaný jednou za řádek během validace.
    :param performed_action: Typ akce importu (insert/update/delete) z ``ImportDataAdminForm``.
    """
    logger.debug("cron.tasks.run_data_import_validation.start", extra={"job_id": job_id})

    redis_connector = RedisConnector.get_connection()

    def job_key(key):
        return "{}_{}".format(key, job_id)

    def record_key(record_id):
        return "import_data_{}_record_{}".format(job_id, record_id)

    def chunk_key(index):
        return "import_data_file_{}_{}".format(job_id, index)

    def refresh_lock_or_raise():
        if not RedisConnector.refresh_import_lock(redis_connector, lock_token, IMPORT_DATA_RUNNING_TTL_SECONDS):
            raise ImportLockLostError("Import data lock lost during validation")

    # Per-job datové klíče: na úspěšné cestě se persistují (bez TTL) pro okno awaiting_approval,
    # na terminální cestě expirují na 6 h kvůli retenci reportu. Sdílený zdroj pravdy — viz
    # ``IMPORT_DATA_JOB_KEY_SUFFIXES``.
    per_job_data_keys = list(IMPORT_DATA_JOB_KEY_SUFFIXES)

    failure_reason = None  # None = úspěch; jinak IMPORT_FAILURE_REASON_*
    stopped = False
    chunk_count = 0
    records: list = []
    validation_results: list = []
    invalid_records: list = []
    record_id = 0  # index platných záznamů — sufix Redis klíče a records_count
    row_order = 0  # index každého CSV řádku (platný i neplatný) — item_order ve validačních výsledcích

    def fail_error(message_id, **params):
        # Store the translation ID (not a translated string); the reader translates it.
        nonlocal failure_reason
        failure_reason = IMPORT_FAILURE_REASON_ERROR
        redis_connector.set(
            job_key("import_data_status_message_tr"),
            translation_value(message_id, **params),
            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
        )

    def fail_lock_lost():
        nonlocal failure_reason
        failure_reason = IMPORT_FAILURE_REASON_ERROR
        redis_connector.set(
            job_key("import_data_status_message_tr"),
            translation_value("cron.tasks.run_data_import.failed_lock_lost"),
            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
        )
        redis_connector.set(job_key("import_data_stop"), 1, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)

    def push_validation_result(vr):
        # rpush the live incremental-rendering lists the UI reads; checkpoint the JSON
        # report snapshot every VALIDATION_REDIS_UPDATE_INTERVAL rows.
        validation_results.append(vr)
        redis_connector.rpush(job_key("import_data_validation_details"), json.dumps(vr.to_dict()))
        redis_connector.rpush(job_key("import_data_validation_ids"), vr.item_order)
        redis_connector.incr(job_key("import_data_validation_progress"))
        if len(validation_results) % VALIDATION_REDIS_UPDATE_INTERVAL == 0:
            redis_connector.set(
                job_key("import_data_validation_results"),
                json.dumps([r.to_dict() for r in validation_results]),
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )

    def flush_validation_results():
        """Zapíše kompletní validační seznam před terminálním XLSX snapshotem."""
        redis_connector.set(
            job_key("import_data_validation_results"),
            json.dumps([result.to_dict() for result in validation_results]),
            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
        )

    LookupImportField.clear_cache()
    LookupImportField.clear_records()
    LookupImportField.set_records(records)

    # None until the reports directory check below succeeds; guards the finally block, which must
    # not attempt to save when the directory was never usable (customer requirement — the XLSX
    # report is the durable record of the run).
    reports_directory_path = None

    try:
        # Up-front lock refresh; on loss mirror run_data_import's ImportLockLostError pattern.
        try:
            refresh_lock_or_raise()
        except ImportLockLostError:
            fail_lock_lost()
            return

        # Gate the whole run on a usable report directory (defense in depth — core.admin_sites
        # already checks this before accepting the upload, but settings can change between the
        # POST and this async task running).
        _import_directory_path, reports_directory_path, dir_error = check_import_report_directory()
        if dir_error:
            logger.error(
                "cron.tasks.run_data_import_validation.report_directory_not_configured",
                extra={"job_id": job_id, "error": dir_error},
            )
            fail_error("cron.tasks.run_data_import.import_directory_not_configured")
            return
        if save_import_report_to_disk(job_id, redis_connector, reports_directory_path) is None:
            fail_error("core.admin.import_data.error.unexpected_error")
            return

        # Reassemble the staged ZIP from Redis chunks.
        chunk_count_raw = redis_connector.get(job_key("import_data_file_chunks"))
        chunk_count = int(chunk_count_raw) if chunk_count_raw else 0
        blob = bytearray()
        if chunk_count:
            pipe = redis_connector.pipeline()
            for i in range(chunk_count):
                pipe.get(chunk_key(i))
            chunk_values = pipe.execute()
            for i in range(len(chunk_values)):
                if chunk_values[i]:
                    blob.extend(chunk_values[i])
                # Free each chunk from worker memory as soon as it is appended.
                chunk_values[i] = None
        blob = bytes(blob)

        antivirus_result = Soubor.check_antivirus(io.BytesIO(blob))
        if antivirus_result == AntivirusCheckResult.VIRUS_FOUND:
            fail_error("core.admin.import_data.error.virus_found")
            return
        if antivirus_result == AntivirusCheckResult.CHECK_FAILED:
            logger.warning("cron.tasks.run_data_import_validation.antivirus_check_failed", extra={"job_id": job_id})

        redis_connector.set(
            job_key("import_data_status_message_tr"),
            translation_value("cron.tasks.run_data_import.validating"),
            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
        )

        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as zf:
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
                normalized_imported_file_names = set(
                    [_normalize_import_file_name(file_name) for file_name in file_names]
                )
                if not normalized_imported_file_names.issubset(allowed_file_names):
                    raise ImportDataUnsupportedFilesError(normalized_imported_file_names - allowed_file_names)
                file_names.sort(
                    key=lambda fn: mapper_key_order.get(_normalize_import_file_name(fn), len(mapper_key_order))
                )
                # Lazy import to avoid a module-load cycle: the uncompressed-size guardrail lives on
                # the admin site next to IMPORT_DATA_REDIS_CHUNK_SIZE.
                from core.admin_sites import AmcrCustomAdminSite

                total_uncompressed_size = sum(zf.getinfo(fn).file_size for fn in file_names)
                if total_uncompressed_size > AmcrCustomAdminSite.IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE:
                    raise ValueError("core.admin.import_data.error.zip_too_large")

                # Best-effort denominator for the validation progress bar: count data rows
                # across all CSVs. The sheets stay transient — the main loop re-reads each file, and
                # any real parse error surfaces there, not here.
                total_rows = 0
                seen_in_batch_by_mapper: dict[str, set] = {}
                for file_name in file_names:
                    try:
                        with zf.open(file_name) as file:
                            total_rows += len(pd.read_csv(file, dtype=str, usecols=[0]))
                    except Exception:
                        pass
                redis_connector.set(
                    job_key("import_data_validation_total"), total_rows, ex=IMPORT_DATA_RUNNING_TTL_SECONDS
                )

                for file_name in file_names:
                    with zf.open(file_name) as file:
                        sheet = pd.read_csv(file, dtype=str)
                    file_name = _normalize_import_file_name(file_name)
                    mapper_class = ImportModelMapper.get_import_data_mapper(file_name)
                    seen_in_batch = seen_in_batch_by_mapper.setdefault(file_name, set())
                    try:
                        mapper_class.validate_batch_ordering(sheet.to_dict("records"))
                    except ImportDataBatchOrderingError as err:
                        push_validation_result(
                            ImportDataValidationResult(
                                item_order=row_order,
                                file_name=file_name,
                                validation_result=str(err),
                            )
                        )
                        invalid_records.append(row_order)
                        row_order += 1
                        continue
                    for idx, row in sheet.iterrows():
                        # Refresh the lock once per row and poll the stop sentinel — the same cadence
                        # the import task uses at the top of its record loop.
                        refresh_lock_or_raise()
                        if redis_connector.get(job_key("import_data_stop")) is not None:
                            stopped = True
                            redis_connector.set(
                                job_key("import_data_status_message_tr"),
                                translation_value("cron.tasks.run_data_import.stopped_by_user"),
                                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                            )
                            return
                        # Throttle the human-readable status message to one write per
                        # VALIDATION_REDIS_UPDATE_INTERVAL rows (plus the first row) — the numeric
                        # progress bar is driven separately by import_data_validation_progress, so
                        # this label only needs to advance coarsely. Avoids one Redis SET per row.
                        if row_order % VALIDATION_REDIS_UPDATE_INTERVAL == 0:
                            redis_connector.set(
                                job_key("import_data_status_message_tr"),
                                translation_value(
                                    "cron.tasks.run_data_import.validating", n=row_order + 1, total=total_rows
                                ),
                                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                            )
                        if mapper_class:
                            try:
                                mapper = mapper_class(row.to_dict())
                                record = mapper.map(performed_action, serialize=True, include_primary_key=True)
                                mapper.check_required_fields(performed_action)
                                primary_key = mapper.import_validation(
                                    performed_action, user_id, seen_in_batch=seen_in_batch
                                )
                                # create_records is called for serialization only and must remain
                                # read-only — it must not call save()/delete() or otherwise mutate
                                # the DB during validation (read-only contract).
                                records += mapper.create_records(performed_action)
                                record["__file_name"] = file_name
                            except ImportDataIntegrityError as err:
                                push_validation_result(
                                    ImportDataValidationResult(
                                        item_order=row_order,
                                        file_name=file_name,
                                        primary_key_import=_format_import_primary_key(err.record_id),
                                        validation_result=str(err),
                                    )
                                )
                                invalid_records.append(row_order)
                            except ImportDataError as err:
                                push_validation_result(
                                    ImportDataValidationResult(
                                        item_order=row_order,
                                        file_name=file_name,
                                        validation_result=str(err),
                                    )
                                )
                                invalid_records.append(row_order)
                            else:
                                records.append(record)
                                push_validation_result(
                                    ImportDataValidationResult(
                                        item_order=row_order,
                                        file_name=file_name,
                                        primary_key_import=_format_import_primary_key(primary_key),
                                        validation_result="core.admin.import_data.record_valid",
                                    )
                                )
                                redis_connector.set(
                                    record_key(record_id),
                                    json.dumps(record),
                                    ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                                )
                                record_id += 1
                            row_order += 1
                        else:
                            raise ImportDataUnsupportedFileError(file_name)
                if row_order == 0:
                    raise ImportDataEmptyError()
        except ImportLockLostError:
            fail_lock_lost()
            return
        except zipfile.BadZipFile:
            fail_error("core.admin.import_data.error.bad_zip_file")
            return
        except (ImportDataUnsupportedFilesError, ImportDataUnsupportedFileError) as err:
            fail_error("cron.tasks.run_data_import.error.raw", raw=True, message=str(err))
            return
        except ImportDataEmptyError as err:
            fail_error("cron.tasks.run_data_import.error.raw", raw=True, message=str(err))
            return
        except ImportDataMissingFileError as err:
            fail_error("cron.tasks.run_data_import.error.raw", raw=True, message=str(err))
            return
        except ValueError as err:
            # ValueError carries a translation ID (e.g. zip_too_large) raised above.
            fail_error(str(err))
            return
        except Exception:
            logger.exception("cron.tasks.run_data_import_validation.unexpected_error", extra={"job_id": job_id})
            fail_error("core.admin.import_data.error.unexpected_error")
            return

        # Success path: all files parsed. Finalize the per-job keys the import phase/report consume.
        record_count = record_id
        redis_connector.set(job_key("import_data_count"), record_count, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(
            job_key("import_data_valid"), "1" if not invalid_records else "0", ex=IMPORT_DATA_RUNNING_TTL_SECONDS
        )
        redis_connector.set(
            job_key("import_data_validation_results"),
            json.dumps([r.to_dict() for r in validation_results]),
            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
        )
        redis_connector.set(job_key("import_data_primary_keys"), json.dumps({}), ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(job_key("import_data_files"), json.dumps([]), ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(
            job_key("import_data_history_record_result_tr"), json.dumps({}), ex=IMPORT_DATA_RUNNING_TTL_SECONDS
        )
        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps({}), ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(
            job_key("import_fedora_target_results_tr"), json.dumps([]), ex=IMPORT_DATA_RUNNING_TTL_SECONDS
        )
        redis_connector.set(job_key("import_data_progress"), 0, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        if invalid_records:
            # Distinguish validation-rejected (fixable invalid rows) from a crash:
            # terminal failed phase with the lock released, but a distinct failure reason and a
            # distinct status message carrying the invalid-row count.
            redis_connector.set(
                job_key("import_data_invalid_records"),
                json.dumps(invalid_records),
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
            failure_reason = IMPORT_FAILURE_REASON_VALIDATION_REJECTED
            # Store the translation ID + the invalid-row count as an envelope; the reader interpolates
            # after translating. Never wrap _() in an f-string.
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.validation_rejected", count=len(invalid_records)),
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
        else:
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.validation_done"),
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
    finally:
        LookupImportField.clear_records()
        LookupImportField.clear_cache()

        # Free the staged ZIP as soon as validation is done with the bytes — the import task
        # consumes the per-record JSON keys, not the ZIP.
        chunk_keys = [chunk_key(i) for i in range(chunk_count)]
        chunk_keys.append(job_key("import_data_file_chunks"))
        redis_connector.delete(*chunk_keys)

        all_data_keys = [job_key(k) for k in per_job_data_keys]
        all_data_keys += [record_key(i) for i in range(record_id)]

        if not stopped and failure_reason is None:
            # Validation OK, all rows valid → hold the lock across awaiting_approval and persist the
            # lock and every per-job data key (remove the TTL) so a slow reviewer does not find the
            # job gone. No refresher runs during awaiting_approval.
            if not RedisConnector.finalize_validation(redis_connector, job_id):
                failure_reason = IMPORT_FAILURE_REASON_ERROR
                redis_connector.set(
                    job_key("import_data_status_message_tr"),
                    translation_value("cron.tasks.run_data_import.failed_lock_lost"),
                    ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                )
                redis_connector.set(job_key("import_data_stop"), 1, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
                stopped = False
            else:
                persist_pipe = redis_connector.pipeline()
                for key in all_data_keys:
                    persist_pipe.persist(key)
                # The per-user "current job" pointer is keyed by user_id, not job_id, so it is NOT in
                # per_job_data_keys. Persist it too on the success path — otherwise its 6 h TTL from the
                # POST expires during a long awaiting_approval review and the owner is locked out of
                # their own still-valid, still-lock-holding job ("Leave and come back" case).
                persist_pipe.persist("import_data_current_job_{}".format(user_id))
                # Keep the lock → job back-reference alive exactly as long as the (now persisted) lock,
                # so a manual reset can still target this job during a long awaiting_approval review.
                persist_pipe.persist(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY)
                persist_pipe.execute()
        if stopped or failure_reason is not None:
            # Terminal failure/stop → release the lock, clear the per-user pointer, and expire (not
            # delete) the data keys to 6 h so the page can still show why validation failed and the
            # report stays downloadable.
            if stopped:
                redis_connector.set(job_key("import_data_phase"), IMPORT_PHASE_STOPPED)
            else:
                redis_connector.set(job_key("import_data_phase"), IMPORT_PHASE_FAILED)
                redis_connector.set(job_key("import_data_failure_reason"), failure_reason)
            RedisConnector.release_import_lock(redis_connector, lock_token)
            user_pointer = redis_connector.get(job_key("import_data_user"))
            if user_pointer is not None:
                if isinstance(user_pointer, bytes):
                    user_pointer = user_pointer.decode("utf-8")
                # Compare-then-delete: a replacement job may already own this pointer (r3703505227).
                RedisConnector.delete_if_value_matches(
                    redis_connector, "import_data_current_job_{}".format(user_pointer), job_id
                )
            RedisConnector.delete_if_value_matches(redis_connector, RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, job_id)
            expire_pipe = redis_connector.pipeline()
            for key in all_data_keys:
                expire_pipe.expire(key, IMPORT_DATA_EXPIRATION_SECONDS)
            expire_pipe.execute()

        # Terminal snapshot — phase is now awaiting_approval/stopped/failed above, so this is the
        # report an operator sees if they never return to the polling page.
        if reports_directory_path:
            flush_validation_results()
            save_import_report_to_disk(job_id, redis_connector, reports_directory_path)

    logger.debug(
        "cron.tasks.run_data_import_validation.end",
        extra={"job_id": job_id, "failure_reason": failure_reason, "stopped": stopped, "record_count": record_id},
    )


@shared_task
def run_data_import(job_id, user_id, lock_token):
    """
    Spustí data import.

    :param job_id: Identifikátor objektu ``job``.
    :param user_id: Identifikátor objektu ``user``.
    :param lock_token: Token pro ověření vlastnictví importního zámku v Redis.

    Možné hodnoty Redis klíče ``import_data_status_message_tr_{job_id}`` (ukládá se překladové
    ID, případně obálka ``{id, params}`` pro parametrizované zprávy; překlad provádí až čtenář
    v locale přihlášeného admina — viz ``translation_value`` a ``_translate_status_value``):

    .. list-table::
        :header-rows: 1
        :widths: 35 65

        * - Hodnota stavu
          - Situace, kdy se stav nastaví
        * - ``cron.tasks.run_data_import.failed_lock_lost``
          - Import už běžel, ale při obnově Redis locku se zjistí, že task lock ztratil.
        * - ``cron.tasks.run_data_import.failed_lock_acquisition``
          - Task na začátku nezíská nebo neobnoví importní lock, takže import nepokračuje.
        * - ``cron.tasks.run_data_import.importing_record_data {n}/{total}``
          - Během hlavní fáze importu dat, před zpracováním jednotlivého záznamu.
        * - ``cron.tasks.run_data_import.stopped_by_user``
          - Uživatel zastavil import přes ``import_data_stop_{job_id}``.
        * - ``cron.tasks.run_data_import.failed_during_data_import``
          - Selže zpracování datového záznamu, databázová transakce nebo hlavní fáze importu dat.
        * - ``cron.tasks.run_data_import.creating_history_records``
          - Hlavní import dat doběhl bez chyby a začíná fáze vytváření historie.
        * - ``cron.tasks.run_data_import.creating_history_records {n}/{total}``
          - Během fáze historie, před vytvořením konkrétního historického záznamu.
        * - ``cron.tasks.run_data_import.failed_during_history``
          - Selže vytvoření některého záznamu historie.
        * - ``cron.tasks.run_data_import.updating_fedora_records``
          - Historie doběhla bez chyby a začíná fáze aktualizace Fedora metadat.
        * - ``cron.tasks.run_data_import.updating_fedora_records {n}/{total}``
          - Během aktualizace jednotlivých Fedora záznamů.
        * - ``cron.tasks.run_data_import.failed_during_fedora``
          - Selže uložení metadat do Fedory pro některý z dotčených záznamů.
        * - ``cron.tasks.run_data_import.finalizing``
          - Fedora fáze doběhla bez chyby a import přechází do finální fáze.
        * - ``cron.tasks.run_data_import.file_import.validating_directory_settings``
          - Před importem binárních souborů se kontroluje konfigurace importního adresáře.
        * - ``cron.tasks.run_data_import.import_directory_not_configured``
          - Import souborů je potřeba, ale chybí nebo je neplatná konfigurace ``DIRECTORY_PATH``.
        * - ``cron.tasks.run_data_import.file_import.connected``
          - Konfigurace importního adresáře je validní a začíná příprava importu souborů.
        * - ``cron.tasks.run_data_import.importing_file {n}/{total}: {filename} ({ident_cely})``
          - Během importu konkrétního binárního souboru.
        * - ``cron.tasks.run_data_import.cannot_read_from_directory``
          - Při importu souborů nastane chyba čtení z adresáře nebo zpracování souboru.
        * - ``cron.tasks.run_data_import.finished``
          - Import doběhl úspěšně, nebyl zastaven a nebyla nastavena chyba.

    :raises ValueError: Vyvolá se při splnění podmínky ``isinstance(record, Model)``; nebo s textem
        "Missing required DIRECTORY_PATH setting".
    """
    logger.debug("cron.tasks.run_data_import.start", extra={"job_id": job_id})

    redis_connector = RedisConnector().get_connection()
    record_count = 0
    failed = True
    stopped = False  # initialized up front so the terminal finally can set the phase safely
    # None until the reports directory check below succeeds; guards the except/finally blocks,
    # which must not attempt to save when the directory was never usable (customer requirement —
    # the XLSX report is the durable record of the run).
    reports_directory_path = None
    LookupImportField.clear_cache()
    LookupImportField.clear_records()

    try:

        def job_key(key):
            return "{}_{}".format(key, job_id)

        def record_key(record_id):
            return "import_data_{}_record_{}".format(job_id, record_id)

        def refresh_import_lock():
            if not RedisConnector.refresh_import_lock(redis_connector, lock_token, IMPORT_DATA_RUNNING_TTL_SECONDS):
                redis_connector.set(
                    job_key("import_data_status_message_tr"),
                    translation_value("cron.tasks.run_data_import.failed_lock_lost"),
                )
                redis_connector.set(job_key("import_data_stop"), 1)
                raise ImportLockLostError("Import data lock lost")

        if not RedisConnector.refresh_import_lock(redis_connector, lock_token, IMPORT_DATA_RUNNING_TTL_SECONDS):
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.failed_lock_acquisition"),
            )
            redis_connector.set(job_key("import_data_stop"), 1)
            logger.warning("cron.tasks.run_data_import.lock_not_owned", extra={"job_id": job_id})
            return

        # Gate the whole run on a usable report directory (defense in depth — core.admin_sites
        # already checks this before accepting the upload, but settings can change between the
        # upload and this async task running).
        _import_directory_path, reports_directory_path, dir_error = check_import_report_directory()
        if dir_error:
            logger.error(
                "cron.tasks.run_data_import.report_directory_not_configured",
                extra={"job_id": job_id, "error": dir_error},
            )
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.import_directory_not_configured"),
            )
            redis_connector.set(job_key("import_data_stop"), 1)
            return
        if save_import_report_to_disk(job_id, redis_connector, reports_directory_path) is None:
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.failed_during_data_import"),
            )
            redis_connector.set(job_key("import_data_stop"), 1)
            logger.error("cron.tasks.run_data_import.initial_report_save_failed", extra={"job_id": job_id})
            return

        record_count_raw = redis_connector.get(job_key("import_data_count"))
        record_count = int(record_count_raw.decode("utf-8")) if record_count_raw else 0
        if record_count <= 0:
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.failed_during_data_import"),
            )
            redis_connector.set(job_key("import_data_stop"), 1)
            redis_connector.set(
                job_key("import_data_progress"),
                IMPORT_PROGRESS_PHASE_FAILED,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
            logger.error(
                "cron.tasks.run_data_import.invalid_record_count",
                extra={"job_id": job_id, "record_count": record_count, "record_count_raw": record_count_raw},
            )
            return
        performed_action_raw = redis_connector.get(job_key("import_performed_action"))
        performed_action = performed_action_raw.decode("utf-8") if performed_action_raw else None
        redis_connector.delete(job_key("import_data_progress_ids"), job_key("import_data_progress_details_tr"))
        redis_connector.set(job_key("import_data_files"), json.dumps([]), ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(
            job_key("import_data_history_record_result_tr"), json.dumps({}), ex=IMPORT_DATA_RUNNING_TTL_SECONDS
        )
        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps({}), ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(
            job_key("import_fedora_target_results_tr"), json.dumps([]), ex=IMPORT_DATA_RUNNING_TTL_SECONDS
        )
        failed = False
        import_primary_keys = {}
        import_history_record_result = {}
        mapper_classes = {}
        import_files_list: list[Soubor] = []
        import_files_record_ids: set = set()
        stopped = False
        fedora_update_targets_dict: dict = {}
        fedora_update_targets_record_ids_dict = defaultdict(set)
        updated_history_dict = defaultdict(lambda: {"files": set(), "record_ids": set()})
        import_fedora_result = defaultdict(list)
        # One entry per planned deduplicated Fedora target (not per import record) — including
        # targets that remain unattempted after a failure or stop.
        fedora_target_items: list = []
        fedora_target_results: list = []
        transaction_user = User.objects.get(pk=user_id)

        pending_fedora_update = []
        pending_history_update = []
        pending_soubor_fedora_deletes: list = []
        # Ordered queue of Fedora deletion transactions committed only once the database transaction
        # has committed, so the database is the single commit point.
        pending_fedora_delete_commits: list = []

        def queue_fedora_delete_commit(record_id, fedora_transaction, identity=None):
            """Zařadí Fedora transakci mazání do fronty potvrzované až po commitu databáze.

            :param record_id: Pořadové číslo importovaného záznamu, pod kterým se hlásí případné selhání.
            :param fedora_transaction: Transakce, která se potvrdí až po úspěšném commitu databáze.
            :param identity: Popis mazaného objektu pro jeho dohledání ve Fedoře, pokud potvrzení selže."""
            pending_fedora_delete_commits.append(
                {"record_id": record_id, "transaction": fedora_transaction, "identity": identity or {}}
            )

        def rollback_pending_fedora_delete_commits():
            """Zruší všechny dosud nepotvrzené Fedora transakce mazání a vyprázdní frontu.

            Volá se na každé cestě, která ruší datovou fázi, aby ve Fedoře nezůstaly otevřené transakce
            po záznamech zpracovaných před chybou."""
            for entry in pending_fedora_delete_commits:
                try:
                    entry["transaction"].rollback_transaction()
                except Exception as rollback_err:
                    logger.error(
                        "cron.tasks.run_data_import.fedora_delete_rollback.error",
                        extra={"job_id": job_id, "record_id": entry["record_id"], "error": rollback_err},
                    )
            pending_fedora_delete_commits.clear()

        def commit_pending_fedora_delete_commits():
            """Potvrdí frontu Fedora transakcí mazání po úspěšném commitu databáze.

            Spouští se přes ``transaction.on_commit``, takže při rollbacku databáze neproběhne vůbec —
            databáze je jediný bod commitu. Selhání jednoho potvrzení nezastaví zbytek fronty: data jsou
            už potvrzená a zbývající mazání musí doběhnout. Nedokončené mazání zůstane ve Fedoře jako
            osiřelý objekt bez řádku v databázi, proto se loguje a hlásí u dotčeného záznamu. Metoda
            nesmí vyhodit výjimku — ta by na výstupu z ``atomic()`` označila potvrzený import za chybu."""
            failed_commits = False
            for entry in pending_fedora_delete_commits:
                try:
                    entry["transaction"].mark_transaction_as_closed()
                except Exception as commit_err:
                    failed_commits = True
                    logger.error(
                        "cron.tasks.run_data_import.fedora_delete_commit.error",
                        extra={
                            "job_id": job_id,
                            "record_id": entry["record_id"],
                            "identity": entry["identity"],
                            "error": commit_err,
                        },
                    )
                    # Raw error envelope: composed at runtime from a translated fragment plus the
                    # identity of the object an operator has to clean up in Fedora by hand.
                    import_fedora_result[entry["record_id"]].append(
                        translation_value(
                            "cron.tasks.run_data_import.fedora_delete_commit_failed",
                            raw=True,
                            message=(
                                _("cron.tasks.run_data_import.fedora_delete_commit_failed")
                                + " "
                                + str(entry["identity"])
                                + ": "
                                + str(commit_err)
                            ),
                        )
                    )
            pending_fedora_delete_commits.clear()
            if failed_commits:
                # Must not raise either — an exception here would escape on_commit() and mislabel
                # the already-committed import as failed.
                try:
                    redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                except Exception as redis_err:
                    logger.error(
                        "cron.tasks.run_data_import.fedora_delete_commit.redis_write_failed",
                        extra={"job_id": job_id, "error": redis_err},
                    )

        def add_updated_history(mapper_class, history_target, record_id):
            if history_target:
                entry = updated_history_dict[(history_target.__class__, history_target.pk)]
                entry["files"].add(mapper_class.get_file_name_for_mapper(mapper_class))
                entry["record_ids"].add(record_id)

        def add_item_fedora_update_target(items, record_id):
            for item in items:
                if item is None:
                    continue
                if isinstance(item, tuple) and len(item) == 2:
                    item_class, item_pk = item
                    record = item_class.objects.get(pk=item_pk)
                    if getattr(record, "ident_cely", None):
                        converted_key = record.ident_cely
                        fedora_update_targets_dict.setdefault(converted_key, None)
                        fedora_update_targets_record_ids_dict[converted_key].add(record_id)
                        continue
                fedora_update_targets_dict.setdefault(item, None)
                fedora_update_targets_record_ids_dict[item].add(record_id)

        def fedora_target_identity(item):
            """Return a stable, actionable identity without relying on a model instance repr."""
            if isinstance(item, str):
                return item
            if isinstance(item, tuple) and len(item) == 2:
                item_class, item_pk = item
                model_label = getattr(getattr(item_class, "_meta", None), "label", item_class.__name__)
                return "{}:{}".format(model_label, item_pk)
            return str(item)

        # Tracks whether the data-phase atomic() block was rolled back (via set_rollback or a
        # propagating exception). Drives the success -> rolled_back relabel.
        data_rolled_back = False
        try:
            with transaction.atomic():
                for record_id in range(record_count):
                    refresh_import_lock()
                    primary_key_record = None
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value(
                            "cron.tasks.run_data_import.importing_record_data",
                            n=record_id + 1,
                            total=record_count,
                        ),
                    )
                    try:
                        if performed_action in (
                            ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                        ):
                            fedora_transaction = DryRunFedoraTransaction()
                        else:
                            fedora_transaction = FedoraDeletionOnlyTransaction()
                            fedora_transaction.override_tombstone = True
                        serialized_record = json.loads(redis_connector.get(record_key(record_id)).decode("utf-8"))
                        mapper_class = ImportModelMapper.get_import_data_mapper(serialized_record.pop("__file_name"))
                        mapper_classes[record_id] = mapper_class
                        records = mapper_class(serialized_record).create_records(performed_action)
                        if (
                            performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE
                            and not mapper_class.allow_update
                        ):
                            raise ImportDataError(_("cron.tasks.run_data_import.update_now_allowed"))
                        if mapper_class == SouborMapper:
                            if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
                                for record in records:
                                    record: Soubor
                                    fedora_update_targets = mapper_class.fedora_update_targets(record)
                                    related_history_targets = SouborMapper.get_related_history_targets(record)
                                    for related_target in related_history_targets:
                                        if getattr(related_target, "ident_cely", None):
                                            fedora_update_targets.add((related_target.__class__, related_target.pk))
                                        add_updated_history(mapper_class, related_target, record_id)
                                    add_item_fedora_update_target(fedora_update_targets, record_id)
                                    pending_soubor_fedora_deletes.append(
                                        {
                                            "record_id": record_id,
                                            "soubor": record,
                                            "navazany_objekt": (
                                                record.vazba.navazany_objekt if record.vazba_id else None
                                            ),
                                        }
                                    )
                                # This transaction carries no Fedora work (the delete is deferred below),
                                # but it is still queued so that nothing commits inside atomic().
                                queue_fedora_delete_commit(record_id, fedora_transaction)
                                redis_connector.rpush(job_key("import_data_progress_ids"), record_id)
                                redis_connector.rpush(
                                    job_key("import_data_progress_details_tr"), "cron.tasks.run_data_import.success"
                                )
                                continue
                            for record in records:
                                record.import_record_id = record_id
                            import_files_list += records
                            import_files_record_ids.add(record_id)
                            record: Soubor = records[0]
                            redis_connector.rpush(job_key("import_data_progress_ids"), record_id)
                            redis_connector.rpush(
                                job_key("import_data_progress_details_tr"), "cron.tasks.run_data_import.file"
                            )
                            continue
                        for record in records:
                            record.active_transaction = fedora_transaction
                            if isinstance(record, ModelWithMetadata):
                                primary_key_record = record
                            elif hasattr(record, "ident_cely") and primary_key_record is None:
                                primary_key_record = record
                            if mapper_class == UzivatelOpravneniMapper:
                                record: User
                                group = Group.objects.get(name=serialized_record["skupina"])
                                if (
                                    performed_action
                                    in (
                                        ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                                        ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                                    )
                                    and group not in record.groups.all()
                                ):
                                    record.groups.add(group)
                                elif (
                                    performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE
                                    and group in record.groups.all()
                                ):
                                    record.groups.remove(group)
                                else:
                                    continue
                                pending_fedora_update.append((mapper_class, record))
                                pending_history_update.append((mapper_class, record))
                            elif mapper_class == UzivatelNotifikaceMapper:
                                record: User
                                group = UserNotificationType.objects.get(ident_cely=serialized_record["notifikace"])
                                if (
                                    performed_action
                                    in (
                                        ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                                        ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                                    )
                                    and group not in record.notification_types.all()
                                ):
                                    record.notification_types.add(group)
                                elif (
                                    performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE
                                    and group in record.notification_types.all()
                                ):
                                    record.notification_types.remove(group)
                                else:
                                    continue
                                pending_fedora_update.append((mapper_class, record))
                                pending_history_update.append((mapper_class, record))
                            else:
                                if performed_action in (
                                    ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                                    ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                                ):
                                    if isinstance(record, Model):
                                        record_db = mapper_class.load_record_from_db(record)
                                        record_db_dict = model_to_dict(record_db) if record_db else None
                                        mapper_class.create_relations(record)
                                        mapper_class.record_postprocessing(record, performed_action, fedora_transaction)
                                        record.save()
                                        record_saved = mapper_class.load_record_from_db(record)
                                        pending_fedora_update.append((mapper_class, record_saved or record))
                                        record_dict = (
                                            model_to_dict(record_saved) if record_saved else model_to_dict(record)
                                        )
                                        if (
                                            performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT
                                            or record_dict != record_db_dict
                                        ) and mapper_class is not SouborMapper:
                                            pending_history_update.append((mapper_class, record_saved or record))

                                    else:
                                        raise ValueError(
                                            "{} {}".format(_("cron.tasks.run_data_import.error.not_model"), record_id)
                                        )
                                elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
                                    fedora_update_targets = mapper_class.fedora_update_targets(record)
                                    if isinstance(record, Model):
                                        fedora_update_targets = {
                                            target
                                            for target in fedora_update_targets
                                            if target != (record.__class__, record.pk)
                                            and target != getattr(record, "ident_cely", None)
                                        }
                                    add_item_fedora_update_target(fedora_update_targets, record_id)
                                    history_target = mapper_class.get_record_history(record)
                                    if history_target is not None and history_target is not record:
                                        add_updated_history(mapper_class, history_target, record_id)
                                    record.active_transaction = fedora_transaction
                                    record.delete()
                        # Defer the real commit until the database transaction has committed
                        # mirrors the Soubor delete deferral below.
                        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
                            deleted_record = primary_key_record or (records[0] if records else None)
                            queue_fedora_delete_commit(
                                record_id,
                                fedora_transaction,
                                {"ident_cely": getattr(deleted_record, "ident_cely", None)},
                            )
                        else:
                            fedora_transaction.mark_transaction_as_closed()

                        for item in pending_history_update:
                            mapper_class, record = item
                            add_updated_history(mapper_class, mapper_class.get_record_history(record), record_id)
                        pending_history_update.clear()

                        for item in pending_fedora_update:
                            mapper_class, record = item
                            add_item_fedora_update_target(mapper_class.fedora_update_targets(record), record_id)
                        pending_fedora_update.clear()

                        add_item_fedora_update_target(fedora_transaction.updated_ident_cely, record_id)
                        logger.info(
                            "cron.tasks.run_data_import.success", extra={"record_id": record_id, "job_id": job_id}
                        )
                        redis_connector.rpush(job_key("import_data_progress_ids"), record_id)
                        redis_connector.rpush(
                            job_key("import_data_progress_details_tr"), "cron.tasks.run_data_import.success"
                        )
                        if primary_key_record:
                            import_primary_keys[record_id] = "ident_cely: {}".format(primary_key_record.ident_cely)
                        else:
                            import_primary_keys[record_id] = records[0].pk
                        redis_connector.set(
                            job_key("import_data_primary_keys"),
                            json.dumps(import_primary_keys),
                            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                        )
                    except Exception as err:
                        logger.info(
                            "cron.tasks.run_data_import.error",
                            extra={"error": err, "record_id": record_id, "job_id": job_id},
                        )
                        fedora_transaction.rollback_transaction()
                        transaction.set_rollback(True)
                        data_rolled_back = True
                        redis_connector.rpush(job_key("import_data_progress_ids"), record_id)
                        # Raw error envelope: the row-failure message is composed at raise time from
                        # translated fragments + runtime data (err, serialized_record, action, traceback);
                        # rendered verbatim (carve-out, see translation_value docstring).
                        redis_connector.rpush(
                            job_key("import_data_progress_details_tr"),
                            translation_value(
                                "cron.tasks.run_data_import.error.row",
                                raw=True,
                                message=(
                                    _("cron.tasks.run_data_import.error.part_1")
                                    + ": "
                                    + str(err)
                                    + ", "
                                    + _("cron.tasks.run_data_import.error.part_2")
                                    + " "
                                    + str(serialized_record)
                                    + ", "
                                    + _("cron.tasks.run_data_import.error.part_3")
                                    + " "
                                    + str(performed_action)
                                    + traceback.format_exc()
                                ),
                            ),
                        )
                        fedora_update_targets_dict = {}
                        updated_history_dict = defaultdict(lambda: {"files": set(), "record_ids": set()})
                        pending_fedora_update.clear()
                        pending_history_update.clear()
                        failed = True
                    stopped = redis_connector.get(job_key("import_data_stop")) is not None or failed
                    if stopped:
                        if not failed:
                            # User stop during the data phase: roll back every record committed so far
                            # so the abort leaves nothing persisted — a true abort.
                            transaction.set_rollback(True)
                            data_rolled_back = True
                            redis_connector.set(
                                job_key("import_data_status_message_tr"),
                                translation_value("cron.tasks.run_data_import.stopped_by_user"),
                            )
                        else:
                            redis_connector.set(
                                job_key("import_data_status_message_tr"),
                                translation_value("cron.tasks.run_data_import.failed_during_data_import"),
                            )
                        redis_connector.set(job_key("import_data_stop"), 1)
                        logger.info("cron.tasks.run_data_import.files.insert.stopped", extra={"job_id": job_id})
                        break
                if not failed and not stopped and pending_soubor_fedora_deletes:
                    try:
                        for entry in pending_soubor_fedora_deletes:
                            soubor = entry["soubor"]
                            navazany_objekt = entry["navazany_objekt"]
                            delete_fedora_transaction = FedoraDeletionOnlyTransaction()
                            delete_fedora_transaction.override_tombstone = True
                            # Identity is captured before delete() — afterwards Django clears the pk and
                            # the row is gone, so a post-commit failure could not be reported.
                            queue_fedora_delete_commit(
                                entry["record_id"],
                                delete_fedora_transaction,
                                {
                                    "soubor": soubor.nazev,
                                    "path": soubor.path,
                                    "repository_uuid": soubor.repository_uuid,
                                },
                            )
                            soubor.active_transaction = delete_fedora_transaction
                            soubor.suppress_signal = True
                            soubor.delete()
                            if navazany_objekt is not None:
                                FedoraRepositoryConnector(
                                    navazany_objekt, delete_fedora_transaction
                                ).delete_binary_file(soubor)
                    except Exception as err:
                        logger.error(
                            "cron.tasks.run_data_import.soubor_delete.error",
                            extra={"job_id": job_id, "soubor_pk": soubor.pk, "error": err},
                        )
                        transaction.set_rollback(True)
                        data_rolled_back = True
                        failed = True
                        redis_connector.set(
                            job_key("import_data_status_message_tr"),
                            translation_value("cron.tasks.run_data_import.failed_during_data_import"),
                        )
                        redis_connector.set(job_key("import_data_stop"), 1)
                if not failed and not stopped:
                    fedora_target_items = list(fedora_update_targets_dict)
                    fedora_target_results = [
                        {
                            "ident_cely": fedora_target_identity(item),
                            "transaction_uid": None,
                            "record_ids": sorted(fedora_update_targets_record_ids_dict.get(item, set())),
                            "result": translation_value("cron.tasks.run_data_import.fedora_target_unattempted"),
                        }
                        for item in fedora_target_items
                    ]
                    redis_connector.set(job_key("import_fedora_target_results_tr"), json.dumps(fedora_target_results))
                    # Fail closed before the data transaction commits. Once the commit succeeds, a
                    # hard worker exit can no longer leave committed database changes without the
                    # complete actionable Fedora plan already present in the durable XLSX report.
                    if save_import_report_to_disk(job_id, redis_connector, reports_directory_path) is None:
                        transaction.set_rollback(True)
                        data_rolled_back = True
                        failed = True
                        redis_connector.set(
                            job_key("import_data_status_message_tr"),
                            translation_value("cron.tasks.run_data_import.failed_during_data_import"),
                        )
                        redis_connector.set(job_key("import_data_stop"), 1)
                        logger.error(
                            "cron.tasks.run_data_import.fedora_plan_report_save_failed", extra={"job_id": job_id}
                        )
                if failed or stopped:
                    # Nothing from this batch will persist — do not leave the queued Fedora
                    # transactions open.
                    rollback_pending_fedora_delete_commits()
                elif pending_fedora_delete_commits:
                    # The database is the single commit point: Fedora deletions are committed only
                    # after the database transaction commits, so a rollback — including a failure of
                    # the database commit itself — can never leave them committed.
                    transaction.on_commit(commit_pending_fedora_delete_commits)
        except Exception as err:
            # An exception propagating out of the atomic() block rolls the data phase back. This also
            # covers a failure of the database commit itself: Django then discards the on_commit
            # callbacks, so the queued Fedora deletions are still uncommitted and can be aborted here.
            rollback_pending_fedora_delete_commits()
            data_rolled_back = True
            if not isinstance(err, ImportLockLostError):
                redis_connector.set(
                    job_key("import_data_status_message_tr"),
                    translation_value("cron.tasks.run_data_import.failed_during_data_import"),
                )
            redis_connector.set(job_key("import_data_stop"), 1)
            logger.error("cron.tasks.run_data_import.database_error", extra={"error": err, "job_id": job_id})
            for record_id in range(record_count):
                redis_connector.rpush(job_key("import_data_progress_ids"), record_id)
                redis_connector.rpush(
                    job_key("import_data_progress_details_tr"),
                    translation_value(
                        "cron.tasks.run_data_import.error.database_error",
                        raw=True,
                        message="{}: {}, ".format(_("cron.tasks.run_data_import.error.database_error"), err),
                    ),
                )
            failed = True
            fedora_update_targets_dict = {}
            updated_history_dict = defaultdict(lambda: {"files": set(), "record_ids": set()})
            fedora_target_items = []
            fedora_target_results = []
            redis_connector.set(job_key("import_fedora_target_results_tr"), json.dumps(fedora_target_results))
            pending_fedora_update.clear()
            pending_history_update.clear()

        if failed:
            redis_connector.set(
                job_key("import_data_progress"),
                IMPORT_PROGRESS_PHASE_FAILED,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
        elif not stopped:
            redis_connector.set(
                job_key("import_data_progress"),
                IMPORT_PROGRESS_PHASE_DATA_DONE,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
        if not failed and not stopped:
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.creating_history_records"),
            )
        if reports_directory_path:
            save_import_report_to_disk(job_id, redis_connector, reports_directory_path)

        # Relabel committed "success" markers to "rolled_back" whenever the data phase was rolled
        # back — both on failure and on a user stop during the data phase.
        if data_rolled_back:
            success_marker = "cron.tasks.run_data_import.success".encode("utf-8")
            rollback_marker = "cron.tasks.run_data_import.rolled_back".encode("utf-8")
            details = redis_connector.lrange(job_key("import_data_progress_details_tr"), 0, -1)
            for index, detail in enumerate(details):
                if detail == success_marker:
                    redis_connector.lset(job_key("import_data_progress_details_tr"), index, rollback_marker)

        HISTORY_REDIS_UPDATE_INTERVAL = 10
        history_total = len(updated_history_dict)
        redis_connector.set(job_key("import_data_history_total"), history_total, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(job_key("import_data_history_progress"), 0, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        history_skipped_id = "cron.tasks.run_data_import.history_record_skipped"
        for record_id in range(record_count):
            if record_id not in import_history_record_result:
                import_history_record_result[record_id] = history_skipped_id
        redis_connector.set(job_key("import_data_history_record_result_tr"), json.dumps(import_history_record_result))
        for history_index, (history_target_key, entry) in enumerate(updated_history_dict.items()):
            # Honor a stop — whether set during the data phase (skips history entirely) or arriving
            # now during the history phase. Data is already committed at this point, so
            # this only halts further work; it does not roll back.
            if not failed and not stopped and redis_connector.get(job_key("import_data_stop")) is not None:
                stopped = True
                redis_connector.set(
                    job_key("import_data_status_message_tr"),
                    translation_value("cron.tasks.run_data_import.stopped_by_user"),
                )
            if failed or stopped:
                break
            refresh_import_lock()
            if not failed and not stopped:
                redis_connector.set(
                    job_key("import_data_status_message_tr"),
                    translation_value(
                        "cron.tasks.run_data_import.creating_history_records",
                        n=history_index + 1,
                        total=history_total,
                    ),
                )
            history_target_class, history_target_pk = history_target_key
            files = entry["files"]
            record_ids = entry["record_ids"]
            try:
                record = history_target_class.objects.get(pk=history_target_pk)
                historie_vazba = record.history_vazba if isinstance(record, User) else record.historie
                history_record = Historie(
                    typ_zmeny=IMPORT,
                    uzivatel=transaction_user,
                    vazba=historie_vazba,
                    poznamka=",".join(sorted(files)),
                )
                history_record.save()
                history_result_value = translation_value(
                    "cron.tasks.run_data_import.history_record_created", pk=history_record.pk
                )
                for record_id in record_ids:
                    import_history_record_result[record_id] = history_result_value
            except Exception as err:
                logger.error(
                    "cron.tasks.run_data_import.history.error",
                    extra={"job_id": job_id, "history_target": history_target_key, "error": err},
                )
                failed = True
                redis_connector.set(
                    job_key("import_data_status_message_tr"),
                    translation_value("cron.tasks.run_data_import.failed_during_history"),
                )
                redis_connector.set(job_key("import_data_stop"), 1)
                history_error_value = translation_value(
                    "cron.tasks.run_data_import.history_record_error", raw=True, message=str(err)
                )
                for record_id in record_ids:
                    import_history_record_result[record_id] = history_error_value
            redis_connector.set(
                job_key("import_data_history_progress"),
                history_index + 1,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
            if (history_index + 1) % HISTORY_REDIS_UPDATE_INTERVAL == 0:
                redis_connector.set(
                    job_key("import_data_history_record_result_tr"), json.dumps(import_history_record_result)
                )
        redis_connector.set(job_key("import_data_history_record_result_tr"), json.dumps(import_history_record_result))

        if failed:
            redis_connector.set(
                job_key("import_data_progress"),
                IMPORT_PROGRESS_PHASE_FAILED,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
        elif not stopped:
            redis_connector.set(
                job_key("import_data_progress"),
                IMPORT_PROGRESS_PHASE_HISTORY_DONE,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
        if not failed and not stopped:
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.updating_fedora_records"),
            )
        fedora_total = len(fedora_update_targets_dict)
        redis_connector.set(job_key("import_data_fedora_total"), fedora_total, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(job_key("import_data_fedora_progress"), 0, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        fedora_skipped_id = FEDORA_SKIPPED_ID
        fedora_waiting_data_import_id = "cron.tasks.run_data_import.fedora_waiting_data_import"
        if reports_directory_path:
            save_import_report_to_disk(job_id, redis_connector, reports_directory_path)
        if not failed and not stopped:
            fedora_pending_record_ids = set()
            for affected_ids in fedora_update_targets_record_ids_dict.values():
                fedora_pending_record_ids.update(affected_ids)
            for record_id in range(record_count):
                if record_id in import_fedora_result:
                    continue
                if record_id not in fedora_pending_record_ids:
                    if record_id in import_files_record_ids:
                        import_fedora_result[record_id] = [fedora_waiting_data_import_id]
                    else:
                        import_fedora_result[record_id] = [fedora_skipped_id]
            redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
            for fedora_index, item in enumerate(fedora_target_items):
                # Honor a stop that first arrives during the Fedora phase. Each Fedora
                # update is its own committed transaction, so this only halts further work — it does
                # not (and cannot) roll back the updates already committed.
                if not failed and not stopped and redis_connector.get(job_key("import_data_stop")) is not None:
                    stopped = True
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value("cron.tasks.run_data_import.stopped_by_user"),
                    )
                if failed or stopped:
                    break
                refresh_import_lock()
                if not failed and not stopped:
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value(
                            "cron.tasks.run_data_import.updating_fedora_records",
                            n=fedora_index + 1,
                            total=fedora_total,
                        ),
                    )
                affected_record_ids = fedora_update_targets_record_ids_dict.get(item, set())
                record = None
                fedora_transaction = None
                try:
                    if isinstance(item, tuple) and len(item) == 2:
                        item_class, item_pk = item
                        record = item_class.objects.get(pk=item_pk)
                    else:
                        record = get_record_from_ident(item)
                    fedora_transaction = FedoraTransaction(transaction_user=transaction_user)
                    record.save_metadata(fedora_transaction)
                    fedora_transaction.mark_transaction_as_closed()
                    fedora_target_results[fedora_index].update(
                        {
                            "ident_cely": getattr(record, "ident_cely", None)
                            or fedora_target_results[fedora_index]["ident_cely"],
                            "transaction_uid": fedora_transaction.uid,
                            "result": translation_value("cron.tasks.run_data_import.fedora_target_success"),
                        }
                    )
                    for record_id in affected_record_ids:
                        if hasattr(record, "ident_cely"):
                            fedora_result_str = "{} ({})".format(fedora_transaction.uid, record.ident_cely)
                        else:
                            fedora_result_str = fedora_transaction.uid
                        # Raw envelope: the fedora transaction UID (+ ident_cely) is pure runtime data,
                        # not a translation; rendered verbatim.
                        import_fedora_result[record_id].append(
                            translation_value(
                                "cron.tasks.run_data_import.fedora_record", raw=True, message=fedora_result_str
                            )
                        )
                    redis_connector.set(job_key("import_fedora_target_results_tr"), json.dumps(fedora_target_results))
                    if (fedora_index + 1) % HISTORY_REDIS_UPDATE_INTERVAL == 0:
                        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                except Exception as err:
                    if fedora_transaction is not None:
                        try:
                            fedora_transaction.rollback_transaction()
                        except Exception as rollback_err:
                            logger.error(
                                "cron.tasks.run_data_import.fedora_rollback.error",
                                extra={"job_id": job_id, "error": rollback_err},
                            )
                    fedora_error_stack = traceback.format_exc()
                    logger.error(
                        "cron.tasks.run_data_import.fedora.error",
                        extra={
                            "job_id": job_id,
                            "record_ids": affected_record_ids,
                            "error": err,
                            "traceback": fedora_error_stack,
                        },
                    )
                    fedora_error_result = translation_value(
                        "cron.tasks.run_data_import.fedora_error",
                        raw=True,
                        message="{}: {}".format(_("cron.tasks.run_data_import.fedora_error"), fedora_error_stack),
                    )
                    for record_id in affected_record_ids:
                        import_fedora_result[record_id].append(fedora_error_result)
                    redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                    # record may be unset (the exception can occur before it's assigned above), and its
                    # ident_cely may be missing even when set — fall back to the raw target key.
                    fedora_target_results[fedora_index].update(
                        {
                            "ident_cely": getattr(record, "ident_cely", None)
                            or fedora_target_results[fedora_index]["ident_cely"],
                            "transaction_uid": getattr(fedora_transaction, "uid", None),
                            "result": translation_value("cron.tasks.run_data_import.fedora_target_error"),
                        }
                    )
                    redis_connector.set(job_key("import_fedora_target_results_tr"), json.dumps(fedora_target_results))
                    failed = True
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value("cron.tasks.run_data_import.failed_during_fedora"),
                    )
                    redis_connector.set(job_key("import_data_stop"), 1)
                redis_connector.set(
                    job_key("import_data_fedora_progress"),
                    fedora_index + 1,
                    ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                )
                if failed:
                    break
        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
        redis_connector.set(job_key("import_fedora_target_results_tr"), json.dumps(fedora_target_results))

        if failed:
            redis_connector.set(
                job_key("import_data_progress"),
                IMPORT_PROGRESS_PHASE_FAILED,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
        elif not stopped:
            redis_connector.set(
                job_key("import_data_progress"),
                IMPORT_PROGRESS_PHASE_FEDORA_DONE,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
        if not failed and not stopped:
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.finalizing"),
            )
        if reports_directory_path:
            save_import_report_to_disk(job_id, redis_connector, reports_directory_path)

        import_results_files = []
        if (
            not failed
            and not stopped
            and import_files_list
            and performed_action
            in (
                ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
            )
        ):
            refresh_import_lock()
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.file_import.validating_directory_settings"),
            )
            # Re-validate right before using the directory for binary writes: a run can span up to
            # 48h (IMPORT_DATA_RUNNING_TTL_SECONDS), long enough for settings/mount state to change
            # since the start-of-task gate. Shared with core.admin_sites.
            import_directory_path, revalidated_reports_directory_path, dir_error = check_import_report_directory(
                check_writable=False
            )
            if dir_error:
                logger.error(
                    "cron.tasks.run_data_import.import_directory_not_configured",
                    extra={"job_id": job_id, "error": dir_error},
                )
                redis_connector.set(
                    job_key("import_data_status_message_tr"),
                    translation_value("cron.tasks.run_data_import.import_directory_not_configured"),
                )
                redis_connector.set(job_key("import_data_stop"), 1)
                failed = True
            else:
                reports_directory_path = revalidated_reports_directory_path
            if not failed:
                fedora_transaction = None
                filename = None
                record_id = None
                try:
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value("cron.tasks.run_data_import.file_import.connected"),
                    )
                    redis_connector.set(
                        job_key("import_data_files_total"),
                        len(import_files_list),
                        ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                    )
                    redis_connector.set(job_key("import_data_files_progress"), 0, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
                    pending_related_metadata: dict = {}
                    for file_index, soubor in enumerate(import_files_list):
                        fedora_transaction = None
                        record_id = None
                        refresh_import_lock()
                        soubor: Soubor
                        logger.debug(
                            "cron.tasks.run_data_import.files.import_started",
                            extra={"job_id": job_id, "file_index": file_index, "file_name": soubor.nazev},
                        )
                        if stopped:
                            break
                        ident_cely = soubor.vazba.navazany_objekt.ident_cely
                        filename = soubor.nazev
                        file_path = os.path.join(import_directory_path, filename)
                        stopped = redis_connector.get(job_key("import_data_stop")) is not None
                        if stopped:
                            logger.info("cron.tasks.run_data_import.files.insert.stopped", extra={"job_id": job_id})
                            redis_connector.set(
                                job_key("import_data_status_message_tr"),
                                translation_value("cron.tasks.run_data_import.stopped_by_user"),
                            )
                            break
                        name_conflict_query = Soubor.objects.filter(nazev=filename, vazba=soubor.vazba)
                        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                            if name_conflict_query.exists():
                                import_results_files.append(
                                    {
                                        "ident_cely": ident_cely,
                                        "file_name": filename,
                                        "size_mb": None,
                                        "additional_info_tr": "cron.tasks.run_data_import.already_exists",
                                    }
                                )
                                redis_connector.set(job_key("import_data_files"), json.dumps(import_results_files))
                                failed = True
                                stopped = True
                                redis_connector.set(job_key("import_data_stop"), 1)
                                redis_connector.set(
                                    job_key("import_data_status_message_tr"),
                                    translation_value("cron.tasks.run_data_import.failed_during_data_import"),
                                )
                                break
                        elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE:
                            if name_conflict_query.exclude(pk=soubor.pk).exists():
                                import_results_files.append(
                                    {
                                        "ident_cely": ident_cely,
                                        "file_name": filename,
                                        "size_mb": None,
                                        "additional_info_tr": "cron.tasks.run_data_import.already_exists",
                                    }
                                )
                                redis_connector.set(job_key("import_data_files"), json.dumps(import_results_files))
                                failed = True
                                stopped = True
                                redis_connector.set(job_key("import_data_stop"), 1)
                                redis_connector.set(
                                    job_key("import_data_status_message_tr"),
                                    translation_value("cron.tasks.run_data_import.failed_during_data_import"),
                                )
                                break
                        if not os.path.isfile(file_path):
                            import_results_files.append(
                                {
                                    "ident_cely": ident_cely,
                                    "file_name": filename,
                                    "size_mb": None,
                                    "additional_info_tr": "cron.tasks.run_data_import.file_not_found_in_directory",
                                }
                            )
                            redis_connector.set(job_key("import_data_files"), json.dumps(import_results_files))
                            failed = True
                            stopped = True
                            redis_connector.set(job_key("import_data_stop"), 1)
                            redis_connector.set(
                                job_key("import_data_status_message_tr"),
                                translation_value("cron.tasks.run_data_import.cannot_read_from_directory"),
                            )
                            break
                        record_id = getattr(soubor, "import_record_id", None)
                        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                            soubor = name_conflict_query.first() or soubor
                        redis_connector.set(
                            job_key("import_data_status_message_tr"),
                            translation_value(
                                "cron.tasks.run_data_import.importing_file",
                                n=file_index + 1,
                                total=len(import_files_list),
                                filename=filename,
                                ident_cely=ident_cely,
                            ),
                        )
                        fedora_transaction = FedoraTransaction()
                        conn = FedoraRepositoryConnector(
                            soubor.vazba.navazany_objekt, fedora_transaction, skip_container_check=False
                        )
                        with open(file_path, "rb") as f:
                            bio = BytesIO(f.read())
                        mimetype = Soubor.get_mime_types(bio)
                        mime_extensions = Soubor.extensions_for_mime(mimetype)
                        if not mime_extensions:
                            raise SouborMimeUnsupportedError(filename, mimetype)
                        file_extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                        if file_extension not in mime_extensions:
                            raise SouborMimeExtensionMismatchError(filename, file_extension, mimetype)
                        if mimetype not in Soubor.allowed_mimes_for_record(soubor.vazba.navazany_objekt):
                            raise SouborMimeNotAllowedError(filename, mimetype, ident_cely)
                        if mimetype in ["image/png", "image/jpeg", "image/tiff"] and isinstance(
                            soubor.vazba.navazany_objekt, SamostatnyNalez
                        ):
                            bio = Soubor.remove_gps_data(bio)
                        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                            rep_bin_file = conn.save_binary_file(filename, mimetype, bio)
                        elif not soubor.repository_uuid:
                            raise SouborMissingRepositoryUuidError(soubor.pk, filename)
                        else:
                            rep_bin_file = conn.update_binary_file(
                                filename, mimetype, bio, soubor.repository_uuid, save_thumbs=True
                            )

                        soubor.mimetype = mimetype
                        soubor.size_mb = rep_bin_file.size_mb
                        soubor.sha_512 = rep_bin_file.sha_512
                        soubor.path = rep_bin_file.url_without_domain
                        soubor.rozsah = soubor.calculate_rozsah(bio, filename)
                        soubor.suppress_signal = True
                        soubor.save()
                        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                            soubor.create_soubor_vazby()
                        history_record = Historie(
                            typ_zmeny=IMPORT,
                            uzivatel=transaction_user,
                            vazba=soubor.historie,
                            poznamka="{} {}/{}/{}".format(
                                _("cron.tasks.run_data_import.imported_file"),
                                import_directory_path,
                                ident_cely,
                                filename,
                            ),
                        )
                        history_record.save()
                        if record_id is not None:
                            import_history_record_result[record_id] = translation_value(
                                "cron.tasks.run_data_import.history_record_created", pk=history_record.pk
                            )
                            redis_connector.set(
                                job_key("import_data_history_record_result_tr"),
                                json.dumps(import_history_record_result),
                            )
                        for related_history_target in SouborMapper.get_related_history_targets(soubor):
                            if not getattr(related_history_target, "ident_cely", None):
                                continue
                            rht_key = (related_history_target.__class__, related_history_target.pk)
                            if rht_key not in pending_related_metadata:
                                pending_related_metadata[rht_key] = {
                                    "ident_cely": related_history_target.ident_cely,
                                    "record_ids": set(),
                                }
                            if record_id is not None:
                                pending_related_metadata[rht_key]["record_ids"].add(record_id)
                        logger.info(
                            "cron.tasks.run_data_import.files.insert.saved",
                            extra={
                                "imported_filename": filename,
                                "ident_cely": ident_cely,
                                "job_id": job_id,
                            },
                        )
                        soubor.active_transaction = fedora_transaction
                        soubor.save()
                        fedora_transaction.mark_transaction_as_closed()
                        navazany = soubor.vazba.navazany_objekt
                        nav_key = (navazany.__class__, navazany.pk)
                        if nav_key not in pending_related_metadata:
                            pending_related_metadata[nav_key] = {
                                "ident_cely": navazany.ident_cely,
                                "record_ids": set(),
                            }
                        if record_id is not None:
                            pending_related_metadata[nav_key]["record_ids"].add(record_id)
                        import_results_files.append(
                            {
                                "ident_cely": ident_cely,
                                "file_name": filename,
                                "size_mb": round(rep_bin_file.size_mb, 3),
                                "additional_info_tr": translation_value(
                                    "cron.tasks.run_data_import.file_mime_type", raw=True, message=mimetype
                                ),
                            }
                        )
                        redis_connector.set(job_key("import_data_files"), json.dumps(import_results_files))
                        redis_connector.set(
                            job_key("import_data_files_progress"),
                            file_index + 1,
                            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                        )
                    if not failed and not stopped:
                        record_id = None
                        for (obj_class, obj_pk), entry in pending_related_metadata.items():
                            fedora_transaction = None
                            refresh_import_lock()
                            fedora_transaction = FedoraTransaction()
                            obj = obj_class.objects.get(pk=obj_pk)
                            obj.active_transaction = fedora_transaction
                            obj.save_metadata(fedora_transaction)
                            fedora_transaction.mark_transaction_as_closed()
                            related_history_vazba = obj.history_vazba if isinstance(obj, User) else obj.historie
                            Historie(
                                typ_zmeny=IMPORT,
                                uzivatel=transaction_user,
                                vazba=related_history_vazba,
                                poznamka=SouborMapper.get_file_name_for_mapper(SouborMapper),
                            ).save()
                            for rid in entry["record_ids"]:
                                if import_fedora_result.get(rid) == [fedora_waiting_data_import_id]:
                                    import_fedora_result[rid] = []
                                import_fedora_result[rid].append(
                                    translation_value(
                                        "cron.tasks.run_data_import.fedora_record",
                                        raw=True,
                                        message="{} ({})".format(fedora_transaction.uid, entry["ident_cely"]),
                                    )
                                )
                            redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                except SouborMissingRepositoryUuidError as err:
                    if fedora_transaction is not None:
                        fedora_transaction.rollback_transaction()
                    logger.error(
                        "cron.tasks.run_data_import.files.missing_repository_uuid",
                        extra={"error": err, "job_id": job_id, "import_filename": filename, "soubor_pk": err.soubor_pk},
                    )
                    if record_id is not None:
                        import_fedora_result[record_id] = [
                            translation_value("cron.tasks.run_data_import.error.raw", raw=True, message=str(err))
                        ]
                        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                    redis_connector.set(job_key("import_data_stop"), 1)
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value("cron.tasks.run_data_import.failed_missing_repository_uuid"),
                    )
                    failed = True
                except SouborMimeUnsupportedError as err:
                    if fedora_transaction is not None:
                        fedora_transaction.rollback_transaction()
                    logger.error(
                        "cron.tasks.run_data_import.files.mime_unsupported",
                        extra={
                            "error": err,
                            "job_id": job_id,
                            "import_filename": filename,
                            "detected_mime": err.mime_type,
                        },
                    )
                    if record_id is not None:
                        import_fedora_result[record_id] = [
                            translation_value("cron.tasks.run_data_import.error.raw", raw=True, message=str(err))
                        ]
                        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                    redis_connector.set(job_key("import_data_stop"), 1)
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value("cron.tasks.run_data_import.failed_mime_unsupported"),
                    )
                    failed = True
                except SouborMimeExtensionMismatchError as err:
                    if fedora_transaction is not None:
                        fedora_transaction.rollback_transaction()
                    logger.error(
                        "cron.tasks.run_data_import.files.mime_extension_mismatch",
                        extra={
                            "error": err,
                            "job_id": job_id,
                            "import_filename": filename,
                            "detected_mime": err.mime_type,
                        },
                    )
                    if record_id is not None:
                        import_fedora_result[record_id] = [
                            translation_value("cron.tasks.run_data_import.error.raw", raw=True, message=str(err))
                        ]
                        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                    redis_connector.set(job_key("import_data_stop"), 1)
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value("cron.tasks.run_data_import.failed_mime_extension_mismatch"),
                    )
                    failed = True
                except SouborMimeNotAllowedError as err:
                    if fedora_transaction is not None:
                        fedora_transaction.rollback_transaction()
                    logger.error(
                        "cron.tasks.run_data_import.files.mime_not_allowed",
                        extra={
                            "error": err,
                            "job_id": job_id,
                            "import_filename": filename,
                            "detected_mime": err.mime_type,
                            "navazany_ident_cely": err.navazany_ident_cely,
                        },
                    )
                    if record_id is not None:
                        import_fedora_result[record_id] = [
                            translation_value("cron.tasks.run_data_import.error.raw", raw=True, message=str(err))
                        ]
                        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                    redis_connector.set(job_key("import_data_stop"), 1)
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value("cron.tasks.run_data_import.failed_mime_not_allowed"),
                    )
                    failed = True
                except FedoraError as err:
                    if fedora_transaction is not None:
                        fedora_transaction.rollback_transaction()
                    fedora_error_stack = traceback.format_exc()
                    logger.error(
                        "cron.tasks.run_data_import.files.fedora_error",
                        extra={
                            "error": err,
                            "job_id": job_id,
                            "import_filename": filename,
                            "traceback": fedora_error_stack,
                        },
                    )
                    fedora_error_result = translation_value(
                        "cron.tasks.run_data_import.fedora_error",
                        raw=True,
                        message="{}: {}".format(_("cron.tasks.run_data_import.fedora_error"), fedora_error_stack),
                    )
                    if record_id is not None:
                        import_fedora_result[record_id] = [fedora_error_result]
                        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                    redis_connector.set(job_key("import_data_stop"), 1)
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value("cron.tasks.run_data_import.failed_during_fedora"),
                    )
                    failed = True
                except Exception as err:
                    if fedora_transaction is not None:
                        fedora_transaction.rollback_transaction()
                    error_stack = traceback.format_exc()
                    logger.error(
                        "cron.tasks.run_data_import.directory_error",
                        extra={"error": err, "job_id": job_id, "import_filename": filename, "traceback": error_stack},
                    )
                    error_result = translation_value(
                        "cron.tasks.run_data_import.cannot_read_from_directory",
                        raw=True,
                        message="{}: {}".format(
                            _("cron.tasks.run_data_import.cannot_read_from_directory"), error_stack
                        ),
                    )
                    if record_id is not None:
                        import_fedora_result[record_id] = [error_result]
                        redis_connector.set(job_key("import_fedora_result_tr"), json.dumps(import_fedora_result))
                    redis_connector.set(job_key("import_data_stop"), 1)
                    redis_connector.set(
                        job_key("import_data_status_message_tr"),
                        translation_value("cron.tasks.run_data_import.cannot_read_from_directory"),
                    )
                    failed = True

        if failed:
            redis_connector.set(
                job_key("import_data_progress"),
                IMPORT_PROGRESS_PHASE_FAILED,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
        elif not stopped:
            redis_connector.set(
                job_key("import_data_progress"),
                IMPORT_PROGRESS_PHASE_FINISHED,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.finished"),
            )
        if reports_directory_path:
            save_import_report_to_disk(job_id, redis_connector, reports_directory_path)
    except Exception as err:
        # Escaped a phase-local handler (e.g. a bare refresh_import_lock() call) — record it as a
        # failure so finally below doesn't report the job as finished.
        failed = True
        if not isinstance(err, ImportLockLostError):
            redis_connector.set(
                job_key("import_data_status_message_tr"),
                translation_value("cron.tasks.run_data_import.failed_during_data_import"),
            )
            redis_connector.set(job_key("import_data_stop"), 1)
        redis_connector.set(
            job_key("import_data_progress"), IMPORT_PROGRESS_PHASE_FAILED, ex=IMPORT_DATA_RUNNING_TTL_SECONDS
        )
        logger.error(
            "cron.tasks.run_data_import.unhandled_error",
            extra={"job_id": job_id, "error": err, "traceback": traceback.format_exc()},
        )
        if reports_directory_path:
            save_import_report_to_disk(job_id, redis_connector, reports_directory_path)
    finally:
        LookupImportField.clear_cache()
        LookupImportField.clear_records()
        for suffix in IMPORT_DATA_JOB_KEY_SUFFIXES:
            redis_connector.expire(job_key(suffix), IMPORT_DATA_EXPIRATION_SECONDS)
        for record_id in range(record_count):
            redis_connector.expire(record_key(record_id), IMPORT_DATA_EXPIRATION_SECONDS)
        # Set the terminal phase matching the outcome, clear the per-user in-flight pointer, and
        # defensively delete any staged ZIP chunk keys the validation task should already have
        # removed.
        if failed:
            redis_connector.set(job_key("import_data_phase"), IMPORT_PHASE_FAILED, ex=IMPORT_DATA_EXPIRATION_SECONDS)
            redis_connector.set(
                job_key("import_data_failure_reason"),
                IMPORT_FAILURE_REASON_ERROR,
                ex=IMPORT_DATA_EXPIRATION_SECONDS,
            )
        elif stopped:
            redis_connector.set(job_key("import_data_phase"), IMPORT_PHASE_STOPPED, ex=IMPORT_DATA_EXPIRATION_SECONDS)
        else:
            redis_connector.set(job_key("import_data_phase"), IMPORT_PHASE_FINISHED, ex=IMPORT_DATA_EXPIRATION_SECONDS)
        # Terminal snapshot — phase is now failed/stopped/finished above, so this is the report an
        # operator sees if they never return to the polling page.
        if reports_directory_path:
            save_import_report_to_disk(job_id, redis_connector, reports_directory_path)
        job_user = redis_connector.get(job_key("import_data_user"))
        if job_user is not None:
            if isinstance(job_user, bytes):
                job_user = job_user.decode("utf-8")
            # Compare-then-delete: a replacement job may already own this pointer (r3703505227).
            RedisConnector.delete_if_value_matches(
                redis_connector, "import_data_current_job_{}".format(job_user), job_id
            )
        RedisConnector.delete_if_value_matches(redis_connector, RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, job_id)
        leftover_chunks_raw = redis_connector.get(job_key("import_data_file_chunks"))
        if leftover_chunks_raw:
            leftover_count = int(leftover_chunks_raw)
            stray_keys = ["import_data_file_{}_{}".format(job_id, i) for i in range(leftover_count)]
            stray_keys.append(job_key("import_data_file_chunks"))
            redis_connector.delete(*stray_keys)
        RedisConnector.release_import_lock(redis_connector, lock_token)

    logger.debug(
        "cron.tasks.run_data_import.end", extra={"job_id": job_id, "failed": failed, "record_count": record_count}
    )
