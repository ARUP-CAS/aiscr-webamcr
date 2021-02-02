import logging

from core.constants import PROJEKT_RELATION_TYPE
from core.models import SouborVazby
from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import HistorieVazby
from projekt.models import Projekt

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Projekt)
def create_projekt_vazby(sender, instance, **kwargs):
    if instance.pk is None:
        logger.debug(
            "Creating history records for archaeological record " + str(instance)
        )
        hv = HistorieVazby(typ_vazby=PROJEKT_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        logger.debug(
            "Creating child file and history records for project " + str(instance)
        )
        sv = SouborVazby(typ_vazby=PROJEKT_RELATION_TYPE)
        sv.save()
        instance.soubory = sv
