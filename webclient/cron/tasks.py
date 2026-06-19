import datetime
import json
import logging
import os
import traceback
from collections import defaultdict
from io import BytesIO

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
    ImportDataError,
    ImportModelMapper,
    LookupImportField,
    SouborMapper,
    UzivatelNotifikaceMapper,
    UzivatelOpravneniMapper,
)
from core.models import Soubor, SouborVazby
from core.repository_connector import (
    DryRunFedoraTransaction,
    FedoraDeletionOnlyTransaction,
    FedoraError,
    FedoraRepositoryConnector,
    FedoraTransaction,
)
from core.setting_models import CustomAdminSettings
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

IMPORT_DATA_EXPIRATION_SECONDS = 6 * 60 * 60  # 6 hodin
IMPORT_DATA_RUNNING_TTL_SECONDS = 6 * 60 * 60  # 6 hodin — maximální očekávaná délka importu

# Procentuální checkpointy sjednoceného progress baru importu (po dokončení dané fáze).
IMPORT_PROGRESS_PHASE_FAILED = 0
IMPORT_PROGRESS_PHASE_DATA_DONE = 25
IMPORT_PROGRESS_PHASE_HISTORY_DONE = 50
IMPORT_PROGRESS_PHASE_FEDORA_DONE = 75
IMPORT_PROGRESS_PHASE_FINISHED = 100


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
    url = settings.DIGIARCHIV_URL
    requests.get(url)
    logger.debug("cron.tasks.call_digiarchiv_update_task.end")


@shared_task
def run_data_import(job_id, user_id, lock_token):
    """
    Spustí data import.

    :param job_id: Identifikátor objektu ``job``.
    :param user_id: Identifikátor objektu ``user``.
    :param lock_token: Token pro ověření vlastnictví importního zámku v Redis.

    Možné hodnoty Redis klíče ``import_data_status_message_{job_id}``:

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
                    job_key("import_data_status_message"),
                    _("cron.tasks.run_data_import.failed_lock_lost"),
                )
                redis_connector.set(job_key("import_data_stop"), 1)
                raise ImportLockLostError("Import data lock lost")

        if not RedisConnector.refresh_import_lock(redis_connector, lock_token, IMPORT_DATA_RUNNING_TTL_SECONDS):
            redis_connector.set(
                job_key("import_data_status_message"),
                _("cron.tasks.run_data_import.failed_lock_acquisition"),
            )
            redis_connector.set(job_key("import_data_stop"), 1)
            logger.warning("cron.tasks.run_data_import.lock_not_owned", extra={"job_id": job_id})
            return

        record_count_raw = redis_connector.get(job_key("import_data_count"))
        record_count = int(record_count_raw.decode("utf-8")) if record_count_raw else 0
        if record_count <= 0:
            redis_connector.set(
                job_key("import_data_status_message"),
                _("cron.tasks.run_data_import.failed_during_data_import"),
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
        redis_connector.delete(job_key("import_data_progress_ids"), job_key("import_data_progress_details"))
        redis_connector.set(job_key("import_data_files"), json.dumps([]), ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(
            job_key("import_data_history_record_result"), json.dumps({}), ex=IMPORT_DATA_RUNNING_TTL_SECONDS
        )
        redis_connector.set(job_key("import_fedora_result"), json.dumps({}), ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
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
        transaction_user = User.objects.get(pk=user_id)

        pending_fedora_update = []
        pending_history_update = []
        pending_soubor_fedora_deletes: list = []

        def add_updated_history(mapper_class, history_target, record_id):
            if history_target:
                entry = updated_history_dict[(history_target.__class__, history_target.pk)]
                entry["files"].add(mapper_class.get_file_name_for_mapper(mapper_class))
                entry["record_ids"].add(record_id)

        def add_item_fedora_update_target(items, record_id):
            for item in items:
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

        try:
            with transaction.atomic():
                for record_id in range(record_count):
                    refresh_import_lock()
                    primary_key_record = None
                    redis_connector.set(
                        job_key("import_data_status_message"),
                        "{} {}/{}".format(
                            _("cron.tasks.run_data_import.importing_record_data"),
                            record_id + 1,
                            record_count,
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
                                    if record.historie is None:
                                        record.create_soubor_vazby()
                                    history_record = Historie(
                                        typ_zmeny=IMPORT,
                                        uzivatel=transaction_user,
                                        vazba=record.historie,
                                        poznamka="{} {}".format(
                                            _("cron.tasks.run_data_import.deleted_file"),
                                            record.nazev,
                                        ),
                                    )
                                    history_record.save()
                                    import_history_record_result[record_id] = "{}: {}".format(
                                        _("cron.tasks.run_data_import.history_record_created"), history_record.pk
                                    )
                                    redis_connector.set(
                                        job_key("import_data_history_record_result"),
                                        json.dumps(import_history_record_result),
                                    )
                                    pending_soubor_fedora_deletes.append(
                                        {
                                            "soubor": record,
                                            "navazany_objekt": (
                                                record.vazba.navazany_objekt if record.vazba_id else None
                                            ),
                                        }
                                    )
                                fedora_transaction.mark_transaction_as_closed()
                                redis_connector.rpush(job_key("import_data_progress_ids"), record_id)
                                redis_connector.rpush(
                                    job_key("import_data_progress_details"), "cron.tasks.run_data_import.success"
                                )
                                continue
                            for record in records:
                                record.import_record_id = record_id
                            import_files_list += records
                            import_files_record_ids.add(record_id)
                            record: Soubor = records[0]
                            redis_connector.rpush(job_key("import_data_progress_ids"), record_id)
                            redis_connector.rpush(
                                job_key("import_data_progress_details"), "cron.tasks.run_data_import.file"
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
                            job_key("import_data_progress_details"), "cron.tasks.run_data_import.success"
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
                        redis_connector.rpush(job_key("import_data_progress_ids"), record_id)
                        redis_connector.rpush(
                            job_key("import_data_progress_details"),
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
                            + traceback.format_exc(),
                        )
                        fedora_update_targets_dict = {}
                        updated_history_dict = defaultdict(lambda: {"files": set(), "record_ids": set()})
                        pending_fedora_update.clear()
                        pending_history_update.clear()
                        failed = True
                    stopped = redis_connector.get(job_key("import_data_stop")) is not None or failed
                    if stopped:
                        if not failed:
                            redis_connector.set(
                                job_key("import_data_status_message"), _("cron.tasks.run_data_import.stopped_by_user")
                            )
                        else:
                            redis_connector.set(
                                job_key("import_data_status_message"),
                                _("cron.tasks.run_data_import.failed_during_data_import"),
                            )
                        redis_connector.set(job_key("import_data_stop"), 1)
                        logger.info("cron.tasks.run_data_import.files.insert.stopped", extra={"job_id": job_id})
                        break
        except Exception as err:
            if not isinstance(err, ImportLockLostError):
                redis_connector.set(
                    job_key("import_data_status_message"),
                    _("cron.tasks.run_data_import.failed_during_data_import"),
                )
            redis_connector.set(job_key("import_data_stop"), 1)
            logger.error("cron.tasks.run_data_import.database_error", extra={"error": err, "job_id": job_id})
            for record_id in range(record_count):
                redis_connector.rpush(job_key("import_data_progress_ids"), record_id)
                redis_connector.rpush(
                    job_key("import_data_progress_details"),
                    "{}: {}, ".format(_("cron.tasks.run_data_import.error.database_error"), err),
                )
            failed = True
            fedora_update_targets_dict = {}
            updated_history_dict = defaultdict(lambda: {"files": set(), "record_ids": set()})
            pending_fedora_update.clear()
            pending_history_update.clear()

        redis_connector.set(
            job_key("import_data_progress"),
            IMPORT_PROGRESS_PHASE_FAILED if failed else IMPORT_PROGRESS_PHASE_DATA_DONE,
            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
        )
        if not failed and not stopped:
            redis_connector.set(
                job_key("import_data_status_message"),
                _("cron.tasks.run_data_import.creating_history_records"),
            )

        if failed:
            success_marker = "cron.tasks.run_data_import.success".encode("utf-8")
            rollback_marker = "cron.tasks.run_data_import.rolled_back".encode("utf-8")
            details = redis_connector.lrange(job_key("import_data_progress_details"), 0, -1)
            for index, detail in enumerate(details):
                if detail == success_marker:
                    redis_connector.lset(job_key("import_data_progress_details"), index, rollback_marker)

        if not failed and pending_soubor_fedora_deletes:
            for entry in pending_soubor_fedora_deletes:
                soubor = entry["soubor"]
                navazany_objekt = entry["navazany_objekt"]
                try:
                    delete_fedora_transaction = FedoraDeletionOnlyTransaction()
                    delete_fedora_transaction.override_tombstone = True
                    soubor.active_transaction = delete_fedora_transaction
                    soubor.suppress_signal = True
                    soubor.delete()
                    if navazany_objekt is not None:
                        FedoraRepositoryConnector(navazany_objekt, delete_fedora_transaction).delete_binary_file(soubor)
                    delete_fedora_transaction.mark_transaction_as_closed()
                except Exception as err:
                    logger.error(
                        "cron.tasks.run_data_import.soubor_delete.error",
                        extra={"job_id": job_id, "soubor_pk": soubor.pk, "error": err},
                    )
                    failed = True
                    redis_connector.set(
                        job_key("import_data_status_message"),
                        _("cron.tasks.run_data_import.failed_during_data_import"),
                    )
                    redis_connector.set(job_key("import_data_stop"), 1)
                    break

        HISTORY_REDIS_UPDATE_INTERVAL = 10
        history_total = len(updated_history_dict)
        redis_connector.set(job_key("import_data_history_total"), history_total, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(job_key("import_data_history_progress"), 0, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        history_skipped_str = _("cron.tasks.run_data_import.history_record_skipped")
        for record_id in range(record_count):
            if record_id not in import_history_record_result:
                import_history_record_result[record_id] = history_skipped_str
        redis_connector.set(job_key("import_data_history_record_result"), json.dumps(import_history_record_result))
        for history_index, (history_target_key, entry) in enumerate(updated_history_dict.items()):
            refresh_import_lock()
            if not failed and not stopped:
                redis_connector.set(
                    job_key("import_data_status_message"),
                    "{} {}/{}".format(
                        _("cron.tasks.run_data_import.creating_history_records"),
                        history_index + 1,
                        history_total,
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
                history_result_str = "{}: {}".format(
                    _("cron.tasks.run_data_import.history_record_created"), history_record.pk
                )
                for record_id in record_ids:
                    import_history_record_result[record_id] = history_result_str
            except Exception as err:
                logger.error(
                    "cron.tasks.run_data_import.history.error",
                    extra={"job_id": job_id, "history_target": history_target_key, "error": err},
                )
                failed = True
                redis_connector.set(
                    job_key("import_data_status_message"),
                    _("cron.tasks.run_data_import.failed_during_history"),
                )
                redis_connector.set(job_key("import_data_stop"), 1)
                error_result_str = "{}: {}".format(_("cron.tasks.run_data_import.history_record_error"), err)
                for record_id in record_ids:
                    import_history_record_result[record_id] = error_result_str
            redis_connector.set(
                job_key("import_data_history_progress"),
                history_index + 1,
                ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
            )
            if (history_index + 1) % HISTORY_REDIS_UPDATE_INTERVAL == 0:
                redis_connector.set(
                    job_key("import_data_history_record_result"), json.dumps(import_history_record_result)
                )
        redis_connector.set(job_key("import_data_history_record_result"), json.dumps(import_history_record_result))

        redis_connector.set(
            job_key("import_data_progress"),
            IMPORT_PROGRESS_PHASE_FAILED if failed else IMPORT_PROGRESS_PHASE_HISTORY_DONE,
            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
        )
        if not failed and not stopped:
            redis_connector.set(
                job_key("import_data_status_message"),
                _("cron.tasks.run_data_import.updating_fedora_records"),
            )

        fedora_total = len(fedora_update_targets_dict)
        redis_connector.set(job_key("import_data_fedora_total"), fedora_total, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        redis_connector.set(job_key("import_data_fedora_progress"), 0, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
        fedora_skipped_str = _("cron.tasks.run_data_import.fedora_skipped")
        fedora_waiting_data_import_str = _("cron.tasks.run_data_import.fedora_waiting_data_import")
        if not failed:
            fedora_pending_record_ids = set()
            for affected_ids in fedora_update_targets_record_ids_dict.values():
                fedora_pending_record_ids.update(affected_ids)
            for record_id in range(record_count):
                if record_id in import_fedora_result:
                    continue
                if record_id not in fedora_pending_record_ids:
                    if record_id in import_files_record_ids:
                        import_fedora_result[record_id] = [fedora_waiting_data_import_str]
                    else:
                        import_fedora_result[record_id] = [fedora_skipped_str]
            redis_connector.set(job_key("import_fedora_result"), json.dumps(import_fedora_result))
            for fedora_index, item in enumerate(fedora_update_targets_dict):
                refresh_import_lock()
                if not stopped:
                    redis_connector.set(
                        job_key("import_data_status_message"),
                        "{} {}/{}".format(
                            _("cron.tasks.run_data_import.updating_fedora_records"),
                            fedora_index + 1,
                            fedora_total,
                        ),
                    )
                affected_record_ids = fedora_update_targets_record_ids_dict.get(item, set())
                try:
                    if isinstance(item, tuple) and len(item) == 2:
                        item_class, item_pk = item
                        record = item_class.objects.get(pk=item_pk)
                    else:
                        record = get_record_from_ident(item)
                    fedora_transaction = FedoraTransaction(transaction_user=transaction_user)
                    record.save_metadata(fedora_transaction)
                    fedora_transaction.mark_transaction_as_closed()
                    for record_id in affected_record_ids:
                        if hasattr(record, "ident_cely"):
                            import_fedora_result_str = "{} ({})".format(fedora_transaction.uid, record.ident_cely)
                        else:
                            import_fedora_result_str = fedora_transaction.uid
                        import_fedora_result[record_id].append(import_fedora_result_str)
                    if (fedora_index + 1) % HISTORY_REDIS_UPDATE_INTERVAL == 0:
                        redis_connector.set(job_key("import_fedora_result"), json.dumps(import_fedora_result))
                except Exception as err:
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
                    fedora_error_result = "{}: {}".format(
                        _("cron.tasks.run_data_import.fedora_error"), fedora_error_stack
                    )
                    result_record_ids = affected_record_ids or range(record_count)
                    for record_id in result_record_ids:
                        import_fedora_result[record_id].append(fedora_error_result)
                    redis_connector.set(job_key("import_fedora_result"), json.dumps(import_fedora_result))
                    failed = True
                    redis_connector.set(
                        job_key("import_data_status_message"),
                        _("cron.tasks.run_data_import.failed_during_fedora"),
                    )
                    redis_connector.set(job_key("import_data_stop"), 1)
                redis_connector.set(
                    job_key("import_data_fedora_progress"),
                    fedora_index + 1,
                    ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                )
        redis_connector.set(job_key("import_fedora_result"), json.dumps(import_fedora_result))

        redis_connector.set(
            job_key("import_data_progress"),
            IMPORT_PROGRESS_PHASE_FAILED if failed else IMPORT_PROGRESS_PHASE_FEDORA_DONE,
            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
        )
        if not failed and not stopped:
            redis_connector.set(
                job_key("import_data_status_message"),
                _("cron.tasks.run_data_import.finalizing"),
            )

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
                job_key("import_data_status_message"),
                _("cron.tasks.run_data_import.file_import.validating_directory_settings"),
            )
            try:
                import_directory_settings_obj = CustomAdminSettings.objects.get(item_id="import_directory_settings")
                import_directory_settings = json.loads(import_directory_settings_obj.value)
                if not import_directory_settings.get("DIRECTORY_PATH"):
                    raise ValueError("Missing required DIRECTORY_PATH setting")
                import_directory_path = import_directory_settings["DIRECTORY_PATH"]
                if not os.path.isdir(import_directory_path):
                    raise ValueError("Import directory does not exist: {}".format(import_directory_path))
            except Exception as err:
                logger.error(
                    "cron.tasks.run_data_import.import_directory_not_configured",
                    extra={"job_id": job_id, "error": str(err)},
                )
                redis_connector.set(
                    job_key("import_data_status_message"),
                    _("cron.tasks.run_data_import.import_directory_not_configured"),
                )
                redis_connector.set(job_key("import_data_stop"), 1)
                failed = True
            if not failed:
                try:
                    redis_connector.set(
                        job_key("import_data_status_message"),
                        _("cron.tasks.run_data_import.file_import.connected"),
                    )
                    redis_connector.set(
                        job_key("import_data_files_total"),
                        len(import_files_list),
                        ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                    )
                    redis_connector.set(job_key("import_data_files_progress"), 0, ex=IMPORT_DATA_RUNNING_TTL_SECONDS)
                    pending_related_metadata: dict = {}
                    for file_index, soubor in enumerate(import_files_list):
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
                                job_key("import_data_status_message"),
                                _("cron.tasks.run_data_import.stopped_by_user"),
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
                                        "additional_info": _("cron.tasks.run_data_import.already_exists"),
                                    }
                                )
                                redis_connector.set(job_key("import_data_files"), json.dumps(import_results_files))
                                failed = True
                                stopped = True
                                redis_connector.set(job_key("import_data_stop"), 1)
                                redis_connector.set(
                                    job_key("import_data_status_message"),
                                    _("cron.tasks.run_data_import.failed_during_data_import"),
                                )
                                break
                        elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE:
                            if name_conflict_query.exclude(pk=soubor.pk).exists():
                                import_results_files.append(
                                    {
                                        "ident_cely": ident_cely,
                                        "file_name": filename,
                                        "size_mb": None,
                                        "additional_info": _("cron.tasks.run_data_import.already_exists"),
                                    }
                                )
                                redis_connector.set(job_key("import_data_files"), json.dumps(import_results_files))
                                failed = True
                                stopped = True
                                redis_connector.set(job_key("import_data_stop"), 1)
                                redis_connector.set(
                                    job_key("import_data_status_message"),
                                    _("cron.tasks.run_data_import.failed_during_data_import"),
                                )
                                break
                        if not os.path.isfile(file_path):
                            import_results_files.append(
                                {
                                    "ident_cely": ident_cely,
                                    "file_name": filename,
                                    "size_mb": None,
                                    "additional_info": _("cron.tasks.run_data_import.file_not_found_in_directory"),
                                }
                            )
                            redis_connector.set(job_key("import_data_files"), json.dumps(import_results_files))
                            failed = True
                            stopped = True
                            redis_connector.set(job_key("import_data_stop"), 1)
                            redis_connector.set(
                                job_key("import_data_status_message"),
                                _("cron.tasks.run_data_import.cannot_read_from_directory"),
                            )
                            break
                        record_id = getattr(soubor, "import_record_id", None)
                        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                            soubor = name_conflict_query.first() or soubor
                        redis_connector.set(
                            job_key("import_data_status_message"),
                            "{} {}/{}: {} ({})".format(
                                _("cron.tasks.run_data_import.importing_file"),
                                file_index + 1,
                                len(import_files_list),
                                filename,
                                ident_cely,
                            ),
                        )
                        fedora_transaction = None
                        fedora_transaction = FedoraTransaction()
                        conn = FedoraRepositoryConnector(
                            soubor.vazba.navazany_objekt, fedora_transaction, skip_container_check=False
                        )
                        with open(file_path, "rb") as f:
                            bio = BytesIO(f.read())
                        mimetype = Soubor.get_mime_types(bio)
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
                            import_history_record_result[record_id] = "{}: {}".format(
                                _("cron.tasks.run_data_import.history_record_created"), history_record.pk
                            )
                            redis_connector.set(
                                job_key("import_data_history_record_result"),
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
                                "additional_info": mimetype,
                            }
                        )
                        redis_connector.set(job_key("import_data_files"), json.dumps(import_results_files))
                        redis_connector.set(
                            job_key("import_data_files_progress"),
                            file_index + 1,
                            ex=IMPORT_DATA_RUNNING_TTL_SECONDS,
                        )
                    if not failed and not stopped:
                        for (obj_class, obj_pk), entry in pending_related_metadata.items():
                            refresh_import_lock()
                            post_fedora_transaction = FedoraTransaction()
                            obj = obj_class.objects.get(pk=obj_pk)
                            obj.active_transaction = post_fedora_transaction
                            obj.save_metadata(post_fedora_transaction)
                            post_fedora_transaction.mark_transaction_as_closed()
                            related_history_vazba = obj.history_vazba if isinstance(obj, User) else obj.historie
                            Historie(
                                typ_zmeny=IMPORT,
                                uzivatel=transaction_user,
                                vazba=related_history_vazba,
                                poznamka=SouborMapper.get_file_name_for_mapper(SouborMapper),
                            ).save()
                            for rid in entry["record_ids"]:
                                if import_fedora_result.get(rid) == [fedora_waiting_data_import_str]:
                                    import_fedora_result[rid] = []
                                import_fedora_result[rid].append(
                                    "{} ({})".format(post_fedora_transaction.uid, entry["ident_cely"])
                                )
                            redis_connector.set(job_key("import_fedora_result"), json.dumps(import_fedora_result))
                except SouborMissingRepositoryUuidError as err:
                    if fedora_transaction is not None:
                        fedora_transaction.rollback_transaction()
                    logger.error(
                        "cron.tasks.run_data_import.files.missing_repository_uuid",
                        extra={"error": err, "job_id": job_id, "import_filename": filename, "soubor_pk": err.soubor_pk},
                    )
                    if record_id is not None:
                        import_fedora_result[record_id] = [str(err)]
                        redis_connector.set(job_key("import_fedora_result"), json.dumps(import_fedora_result))
                    redis_connector.set(job_key("import_data_stop"), 1)
                    redis_connector.set(
                        job_key("import_data_status_message"),
                        _("cron.tasks.run_data_import.failed_missing_repository_uuid"),
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
                    fedora_error_result = "{}: {}".format(
                        _("cron.tasks.run_data_import.fedora_error"), fedora_error_stack
                    )
                    if record_id is not None:
                        import_fedora_result[record_id] = [fedora_error_result]
                        redis_connector.set(job_key("import_fedora_result"), json.dumps(import_fedora_result))
                    redis_connector.set(job_key("import_data_stop"), 1)
                    redis_connector.set(
                        job_key("import_data_status_message"),
                        _("cron.tasks.run_data_import.failed_during_fedora"),
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
                    error_result = "{}: {}".format(
                        _("cron.tasks.run_data_import.cannot_read_from_directory"), error_stack
                    )
                    if record_id is not None:
                        import_fedora_result[record_id] = [error_result]
                        redis_connector.set(job_key("import_fedora_result"), json.dumps(import_fedora_result))
                    redis_connector.set(job_key("import_data_stop"), 1)
                    redis_connector.set(
                        job_key("import_data_status_message"),
                        _("cron.tasks.run_data_import.cannot_read_from_directory"),
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
            redis_connector.set(job_key("import_data_status_message"), _("cron.tasks.run_data_import.finished"))
    finally:
        LookupImportField.clear_cache()
        LookupImportField.clear_records()
        redis_connector.expire(job_key("import_data_history_record_result"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_count"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_files"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_progress"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_status_message"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_fedora_result"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_primary_keys"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_progress_ids"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_progress_details"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_stop"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_history_progress"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_history_total"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_fedora_progress"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_fedora_total"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_files_progress"), IMPORT_DATA_EXPIRATION_SECONDS)
        redis_connector.expire(job_key("import_data_files_total"), IMPORT_DATA_EXPIRATION_SECONDS)
        for record_id in range(record_count):
            redis_connector.expire(record_key(record_id), IMPORT_DATA_EXPIRATION_SECONDS)
        RedisConnector.release_import_lock(redis_connector, lock_token)

    logger.debug(
        "cron.tasks.run_data_import.end", extra={"job_id": job_id, "failed": failed, "record_count": record_count}
    )
