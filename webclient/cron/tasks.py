import datetime
import json
import logging
import traceback
from ftplib import FTP
from io import BytesIO

import requests
from arch_z.models import Akce
from cacheops import invalidate_model
from celery import shared_task
from core.connectors import RedisConnector
from core.constants import (
    IMPORT,
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
from core.forms import ImportDataAdminForm
from core.import_data_mappers import ImportModelMapper, SouborMapper, UzivatelNotifikaceMapper, UzivatelOpravneniMapper
from core.models import Soubor, SouborVazby
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from core.setting_models import CustomAdminSettings
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import connection, transaction
from django.db.models import F, Min, Model, Prefetch, Q
from django.db.models.functions import Coalesce, Upper
from django.utils import timezone
from django.utils.translation import gettext as _
from dokument.models import Dokument, DokumentExtraData
from ez.models import ExterniZdroj
from heslar import hesla_dynamicka
from heslar.hesla import HESLAR_PRISTUPNOST
from heslar.hesla_dynamicka import DOKUMENT_LICENCE_NEZNAMA, TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar
from historie.models import Historie
from lokalita.models import Lokalita
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pian.models import Pian
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
        "select pian.id,ST_AsText(pian.geom) as geometry "
        " from public.pian pian "
        " where pian.geom is not null "
        " and (pian.geom_sjtsk is null)"
        " order by pian.id"
    )
    query_update = (
        "update public.pian pian "
        " set geom_sjtsk = ST_GeomFromText(%s)"
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
        "select samostatny_nalez.id, ST_AsText(samostatny_nalez.geom) as geometry "
        " from public.samostatny_nalez "
        " where samostatny_nalez.geom is not null "
        " and (samostatny_nalez.geom_sjtsk is null)"
        " order by samostatny_nalez.id"
    )
    query_update = (
        "update public.samostatny_nalez "
        " set geom_sjtsk = ST_GeomFromText(%s) "
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
def projekt_to_sjtsk():
    query_select = (
        "select projekt.id,projekt.ident_cely,ST_AsText(projekt.geom) as geometry,ST_AsText(projekt.geom_sjtsk) as geometry_sjtsk "
        " from public.projekt "
        " where projekt.geom is not null "
        " and projekt.geom_sjtsk is null "
        " order by projekt.id"
    )
    query_update = (
        "update public.projekt "
        " set geom_sjtsk = ST_GeomFromText(%s) "
        " where projekt.geom_sjtsk is null and projekt.id=%s "
    )
    PRJs = Projekt.objects.raw(query_select)
    c = len(PRJs)
    for idx, PRJ in enumerate(PRJs):
        if c > 100 and idx % (c // 100) == 0:
            print(f"\r{round(idx / c * 100)}%", end="")

        geom = transform_geom_to_sjtsk(PRJ.geometry)
        if geom[1] == "OK":
            with connection.cursor() as cursor:
                cursor.execute(query_update, [geom[0], PRJ.id])
        else:
            print("chyba PRJ id {PRJ.id}")


@shared_task
def dokument_to_sjtsk():
    query_select = (
        "select dokument_extra_data.dokument,ST_AsText(dokument_extra_data.geom) as geometry,ST_AsText(dokument_extra_data.geom_sjtsk) as geometry_sjtsk "
        " from public.dokument_extra_data "
        " where dokument_extra_data.geom is not null "
        " and dokument_extra_data.geom_sjtsk is null "
        " order by dokument_extra_data.dokument"
    )
    query_update = (
        "update public.dokument_extra_data "
        " set geom_sjtsk = ST_GeomFromText(%s) "
        " where dokument_extra_data.geom_sjtsk is null and dokument_extra_data.dokument=%s "
    )
    DOCs = DokumentExtraData.objects.raw(query_select)
    c = len(DOCs)
    for idx, DOC in enumerate(DOCs):
        if c > 100 and idx % (c // 100) == 0:
            print(f"\r{round(idx / c * 100)}%", end="")
        try:
            geom = transform_geom_to_sjtsk(DOC.geometry)
            if geom[1] == "OK":
                with connection.cursor() as cursor:
                    cursor.execute(query_update, [geom[0], DOC.pk])
            else:
                print("chyba DOC id {DOC.pk}")
        except Exception as err:
            logger.warning("core.cron.dokument_to_sjtsk.warning", extra={"error": err})


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
            project.set_zruseny(User.objects.get(pk=hesla_dynamicka.ADMIN_USER), cancelled_string, RUSENI_STARE_PROJ)
            if project.typ_projektu.pk == TYP_PROJEKTU_ZACHRANNY_ID and project.has_oznamovatel():
                project.create_cancel_confirmation_document(User.objects.get(pk=hesla_dynamicka.ADMIN_USER))
            project.close_active_transaction_when_finished = True
            project.save()
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


@shared_task
def set_pristupnost_snapshot():
    from django.db import transaction

    BATCH_SIZE = 100
    projekt_count = Projekt.objects.all().count()
    for i in range(projekt_count // BATCH_SIZE + 1):
        print(f"\r{i} / {projekt_count // BATCH_SIZE}", end="", flush=True)
        with transaction.atomic():
            projekty = list(Projekt.objects.order_by("id")[i * BATCH_SIZE : (i + 1) * BATCH_SIZE])
            for projekt in projekty:
                projekt.suppress_signal = True
                projekt.set_pristupnost()
            Projekt.objects.bulk_update(projekty, ["pristupnost_snapshot"])


@shared_task
def pians_properties_check():
    """
    Jednorázová oprava dat PIANů v rámci issue 2940
    """
    from django.contrib.gis.db.models.functions import Centroid
    from django.contrib.gis.geos import GeometryCollection, LineString, MultiPolygon, Point, Polygon
    from heslar.hesla_dynamicka import GEOMETRY_BOD, GEOMETRY_LINIE, GEOMETRY_PLOCHA
    from pian.models import get_ZM_from_point

    geom_type = {}
    geom_type[str(Point)] = Heslar.objects.get(id=GEOMETRY_BOD)
    geom_type[str(LineString)] = Heslar.objects.get(id=GEOMETRY_LINIE)
    geom_type[str(Polygon)] = Heslar.objects.get(id=GEOMETRY_PLOCHA)
    geom_type[str(MultiPolygon)] = Heslar.objects.get(id=GEOMETRY_PLOCHA)
    geom_type[str(GeometryCollection)] = Heslar.objects.get(id=GEOMETRY_PLOCHA)
    query = Pian.objects.all()
    pocet = 0
    pocet_pians = query.count()
    index = 0
    for item in query.iterator(chunk_size=1000):
        save = False
        geom = item.geom
        if item.typ.pk != geom_type[str(type(geom))].pk:
            item.typ = geom_type[str(type(geom))]
            save = True
        if type(geom) == Point:
            point = geom
        elif type(geom) == LineString:
            point = geom.interpolate_normalized(0.5)
        else:
            point = Centroid(geom)
        zm10, zm50 = get_ZM_from_point(point)
        if zm10 is not None and zm50 is not None:
            if item.zm10.pk != zm10.pk:
                item.zm10 = zm10
                save = True
            if item.zm50.pk != zm50.pk:
                item.zm50 = zm50
                save = True
        if save is True:
            pocet = pocet + 1
            print(f"\r{pocet} {index}/{pocet_pians}", end="")
            fedora_transaction = FedoraTransaction()
            item.active_transaction = fedora_transaction
            item.update_all_azs = False
            item.close_active_transaction_when_finished = True
            item.save()
        index = index + 1

    print(f"pocet zmen {pocet}")


@shared_task
def run_data_import(job_id, user_id):
    logger.debug("cron.tasks.run_data_import.start", extra={"job_id": job_id})

    redis_connector = RedisConnector().get_connection()

    record_count = int(redis_connector.get(f"import_data_count_{job_id}").decode("utf-8"))
    performed_action = redis_connector.get(f"import_performed_action_{job_id}").decode("utf-8")
    redis_connector.set(f"import_data_progress_{job_id}", json.dumps([]))
    redis_connector.set(f"import_data_files_{job_id}", json.dumps([]))
    failed = False
    import_results = {}
    mapper_classes = {}
    all_records = []
    import_files_list: list[Soubor] = []
    stopped = False

    try:
        with transaction.atomic():
            for record_id in range(record_count):
                try:
                    fedora_transaction = FedoraTransaction()
                    serialized_record = json.loads(
                        redis_connector.get(f"import_data_{job_id}_record_{record_id}").decode("utf-8")
                    )
                    mapper_class = ImportModelMapper.get_import_data_mapper(serialized_record.pop("__file_name"))
                    mapper_classes[record_id] = mapper_class
                    records = mapper_class(serialized_record).create_records(performed_action)
                    if mapper_class == SouborMapper:
                        import_files_list += records
                        record: Soubor = records[0]
                        import_results[
                            record_id
                        ] = f"{_('cron.tasks.run_data_import.file')}, {str(record.nazev)} ({record.vazba.navazany_objekt.ident_cely})"
                        redis_connector.set(f"import_data_progress_{job_id}", json.dumps(import_results))
                        continue
                    for record in records:
                        redis_connector.set(
                            f"import_data_status_message_{job_id}",
                            _("cron.tasks.run_data_import.importing_record_data") + f" {record_id + 1}/{record_count}",
                        )
                        all_records.append(record)
                        if mapper_class == UzivatelOpravneniMapper:
                            record: User
                            group = Group.objects.get(name=serialized_record["skupina"])
                            if performed_action in (
                                ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                                ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                            ):
                                record.groups.add(group)
                            elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
                                record.groups.remove(group)
                        if mapper_class == UzivatelNotifikaceMapper:
                            record: User
                            group = UserNotificationType.objects.get(ident_cely=serialized_record["notifikace"])
                            if performed_action in (
                                ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                                ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                            ):
                                record.notification_types.add(group)
                            elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
                                record.notification_types.remove(group)
                        else:
                            if performed_action in (
                                ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                                ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                            ):
                                if isinstance(record, Model):
                                    record.suppress_signal = True
                                    mapper_class.create_relations(record)
                                    mapper_class.record_postprocessing(record, performed_action)
                                    if hasattr(record, "historie"):
                                        record.save()
                                        Historie(
                                            typ_zmeny=IMPORT,
                                            uzivatel=User.objects.get(pk=user_id),
                                            vazba=record.historie,
                                            poznamka=serialized_record,
                                        ).save()
                                    else:
                                        record.save()
                                else:
                                    raise ValueError(f"{_('cron.tasks.run_data_import.error.not_model')} {record_id}")
                            elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
                                record.suppress_signal = False
                                record.active_transaction = fedora_transaction
                                record.delete()
                        if isinstance(record, ModelWithMetadata):
                            record.save_metadata(fedora_transaction)
                    fedora_transaction.mark_transaction_as_closed()
                    logger.info("cron.tasks.run_data_import.success", extra={"record_id": record_id, "job_id": job_id})
                    import_results[
                        record_id
                    ] = f"{_('cron.tasks.run_data_import.success')}, {[', '.join(str(record.pk) for record in records if record.pk)]}"
                    redis_connector.set(f"import_data_progress_{job_id}", json.dumps(import_results))
                except Exception as err:
                    logger.info(
                        "cron.tasks.run_data_import.error",
                        extra={"error": err, "record_id": record_id, "job_id": job_id},
                    )
                    fedora_transaction.rollback_transaction()
                    transaction.set_rollback(True)
                    import_results[record_id] = (
                        f"{_('cron.tasks.run_data_import.error.part_1')}: {err}, "
                        f"{_('cron.tasks.run_data_import.error.part_2')} {serialized_record}, "
                        f"{_('cron.tasks.run_data_import.error.part_3')} {performed_action}" + traceback.format_exc()
                    )
                    redis_connector.set(f"import_data_progress_{job_id}", json.dumps(import_results))
                    failed = True
                    break
                stopped = redis_connector.get(f"import_data_stop_{job_id}") is not None
                if stopped:
                    redis_connector.set(
                        f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.stopped_by_user")
                    )
                    redis_connector.set(f"import_data_stop_{job_id}", 1)
                    logger.info("cron.tasks.run_data_import.files.insert.stopped", extra={"job_id": job_id})
                    break
    except Exception as err:
        redis_connector.set(f"import_data_stop_{job_id}", 1)
        logger.error("cron.tasks.run_data_import.database_error", extra={"error": err, "job_id": job_id})
        for record_id in range(record_count):
            import_results[record_id] = f"{_('cron.tasks.run_data_import.error.database_error')}: {err}, "
        failed = True

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
            f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.file_import.starting")
        )
        ftp_settings = json.loads(CustomAdminSettings.objects.get(item_id="ftp_import_settings").value)
        try:
            with FTP(
                host=ftp_settings["FILE_IMPORT_FTP_HOSTNAME"],
                user=ftp_settings["FILE_IMPORT_FTP_USER_NAME"],
                passwd=ftp_settings["FILE_IMPORT_FTP_PASSWORD"],
            ) as ftp:
                ftp.cwd(ftp_settings["FILE_IMPORT_FTP_PATH"])
                redis_connector.set(
                    f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.file_import.connected")
                )
                for soubor in import_files_list:
                    soubor: Soubor
                    if stopped:
                        break
                    ident_cely = soubor.vazba.navazany_objekt.ident_cely
                    if ident_cely in ftp.nlst():
                        ftp.cwd(ident_cely)
                        filename = soubor.nazev
                        stopped = redis_connector.get(f"import_data_stop_{job_id}") is not None
                        if stopped:
                            logger.info("cron.tasks.run_data_import.files.insert.stopped", extra={"job_id": job_id})
                            redis_connector.set(
                                f"import_data_status_message_{job_id}",
                                _("cron.tasks.run_data_import.stopped_by_user"),
                            )
                            break
                        soubor_query = Soubor.objects.filter(nazev=filename, vazba=soubor.vazba)
                        if (
                            not soubor_query.exists()
                            and performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE
                        ):
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
                        else:
                            soubor = soubor_query.first() or soubor
                        redis_connector.set(
                            f"import_data_status_message_{job_id}",
                            _("cron.tasks.run_data_import.importing_file") + f" {filename} ({ident_cely})",
                        )
                        fedora_transaction = FedoraTransaction()
                        conn = FedoraRepositoryConnector(
                            soubor.vazba.navazany_objekt, fedora_transaction, skip_container_check=False
                        )
                        bio = BytesIO()
                        ftp.retrbinary(f"RETR {filename}", bio.write)
                        mimetype = Soubor.get_mime_types(bio)
                        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                            rep_bin_file = conn.save_binary_file(filename, mimetype, bio)
                        else:
                            rep_bin_file = conn.update_binary_file(filename, mimetype, bio, soubor.repository_uuid)
                        soubor.mimetype = mimetype
                        soubor.size_mb = rep_bin_file.size_mb
                        soubor.sha_512 = rep_bin_file.sha_512
                        soubor.path = rep_bin_file.url_without_domain
                        """
                                                            soubor: Soubor = Soubor(
                                        vazba=record.soubory,
                                        nazev=filename,
                                        mimetype=mimetype,
                                        size_mb=rep_bin_file.size_mb,
                                        path=rep_bin_file.url_without_domain,
                                        sha_512=sha_512,
                                    )
                        """
                        soubor.suppress_signal = True
                        soubor.save()
                        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                            soubor.create_soubor_vazby()
                        Historie(
                            typ_zmeny=IMPORT,
                            uzivatel=User.objects.get(pk=user_id),
                            vazba=soubor.historie,
                            poznamka=f"{_('cron.tasks.run_data_import.imported_file')} "
                            f"{ftp_settings['FILE_IMPORT_FTP_PATH']}/{ident_cely}/{filename}",
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
                        ftp.cwd("..")
                    redis_connector.set(f"import_data_progress_files_{job_id}", round((record_id + 1) / record_count))
        except Exception as err:
            logger.error("cron.tasks.run_data_import.fpt_error", extra={"error": err, "job_id": job_id})
            redis_connector.set(f"import_data_stop_{job_id}", 1)
            redis_connector.set(
                f"import_data_status_message_{job_id}", _("cron.tasks.run_data_import.cannot_connect_to_ftp")
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

    logger.debug(
        "cron.tasks.run_data_import.end", extra={"job_id": job_id, "failed": failed, "record_count": record_count}
    )
