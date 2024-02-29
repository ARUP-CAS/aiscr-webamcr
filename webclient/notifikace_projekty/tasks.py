import logging

from celery import shared_task

from projekt.models import Projekt
from services.mailer import Mailer
from .models import Pes
from django.contrib.contenttypes.models import ContentType
from heslar.models import RuianKraj, RuianOkres, RuianKatastr
from uzivatel.models import UserNotificationType
from django.db.models import Q

logger = logging.getLogger(__name__)


@shared_task
def check_hlidaci_pes(projekt_id):
    """
    Task pro celery pro skontrolování jestli je nastavený hlídací pes.
    """
    logger.debug("cron.Notifications.collect_watchdogs.start")
    if not Projekt.objects.filter(pk=projekt_id).exists():
        return
    notification_type = UserNotificationType.objects.get(ident_cely='E-P-02')
    projekt = Projekt.objects.get(pk=projekt_id)
    users_to_notify = Pes.objects.none()
    all_katastre = RuianKatastr.objects.filter(Q(pk=projekt.hlavni_katastr.id)|Q(pk__in=projekt.katastry.values_list("id")))
    if notification_type.zasilat_neaktivnim:
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianKraj),
            object_id__in=all_katastre.values_list('okres__kraj__id'),
        )
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianOkres),
            object_id__in=all_katastre.values_list('okres__id'),
        )
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianKatastr),
            object_id__in=all_katastre.values_list('id'),
        )
    else:
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianKraj),
            object_id__in=all_katastre.values_list('okres__kraj__id'),
            user__is_active=True,
        )
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianOkres),
            object_id__in=all_katastre.values_list('okres__id'),
            user__is_active=True,
        )
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianKatastr),
            object_id__in=all_katastre.values_list('id'),
            user__is_active=True,
        )
    logger.debug("cron.Notifications.collect_watchdogs.watchdog_list", extra={"users_to_notify": users_to_notify})
    logger.debug("cron.Notifications.collect_watchdogs.end")
    return Mailer.send_ep02(users_to_notify.distinct("user"), projekt)
