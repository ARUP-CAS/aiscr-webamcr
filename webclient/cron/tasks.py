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
from core.import_data_mappers import ImportModelMapper, SouborMapper, UzivatelNotifikaceMapper, UzivatelOpravneniMapper
from core.models import Soubor, SouborVazby
from core.repository_connector import (
    DryRunFedoraTransaction,
    FedoraDeletionOnlyTransaction,
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
    for item in projekt_query:
        item: Projekt
        logger.debug("core.cron.delete_unsubmited_projects.delete_projekt", extra={"ident_cely": item.ident_cely})
        fedora_transaction = FedoraTransaction()
        item.active_transaction = fedora_transaction
        try:
            if isinstance(item.soubory, SouborVazby):
                for item_file in item.soubory.soubory.all():
                    item.active_transaction = fedora_transaction
                    item_file.delete()
                item.soubory.delete()
                item.soubory = None
            item.suppress_signal = True
            item.delete()
            con = FedoraRepositoryConnector(item, fedora_transaction)
            if con.container_exists():
                con.delete_container(delete_tombstone=False)
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
def update_all_redis_snapshots(rewrite_existing=False):
    """
    Aktualizuje all redis snapshots.

    :param rewrite_existing: Číselná hodnota ``rewrite_existing`` použitá při výpočtu nebo transformaci.
    """
    logger.debug("cron.tasks.update_all_redis_snapshots.start")
    r = RedisConnector.get_connection()
    classes_list = (Akce, Projekt, Dokument, Lokalita, ExterniZdroj, UzivatelSpoluprace, SamostatnyNalez)
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
    """Provádí operaci call digiarchiv update task."""
    logger.debug("cron.tasks.call_digiarchiv_update_task.start")
    url = settings.DIGIARCHIV_URL
    requests.get(url)
    logger.debug("cron.tasks.call_digiarchiv_update_task.end")


@shared_task
def run_data_import(job_id, user_id):
    """
    Spustí data import.

    :param job_id: Identifikátor objektu ``job``.
    :param user_id: Identifikátor objektu ``user``.

        :raises ValueError: Vyvolá se při splnění podmínky ``isinstance(record, Model)``; nebo s textem "Missing required DIRECTORY_PATH setting".
    """
    logger.debug("cron.tasks.run_data_import.start", extra={"job_id": job_id})

    redis_connector = RedisConnector().get_connection()
    redis_connector.set("import_data_running", "true")
    record_count = int(redis_connector.get(f"import_data_count_{job_id}").decode("utf-8"))
    performed_action = redis_connector.get(f"import_performed_action_{job_id}").decode("utf-8")
    redis_connector.set(f"import_data_progress_{job_id}", json.dumps([]))
    redis_connector.set(f"import_data_files_{job_id}", json.dumps([]))
    failed = False
    import_results = {}
    import_primary_keys = {}
    mapper_classes = {}
    all_records = []
    import_files_list: list[Soubor] = []
    stopped = False
    fedora_update_targets_set = set()
    updated_history_dict = defaultdict(set)
    transaction_user = User.objects.get(pk=user_id)

    pending_fedora_update = []
    pending_history_update = []

    def add_updated_history(mapper_class, history_target):
        if history_target:
            updated_history_dict[(history_target.__class__, history_target.pk)].add(
                mapper_class.get_file_name_for_mapper(mapper_class)
            )

    try:
        with transaction.atomic():
            for record_id in range(record_count):
                primary_key_record = None
                try:
                    if performed_action in (
                        ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                        ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                    ):
                        fedora_transaction = DryRunFedoraTransaction()
                    else:
                        fedora_transaction = FedoraDeletionOnlyTransaction()
                    serialized_record = json.loads(
                        redis_connector.get(f"import_data_{job_id}_record_{record_id}").decode("utf-8")
                    )
                    mapper_class = ImportModelMapper.get_import_data_mapper(serialized_record.pop("__file_name"))
                    mapper_classes[record_id] = mapper_class
                    records = mapper_class(serialized_record).create_records(performed_action)
                    if mapper_class == SouborMapper:
                        import_files_list += records
                        record: Soubor = records[0]
                        import_results[record_id] = "cron.tasks.run_data_import.file"
                        redis_connector.set(f"import_data_progress_{job_id}", json.dumps(import_results))
                        continue
                    for record in records:
                        record.active_transaction = fedora_transaction
                        redis_connector.set(
                            f"import_data_status_message_{job_id}",
                            _("cron.tasks.run_data_import.importing_record_data") + f" {record_id + 1}/{record_count}",
                        )
                        if isinstance(record, ModelWithMetadata):
                            primary_key_record = record
                        elif hasattr(record, "ident_cely") and primary_key_record is None:
                            primary_key_record = record
                        all_records.append(record)
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
                                    # Record is saved to make sure Django value processing is done
                                    record.save()
                                    record_saved = mapper_class.load_record_from_db(record)
                                    pending_fedora_update.append((mapper_class, record_saved or record))
                                    record_dict = model_to_dict(record_saved) if record_saved else model_to_dict(record)
                                    if (
                                        performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT
                                        or record_dict != record_db_dict
                                    ):
                                        pending_history_update.append((mapper_class, record_saved or record))

                                else:
                                    raise ValueError(f"{_('cron.tasks.run_data_import.error.not_model')} {record_id}")
                            elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
                                fedora_update_targets_set |= mapper_class.fedora_update_targets(record)
                                record.active_transaction = fedora_transaction
                                record.delete()
                    fedora_transaction.mark_transaction_as_closed()

                    for item in pending_history_update:
                        mapper_class, record = item
                        add_updated_history(mapper_class, mapper_class.get_record_history(record))

                    for item in pending_fedora_update:
                        mapper_class, record = item
                        fedora_update_targets_set |= mapper_class.fedora_update_targets(record)

                    fedora_update_targets_set |= fedora_transaction.updated_ident_cely
                    logger.info("cron.tasks.run_data_import.success", extra={"record_id": record_id, "job_id": job_id})
                    import_results[record_id] = _("cron.tasks.run_data_import.success")
                    if primary_key_record:
                        import_primary_keys[record_id] = f"ident_cely: {primary_key_record.ident_cely}"
                    else:
                        import_primary_keys[record_id] = records[0].pk
                    redis_connector.set(f"import_data_progress_{job_id}", json.dumps(import_results))
                    redis_connector.set(f"import_data_primary_keys_{job_id}", json.dumps(import_primary_keys))
                except Exception as err:
                    logger.info(
                        "cron.tasks.run_data_import.error",
                        extra={"error": err, "record_id": record_id, "job_id": job_id},
                    )
                    fedora_transaction.rollback_transaction()
                    transaction.set_rollback(True)
                    import_results[record_id] = (
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
                    )
                    redis_connector.set(f"import_data_progress_{job_id}", json.dumps(import_results))
                    fedora_update_targets_set = set()
                    updated_history_dict = defaultdict(set)
                    failed = True
                stopped = redis_connector.get(f"import_data_stop_{job_id}") is not None or failed
                if stopped:
                    if not failed:
                        redis_connector.set(
                            f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.stopped_by_user")
                        )
                    else:
                        redis_connector.set(
                            f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.failed")
                        )
                    redis_connector.set(f"import_data_stop_{job_id}", 1)
                    logger.info("cron.tasks.run_data_import.files.insert.stopped", extra={"job_id": job_id})
                    break
    except Exception as err:
        redis_connector.set(f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.failed"))
        redis_connector.set(f"import_data_stop_{job_id}", 1)
        logger.error("cron.tasks.run_data_import.database_error", extra={"error": err, "job_id": job_id})
        for record_id in range(record_count):
            import_results[record_id] = f"{_('cron.tasks.run_data_import.error.database_error')}: {err}, "
        failed = True
        fedora_update_targets_set = set()
        updated_history_dict = defaultdict(set)

    for history_target_key, files in updated_history_dict.items():
        history_target_class, history_target_pk = history_target_key
        record = history_target_class.objects.get(pk=history_target_pk)
        historie_vazba = record.history_vazba if isinstance(record, User) else record.historie
        Historie(
            typ_zmeny=IMPORT,
            uzivatel=transaction_user,
            vazba=historie_vazba,
            poznamka=",".join(sorted(files)),
        ).save()

    for item in fedora_update_targets_set:
        if isinstance(item, tuple) and len(item) == 2:
            item_class, item_pk = item
            record = item_class.objects.get(pk=item_pk)
        else:
            record = get_record_from_ident(item)
        fedora_transaction = FedoraTransaction(transaction_user=transaction_user)
        record.save_metadata(fedora_transaction)
        fedora_transaction.mark_transaction_as_closed()

    import_results_files = []
    if (
        not failed
        and not stopped
        and performed_action
        in (
            ImportDataAdminForm.PERFORMED_ACTION_INSERT,
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )
    ):
        redis_connector.set(
            f"import_data_status_message_{job_id}",
            _("cron.tasks.run_data_import.file_import.validating_directory_settings"),
        )
        try:
            import_directory_settings_obj = CustomAdminSettings.objects.get(item_id="import_directory_settings")
            import_directory_settings = json.loads(import_directory_settings_obj.value)
            if not import_directory_settings.get("DIRECTORY_PATH"):
                raise ValueError("Missing required DIRECTORY_PATH setting")
            import_directory_path = import_directory_settings["DIRECTORY_PATH"]
            if not os.path.isdir(import_directory_path):
                raise ValueError(f"Import directory does not exist: {import_directory_path}")
        except Exception as err:
            logger.error(
                "cron.tasks.run_data_import.import_directory_not_configured",
                extra={"job_id": job_id, "error": str(err)},
            )
            redis_connector.set(
                f"import_data_status_message_{job_id}",
                _("cron.tasks.run_data_import.import_directory_not_configured"),
            )
            redis_connector.set(f"import_data_stop_{job_id}", 1)
            failed = True
        if not failed and import_files_list:
            redis_connector.set(
                f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.file_import.starting")
            )
            try:
                redis_connector.set(
                    f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.file_import.connected")
                )
                for file_index, soubor in enumerate(import_files_list):
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
                    stopped = redis_connector.get(f"import_data_stop_{job_id}") is not None
                    if stopped:
                        logger.info("cron.tasks.run_data_import.files.insert.stopped", extra={"job_id": job_id})
                        redis_connector.set(
                            f"import_data_status_message_{job_id}",
                            _("cron.tasks.run_data_import.stopped_by_user"),
                        )
                        break
                    soubor_query = Soubor.objects.filter(nazev=filename, vazba=soubor.vazba)
                    if not soubor_query.exists() and performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE:
                        import_results_files.append(
                            {
                                "ident_cely": ident_cely,
                                "file_name": filename,
                                "size_mb": None,
                                "additional_info": _("cron.tasks.run_data_import.does_not_exist"),
                            }
                        )
                        redis_connector.set(f"import_data_files_{job_id}", json.dumps(import_results_files))
                        continue
                    elif soubor_query.exists() and performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                        import_results_files.append(
                            {
                                "ident_cely": ident_cely,
                                "file_name": filename,
                                "size_mb": None,
                                "additional_info": _("cron.tasks.run_data_import.already_exists"),
                            }
                        )
                        redis_connector.set(f"import_data_files_{job_id}", json.dumps(import_results_files))
                        continue
                    if not os.path.isfile(file_path):
                        import_results_files.append(
                            {
                                "ident_cely": ident_cely,
                                "file_name": filename,
                                "size_mb": None,
                                "additional_info": _("cron.tasks.run_data_import.file_not_found_in_directory"),
                            }
                        )
                        redis_connector.set(f"import_data_files_{job_id}", json.dumps(import_results_files))
                        continue
                    soubor = soubor_query.first() or soubor
                    redis_connector.set(
                        f"import_data_status_message_{job_id}",
                        _("cron.tasks.run_data_import.importing_file") + f" {filename} ({ident_cely})",
                    )
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
                    else:
                        rep_bin_file = conn.update_binary_file(filename, mimetype, bio, soubor.repository_uuid)

                    soubor.mimetype = mimetype
                    soubor.size_mb = rep_bin_file.size_mb
                    soubor.sha_512 = rep_bin_file.sha_512
                    soubor.path = rep_bin_file.url_without_domain
                    soubor.suppress_signal = True
                    soubor.save()
                    if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                        soubor.create_soubor_vazby()
                    Historie(
                        typ_zmeny=IMPORT,
                        uzivatel=transaction_user,
                        vazba=soubor.historie,
                        poznamka=f"{_('cron.tasks.run_data_import.imported_file')} "
                        f"{import_directory_path}/{ident_cely}/{filename}",
                    ).save()
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
                    import_results_files.append(
                        {
                            "ident_cely": ident_cely,
                            "file_name": filename,
                            "size_mb": round(rep_bin_file.size_mb, 3),
                            "additional_info": mimetype,
                        }
                    )
                    redis_connector.set(f"import_data_files_{job_id}", json.dumps(import_results_files))
                redis_connector.set(
                    f"import_data_progress_files_{job_id}", round((file_index + 1) / len(import_files_list))
                )
            except Exception as err:
                logger.error(
                    "cron.tasks.run_data_import.directory_error",
                    extra={"error": err, "job_id": job_id, "traceback": traceback.format_exc()},
                )
                redis_connector.set(f"import_data_stop_{job_id}", 1)
                redis_connector.set(
                    f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.cannot_read_from_directory")
                )
                failed = True

    if not stopped and not failed:
        redis_connector.set(f"import_data_progress_files_{job_id}", 1)
        redis_connector.set(f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.finished"))
    expiration_seconds = 300
    redis_connector.expire(f"import_data_count_{job_id}", expiration_seconds)
    redis_connector.expire(f"import_data_files_{job_id}", expiration_seconds)
    redis_connector.expire(f"import_data_progress_files_{job_id}", expiration_seconds)
    redis_connector.expire(f"import_data_status_message_{job_id}", expiration_seconds)
    for record_id in range(record_count):
        redis_connector.expire(f"import_data_{job_id}_record_{record_id}", expiration_seconds)

    redis_connector.set("import_data_running", "false")
    logger.debug(
        "cron.tasks.run_data_import.end", extra={"job_id": job_id, "failed": failed, "record_count": record_count}
    )
