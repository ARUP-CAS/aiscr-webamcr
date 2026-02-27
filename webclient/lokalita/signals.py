import logging

from arch_z.models import Akce
from cacheops import invalidate_model
from cron.tasks import update_single_redis_snapshot
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from lokalita.models import Lokalita
from xml_generator.models import UPDATE_REDIS_SNAPSHOT, check_if_task_queued

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Lokalita, weak=False)
def save_lokalita_snapshot(sender, instance: Lokalita, **kwargs):
    """Uloží lokalita snapshot.
    
    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek provedené operace."""
    logger.debug(
        "lokalita.signals.save_lokalita_snapshot.start", extra={"ident_cely": instance.archeologicky_zaznam.ident_cely}
    )
    invalidate_model(Lokalita)
    invalidate_model(Akce)
    try:
        instance.set_snapshots()
    except ValueError as err:
        logger.debug(
            "lokalita.signals.save_lokalita_snapshot.type_error",
            extra={"ident_cely": instance.archeologicky_zaznam.ident_cely, "error": err},
        )
    else:
        logger.debug(
            "lokalita.signals.save_lokalita_snapshot.end",
            extra={"ident_cely": instance.archeologicky_zaznam.ident_cely},
        )


@receiver(post_save, sender=Lokalita, weak=False)
def save_lokalita_redis_snapshot(sender, instance: Lokalita, **kwargs):
    """Uloží lokalita redis snapshot.
    
    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek provedené operace."""
    logger.debug(
        "lokalita.signals.save_lokalita_redis_snapshot.start",
        extra={"ident_cely": instance.archeologicky_zaznam.ident_cely},
    )
    if not check_if_task_queued("Lokalita", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["Lokalita", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    logger.debug(
        "lokalita.signals.save_lokalita_redis_snapshot.end",
        extra={"ident_cely": instance.archeologicky_zaznam.ident_cely},
    )


@receiver(pre_delete, sender=Lokalita, weak=False)
def delete_lokalita(sender, instance: Lokalita, **kwargs):
    """Odstraní lokalita.
    
    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek operace odstranění."""
    logger.debug(
        "lokalita.signals.delete_lokalita.start", extra={"ident_cely": instance.archeologicky_zaznam.ident_cely}
    )
    invalidate_model(Lokalita)
    invalidate_model(Akce)
    logger.debug("lokalita.signals.delete_lokalita.end", extra={"ident_cely": instance.archeologicky_zaznam.ident_cely})
