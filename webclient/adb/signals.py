import logging

from cacheops import invalidate_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from adb.models import Adb, VyskovyBod
from arch_z.models import ArcheologickyZaznam, Akce
from arch_z.signals import invalidate_arch_z_related_models
from core.repository_connector import FedoraTransaction
from historie.models import Historie

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Adb)
def adb_save_metadata(sender, instance: Adb, created, **kwargs):
    logger.debug("adb.signals.adb_save_metadata.start",
                 extra={"ident_cely": instance.ident_cely, "suppress_signal": instance.suppress_signal})
    invalidate_arch_z_related_models()
    if not instance.suppress_signal:
        fedora_transaction: FedoraTransaction = instance.active_transaction
        if instance.tracker.changed():
            if created:
                instance.dokumentacni_jednotka.archeologicky_zaznam.save_metadata(fedora_transaction)
            instance.save_metadata()
        if instance.close_active_transaction_when_finished:
            fedora_transaction.mark_transaction_as_closed()
        logger.debug("adb.signals.adb_save_metadata.save_metadata", extra={"ident_cely": instance.ident_cely,
                                                                           "transaction": fedora_transaction.uid})
    logger.debug("adb.signals.adb_save_metadata.end", extra={"ident_cely": instance.ident_cely})


@receiver(post_save, sender=VyskovyBod)
def vyskovy_bod_save_metadata(sender, instance: VyskovyBod, **kwargs):
    logger.debug("adb.signals.vyskovy_bod_save_metadata.start",
                 extra={"ident_cely": instance.ident_cely, "suppress_signal": instance.suppress_signal})
    invalidate_arch_z_related_models()
    if not instance.suppress_signal and instance.tracker.changed():
        fedora_transaction: FedoraTransaction = instance.active_transaction
        instance.adb.save_metadata(fedora_transaction=fedora_transaction)
        logger.debug("adb.signals.vyskovy_bod_save_metadata.save_metadata",
                     extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction.uid})
    logger.debug("adb.signals.vyskovy_bod_save_metadata.end",
                 extra={"ident_cely": instance.ident_cely, "suppress_signal": instance.suppress_signal})


@receiver(post_delete, sender=Adb)
def adb_delete_repository_container(sender, instance: Adb, **kwargs):
    logger.debug("adb.signals.adb_delete_repository_container.start", extra={"ident_cely": instance.ident_cely})
    invalidate_arch_z_related_models()
    fedora_transaction = instance.active_transaction
    if instance.close_active_transaction_when_finished:
        def save_metadata():
            try:
                instance.initial_dokumentacni_jednotka.archeologicky_zaznam.save_metadata(fedora_transaction)
            except ObjectDoesNotExist as err:
                logger.debug("adb.signals.adb_delete_repository_container.not_exists",
                             extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction.uid,
                                    "err": err})
            instance.record_deletion(fedora_transaction, close_transaction=True)
        transaction.on_commit(save_metadata)
    else:
        instance.initial_dokumentacni_jednotka.archeologicky_zaznam.save_metadata(fedora_transaction)
        instance.record_deletion(fedora_transaction)
    logger.debug("adb.signals.adb_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction.uid})


@receiver(post_delete, sender=VyskovyBod)
def vyskovy_bod_delete_repository_container(sender, instance: VyskovyBod, **kwargs):
    logger.debug("adb.signals.vyskovy_bod_delete_repository_container.start",
                 extra={"ident_cely": instance.ident_cely})
    fedora_transaction = instance.active_transaction
    invalidate_arch_z_related_models()
    if instance.close_active_transaction_when_finished:
        transaction.on_commit(lambda: instance.adb.save_metadata(fedora_transaction, close_transaction=True))
    else:
        instance.adb.save_metadata(fedora_transaction)
    logger.debug("adb.signals.vyskovy_bod_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)})

