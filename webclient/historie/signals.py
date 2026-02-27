import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import Historie

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Historie, weak=False)
def soubor_update_metadata(sender, instance: Historie, **kwargs):
    """Provádí operaci soubor update metadata.

    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek provedené operace."""
    logger.debug("historie.signals.soubor_update_metadata.start")
    if instance.uzivatel:
        instance.organizace_snapshot = instance.uzivatel.organizace
    logger.debug("historie.signals.soubor_update_metadata.end")
