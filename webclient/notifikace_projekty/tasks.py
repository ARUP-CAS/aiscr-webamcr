import structlog
from celery import shared_task
from celery.schedules import crontab
from webclient.celery import app


from projekt.models import Projekt
from services.mailer import Mailer
from .models import Pes
from django.contrib.contenttypes.models import ContentType
from heslar.models import RuianKraj, RuianOkres, RuianKatastr
from datetime import datetime, timedelta
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from historie.models import Historie
from core.constants import ODESLANI_SN, ARCHIVACE_SN

logger_s = structlog.get_logger(__name__)


@shared_task
def check_hlidaci_pes(projekt_id):
    logger_s.debug("cron.Notifications.collect_watchdogs.start")
    projekt = Projekt.objects.get(pk=projekt_id)
    users_to_notify = Pes.objects.none()
    users_to_notify |= Pes.objects.filter(
        content_type=ContentType.objects.get_for_model(RuianKraj),
        object_id=projekt.hlavni_katastr.okres.kraj.id,
    )
    users_to_notify |= Pes.objects.filter(
        content_type=ContentType.objects.get_for_model(RuianOkres),
        object_id=projekt.hlavni_katastr.okres.id,
    )
    users_to_notify |= Pes.objects.filter(
        content_type=ContentType.objects.get_for_model(RuianKatastr),
        object_id=projekt.hlavni_katastr.id,
    )
    logger_s.debug(
        "cron.Notifications.collect_watchdogs.watchdog_list",
        users_to_notify=users_to_notify,
    )
    logger_s.debug("cron.Notifications.collect_watchdogs.end")
    return Mailer.send_ep02(users_to_notify.distinct("user"), projekt)


def collect_en01_en02(self, stav):
    logger_s.debug("cron.Notifications.collect_en01_en02.start")
    yesterday = (datetime.today() - timedelta(days=1)).date()
    entries_with_sent_status = Historie.objects.filter(
        typ_zmeny=stav, datum_zmeny__date=yesterday
    ).all()
    findings = {}
    for entry in entries_with_sent_status:
        sn = SamostatnyNalez.objects.filter(historie=entry.vazba).first()
        cooperations = UzivatelSpoluprace.objects.filter(vedouci=entry.uzivatel).all()
        findings[sn.ident_cely] = {"users": []}
        for cooperation in cooperations:
            user = cooperation.spolupracovnik.email
            findings[sn.ident_cely]["users"].append(user)
    email_to = {}
    for key, finding in findings.items():
        for user in finding["users"]:
            if user not in email_to:
                email_to[user] = [key]
            else:
                email_to[user].append(key)
    logger_s.debug("cron.Notifications.collect_en01_en02.email_to", email_to=email_to)
    return email_to


@app.task
def send_nz_mails():
    logger_s.debug("cron.Notifications.do.start")
    Mailer.send_enz01()
    logger_s.debug("cron.Notifications.do.send_enz_01.end")
    Mailer.send_enz02()
    logger_s.debug("cron.Notifications.do.send_enz_02.end")
    dataEn01 = collect_en01_en02(stav=ODESLANI_SN)
    for email, ids in dataEn01.items():
        Mailer.send_en01(send_to=email, project_ids=ids)
    dataEn02 = collect_en01_en02(stav=ARCHIVACE_SN)
    for email, ids in dataEn02.items():
        Mailer.send_en02(send_to=email, project_ids=ids)


app.conf.beat_schedule = {
 "posli nz emaily": {
 "task": "notifikace_projekty.tasks.send_nz_mails",
 "schedule": crontab(hour=0, minute=0),
 }
}