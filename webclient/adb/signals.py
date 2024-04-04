import logging

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from adb.models import Adb, VyskovyBod
from core.repository_connector import FedoraTransaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Adb)
def adb_save_metadata(sender, instance: Adb, **kwargs):
    logger.debug("adb.signals.adb_save_metadata.start",
                 extra={"ident_cely": instance.ident_cely, "suppress_signal": instance.suppress_signal})
    if not instance.suppress_signal:
        fedora_transaction: FedoraTransaction = instance.active_transaction
        if instance.tracker.changed():
            instance.dokumentacni_jednotka.archeologicky_zaznam.save_metadata(fedora_transaction)
            instance.save_metadata(close_transaction=instance.close_active_transaction_when_finished)
        elif instance.close_active_transaction_when_finished:
            fedora_transaction.mark_transaction_as_closed()
        logger.debug("adb.signals.adb_save_metadata.save_metadata", extra={"ident_cely": instance.ident_cely,
                                                                           "transaction": fedora_transaction.uid})
    logger.debug("adb.signals.adb_save_metadata.end", extra={"ident_cely": instance.ident_cely})


@receiver(post_save, sender=VyskovyBod)
def vyskovy_bod_save_metadata(sender, instance: VyskovyBod, **kwargs):
    logger.debug("adb.signals.vyskovy_bod_save_metadata.start",
                 extra={"ident_cely": instance.ident_cely, "suppress_signal": instance.suppress_signal})
    if not instance.suppress_signal and instance.tracker.changed():
        fedora_transaction: FedoraTransaction = instance.active_transaction
        instance.adb.save_metadata(fedora_transaction=fedora_transaction)
        logger.debug("adb.signals.vyskovy_bod_save_metadata.save_metadata",
                     extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction.uid})
    logger.debug("adb.signals.vyskovy_bod_save_metadata.end",
                 extra={"ident_cely": instance.ident_cely, "suppress_signal": instance.suppress_signal})

@receiver(pre_delete, sender=Adb)
def adb_delete_repository_container(sender, instance: Adb, **kwargs):
    logger.debug("adb.signals.adb_delete_repository_container.start", extra={"ident_cely": instance.ident_cely})
    fedora_transaction = instance.active_transaction
    instance.dokumentacni_jednotka.archeologicky_zaznam.save_metadata(fedora_transaction)
    instance.record_deletion(close_transaction=fedora_transaction.close_active_transaction_when_finished)
    logger.debug("adb.signals.adb_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction.uid})


@receiver(pre_delete, sender=VyskovyBod)
def vyskovy_bod_delete_repository_container(sender, instance: VyskovyBod, **kwargs):
    logger.debug("adb.signals.vyskovy_bod_delete_repository_container.start",
                 extra={"ident_cely": instance.ident_cely})
    fedora_transaction = instance.active_transaction
    instance.adb.save_metadata(fedora_transaction, close_transaction=instance.active_close_transaction_when_finished)
    logger.debug("adb.signals.vyskovy_bod_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)})

