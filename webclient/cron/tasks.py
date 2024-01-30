import datetime
import logging
import traceback

import redis
from celery import shared_task
from django.db.models import Q, F, Min, Prefetch
from django.db.models.functions import Upper
from django.utils import timezone

from adb.models import Adb
from arch_z.models import ArcheologickyZaznam, Akce, ExterniOdkaz
from core.connectors import RedisConnector
from core.constants import ODESLANI_SN, ARCHIVACE_SN, PROJEKT_STAV_ZRUSENY, RUSENI_PROJ, PROJEKT_STAV_VYTVORENY, \
    OZNAMENI_PROJ, ZAPSANI_PROJ
from core.models import Soubor
from cron.convertToSJTSK import get_multi_transform_to_sjtsk
from cron.classes import MyList
from cron.functions import collect_en01_en02
from django.db import connection, transaction
from django.utils.translation import gettext as _

from cron.convertToWGS84 import get_multi_transform_to_wgs84
from dj.models import DokumentacniJednotka
from dokument.models import Dokument, Let, DokumentCast
from ez.models import ExterniZdroj
from heslar.hesla import HESLAR_PRISTUPNOST
from heslar.models import Heslar, RuianKatastr, RuianOkres, RuianKraj
from historie.models import Historie
from lokalita.models import Lokalita
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pian.models import Pian
from projekt.models import Projekt
from services.mailer import Mailer
from uzivatel.models import Organizace, Osoba, User
from webclient.settings.base import get_plain_redis_pass

logger = logging.getLogger(__name__)


NUM_TO_WGS84_CONVERT = 200
NUM_TO_SJTSK_CONVERT = 200


@shared_task
def send_notifications():
    """
     Každý den zkontrolovat a případně odeslat upozornění uživatelům na základě pole projekt.datum_odevzdani_NZ,
     pokud je projekt ve stavu <P5 a zároveň:
        -- pokud [dnes] + 90 dní = datum_odevzdani_NZ => email E-NZ-01
        -- pokud [dnes] - 1 den = datum_odevzdani_NZ => email E-NZ-02

     Každý den kontrola a odeslání emailů E-N-01 a E-N-02
    """
    try:
        logger.debug("cron.Notifications.do.start")
        Mailer.send_enz01()
        logger.debug("cron.Notifications.do.send_enz_01.end")
        Mailer.send_enz02()
        logger.debug("cron.Notifications.do.send_enz_02.end")
        dataEn01 = collect_en01_en02(stav=ODESLANI_SN)
        for email, projekt_id_list in dataEn01.items():
            Mailer.send_en01(send_to=email, projekt_id_list=projekt_id_list)
        dataEn02 = collect_en01_en02(stav=ARCHIVACE_SN)
        for email, ids in dataEn02.items():
            Mailer.send_en02(send_to=email, projekt_id_list=projekt_id_list)
        logger.debug("cron.Notifications.do.end")
    except Exception as err:
        logger.error("cron.send_notifications.do.error", extra={"error": err})


@shared_task
def pian_to_sjstk():
    try:
        count_selected_wgs84 = 0
        count_updated_sjtsk = 0
        count_error_sjtsk = 0
        query_select = (
            "select pian.id,pian.ident_cely,ST_AsText(pian.geom) as geometry,ST_AsText(pian.geom_sjtsk) as geometry_sjtsk "
            " from public.pian pian "
            " where pian.geom is not null "
            " and (pian.geom_sjtsk is null or geom_system in ('5514*','sjtsk*'))"
            " and pian.id not in (select pian_id from public.amcr_geom_migrations_jobs_wgs84_errors)"
            " order by pian.id"
            " limit %s"
        )
        query_update = (
            "update public.pian pian "
            " set geom_sjtsk = ST_GeomFromText(%s), geom_sjtsk_updated_at=CURRENT_TIMESTAMP "
            " where pian.geom_sjtsk is null and pian.id=%s "
            " and ST_AsText(pian.geom)=%s"
        )
        query_insert_err = "insert into public.amcr_geom_migrations_jobs_wgs84_errors(pian_id) values(%s)"
        query_insert_stat = "insert into public.amcr_geom_migrations_jobs(typ,count_selected_wgs84,count_updated_sjtsk,count_error_sjtsk) values(%s,%s,%s,%s)"
        query_delete_jobs = "delete from public.amcr_geom_migrations_jobs where typ='pian:wgs84->sjtsk' and created_at<CURRENT_TIMESTAMP - INTERVAL '1' hour and count_selected_wgs84=0 and count_selected_sjtsk=0"

        try:
            l = MyList()
            xx = []
            pians = Pian.objects.raw(query_select, [self.NUM_TO_SJTSK_CONVERT])
            for pian in pians:
                count_selected_wgs84 += 1
                l.add(pian.id, pian.geometry)
                xx.append(pian.geometry)
            if count_selected_wgs84 > 0:
                l2 = l.simple_list()
                l3 = get_multi_transform_to_sjtsk(l2)
                l4 = l.geom_list(l3)
                for i in range(0, len(l4)):
                    logger.debug("+" + l4[i][1] + "  " + str(l4[i][0]))
                    if l4[i][1] == "ERROR":
                        with connection.cursor() as cursor:
                            count_error_sjtsk += 1
                            cursor.execute(query_insert_err, [l4[i][0]])
                    else:
                        with connection.cursor() as cursor:
                            count_updated_sjtsk += 1
                            cursor.execute(
                                query_update, [l4[i][0], l4[i][1], xx[i]]
                            )
                with connection.cursor() as cursor:
                    cursor.execute(
                        query_insert_stat,
                        [
                            "pian:wgs84->sjtsk",
                            count_selected_wgs84,
                            count_updated_sjtsk,
                            count_error_sjtsk,
                        ],
                    )
                    cursor.execute(query_delete_jobs)
        except Exception as e:
            logger.debug("Error during migrations pians wgs84->sJTSK")
            logger.debug(e)
            logger.debug(traceback.format_exc())
            return None
    except Exception as err:
        logger.error("cron.pian_to_sjstk.do.error", extra={"error": err})


@shared_task
def pian_to_wsg_84():
    try:
        count_selected_sjtsk = 0
        count_selected_wgs84 = 0
        count_error_wgs84 = 0
        query_select = (
            "select pian.id,pian.ident_cely,ST_AsText(pian.geom) as geometry,ST_AsText(pian.geom_sjtsk) as geometry_sjtsk "
            " from public.pian pian "
            " where pian.geom is null "
            " and pian.geom_sjtsk is not null "
            " and pian.id not in (select pian_id from public.amcr_geom_migrations_jobs_sjtsk_errors)"
            " order by pian.id"
            " limit %s"
        )
        query_update = (
            "update public.pian pian "
            " set geom = ST_GeomFromText(%s), geom_updated_at=CURRENT_TIMESTAMP "
            " where pian.geom is null and pian.id=%s "
            " and ST_AsText(pian.geom_sjtsk)=%s"
        )
        query_insert_err = "insert into public.amcr_geom_migrations_jobs_sjtsk_errors(pian_id) values(%s)"
        query_insert_stat = "insert into public.amcr_geom_migrations_jobs(typ,count_selected_sjtsk,count_selected_wgs84,count_error_wgs84) values(%s,%s,%s,%s)"
        query_insert_stat2 = "insert into public.amcr_geom_migrations_jobs(typ,count_selected_sjtsk,detail) values(%s,%s,%s)"
        query_delete_jobs = "delete from public.amcr_geom_migrations_jobs where typ='pian:sjtsk->wgs84' and created_at<CURRENT_TIMESTAMP - INTERVAL '1' hour and count_selected_sjtsk=0 and count_selected_sjtsk=0"

        try:
            l = MyList()
            xx = []
            pians = Pian.objects.raw(query_select, [NUM_TO_WGS84_CONVERT])
            for pian in pians:
                count_selected_sjtsk += 1
                l.add(pian.id, pian.geometry_sjtsk)
                xx.append(pian.geometry_sjtsk)
            if count_selected_sjtsk > 0:
                l2 = l.simple_list()
                l3 = get_multi_transform_to_wgs84(l2)
                if l3 is not None:
                    l4 = l.geom_list(l3)
                    for i in range(0, len(l4)):
                        logger.debug("+" + l4[i][1] + "  " + str(l4[i][0]))
                        if l4[i][1] == "ERROR":
                            with connection.cursor() as cursor:
                                count_error_wgs84 += 1
                                cursor.execute(query_insert_err, [l4[i][0]])
                        else:
                            with connection.cursor() as cursor:
                                count_selected_wgs84 += 1
                                cursor.execute(
                                    query_update, [l4[i][0], l4[i][1], xx[i]]
                                )
                    with connection.cursor() as cursor:
                        cursor.execute(
                            query_insert_stat,
                            [
                                "pian:sjtsk->wgs84",
                                count_selected_sjtsk,
                                count_selected_wgs84,
                                count_error_wgs84,
                            ],
                        )
                        cursor.execute(query_delete_jobs)
                else:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            query_insert_stat2,
                            [
                                "pian:sjtsk->wgs84",
                                count_selected_sjtsk,
                                "Error during connection to CUZK",
                            ],
                        )
                        cursor.execute(query_delete_jobs)
            else:
                with connection.cursor() as cursor:
                    cursor.execute(
                        query_insert_stat,
                        [
                            "pian:sjtsk->wgs84",
                            count_selected_sjtsk,
                            count_selected_wgs84,
                            count_error_wgs84,
                        ],
                    )
                    cursor.execute(query_delete_jobs)
        except Exception as e:
            logger.debug("Error during migrations pians sjtsk->wgs84")
            logger.debug(e)
            logger.debug(traceback.format_exc())
            return None
    except Exception as err:
        logger.error("cron.pian_to_wsg_84.do.error", extra={"error": err})


@shared_task
def nalez_to_sjtsk():
    try:
        count_selected_wgs84 = 0
        count_updated_sjtsk = 0
        count_error_sjtsk = 0
        query_select = (
            "select samostatny_nalez.id,samostatny_nalez.ident_cely,ST_AsText(samostatny_nalez.geom) as geometry,ST_AsText(samostatny_nalez.geom_sjtsk) as geometry_sjtsk "
            " from public.samostatny_nalez "
            " where samostatny_nalez.geom is not null "
            " and (samostatny_nalez.geom_sjtsk is null or geom_system in ('5514*','sjtsk*'))"
            " and samostatny_nalez.id not in (select pian_id from public.amcr_geom_migrations_jobs_wgs84_errors)"
            " order by samostatny_nalez.id"
            " limit %s"
        )
        query_update = (
            "update public.samostatny_nalez "
            " set geom_sjtsk = ST_GeomFromText(%s), geom_sjtsk_updated_at=CURRENT_TIMESTAMP "
            " where samostatny_nalez.geom_sjtsk is null and samostatny_nalez.id=%s "
            " and ST_AsText(samostatny_nalez.geom)=%s"
        )
        query_insert_err = "insert into public.amcr_geom_migrations_jobs_wgs84_errors(pian_id) values(%s)"
        query_insert_stat = "insert into public.amcr_geom_migrations_jobs(typ,count_selected_wgs84,count_updated_sjtsk,count_error_sjtsk) values(%s,%s,%s,%s)"
        query_delete_jobs = "delete from public.amcr_geom_migrations_jobs where typ='samostatny_nalez:wgs84->sjtsk' and created_at<CURRENT_TIMESTAMP - INTERVAL '1' hour and count_selected_wgs84=0 and count_selected_sjtsk=0"

        try:
            l = MyList()
            xx = []
            SNs = SamostatnyNalez.objects.raw(
                query_select, [NUM_TO_SJTSK_CONVERT]
            )
            for SN in SNs:
                count_selected_wgs84 += 1
                l.add(SN.id, SN.geometry)
                xx.append(SN.geometry)
            if count_selected_wgs84 > 0:
                l2 = l.simple_list()
                l3 = get_multi_transform_to_sjtsk(l2)
                l4 = l.geom_list(l3)
                for i in range(0, len(l4)):
                    logger.debug("+" + l4[i][1] + "  " + str(l4[i][0]))
                    if l4[i][1] == "ERROR":
                        with connection.cursor() as cursor:
                            count_error_sjtsk += 1
                            cursor.execute(query_insert_err, [l4[i][0]])
                    else:
                        with connection.cursor() as cursor:
                            count_updated_sjtsk += 1
                            cursor.execute(
                                query_update, [l4[i][0], l4[i][1], xx[i]]
                            )
                with connection.cursor() as cursor:
                    cursor.execute(
                        query_insert_stat,
                        [
                            "samostatny_nalez:wgs84->sjtsk",
                            count_selected_wgs84,
                            count_updated_sjtsk,
                            count_error_sjtsk,
                        ],
                    )
                    cursor.execute(query_delete_jobs)
        except Exception as e:
            logger.debug("Error during migrations pians wgs84->sJTSK")
            logger.debug(e)
            logger.debug(traceback.format_exc())
            return None
    except Exception as err:
        logger.error("cron.nalez_to_sjtsk.do.error", extra={"error": err})


@shared_task
def nalez_to_wsg84(self):
    try:
        count_selected_sjtsk = 0
        count_selected_wgs84 = 0
        count_error_wgs84 = 0
        query_select = (
            "select samostatny_nalez.id,samostatny_nalez.ident_cely,ST_AsText(samostatny_nalez.geom) as geometry,ST_AsText(samostatny_nalez.geom_sjtsk) as geometry_sjtsk "
            " from public.samostatny_nalez "
            " where samostatny_nalez.geom is null "
            " and samostatny_nalez.geom_sjtsk is not null "
            " and samostatny_nalez.id not in (select pian_id from public.amcr_geom_migrations_jobs_sjtsk_errors)"
            " order by samostatny_nalez.id"
            " limit %s"
        )
        query_update = (
            "update public.samostatny_nalez "
            " set geom = ST_GeomFromText(%s), geom_updated_at=CURRENT_TIMESTAMP "
            " where samostatny_nalez.geom is null and samostatny_nalez.id=%s "
            " and ST_AsText(samostatny_nalez.geom_sjtsk)=%s"
        )
        query_insert_err = "insert into public.amcr_geom_migrations_jobs_sjtsk_errors(pian_id) values(%s)"
        query_insert_stat = "insert into public.amcr_geom_migrations_jobs(typ,count_selected_sjtsk,count_selected_wgs84,count_error_wgs84) values(%s,%s,%s,%s)"
        query_insert_stat2 = "insert into public.amcr_geom_migrations_jobs(typ,count_selected_sjtsk,detail) values(%s,%s,%s)"
        query_delete_jobs = "delete from public.amcr_geom_migrations_jobs where typ='samostatny_nalez:sjtsk->wgs84' and created_at<CURRENT_TIMESTAMP - INTERVAL '1' hour and count_selected_sjtsk=0 and count_selected_sjtsk=0"

        try:
            l = MyList()
            xx = []
            SNs = SamostatnyNalez.objects.raw(
                query_select, [self.NUM_TO_WGS84_CONVERT]
            )
            for SN in SNs:
                count_selected_sjtsk += 1
                l.add(SN.id, SN.geometry_sjtsk)
                xx.append(SN.geometry_sjtsk)
            if count_selected_sjtsk > 0:
                l2 = l.simple_list()
                l3 = get_multi_transform_to_wgs84(l2)
                if l3 is not None:
                    l4 = l.geom_list(l3)
                    for i in range(0, len(l4)):
                        logger.debug("+" + l4[i][1] + "  " + str(l4[i][0]))
                        if l4[i][1] == "ERROR":
                            with connection.cursor() as cursor:
                                count_error_wgs84 += 1
                                cursor.execute(query_insert_err, [l4[i][0]])
                        else:
                            with connection.cursor() as cursor:
                                count_selected_wgs84 += 1
                                cursor.execute(
                                    query_update, [l4[i][0], l4[i][1], xx[i]]
                                )
                    with connection.cursor() as cursor:
                        cursor.execute(
                            query_insert_stat,
                            [
                                "samostatny_nalez:sjtsk->wgs84",
                                count_selected_sjtsk,
                                count_selected_wgs84,
                                count_error_wgs84,
                            ],
                        )
                        cursor.execute(query_delete_jobs)
                else:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            query_insert_stat2,
                            [
                                "samostatny_nalez:sjtsk->wgs84",
                                count_selected_sjtsk,
                                "Error during connection to CUZK",
                            ],
                        )
                        cursor.execute(query_delete_jobs)
            else:
                with connection.cursor() as cursor:
                    cursor.execute(
                        query_insert_stat,
                        [
                            "samostatny_nalez:sjtsk->wgs84",
                            count_selected_sjtsk,
                            count_selected_wgs84,
                            count_error_wgs84,
                        ],
                    )
                    cursor.execute(query_delete_jobs)
        except Exception as e:
            logger.debug("Error during migrations pians sjtsk->wgs84")
            logger.debug(e)
            logger.debug(traceback.format_exc())
            return None
    except Exception as err:
        logger.error("cron.nalez_to_wsg84.do.error", extra={"error": err})


def get_record(class_name, record_pk):
    if class_name == "Projekt":
        record = Projekt.objects.get(pk=record_pk)
    elif class_name == "SamostatnyNalez":
        record = SamostatnyNalez.objects.get(pk=record_pk)
    elif class_name == "Heslar":
        record = Heslar.objects.get(pk=record_pk)
    elif class_name == "RuianKatastr":
        record = RuianKatastr.objects.get(pk=record_pk)
    elif class_name == "RuianKraj":
        record = RuianKraj.objects.get(pk=record_pk)
    elif class_name == "RuianOkres":
        record = RuianOkres.objects.get(pk=record_pk)
    elif class_name == "ArcheologickyZaznam":
        record = ArcheologickyZaznam.objects.get(pk=record_pk)
    elif class_name == "ExterniZdroj":
        record = ExterniZdroj.objects.get(pk=record_pk)
    elif class_name == "Adb":
        record = Adb.objects.get(pk=record_pk)
    elif class_name == "Pian":
        record = Pian.objects.get(pk=record_pk)
    elif class_name == "Dokument":
        record = Dokument.objects.get(pk=record_pk)
    elif class_name == "Let":
        record = Let.objects.get(pk=record_pk)
    elif class_name == "Organizace":
        record = Organizace.objects.get(pk=record_pk)
    elif class_name == "Osoba":
        record = Osoba.objects.get(pk=record_pk)
    elif class_name == "User":
        record = User.objects.get(pk=record_pk)
    else:
        logger.debug("cron.tasks.get_record.error.unknown_class",
                     extra={"class_name": class_name, "record_pk": record_pk})
        record = None
    return record


@shared_task
def save_record_metadata(class_name, record_pk):
    try:
        logger.debug("cron.save_record_metadata.do.start", extra={"class_name": class_name,
                                                                  "record_pk": record_pk})
        from xml_generator.models import ModelWithMetadata
        record = get_record(class_name, record_pk)
        if record is not None:
            record: ModelWithMetadata
            from core.repository_connector import FedoraRepositoryConnector
            connector = FedoraRepositoryConnector(record)
            connector.save_metadata(True)
        else:
            ident_cely = record.ident_cely if hasattr(record, "ident_cely") else "no_ident"
            logger.warning("cron.save_record_metadata.do.is_null",
                           extra={"class_name": class_name, "record_pk": record_pk, "ident_cely": ident_cely})
        logger.debug("cron.save_record_metadata.do.end", extra={"class_name": class_name, "record_pk": record_pk})
    except Exception as err:
        logger.error("cron.save_record_metadata.do.error", extra={"class_name": class_name,
                                                                  "record_pk": record_pk, "error": err})


@shared_task
def record_ident_change(class_name, record_pk, old_ident):
    try:
        logger.debug("cron.record_ident_change.do.start", extra={"class_name": class_name, "record_pk": record_pk,
                                                                 "old_ident": old_ident})
        from core.repository_connector import FedoraRepositoryConnector
        record = get_record(class_name, record_pk)
        if record.ident_cely == old_ident or old_ident is None:
            logger.debug("cron.record_ident_change.do.no_change", extra={"class_name": class_name,
                                                                         "record_pk": record_pk, "old_ident": old_ident})
            return
        connector = FedoraRepositoryConnector(record)
        connector.record_ident_change(old_ident)
        logger.debug("cron.record_ident_change.do.end", extra={"class_name": class_name, "record_pk": record_pk,
                                                               "old_ident": old_ident})

        def process_arch_z(inner_item: ArcheologickyZaznam):
            for inner_item in record.dokumentacni_jednotky_akce.all():
                inner_item: DokumentacniJednotka
                if inner_item.pian:
                    inner_item.pian.save_metadata()
                if inner_item.adb:
                    inner_item.adb.save_metadata()
            for inner_item in record.casti_dokumentu.all():
                inner_item: DokumentCast
                inner_item.dokument.save_metadata()
            for inner_item in record.externi_odkazy.all():
                inner_item: ExterniOdkaz
                inner_item.externi_zdroj.save_metadata()
            if inner_item.projekt:
                inner_item.projekt.save_metadata()

        if isinstance(record, ArcheologickyZaznam):
            process_arch_z(record)
        elif isinstance(record, Dokument):
            for item in record.casti.all():
                item: DokumentCast
                if item.archeologicky_zaznam:
                    item.archeologicky_zaznam.save_metadata()
                if item.projekt:
                    item.projekt.save_metadata()
            if item.let:
                item.let.save_metadata()
        elif isinstance(record, ExterniZdroj):
            for item in record.externi_odkazy_zdroje.all():
                item: ExterniOdkaz
                item.archeologicky_zaznam.save_metadata()
        elif isinstance(record, Projekt):
            for item in record.casti_dokumentu.all():
                item: DokumentCast
                item.dokument.save_metadata()
            for item in record.samostatne_nalezy.all():
                item: SamostatnyNalez
                item.save_metadata()
        elif isinstance(record, Lokalita):
            archeologicky_zaznam: ArcheologickyZaznam = record.archeologicky_zaznam
            process_arch_z(archeologicky_zaznam)
        elif isinstance(record, SamostatnyNalez):
            if record.projekt:
                record.projekt.save_metadata()
        elif isinstance(record, Pian):
            for item in record.dokumentacni_jednotky_pianu.all():
                item: DokumentacniJednotka
                item.archeologicky_zaznam.save_metadata()

    except Exception as err:
        logger.error("cron.record_ident_change.do.error", extra={"error": err})


@shared_task
def delete_personal_data_canceled_projects():
    """
     Rok po zrušení projektu nahradit související údaje v tabulce oznamovatel řetězcem “RRRR-MM-DD: údaj odstraněn”,
     kromě pole projekt.oznamovatel + odstranit projektovou dokumentaci a vytvořit log (jako při archivaci projektu).
    """
    try:
        logger.debug("core.cron.delete_personal_data_canceled_projects.do.start")
        deleted_string = _("core.tasks.nalez_to_sjtsk.data_deleted")
        today = datetime.datetime.now().date()
        year_ago = today - datetime.timedelta(days=365)
        projects = Projekt.objects.filter(stav=PROJEKT_STAV_ZRUSENY)\
            .filter(~Q(oznamovatel__email__icontains=deleted_string))\
            .filter(historie__historie__typ_zmeny=RUSENI_PROJ)\
            .filter(historie__historie__datum_zmeny__lt=year_ago)
        for item in projects:
            item: Projekt
            if item.has_oznamovatel():
                logger.debug("core.cron.delete_personal_data_canceled_projects.do.project",
                             extra={"project": item.ident_cely})
                item.oznamovatel.email = f"{today.strftime('%Y%m%d')}: {deleted_string}"
                item.oznamovatel.adresa = f"{today.strftime('%Y%m%d')}: {deleted_string}"
                item.oznamovatel.odpovedna_osoba = f"{today.strftime('%Y%m%d')}: {deleted_string}"
                item.oznamovatel.oznamovatel = f"{today.strftime('%Y%m%d')}: {deleted_string}"
                item.oznamovatel.telefon = f"{today.strftime('%Y%m%d')}: {deleted_string}"
                item.oznamovatel.save()
                item.archive_project_documentation()
        logger.debug("core.cron.delete_personal_data_canceled_projects.do.end")
    except Exception as err:
        logger.error("core.cron.delete_personal_data_canceled_projects.do.error", extra={"error": err})


@shared_task
def delete_reporter_data_canceled_projects():
    """
     Deset let po zápisu projektu smazat související záznam z tabulky oznamovatel + odstranit projektovou dokumentaci
     a vytvořit log (jako při archivaci projektu).
    """
    try:
        logger.debug("core.cron.delete_reporter_data_canceled_projects.do.start")
        today = datetime.datetime.now().date()
        ten_years_ago = today - datetime.timedelta(days=365*10)
        projects = Projekt.objects.filter(stav=PROJEKT_STAV_ZRUSENY)\
            .filter(oznamovatel__isnull=False)\
            .filter(historie__historie__datum_zmeny__lt=ten_years_ago)
        for item in projects:
            logger.debug("core.cron.delete_reporter_data_canceled_projects.do.project", extra={"project": item.ident_cely})
            item.oznamovatel.delete()
            item.archive_project_documentation()
        logger.debug("core.cron.delete_reporter_data_canceled_projects.do.end")
    except Exception as err:
        logger.error("core.cron.delete_reporter_data_canceled_projects.do.error", extra={"error": err})


@shared_task
def change_document_accessibility():
    """
    Každý den změnit přístupnost dokumentů, u kterých datum_zverejneni<=[dnes], a to na přístupnost stanovenou
    v hesláři organizace (podle vazby dokument.organizace), ale nikdy ne na vyšší přístupnost, než má nejlépe
    přístupný připojený archeologický záznam (tj. když mají připojené AZ C a D, bude mít dokument nejvýše C).
    """
    try:
        logger.debug("core.cron.change_document_accessibility.do.start")
        documents = Dokument.objects\
            .filter(datum_zverejneni__lte=datetime.datetime.now().date()) \
            .annotate(min_pristupnost_razeni=Min(F("casti__archeologicky_zaznam__pristupnost__razeni"))) \
            .filter(Q(pristupnost__razeni__gt=F("min_pristupnost_razeni"))
                    | ~Q(pristupnost__razeni=F('organizace__zverejneni_pristupnost__razeni')))
        for item in documents:
            item: Dokument
            pristupnost_razeni = min(*[x.archeologicky_zaznam.pristupnost.razeni for x in item.casti.all()],
                                     item.organizace.zverejneni_pristupnost.razeni)
            pristupnost = Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST)\
                .filter(razeni=pristupnost_razeni).first()
            if item.pristupnost != pristupnost:
                item.pristupnost = pristupnost
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
    try:
        logger.debug("core.cron.delete_unsubmited_projects.do.start")
        now_minus_12_hours = timezone.now() - datetime.timedelta(hours=12)
        Projekt.objects.filter(stav=PROJEKT_STAV_VYTVORENY).filter(historie__historie__typ_zmeny=OZNAMENI_PROJ)\
            .filter(historie__historie__datum_zmeny__lt=now_minus_12_hours).delete()
        logger.debug("core.cron.delete_unsubmited_projects.do.end")
    except Exception as err:
        logger.error("core.cron.delete_unsubmited_projects.do.error", extra={"error": err})


@shared_task
def cancel_old_projects():
    """
     Každý den převést na P8 projekty v P1 starší tří let, které mají plánované datum zahájení více než rok
     v minulosti. Do poznámky ke zrušení uvést “Automatické zrušení projektů starších tří let, u kterých již
     nelze očekávat zahájení.”
    """
    try:
        logger.debug("core.cron.cancel_old_projects.do.start")
        toady_minus_3_years = timezone.now() - datetime.timedelta(days=365 * 3)
        toady_minus_1_year = timezone.now() - datetime.timedelta(days=365)
        projects = Projekt.objects.filter(stav=PROJEKT_STAV_VYTVORENY) \
            .filter(Q(historie__historie__typ_zmeny=ZAPSANI_PROJ)
                    & Q(historie__historie__datum_zmeny__lt=toady_minus_3_years)) \
            .annotate(upper=Upper('planovane_zahajeni')).annotate(new_upper=F('upper')) \
            .filter(upper__lte=toady_minus_1_year)
        cancelled_string = _("core.tasks.cancel_old_projects.cancelled")
        for project in projects:
            project: Projekt
            project.set_zruseny(User.objects.get(email="amcr@arup.cas.cz"), cancelled_string)
            logger.debug("core.cron.cancel_old_projects.do.project", extra={"ident_cely": project.ident_cely})
        logger.debug("core.cron.cancel_old_projects.do.end")
    except Exception as err:
        logger.error("core.cron.cancel_old_projects.do.error", extra={"error": err})


@shared_task
def update_snapshot_fields():
    try:
        logger.debug("core.cron.update_snapshot_fields.do.start")
        for item in ExterniZdroj.objects.filter((Q(autori_snapshot__isnull=True) | Q(editori_snapshot__isnull=True))
                                                & (Q(externizdrojautor__isnull=False)
                                                   | Q(externizdrojeditor__isnull=False))):
            item.suppress_signal = True
            item.save()
        for item in Dokument.objects.filter((Q(autori_snapshot__isnull=True) | Q(osoby_snapshot__isnull=True))
                                            & (Q(dokumentautor__isnull=False) | Q(dokumentosoba__isnull=False))):
            item: Dokument
            item.suppress_signal = True
            item.save()
        for item in Lokalita.objects.filter(Q(dalsi_katastry_snapshot__isnull=True)
                                            & Q(archeologicky_zaznam__katastry__isnull=False)):
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
        logger.debug("cron.tasks.update_all_redis_snapshots.class_start",
                     extra={"current_class": current_class.__name__})
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
        logger.debug("cron.tasks.update_all_redis_snapshots.class_end",
                     extra={"current_class": current_class.__name__})
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
