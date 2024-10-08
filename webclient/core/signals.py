import logging

from core.models import Soubor
from core.repository_connector import FedoraTransaction
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from PIL import Image
from pypdf import PdfReader
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Soubor, weak=False)
def soubor_get_rozsah(sender, instance, **kwargs):
    if instance.binary_data:
        if instance.nazev.lower().endswith("pdf"):
            try:
                reader = PdfReader(instance.binary_data)
                instance.rozsah = len(reader.pages)
            except Exception:
                logger.debug("core.models.Soubor.save_error_reading_pdf")
                instance.rozsah = 1
        elif instance.nazev.lower().endswith("tif"):
            try:
                img = Image.open(instance.binary_data)
            except Exception:
                logger.debug("core.models.Soubor.save_error_reading_tif")
                instance.rozsah = 1
            else:
                instance.rozsah = img.n_frames
        else:
            instance.rozsah = 1


@receiver(post_save, sender=Soubor, weak=False)
def soubor_save_update_record_metadata(sender, instance: Soubor, **kwargs):
    logger.debug(
        "cron.signals.soubor_save_update_record_metadata.start",
        extra={"close_active_transaction_when_finished": instance.close_active_transaction_when_finished},
    )
    if not instance.suppress_signal:
        fedora_transaction: FedoraTransaction = instance.active_transaction
        if (
            instance.vazba is not None
            and isinstance(instance.vazba.navazany_objekt, ModelWithMetadata)
            and instance.suppress_signal is False
        ):
            instance.vazba.navazany_objekt.save_metadata(
                fedora_transaction, close_transaction=instance.close_active_transaction_when_finished
            )
            logger.debug(
                "cron.signals.soubor_save_update_record_metadata.save_metadata",
                extra={
                    "transaction": getattr(fedora_transaction, "uid", ""),
                    "navazany_objekt": getattr(instance, "ident_cely", ""),
                },
            )
        elif instance.close_active_transaction_when_finished:
            fedora_transaction.mark_transaction_as_closed()
    logger.debug("cron.signals.soubor_save_update_record_metadata.no_action")


@receiver(pre_delete, sender=Soubor, weak=False)
def soubor_delete_connections(sender, instance: Soubor, **kwargs):
    logger.debug("cron.signals.soubor_delete_connections.start", extra={"instance": instance.pk})
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    logger.debug("cron.signals.soubor_delete_connections.end", extra={"instance": instance.pk})


@receiver(post_delete, sender=Soubor, weak=False)
def soubor_delete_update_metadata(sender, instance: Soubor, **kwargs):
    logger.debug("cron.signals.soubor_delete_update_metadata.start", extra={"instance": instance.pk})
    if instance.suppress_signal is True:
        logger.debug("cron.signals.soubor_delete_update_metadata.suppress_signal", extra={"instance": instance.pk})
        return
    if instance.vazba is not None and isinstance(instance.vazba.navazany_objekt, ModelWithMetadata):
        fedora_transaction = instance.active_transaction
        instance.vazba.navazany_objekt.save_metadata(
            fedora_transaction, close_transaction=instance.close_active_transaction_when_finished
        )
        logger.debug(
            "cron.signals.soubor_delete_update_metadata.save_metadata",
            extra={"transaction": transaction, "navazany_objekt": getattr(instance, "ident_cely", "")},
        )
    logger.debug("cron.signals.soubor_delete_update_metadata.no_action", extra={"instance": instance.pk})
