import logging

from .models import ExterniZdroj
from core.constants import EXTERNI_ZDROJ_RELATION_TYPE
from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import HistorieVazby

logger = logging.getLogger('python-logstash-logger')


@receiver(pre_save, sender=ExterniZdroj)
def create_ez_vazby(sender, instance, **kwargs):
    if instance.pk is None:
        logger.debug("ez.signals.create_ez_vazby", extra={"instance": instance})
        hv = HistorieVazby(typ_vazby=EXTERNI_ZDROJ_RELATION_TYPE)
        hv.save()
        instance.historie = hv
