import logging
import traceback

from cron.convertToWGS84 import get_multi_transform_to_wgs84
from cron.list import MyList
from django.db import connection
from django_cron import CronJobBase, Schedule
from pas.models import SamostatnyNalez

logger = logging.getLogger("django_cron")


class MyCronJobPianToWGS84(CronJobBase):
    RUN_EVERY_MINS = 2  # every 2 minutes
    NUM_TO_WGS84_CONVERT = 200

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "cron.job04.MyCronJobSamNalezToWGS84"  # a unique code

    def do(self):
        try:
            count_selected_sjtsk = 0
            count_selected_wgs84 = 0
            count_error_wgs84 = 0
            query_select = (
                "select samostatny_nalez.id,samostatny_nalez.ident_cely,ST_AsText(samostatny_nalez.geom) as geometry,ST_AsText(samostatny_nalez.geom_sjtsk) as geometry_sjtsk "
                " from public.pian pian "
                # " where samostatny_nalez.id in (141341,141342) "
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
                    # if count_selected_sjtsk==2:
                    #    l.add(samostatny_nalez.id, 'MULTIPOINT ((10 40), (40 30), (20 20), (30 10))')
                    #    xx.append('MULTIPOINT ((10 40), (40 30), (20 20), (30 10))')
                    # else:
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
                                # logger.debug(l4[i][1],)
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
        pass  # do your thing here
