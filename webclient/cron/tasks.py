import datetime
import logging
import traceback

import requests
from arch_z.models import Akce, ArcheologickyZaznam
from cacheops import invalidate_model
from celery import shared_task
from core.connectors import RedisConnector
from core.constants import (
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
from core.coordTransform import transform_geom_to_sjtsk
from core.models import SouborVazby
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from django.conf import settings
from django.db import connection
from django.db.models import F, Min, Prefetch, Q
from django.db.models.functions import Coalesce, Upper
from django.utils import timezone
from dokument.models import Dokument
from ez.models import ExterniZdroj
from heslar.hesla import HESLAR_PRISTUPNOST
from heslar.hesla_dynamicka import TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar
from historie.models import Historie
from lokalita.models import Lokalita
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pian.models import Pian
from projekt.models import Projekt
from services.mailer import Mailer
from uzivatel.models import Organizace, Osoba, User

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
        logger.debug("cron.tasks.send_notifications.do.send_enz_02.end")
        logger.debug("cron.tasks.send_notifications_enz.do.end")
    except Exception as err:
        logger.error(
            "cron.tasks.send_notifications_enz.do.error", extra={"error": str(err), "traceback": traceback.format_exc()}
        )


@shared_task
def send_notifications_en():
    """
    Každý den kontrola a odeslání emailů E-N-01 a E-N-02
    """
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
def pian_to_sjtsk():

    query_select = (
        "select pian.id,pian.ident_cely,ST_AsText(pian.geom) as geometry,ST_AsText(pian.geom_sjtsk) as geometry_sjtsk "
        " from public.pian pian "
        " where pian.geom is not null "
        " and (pian.geom_sjtsk is null or geom_system in ('5514*','sjtsk*'))"
        " and pian.id not in (select pian_id from public.amcr_geom_migrations_jobs_wgs84_errors)"
        " order by pian.id"
    )
    query_update = (
        "update public.pian pian "
        " set geom_sjtsk = ST_GeomFromText(%s), geom_sjtsk_updated_at=CURRENT_TIMESTAMP "
        " where pian.geom_sjtsk is null and pian.id=%s "
    )
    pians = Pian.objects.raw(query_select)
    c = len(pians)
    for idx, pian in enumerate(pians):
        if idx % (c // 100) == 0:
            print(f"\r{round(idx / c * 100)}%", end="")
        geom = transform_geom_to_sjtsk(pian.geometry)
        if geom[1] == "OK":
            with connection.cursor() as cursor:
                cursor.execute(query_update, [geom[0], pian.id])
        else:
            print("chyba pian id {pian.id}")


@shared_task
def nalez_to_sjtsk():
    query_select = (
        "select samostatny_nalez.id,samostatny_nalez.ident_cely,ST_AsText(samostatny_nalez.geom) as geometry,ST_AsText(samostatny_nalez.geom_sjtsk) as geometry_sjtsk "
        " from public.samostatny_nalez "
        " where samostatny_nalez.geom is not null "
        " and (samostatny_nalez.geom_sjtsk is null or geom_system in ('5514*','sjtsk*'))"
        " and samostatny_nalez.id not in (select pian_id from public.amcr_geom_migrations_jobs_wgs84_errors)"
        " order by samostatny_nalez.id"
    )
    query_update = (
        "update public.samostatny_nalez "
        " set geom_sjtsk = ST_GeomFromText(%s), geom_sjtsk_updated_at=CURRENT_TIMESTAMP "
        " where samostatny_nalez.geom_sjtsk is null and samostatny_nalez.id=%s "
    )
    SNs = SamostatnyNalez.objects.raw(query_select)
    c = len(SNs)
    for idx, SN in enumerate(SNs):
        if idx % (c // 100) == 0:
            print(f"\r{round(idx / c * 100)}%", end="")

        geom = transform_geom_to_sjtsk(SN.geometry)
        if geom[1] == "OK":
            with connection.cursor() as cursor:
                cursor.execute(query_update, [geom[0], SN.id])
        else:
            print("chyba SN id {SN.id}")


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
                    "core.cron.delete_personal_data_canceled_projects.do.project", extra={"project": item.ident_cely}
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
                extra={"project": item.ident_cely, "transaction": item.active_transaction.uid},
            )
            item.oznamovatel.delete()
            item.archive_project_documentation()
            item.oznamovatel = None
            item.save()
            item.close_active_transaction_when_finished = True
            item.save()
            logger.debug(
                "core.cron.delete_reporter_data_canceled_projects.do.end",
                extra={"project": item.ident_cely, "transaction": item.active_transaction.uid},
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
    invalidate_model(ArcheologickyZaznam)
    invalidate_model(Organizace)
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
            if item.pristupnost != pristupnost:
                item.active_transaction = FedoraTransaction()
                item.pristupnost = pristupnost
                item.close_active_transaction_when_finished = True
                item.save()
                logger.debug("core.cron.change_document_accessibility.do.dokument", extra={"dokument": item.ident_cely})
        logger.debug("core.cron.change_document_accessibility.do.end")
    except Exception as err:
        logger.error("core.cron.change_document_accessibility.do.error", extra={"error": err})


@shared_task
def delete_unsubmited_projects():
    """
    Každý den smazat projekty ve stavu -1, které vznikly před více než 12 hodinami.
    """
    logger.debug("core.cron.delete_unsubmited_projects.do.start")
    now_minus_12_hours = timezone.now() - datetime.timedelta(hours=12)
    projekt_query = (
        Projekt.objects.filter(stav=PROJEKT_STAV_VYTVORENY)
        .filter(historie__historie__datum_zmeny__lt=now_minus_12_hours)
        .distinct("id")
    )
    for item in projekt_query:
        item: Projekt
        fedora_transaction = FedoraTransaction()
        item.active_transaction = fedora_transaction
        try:
            has_soubory = False
            if isinstance(item.soubory, SouborVazby):
                for item_file in item.soubory.soubory.all():
                    item.active_transaction = fedora_transaction
                    item_file.delete()
                    has_soubory = True
                item.soubory.delete()
                item.soubory = None
            item.suppress_signal = True
            item.delete()
            if has_soubory:
                con = FedoraRepositoryConnector(item, fedora_transaction)
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
            project.close_active_transaction_when_finished = True
            project.set_zruseny(User.objects.get(email="amcr@arup.cas.cz"), cancelled_string, RUSENI_STARE_PROJ)
            logger.debug("core.cron.cancel_old_projects.do.project", extra={"ident_cely": project.ident_cely})
        logger.debug("core.cron.cancel_old_projects.do.end")
    except Exception as err:
        logger.error("core.cron.cancel_old_projects.do.error", extra={"error": err})


@shared_task
def update_snapshot_fields():
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
    logger.debug("cron.tasks.update_all_redis_snapshots.start")
    r = RedisConnector.get_connection()
    classes_list = (Akce, Projekt, Dokument, Lokalita, ExterniZdroj, UzivatelSpoluprace, SamostatnyNalez)
    for current_class in classes_list:
        logger.debug(
            "cron.tasks.update_all_redis_snapshots.class_start", extra={"current_class": current_class.__name__}
        )
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
        for item in query:
            if rewrite_existing or not r.exists(item.redis_snapshot_id):
                key, value = item.generate_redis_snapshot()
                if key and value:
                    pipe.hset(key, mapping=value)
        pipe.execute()
        logger.debug("cron.tasks.update_all_redis_snapshots.class_end", extra={"current_class": current_class.__name__})
    logger.debug("cron.tasks.update_all_redis_snapshots.end")


@shared_task
def update_single_redis_snapshot(class_name: str, record_pk):
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
    redis_connection = RedisConnector.get_connection()
    redis_connection.set(key, value)
    return key, value


@shared_task
def call_digiarchiv_update_task():
    logger.debug("cron.tasks.call_digiarchiv_update_task.start")
    url = settings.DIGIARCHIV_URL
    requests.get(url)
    logger.debug("cron.tasks.call_digiarchiv_update_task.end")
