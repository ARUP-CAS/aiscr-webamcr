import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import Historie

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Historie, weak=False)
def soubor_update_metadata(sender, instance: Historie, **kwargs):
    """
    Provádí operaci soubor update metadata.

    :param sender: Třída modelu, která signal vyvolala.
    :param instance: Instance modelu, které se operace týká.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    """
    logger.debug("historie.signals.soubor_update_metadata.start")
    if instance.uzivatel:
        instance.organizace_snapshot = instance.uzivatel.organizace
    logger.debug("historie.signals.soubor_update_metadata.end")
