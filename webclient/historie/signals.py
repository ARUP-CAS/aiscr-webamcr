import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import Historie

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Historie, weak=False)
def soubor_update_metadata(sender, instance: Historie, **kwargs):
    """Funkce `soubor_update_metadata` v modulu `webclient.historie.signals`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param sender: Vstupní hodnota používaná při zpracování.
    :param instance: Vstupní hodnota používaná při zpracování.
    :param kwargs: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    logger.debug("historie.signals.soubor_update_metadata.start")
    if instance.uzivatel:
        instance.organizace_snapshot = instance.uzivatel.organizace
    logger.debug("historie.signals.soubor_update_metadata.end")
