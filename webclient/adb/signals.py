import logging

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from adb.models import Adb, VyskovyBod

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Adb)
def adb_save_metadata(sender, instance: Adb, **kwargs):
    logger.debug("adb.signals.adb_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    if not instance.suppress_signal:
        transaction = instance.save_metadata()
        instance.dokumentacni_jednotka.archeologicky_zaznam.save_metadata(transaction)
        transaction.mark_transaction_as_closed()
        logger.debug("adb.signals.adb_save_metadata.save_metadata", extra={"ident_cely": instance.ident_cely,
                                                                           "transaction": transaction})
    logger.debug("adb.signals.adb_save_metadata.end", extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=Adb)
def adb_delete_repository_container(sender, instance: Adb, **kwargs):
    logger.debug("adb.signals.adb_delete_repository_container.start", extra={"ident_cely": instance.ident_cely})
    transaction = instance.record_deletion()
    instance.dokumentacni_jednotka.archeologicky_zaznam.save_metadata(transaction)
    transaction.mark_transaction_as_closed()
    logger.debug("adb.signals.adb_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": transaction})


@receiver(pre_delete, sender=VyskovyBod)
def vyskovy_bod_delete_repository_container(sender, instance: VyskovyBod, **kwargs):
    logger.debug("adb.signals.vyskovy_bod_delete_repository_container.start",
                 extra={"ident_cely": instance.ident_cely})
    transaction = instance.adb.save_metadata()
    transaction.mark_transaction_as_closed()
    logger.debug("adb.signals.vyskovy_bod_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": transaction})

