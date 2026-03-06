import logging
import time

from celery import shared_task
from core.constants import ROLE_ADMIN_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from heslar.hesla_dynamicka import TYP_PROJEKTU_BADATELSKY_ID, TYP_PROJEKTU_PRUZKUM_ID, TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import RuianKatastr, RuianKraj, RuianOkres
from projekt.models import Projekt
from services.mailer import Mailer
from uzivatel.models import User, UserNotificationType

from .models import Pes

logger = logging.getLogger(__name__)


def get_project_type_notification(projekt_type):
    """
    Vrací project type notification.

    :param projekt_type: Parametr ``projekt_type`` předává se do volání ``get()``, vstupuje do návratové hodnoty.

        :return: Vrací výsledek volání ``get()``.
    """
    projekt_notifikace = {
        TYP_PROJEKTU_BADATELSKY_ID: "S-E-P-02a",
        TYP_PROJEKTU_PRUZKUM_ID: "S-E-P-02b",
        TYP_PROJEKTU_ZACHRANNY_ID: "S-E-P-02c",
    }
    return UserNotificationType.objects.get(ident_cely=projekt_notifikace.get(projekt_type))


@shared_task
def check_hlidaci_pes(projekt_id):
    """
    Task pro celery pro skontrolování jestli je nastavený hlídací pes.

    :param projekt_id: Identifikátor ``projekt_id`` používaný pro dohledání cílového záznamu.

        :return: Vrací výsledek volání ``send_ep02()``.
    """
    logger.debug("cron.Notifications.collect_watchdogs.start")
    notification_type = UserNotificationType.objects.get(ident_cely="E-P-02")
    # čekání na uložení do DB
    projekts = Projekt.objects.filter(pk=projekt_id)
    while projekts.count() < 1:
        time.sleep(0.5)
        projekts = Projekt.objects.filter(pk=projekt_id)
    projekt = projekts.first()
    users_to_notify = Pes.objects.none()
    all_katastre = RuianKatastr.objects.filter(
        Q(pk=projekt.hlavni_katastr.id) | Q(pk__in=projekt.katastry.values_list("id"))
    )
    projekt_notify_type = get_project_type_notification(projekt.typ_projektu_id)
    users_with_notification = User.objects.filter(notification_types=projekt_notify_type)
    if users_with_notification.count() == 0:
        logger.debug("cron.Notifications.collect_watchdogs.end.noUsers")
        return
    if notification_type.zasilat_neaktivnim:
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianKraj),
            object_id__in=all_katastre.values_list("okres__kraj__id"),
            user__in=users_with_notification,
        )
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianOkres),
            object_id__in=all_katastre.values_list("okres__id"),
            user__in=users_with_notification,
        )
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianKatastr),
            object_id__in=all_katastre.values_list("id"),
            user__in=users_with_notification,
        )
    else:
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianKraj),
            object_id__in=all_katastre.values_list("okres__kraj__id"),
            user__is_active=True,
            user__in=users_with_notification,
        )
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianOkres),
            object_id__in=all_katastre.values_list("okres__id"),
            user__is_active=True,
            user__in=users_with_notification,
        )
        users_to_notify |= Pes.objects.filter(
            content_type=ContentType.objects.get_for_model(RuianKatastr),
            object_id__in=all_katastre.values_list("id"),
            user__is_active=True,
            user__in=users_with_notification,
        )
    logger.debug(
        "cron.Notifications.collect_watchdogs.watchdog_list",
        extra={"value": users_to_notify.values_list("user")},
    )
    logger.debug("cron.Notifications.collect_watchdogs.end")
    users_to_notify = users_to_notify.filter(
        user__groups__id__in=([ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID])
    )
    return Mailer.send_ep02(users_to_notify.distinct("user"), projekt)
