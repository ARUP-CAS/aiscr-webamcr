import logging
import traceback

from celery import shared_task

from core.constants import ODESLANI_SN, ARCHIVACE_SN
from cron.convertToSJTSK import get_multi_transform_to_sjtsk
from cron.classes import MyList
from cron.functions import collect_en01_en02
from django.db import connection

from cron.convertToWGS84 import get_multi_transform_to_wgs84
from pas.models import SamostatnyNalez
from pian.models import Pian
from services.mailer import Mailer

logger = logging.getLogger(__name__)


NUM_TO_WGS84_CONVERT = 200
NUM_TO_SJTSK_CONVERT = 200


@shared_task
def send_notifications():
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


@shared_task
def pian_to_jstk():
    try:
        count_selected_wgs84 = 0
        count_updated_sjtsk = 0
        count_error_sjtsk = 0
        query_select = (
            "select pian.id,pian.ident_cely,ST_AsText(pian.geom) as geometry,ST_AsText(pian.geom_sjtsk) as geometry_sjtsk "
            " from public.pian pian "
            " where pian.geom is not null "
            " and pian.geom_sjtsk is null "
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
                                query_update, [l4[i][1], l4[i][0], xx[i]]
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
    except Exception as e:
        logger.debug(e)


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
                                    query_update, [l4[i][1], l4[i][0], xx[i]]
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
    except Exception as e:
        logger.debug(e)


@shared_task
def nalez_to_jsk():
    try:
        count_selected_wgs84 = 0
        count_updated_sjtsk = 0
        count_error_sjtsk = 0
        query_select = (
            "select samostatny_nalez.id,samostatny_nalez.ident_cely,ST_AsText(samostatny_nalez.geom) as geometry,ST_AsText(samostatny_nalez.geom_sjtsk) as geometry_sjtsk "
            " from public.pian pian "
            " where samostatny_nalez.geom is not null "
            " and samostatny_nalez.geom_sjtsk is null "
            " and samostatny_nalez.id not in (select pian_id from public.amcr_geom_migrations_jobs_wgs84_errors)"
            " order by samostatny_nalez.id"
            " limit %s"
        )
        query_update = (
            "update public.pian pian "
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
                                query_update, [l4[i][1], l4[i][0], xx[i]]
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
    except Exception as e:
        logger.debug(e)


@shared_task
def nalez_to_wsg84(self):
    try:
        count_selected_sjtsk = 0
        count_selected_wgs84 = 0
        count_error_wgs84 = 0
        query_select = (
            "select samostatny_nalez.id,samostatny_nalez.ident_cely,ST_AsText(samostatny_nalez.geom) as geometry,ST_AsText(samostatny_nalez.geom_sjtsk) as geometry_sjtsk "
            " from public.pian pian "
            " where samostatny_nalez.geom is null "
            " and samostatny_nalez.geom_sjtsk is not null "
            " and samostatny_nalez.id not in (select pian_id from public.amcr_geom_migrations_jobs_sjtsk_errors)"
            " order by samostatny_nalez.id"
            " limit %s"
        )
        query_update = (
            "update public.pian pian "
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
                                    query_update, [l4[i][1], l4[i][0], xx[i]]
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
    except Exception as e:
        logger.debug(e)
