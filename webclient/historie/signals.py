import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import Historie

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Historie, weak=False)
def soubor_update_metadata(sender, instance: Historie, **kwargs):
    """
    Provádí operaci soubor update metadata.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``soubor_update_metadata``.
    :param instance: Parametr ``instance`` pracuje se s atributy ``uzivatel``, ``organizace_snapshot``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``soubor_update_metadata``.
    """
    logger.debug("historie.signals.soubor_update_metadata.start")
    if instance.uzivatel:
        instance.organizace_snapshot = instance.uzivatel.organizace
    logger.debug("historie.signals.soubor_update_metadata.end")
