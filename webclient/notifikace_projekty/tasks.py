import logging

from celery import shared_task

from projekt.models import Projekt
from services.mailer import Mailer
from .models import Pes
from django.contrib.contenttypes.models import ContentType
from heslar.models import RuianKraj, RuianOkres, RuianKatastr

logger_s = logging.getLogger(__name__)


@shared_task
def check_hlidaci_pes(projekt_id):
    """
    Task pro celery pro skontrolování jestli je nastavený hlídací pes.
    """
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
    logger_s.debug("cron.Notifications.collect_watchdogs.watchdog_list", extra={"users_to_notify": users_to_notify})
    logger_s.debug("cron.Notifications.collect_watchdogs.end")
    return Mailer.send_ep02(users_to_notify.distinct("user"),projekt)