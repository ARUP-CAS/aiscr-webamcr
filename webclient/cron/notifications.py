


from django_cron import CronJobBase, Schedule
from services.mailer import Mailer
from datetime import datetime, timedelta
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from historie.models import Historie
from core.constants import ODESLANI_SN, ARCHIVACE_SN


import logging
import logstash

logger_s = logging.getLogger('python-logstash-logger')


class Notifications(CronJobBase):
    code = "cron.notifications.Notifications"  # a unique code
    RUN_AT_TIMES = ["00:00", ]
    schedule = Schedule(run_at_times=RUN_AT_TIMES)

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
