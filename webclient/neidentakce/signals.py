import logging

from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from core.repository_connector import FedoraTransaction
from neidentakce.models import NeidentAkce


logger = logging.getLogger(__name__)


@receiver(post_save, sender=NeidentAkce)
def neident_akce_post_save(sender, instance: NeidentAkce, **kwargs):
    if instance.dokument_cast and instance.dokument_cast.dokument and not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda:
                              instance.initial_dokument.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug("neidentakce.signals.neident_akce_post_save.save_metadata.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_delete, sender=NeidentAkce)
def neident_akce_post_delete(sender, instance: NeidentAkce, **kwargs):
    if instance.dokument_cast and instance.dokument_cast.dokument and not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda:
                              instance.initial_dokument.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug("neidentakce.signals.neident_akce_post_delete.save_metadata.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})
