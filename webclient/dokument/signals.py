import logging

from core.constants import DOKUMENT_RELATION_TYPE
from core.models import SouborVazby
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from dokument.models import Dokument, DokumentAutor
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


@receiver(post_save, sender=DokumentAutor)
def create_main_autor(sender, instance, **kwargs):
    if instance.poradi == 1:
        dokument = instance.dokument
        dokument.main_autor = instance.autor.prijmeni
        dokument.save()
