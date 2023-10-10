import logging
import sys

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from komponenta.models import KomponentaVazby, Komponenta

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Komponenta)
def delete_komponenta_vazby(sender, instance, **kwargs):
    """
    Náhrada triggeru delete_connected_komponenta_vazby_relations.
    """
    logger.debug("komponenta.signals.delete_komponenta_vazby.start")
    try:
        KomponentaVazby.objects.filter(komponenty=instance).delete()
    except RecursionError:
        # https://www.appsloveworld.com/django/100/13/django-cascade-delete-on-reverse-foreign-keys
        pass
    logger.debug("komponenta.signals.delete_komponenta_vazby.end")
