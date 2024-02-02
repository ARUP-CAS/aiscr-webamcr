import logging

from historie.models import Historie
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Historie)
def soubor_update_metadata(sender, instance: Historie, **kwargs):
    """
    Funkce pro uložení metadat k objektům navázaným na soubor
    """
    logger.debug("historie.signals.soubor_update_metadata.start", extra={"pk": instance.pk})
    if (not hasattr(instance, "suppress_signal") or instance.suppress_signal is False) and (
            hasattr(instance.vazba.navazany_objekt, "suppress_signall")
            or instance.vazba.navazany_objekt.suppress_signal is False):
        navazany_objekt = instance.vazba.navazany_objekt
        if isinstance(navazany_objekt, ModelWithMetadata):
            transaction = navazany_objekt.save_metadata()
            transaction.mark_transaction_as_closed()
            logger.debug("historie.signals.soubor_update_metadata.save_metadata",
                         extra={"pk": instance.pk, "transaction": transaction})
    logger.debug("historie.signals.soubor_update_metadata.end", extra={"pk": instance.pk})


@receiver(pre_save, sender=Historie)
def soubor_update_metadata(sender, instance: Historie, **kwargs):
    logger.debug("historie.signals.soubor_update_metadata.start")
    if instance.uzivatel:
        instance.organizace_snapshot = instance.uzivatel.organizace
    logger.debug("historie.signals.soubor_update_metadata.end")
