import logging

from arch_z.signals import invalidate_arch_z_related_models
from core.constants import PIAN_RELATION_TYPE
from dj.models import DokumentacniJednotka
from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from historie.models import HistorieVazby
from pian.models import Pian

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Pian, weak=False)
def create_pian_vazby(sender, instance, **kwargs):
    """
    Metoda pro vytvoření historických vazeb pianu.

    Metoda se volá pred uložením záznamu.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_pian_vazby``.
    :param instance: Parametr ``instance`` pracuje se s atributy ``pk``, ``historie``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_pian_vazby``.
    """
    logger.debug("pian.signals.create_pian_vazby.start")
    if instance.pk is None:
        hv = HistorieVazby(typ_vazby=PIAN_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        logger.debug("pian.signals.create_pian_vazby.created_history_records")
    logger.debug("pian.signals.create_pian_vazby.end")


@receiver(post_save, sender=Pian, weak=False)
def pian_save_metadata(sender, instance: Pian, **kwargs):
    """
    Metoda pro vytvoření historických vazeb pianu.

    Metoda se volá pred uložením záznamu.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``pian_save_metadata``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``save_metadata()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``pian_save_metadata``.
    """
    logger.debug("pian.signals.pian_save_metadata.start", extra={"instance": instance.ident_cely})
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction
        invalidate_arch_z_related_models()
        if instance.update_all_azs:
            for dj in instance.dokumentacni_jednotky_pianu.all():
                dj: DokumentacniJednotka
                dj.archeologicky_zaznam.save_metadata(fedora_transaction)
                logger.debug(
                    "pian.signals.pian_save_metadata.save_metadata",
                    extra={"transaction": getattr(fedora_transaction, "uid", None)},
                )
        instance.save_metadata(fedora_transaction, close_transaction=instance.close_active_transaction_when_finished)
        logger.debug(
            "pian.signals.pian_save_metadata.end",
            extra={
                "instance": instance.ident_cely,
                "transaction": getattr(fedora_transaction, "uid", None),
                "close_transaction": instance.close_active_transaction_when_finished,
            },
        )


@receiver(pre_delete, sender=Pian, weak=False)
def samostatny_nalez_okres_delete_repository_container(sender, instance: Pian, **kwargs):
    """
    Provádí operaci samostatny nalez okres delete repository container.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``samostatny_nalez_okres_delete_repository_container``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``samostatny_nalez_okres_delete_repository_container``.
    """
    logger.debug(
        "pian.signals.samostatny_nalez_okres_delete_repository_container.start", extra={"instance": instance.ident_cely}
    )
    invalidate_arch_z_related_models()
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction
        instance.record_deletion(fedora_transaction)
        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: fedora_transaction.mark_transaction_as_closed())
        logger.debug(
            "pian.signals.samostatny_nalez_okres_delete_repository_container.save_metadata",
            extra={"instance": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)},
        )
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
        logger.debug(
            "pian.signals.samostatny_nalez_okres_delete_repository_container.history_delete",
            extra={"instance": instance.ident_cely},
        )
    logger.debug(
        "pian.signals.samostatny_nalez_okres_delete_repository_container.start", extra={"instance": instance.ident_cely}
    )
