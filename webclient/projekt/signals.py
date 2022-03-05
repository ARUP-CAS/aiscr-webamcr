from datetime import timedelta
import logging

from core.constants import PROJEKT_RELATION_TYPE
from core.models import SouborVazby
from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import HistorieVazby
from projekt.models import Projekt

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Projekt)
def projekt_pre_save(sender, instance, **kwargs):
    create_projekt_vazby(sender, instance)
    change_termin_odevzdani_NZ(sender, instance)

def change_termin_odevzdani_NZ(sender, instance, **kwargs):
    try:
        instance_db = sender.objects.get(pk = instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if instance.termin_odevzdani_nz == instance_db.termin_odevzdani_nz:
            if instance.datum_ukonceni != instance_db.datum_ukonceni:
                logger.debug("Zmene datum ukonceni a nezmenene termin_odevzdani_NZ - menim automaticky termin_odevzdani_NZ")
                instance.termin_odevzdani_nz = instance.datum_ukonceni
                instance.termin_odevzdani_nz.replace(year=instance.termin_odevzdani_nz.year + 3)

def create_projekt_vazby(sender, instance, **kwargs):
    if instance.pk is None:
        logger.debug("Creating history records for projekt " + str(instance))
        hv = HistorieVazby(typ_vazby=PROJEKT_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        logger.debug(
            "Creating child file for soubory records for project " + str(instance)
        )
        sv = SouborVazby(typ_vazby=PROJEKT_RELATION_TYPE)
        sv.save()
        instance.soubory = sv
