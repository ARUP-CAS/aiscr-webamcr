import logging

from arch_z.models import ArcheologickyZaznam
from core.constants import DOKUMENT_CAST_RELATION_TYPE, DOKUMENT_RELATION_TYPE
from core.models import SouborVazby
from core.repository_connector import FedoraTransaction
from cron.tasks import update_single_redis_snapshot
from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from dokument.models import Dokument, DokumentCast, Let, Tvar
from historie.models import HistorieVazby
from komponenta.models import KomponentaVazby, Komponenta
from xml_generator.models import check_if_task_queued, UPDATE_REDIS_SNAPSHOT

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Dokument)
def create_dokument_vazby(sender, instance: Dokument, **kwargs):
    """
    Metóda pro vytvoření historických vazeb dokumentu.
    Metóda se volá pred uložením záznamu.
    """
    fedora_transaction = instance.active_transaction
    logger.debug("dokument.signals.create_dokument_vazby.start",
                 extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid")})
    if instance.pk is None:
        logger.debug("dokument.signals.create_dokument_vazby.creating_history_for_dokument.create_history",
                     extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid")})
        hv = HistorieVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        sv = SouborVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        sv.save()
        instance.soubory = sv
        if instance.let is not None:
            fedora_transaction = instance.let.save_metadata(fedora_transaction)
    else:
        old_instance = Dokument.objects.get(pk=instance.pk)
        if not instance.suppress_signal:
            if old_instance.let is None and instance.let is not None:
                fedora_transaction = instance.let.save_metadata(fedora_transaction)
            elif old_instance.let is not None and instance.let is None:
                fedora_transaction = old_instance.let.save_metadata(fedora_transaction)
            elif old_instance.let is not None and instance.let is not None and old_instance.let != instance.let:
                fedora_transaction = old_instance.let.save_metadata(fedora_transaction)
                instance.let.save_metadata(fedora_transaction)
    try:
        instance.set_snapshots()
    except ValueError as err:
        logger.debug("dokument.signals.create_dokument_vazby.type_error",
                     extra={"pk": instance.pk, "err": err, "transaction": getattr(fedora_transaction, "uid")})
    logger.debug("dokument.signals.create_dokument_vazby.end",
                 extra={"ident_cely": instance.ident_cely,"transaction": getattr(fedora_transaction, "uid")})


@receiver(pre_save, sender=DokumentCast)
def create_dokument_cast_vazby(sender, instance: DokumentCast, **kwargs):
    """
    Metóda pro vytvoření komponent vazeb dokument části.
    Metóda se volá pred uložením dokument části.
    """
    logger.debug("dokument.signals.create_dokument_cast_vazby.start", extra={"record_pk": instance.pk})
    if instance.pk is None:
        logger.debug("Creating child komponenty for dokument cast" + str(instance))
        k = KomponentaVazby(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
        k.save()
        instance.komponenty = k
    logger.debug("dokument.signals.create_dokument_cast_vazby.end", extra={"record_pk": instance.pk})


@receiver(post_save, sender=Dokument)
def dokument_save_metadata(sender, instance: Dokument, **kwargs):
    logger.debug("dokument.signals.dokument_save_metadata.startdokument.signals.dokument_save_metadata.start",
                 extra={"ident_cely": instance.ident_cely, "record_pk": instance.pk,
                        "close_active_transaction_when_finished": instance.close_active_transaction_when_finished})
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction
        close_transaction = instance.close_active_transaction_when_finished
        if close_transaction:
            transaction.on_commit(lambda:
                                  instance.save_metadata(fedora_transaction, close_transaction=close_transaction))
        else:
            instance.save_metadata(fedora_transaction)
        logger.debug("dokument.signals.dokument_save_metadata.done",
                     extra={"transaction": getattr(instance.active_transaction, "uid")})
    if not check_if_task_queued("Dokument", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["Dokument", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    logger.debug("dokument.signals.dokument_save_metadata.end", extra={"ident_cely": instance.ident_cely,
                                                                       "record_pk": instance.pk})


@receiver(post_save, sender=Let)
def let_save_metadata(sender, instance: Let, **kwargs):
    logger.debug("dokument.signals.let_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction
        instance.save_metadata(fedora_transaction)
        logger.debug("dokument.signals.let_save_metadata.save_metadata",
                     extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid")})
    logger.debug("dokument.signals.let_save_metadata.no_action", extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=Dokument)
def dokument_delete_repository_container(sender, instance: Dokument, **kwargs):
    logger.debug("dokument.signals.dokument_delete_repository_container.start",
                 extra={"ident_cely": instance.ident_cely})
    fedora_transaction = instance.record_deletion()
    for item in instance.casti.all():
        item: DokumentCast
        if item.archeologicky_zaznam is not None:
            item.archeologicky_zaznam.save_metadata()
        if item.projekt is not None:
            item.projekt.save_metadata(fedora_transaction)
    if instance.let:
        fedora_transaction = instance.let.save_metadata(fedora_transaction)
    for k in Komponenta.objects.filter(ident_cely__startswith=instance.ident_cely):
        logger.debug("dokument.signals.dokument_delete_repository_container.deleting",
                     extra={"ident_cely": k.ident_cely, "transaction": getattr(fedora_transaction, "uid")})
        k: Komponenta
        k.delete()
        k.komponenta_vazby.delete()
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    if instance.soubory and instance.soubory.pk:
        instance.soubory.delete()
    if fedora_transaction and instance.close_active_transaction_when_finished:
        fedora_transaction.mark_transaction_as_closed()
    logger.debug("dokument.signals.dokument_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid")})


@receiver(pre_delete, sender=Let)
def let_delete_repository_container(sender, instance: Let, **kwargs):
    logger.debug("dokument.signals.let_delete_repository_container.start",
                 extra={"ident_cely": instance.ident_cely})
    fedora_transaction = instance.active_transaction
    instance.record_deletion(fedora_transaction, close_transaction=instance.close_active_transaction_when_finished)
    logger.debug("dokument.signals.let_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid")})


@receiver(post_save, sender=DokumentCast)
def dokument_cast_save_metadata(sender, instance: DokumentCast, created, **kwargs):
    extra = {"dokument_cast": instance.pk, "signal_created": created}
    logger.debug("dokument.signals.dokument_cast_save_metadata.start", extra=extra)
    from core.repository_connector import FedoraTransaction
    fedora_transaction: FedoraTransaction = instance.active_transaction
    if (created or instance.initial_projekt != instance.projekt or
            instance.initial_archeologicky_zaznam != instance.archeologicky_zaznam):
        instance.dokument.save_metadata(fedora_transaction)
        extra["transaction"] = str(fedora_transaction.uid)
        if instance.archeologicky_zaznam is not None:
            instance.archeologicky_zaznam.save_metadata(fedora_transaction)
            extra.update({"archeologicky_zaznam": instance.archeologicky_zaznam.ident_cely,
                          "record_pk": instance.archeologicky_zaznam.pk})
        if instance.initial_archeologicky_zaznam is not None:
            instance.initial_archeologicky_zaznam.save_metadata(fedora_transaction)
            extra.update({"initial_archeologicky_zaznam": instance.initial_archeologicky_zaznam.ident_cely,
                          "initial_record_pk": instance.initial_archeologicky_zaznam.pk})
        if instance.projekt is not None:
            instance.projekt.save_metadata(fedora_transaction)
            extra.update({"projekt": instance.projekt.ident_cely, "record_pk": instance.projekt.pk})
        if instance.initial_projekt is not None:
            instance.initial_projekt.save_metadata(fedora_transaction)
            extra.update({"initial_projekt": instance.initial_projekt.ident_cely,
                          "initial_record_pk": instance.initial_projekt.pk})
        logger.debug("dokument.signals.dokument_cast_save_metadata.changed", extra=extra)
    else:
        logger.debug("dokument.signals.dokument_cast_save_metadata.no_change", extra=extra)
    if fedora_transaction and instance.close_active_transaction_when_finished:
        fedora_transaction.mark_transaction_as_closed()
    logger.debug("dokument.signals.dokument_cast_save_metadata.end", extra=extra)


@receiver(post_delete, sender=DokumentCast)
def dokument_cast_save_metadata(sender, instance: DokumentCast, **kwargs):
    logger.debug("dokument.signals.dokument_cast_save_metadata.start", extra={"pk": instance.pk})
    fedora_transaction: FedoraTransaction = instance.active_transaction
    if instance.initial_archeologicky_zaznam is not None:
        instance.initial_archeologicky_zaznam.save_metadata(fedora_transaction)
    if instance.initial_projekt is not None:
        instance.initial_projekt.save_metadata(fedora_transaction)
    if instance.close_active_transaction_when_finished:
        fedora_transaction.mark_transaction_as_closed()
    logger.debug("dokument.signals.dokument_cast_save_metadata.end", extra={"pk": instance.pk,
                                                                            "transaction": fedora_transaction})


@receiver(post_save, sender=Tvar)
def tvar_save(sender, instance: Tvar, created, **kwargs):
    logger.debug("dokument.signals.tvar_save.start", extra={"pk": instance.pk})
    if instance.dokument:
        fedora_transaction = instance.active_transaction
        instance.dokument.save_metadata(fedora_transaction,
                                        close_transaction=instance.close_active_transaction_when_finished)
    logger.debug("dokument.signals.tvar_save.end", extra={"pk": instance.pk, "transaction": transaction})


@receiver(pre_delete, sender=Tvar)
def tvar_delete(sender, instance: Tvar, **kwargs):
    logger.debug("dokument.signals.tvar_delete.start", extra={"pk": instance.pk})
    if instance.dokument:
        fedora_transaction = instance.active_transaction
        instance.dokument.save_metadata(fedora_transaction,
                                        close_transaction=instance.close_active_transaction_when_finished)
    logger.debug("dokument.signals.tvar_delete.end", extra={"pk": instance.pk, "transaction": transaction})
