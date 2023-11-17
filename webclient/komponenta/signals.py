import logging
import sys

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from komponenta.models import KomponentaVazby, Komponenta

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=KomponentaVazby)
def delete_komponenta_vazby(sender, instance: KomponentaVazby, **kwargs):
    """
    Náhrada triggeru delete_connected_komponenta_vazby_relations.
    """
    logger.debug("komponenta.signals.delete_komponenta_vazby.start")
    try:
        Komponenta.objects.filter(komponenta_vazby=instance).delete()
    except RecursionError:
        # https://www.appsloveworld.com/django/100/13/django-cascade-delete-on-reverse-foreign-keys
        pass
    logger.debug("komponenta.signals.delete_komponenta_vazby.end")
