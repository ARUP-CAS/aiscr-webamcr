import structlog

from django.contrib.contenttypes.models import ContentType
from django_cron import CronJobBase, Schedule
from services.mailer import Mailer
from datetime import datetime, timedelta
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from historie.models import Historie
from watchdog.models import Watchdog
from core.constants import ODESLANI_SN, ARCHIVACE_SN
from heslar.models import RuianKraj, RuianOkres, RuianKatastr
from core.constants import PROJEKT_STAV_ZAPSANY, SCHVALENI_OZNAMENI_PROJ
from projekt.models import Projekt
from django.db import connection


logger_s = structlog.get_logger(__name__)


class Notifications(CronJobBase):
    code = "cron.notifications.Notifications"  # a unique code
    RUN_AT_TIMES = ["00:00", ]
    schedule = Schedule(run_at_times=RUN_AT_TIMES)

    def collect_projects_by_okres(self, okres: RuianOkres):
        logger_s.debug("cron.Notifications.collect_projects_by_okres.start")
        katastry = RuianKatastr.objects.filter(okres=okres).values_list('id', flat=True)
        yesterday_start = str(datetime.today() - timedelta(days=1))
        yesterday_end = str(datetime.today())
        logger_s.debug("cron.Notifications.do.dates", yesterday_start=yesterday_start, yesterday_end=yesterday_end)
        with connection.cursor() as cursor:
            query = "SELECT ident_cely FROM projekt LEFT OUTER JOIN historie ON projekt.historie=historie.vazba " \
                    f"WHERE projekt.hlavni_katastr IN {tuple(katastry)} " \
                    f"AND historie.typ_zmeny={SCHVALENI_OZNAMENI_PROJ} " \
                    f"AND historie.datum_zmeny >= {yesterday_start} " \
                    f"AND historie.datum_zmeny <= {yesterday_end}"
            logger_s.debug("cron.Notifications.do.dates", query=query)
            cursor.execute(query)
            result = cursor.fetchall()
            return [element for tupl in result for element in tupl]

    def collect_projects_by_kraj(self, kraj: RuianKraj):
        logger_s.debug("cron.Notifications.collect_projects_by_kraj.start")
        result = []
        okresy = RuianOkres.objects.filter(kraj=kraj)
        for okres in okresy:
            result = list(set(self.collect_projects_by_okres(okres=okres) + result))
        return result

    def collect_watchdogs(self):
        logger_s.debug("cron.Notifications.collect_watchdogs.start")
        watchdog_list = []
        emails_with_projects = {}
        content_type = ContentType.objects.get_for_model(RuianKraj)
        watchdogs = Watchdog.objects.filter(content_type=content_type)
        # Collect Kraj watchdogs and projects
        for watchdog in watchdogs:
            kraj = RuianKraj.objects.get(pk=watchdog.object_id)
            watchdog_list.append({
                "email": watchdog.user.email,
                "projects": self.collect_projects_by_kraj(kraj=kraj)
            })
        logger_s.debug("cron.Notifications.collect_watchdogs.watchdog_list", watchdog_list=watchdog_list)
        # Collect Okres watchdogs and projects
        content_type = ContentType.objects.get_for_model(RuianOkres)
        watchdogs = Watchdog.objects.filter(content_type=content_type)
        for watchdog in watchdogs:
            okres = RuianOkres.objects.get(pk=watchdog.object_id)
            watchdog_list.append({
                "email": watchdog.user.email,
                "projects": self.collect_projects_by_okres(okres=okres)
            })
        logger_s.debug("cron.Notifications.collect_watchdogs.watchdog_list", watchdog_list=watchdog_list)
        for watchdog in watchdog_list:
            if watchdog['email'] not in emails_with_projects.keys():
                emails_with_projects[watchdog['email']] = watchdog['projects']
            else:
                emails_with_projects[watchdog['email']] = list(
                    set(emails_with_projects[watchdog['email']] + watchdog['projects']))
        logger_s.debug("cron.Notifications.collect_watchdogs.end")
        return emails_with_projects

    def collect_en01_en02(self, stav):
        logger_s.debug("cron.Notifications.collect_en01_en02.start")
        yesterday = (datetime.today() - timedelta(days=1)).date()
        entries_with_sent_status = Historie.objects.filter(typ_zmeny=stav, datum_zmeny__date=yesterday).all()
        findings = {}
        for entry in entries_with_sent_status:
            sn = SamostatnyNalez.objects.filter(historie=entry.vazba).first()
            cooperations = UzivatelSpoluprace.objects.filter(vedouci=entry.uzivatel).all()
            findings[sn.ident_cely] = {
                "users": []
            }
            for cooperation in cooperations:
                user = cooperation.spolupracovnik.email
                findings[sn.ident_cely]["users"].append(user)
        email_to = {}
        for key, finding in findings.items():
            for user in finding['users']:
                if user not in email_to:
                    email_to[user] = [key]
                else:
                    email_to[user].append(key)
        logger_s.debug("cron.Notifications.collect_en01_en02.email_to", email_to=email_to)
        return email_to

    def do(self):
        logger_s.debug("cron.Notifications.do.start")
        Mailer.send_enz01()
        logger_s.debug("cron.Notifications.do.send_enz_01.end")
        Mailer.send_enz02()
        logger_s.debug("cron.Notifications.do.send_enz_02.end")
        dataEn01 = self.collect_en01_en02(stav=ODESLANI_SN)
        for email, ids in dataEn01.items():
            Mailer.send_en01(send_to=email, project_ids=ids)
        dataEn02 = self.collect_en01_en02(stav=ARCHIVACE_SN)
        for email, ids in dataEn02.items():
            Mailer.send_en02(send_to=email, project_ids=ids)
