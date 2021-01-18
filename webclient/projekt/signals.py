import logging

from core.constants import PROJEKT_RELATION_TYPE
from core.models import SouborVazby
from django.db.models.signals import post_save
from django.dispatch import receiver
from historie.models import HistorieVazby
from projekt.models import Projekt

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Projekt)
def create_projekt_vazby(sender, instance, created, **kwargs):
    logger.debug("Running create_projekt_vazby receiver ...")
    if created:
        logger.debug("Creating child file and history records")
        sv = SouborVazby(typ_vazby=PROJEKT_RELATION_TYPE)
        sv.save()
        instance.soubory = sv
        hv = HistorieVazby(typ_vazby=PROJEKT_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        instance.save()
