from datetime import datetime, timedelta
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from historie.models import Historie


import logging

logger = logging.getLogger(__name__)


def collect_en01_en02(stav):
    logger.debug("cron.Notifications.collect_en01_en02.start")
    yesterday = (datetime.today() - timedelta(days=1)).date()
    entries_with_sent_status = Historie.objects.filter(typ_zmeny=stav, datum_zmeny__date=yesterday).all()
    findings = {}
    for entry in entries_with_sent_status:
        sn = SamostatnyNalez.objects.filter(historie=entry.vazba).first()
        cooperation = UzivatelSpoluprace.objects.filter(vedouci=entry.uzivatel).all()
        findings[sn.ident_cely] = {
            "users": []
        }
        for cooperation in cooperation:
            user = cooperation.spolupracovnik.email
            findings[sn.ident_cely]["users"].append(user)
    email_to = {}
    for key, finding in findings.items():
        for user in finding['users']:
            if user not in email_to:
                email_to[user] = [key]
            else:
                email_to[user].append(key)
    logger.debug("cron.Notifications.collect_en01_en02.email_to", extra={"email_to": email_to})
    return email_to
