import logging

from cacheops import invalidate_model

from cron.tasks import update_single_redis_snapshot
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver

from lokalita.models import Lokalita
from arch_z.models import ArcheologickyZaznam
from xml_generator.models import UPDATE_REDIS_SNAPSHOT, check_if_task_queued

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Lokalita)
def save_lokalita_snapshot(sender, instance: Lokalita, **kwargs):
    logger.debug("lokalita.signals.save_lokalita_snapshot.start",
                 extra={"ident_cely": instance.archeologicky_zaznam.ident_cely})
    invalidate_model(Lokalita)
    invalidate_model(ArcheologickyZaznam)
    try:
        instance.set_snapshots()
    except ValueError as err:
        logger.debug("lokalita.signals.save_lokalita_snapshot.type_error",
                     extra={"ident_cely": instance.archeologicky_zaznam.ident_cely, "err": err})
    else:
        logger.debug("lokalita.signals.save_lokalita_snapshot.end",
                     extra={"ident_cely": instance.archeologicky_zaznam.ident_cely})


@receiver(post_save, sender=Lokalita)
def save_lokalita_redis_snapshot(sender, instance: Lokalita, **kwargs):
    logger.debug("lokalita.signals.save_lokalita_redis_snapshot.start",
                 extra={"ident_cely": instance.archeologicky_zaznam.ident_cely})
    if not check_if_task_queued("Lokalita", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["Lokalita", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    logger.debug("lokalita.signals.save_lokalita_redis_snapshot.start",
                 extra={"ident_cely": instance.archeologicky_zaznam.ident_cely})


@receiver(pre_delete, sender=Lokalita)
def delete_lokalita(sender, instance: Lokalita, **kwargs):
    logger.debug("lokalita.signals.delete_lokalita.start",
                 extra={"ident_cely": instance.archeologicky_zaznam.ident_cely})
    invalidate_model(Lokalita)
    invalidate_model(ArcheologickyZaznam)
    logger.debug("lokalita.signals.delete_lokalita.end",
                 extra={"ident_cely": instance.archeologicky_zaznam.ident_cely})