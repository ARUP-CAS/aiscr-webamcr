from django_cron import CronJobBase, Schedule
from services.mailer import Mailer
from datetime import datetime, timedelta
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from historie.models import Historie
from core.constants import ODESLANI_SN, ARCHIVACE_SN


class FindingsNotification(CronJobBase):
    code = "cron.job777.MyProjectCronJob"  # a unique code
    RUN_EVERY_MINS = 2  # every 2 minutes

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)

    def do(self):
        yesterday = (datetime.today() - timedelta(days=1)).date()
        entries_with_sent_status = Historie.objects.filter(typ_zmeny=ODESLANI_SN, datum_zmeny__date=yesterday).all()
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

    def do2(self):
        yesterday = (datetime.today() - timedelta(days=1)).date()
        entries_with_sent_status = Historie.objects.filter(typ_zmeny=ARCHIVACE_SN, datum_zmeny__date=yesterday).all()
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