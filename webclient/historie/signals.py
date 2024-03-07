import logging

from historie.models import Historie
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from cron.tasks import update_cached_queryset

from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Historie)
def soubor_update_metadata(sender, instance: Historie, **kwargs):
    logger.debug("historie.signals.soubor_update_metadata.start")
    if instance.uzivatel:
        instance.organizace_snapshot = instance.uzivatel.organizace
    logger.debug("historie.signals.soubor_update_metadata.end")
