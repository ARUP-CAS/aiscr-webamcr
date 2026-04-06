import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import Historie

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Historie, weak=False)
def soubor_update_metadata(sender, instance: Historie, **kwargs):
    """
    Před uložením záznamu Historie nastaví snímek organizace podle přiřazeného uživatele.

    :param sender: Třída modelu, která signál vyslala.
    :param instance: Ukládaná instance záznamu Historie.
    :param kwargs: Další parametry signálu.
    """
    logger.debug("historie.signals.soubor_update_metadata.start")
    if instance.uzivatel:
        instance.organizace_snapshot = instance.uzivatel.organizace
    logger.debug("historie.signals.soubor_update_metadata.end")
