import logging

from core.constants import PIAN_RELATION_TYPE
from django.db.models.signals import post_save, pre_save
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
    if instance.pk is None:
        logger.debug("Creating history records for Pian " + str(instance))
        hv = HistorieVazby(typ_vazby=PIAN_RELATION_TYPE)
        hv.save()
        instance.historie = hv


@receiver(post_save, sender=Pian)
def pian_save_metadata(sender, instance: Pian, **kwargs):
    """
    Metóda pro vytvoření historických vazeb pianu.
    Metóda se volá pred uložením záznamu.
    """
    instance.save_metadata()
    for dj in instance.dokumentacni_jednotky_pianu:
        dj: DokumentacniJednotka
        dj.archeologicky_zaznam.save_metadata()
