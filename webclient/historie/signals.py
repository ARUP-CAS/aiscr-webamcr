import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import Historie

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Historie, weak=False)
def soubor_update_metadata(sender, instance: Historie, **kwargs):
    """Zajišťuje logiku funkce ``soubor_update_metadata``.
    
    :param sender: Vstupní hodnota parametru ``sender`` použitého při zpracování.
    :param instance: Vstupní hodnota parametru ``instance`` použitého při zpracování. (typ: ``Historie``).
    :param kwargs: Pojmenované argumenty předané voláním.
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    logger.debug("historie.signals.soubor_update_metadata.start")
    if instance.uzivatel:
        instance.organizace_snapshot = instance.uzivatel.organizace
    logger.debug("historie.signals.soubor_update_metadata.end")
