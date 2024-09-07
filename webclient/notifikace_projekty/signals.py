import logging

from django.db import transaction
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from core.repository_connector import FedoraTransaction, FedoraError
from notifikace_projekty.models import Pes


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Pes, weak=False)
def pes_save(sender, instance: Pes, **kwargs):
    if instance.user and not getattr(instance, "suppress_signal", False):
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda: instance.user.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug("notifikace_projekty.signals.pes_save.save_metadata.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(pre_delete, sender=Pes, weak=False)
def pes_delete(sender, instance: Pes, **kwargs):
    if instance.user and not getattr(instance, "suppress_signal", False):
        fedora_transaction = FedoraTransaction()
        try:
            transaction.on_commit(lambda: instance.user.save_metadata(fedora_transaction, close_transaction=True))
        except FedoraError as err:
            # Occurs when record is update via admin interface
            logger.debug("notifikace_projekty.signals.pes_delete.save_metadata.error",
                         extra={"err": err})
        logger.debug("notifikace_projekty.signals.pes_delete.save_metadata.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})

