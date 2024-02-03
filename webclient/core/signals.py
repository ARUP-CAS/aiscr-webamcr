import logging

from core.models import Soubor
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from historie.models import Historie
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Soubor)
def soubor_save_update_record_metadata(sender, instance: Soubor, **kwargs):
    logger.debug("cron.signals.soubor_save_update_record_metadata.start")
    if instance.vazba is not None and isinstance(instance.vazba.navazany_objekt, ModelWithMetadata) \
            and instance.suppress_signal is False:
        transaction = instance.vazba.navazany_objekt.save_metadata()
        if transaction:
            transaction.mark_transaction_as_closed()
        logger.debug("cron.signals.soubor_save_update_record_metadata.save_metadata",
                     extra={"transaction": transaction, "navazany_objekt": instance.ident_cely})
    logger.debug("cron.signals.soubor_save_update_record_metadata.no_action")


@receiver(pre_delete, sender=Soubor)
def soubor_delete_connections(sender, instance: Soubor, **kwargs):
    logger.debug("cron.signals.soubor_delete_connections.start", extra={"instance": instance.pk})
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    logger.debug("cron.signals.soubor_delete_connections.end", extra={"instance": instance.pk})


@receiver(post_delete, sender=Soubor)
def soubor_delete_update_metadata(sender, instance: Soubor, **kwargs):
    logger.debug("cron.signals.soubor_delete_update_metadata.start", extra={"instance": instance.pk})
    if instance.vazba is not None and isinstance(instance.vazba.navazany_objekt, ModelWithMetadata) \
            and instance.suppress_signal is False:
        transaction = instance.vazba.navazany_objekt.save_metadata()
        if transaction:
            transaction.mark_transaction_as_closed()
        logger.debug("cron.signals.soubor_delete_update_metadata.save_metadata",
                     extra={"transaction": transaction,  "navazany_objekt": instance.ident_cely})
    logger.debug("cron.signals.soubor_delete_update_metadata.no_action", extra={"instance": instance.pk})
