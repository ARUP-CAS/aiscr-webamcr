import logging

from cron.tasks import update_single_redis_snapshot
from django.db.models.signals import post_save
from django.dispatch import receiver

from lokalita.models import Lokalita
from xml_generator.models import UPDATE_REDIS_SNAPSHOT, check_if_task_queued

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Lokalita)
def save_lokalita_snapshot(sender, instance: Lokalita, **kwargs):
    logger.debug("lokalita.signals.save_lokalita_snapshot.start",
                 extra={"ident_cely": instance.archeologicky_zaznam.ident_cely})
    instance.set_snapshots()
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
