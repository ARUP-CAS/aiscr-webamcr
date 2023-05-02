import logging

from core.constants import SAMOSTATNY_NALEZ_RELATION_TYPE
from core.models import SouborVazby
from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import HistorieVazby
from pas.models import SamostatnyNalez

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=SamostatnyNalez)
def create_dokument_vazby(sender, instance, **kwargs):
    """
    Metóda pro vytvoření historických a souborových vazeb samostatnýho náleze.
    Metóda se volá pred uložením záznamu.
    """
    if instance.pk is None:
        logger.debug("Creating history records for SN " + str(instance))
        hv = HistorieVazby(typ_vazby=SAMOSTATNY_NALEZ_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        logger.debug("Creating child file and soubory for SN " + str(instance))
        sv = SouborVazby(typ_vazby=SAMOSTATNY_NALEZ_RELATION_TYPE)
        sv.save()
        instance.soubory = sv
