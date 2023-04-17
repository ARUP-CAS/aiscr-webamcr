import logging

from core.constants import PIAN_RELATION_TYPE
from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import HistorieVazby
from pian.models import Pian

logger = logging.getLogger('python-logstash-logger')


@receiver(pre_save, sender=Pian)
def create_pian_vazby(sender, instance, **kwargs):
    if instance.pk is None:
        logger.debug("Creating history records for Pian " + str(instance))
        hv = HistorieVazby(typ_vazby=PIAN_RELATION_TYPE)
        hv.save()
        instance.historie = hv
