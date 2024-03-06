import logging

from core.constants import PIAN_RELATION_TYPE
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver

from dj.models import DokumentacniJednotka
from historie.models import HistorieVazby
from pian.models import Pian

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
    transaction = instance.save_metadata()
    for dj in instance.dokumentacni_jednotky_pianu.all():
        dj: DokumentacniJednotka
        transaction = dj.archeologicky_zaznam.save_metadata(transaction)
        logger.debug("pian.signals.pian_save_metadata.save_metadata", extra={"transaction": transaction})
    logger.debug("pian.signals.pian_save_metadata.end", extra={"instance": instance.ident_cely,
                                                               "transaction": transaction})


@receiver(pre_delete, sender=Pian)
def samostatny_nalez_okres_delete_repository_container(sender, instance: Pian, **kwargs):
    logger.debug("pian.signals.samostatny_nalez_okres_delete_repository_container.start",
                 extra={"instance": instance.ident_cely})
    if not instance.suppress_signal:
        transaction = instance.record_deletion()
        logger.debug("pian.signals.samostatny_nalez_okres_delete_repository_container.save_metadata",
                     extra={"instance": instance.ident_cely, "transaction": transaction})
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
        logger.debug("pian.signals.samostatny_nalez_okres_delete_repository_container.history_delete",
                     extra={"instance": instance.ident_cely})
    logger.debug("pian.signals.samostatny_nalez_okres_delete_repository_container.start",
                 extra={"instance": instance.ident_cely})
