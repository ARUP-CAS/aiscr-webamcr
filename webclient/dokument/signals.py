import logging

from core.constants import DOKUMENT_RELATION_TYPE
from core.models import SouborVazby
from django.db.models.signals import pre_save
from django.dispatch import receiver
from dokument.models import Dokument
from historie.models import HistorieVazby

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Dokument)
def create_dokument_vazby(sender, instance, **kwargs):
    if instance.pk is None:
        logger.debug("Creating history records for dokument " + str(instance))
        hv = HistorieVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        logger.debug("Creating child file and soubory for dokument " + str(instance))
        sv = SouborVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        sv.save()
        instance.soubory = sv
