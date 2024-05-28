import logging

from cacheops import invalidate_model
from django.db import transaction

from core.constants import PIAN_RELATION_TYPE
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver

from dj.models import DokumentacniJednotka
from historie.models import HistorieVazby
from pian.models import Pian
from arch_z.models import Akce, ArcheologickyZaznam

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Pian)
def create_pian_vazby(sender, instance, **kwargs):
    """
    Metóda pro vytvoření historických vazeb pianu.
    Metóda se volá pred uložením záznamu.
    """
    logger.debug("pian.signals.create_pian_vazby.start")
    if instance.pk is None:
        hv = HistorieVazby(typ_vazby=PIAN_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        logger.debug("pian.signals.create_pian_vazby.created_history_records")
    logger.debug("pian.signals.create_pian_vazby.end")


@receiver(post_save, sender=Pian)
def pian_save_metadata(sender, instance: Pian, **kwargs):
    """
    Metóda pro vytvoření historických vazeb pianu.
    Metóda se volá pred uložením záznamu.
    """
    logger.debug("pian.signals.pian_save_metadata.start", extra={"instance": instance.ident_cely})
    fedora_transaction = instance.active_transaction
    invalidate_model(Pian)
    invalidate_model(Akce)
    invalidate_model(ArcheologickyZaznam)
    if instance.update_all_azs:
        for dj in instance.dokumentacni_jednotky_pianu.all():
            dj: DokumentacniJednotka
            dj.archeologicky_zaznam.save_metadata(fedora_transaction)
            logger.debug("pian.signals.pian_save_metadata.save_metadata",
                         extra={"transaction": getattr(fedora_transaction, "uid", None)})
    instance.save_metadata(fedora_transaction, close_transaction=instance.close_active_transaction_when_finished)
    logger.debug("pian.signals.pian_save_metadata.end",
                 extra={"instance": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None),
                        "close_transaction": instance.close_active_transaction_when_finished})


@receiver(pre_delete, sender=Pian)
def samostatny_nalez_okres_delete_repository_container(sender, instance: Pian, **kwargs):
    logger.debug("pian.signals.samostatny_nalez_okres_delete_repository_container.start",
                 extra={"instance": instance.ident_cely})
    invalidate_model(Pian)
    invalidate_model(Akce)
    invalidate_model(ArcheologickyZaznam)
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction
        instance.record_deletion(fedora_transaction)
        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: fedora_transaction.mark_transaction_as_closed())
        logger.debug("pian.signals.samostatny_nalez_okres_delete_repository_container.save_metadata",
                     extra={"instance": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)})
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
        logger.debug("pian.signals.samostatny_nalez_okres_delete_repository_container.history_delete",
                     extra={"instance": instance.ident_cely})
    logger.debug("pian.signals.samostatny_nalez_okres_delete_repository_container.start",
                 extra={"instance": instance.ident_cely})
