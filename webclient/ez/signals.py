import logging

from .models import ExterniZdroj
from core.constants import EXTERNI_ZDROJ_RELATION_TYPE
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from historie.models import HistorieVazby

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ExterniZdroj)
def create_ez_vazby(sender, instance: ExterniZdroj, **kwargs):
    """
    Metóda pro vytvoření historických vazeb externího zdroje.
    Metóda se volá pred uložením záznamu.
    """
    logger.debug("ez.signals.create_ez_vazby.start", extra={"ident_cely": instance.ident_cely})
    if instance.pk is None:
        logger.debug("ez.signals.create_ez_vazby", extra={"instance": instance})
        hv = HistorieVazby(typ_vazby=EXTERNI_ZDROJ_RELATION_TYPE)
        hv.save()
        instance.historie = hv
    instance.set_snapshots()
    logger.debug("ez.signals.create_ez_vazby.end", extra={"ident_cely": instance.ident_cely})


@receiver(post_save, sender=ExterniZdroj)
def externi_zdroj_save_metadata(sender, instance: ExterniZdroj, **kwargs):
    logger.debug("ez.signals.externi_zdroj_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    if not instance.suppress_signal:
        instance.save_metadata()
    logger.debug("ez.signals.externi_zdroj_save_metadata.end", extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=ExterniZdroj)
def delete_externi_zdroj_repository_container(sender, instance: ExterniZdroj, **kwargs):
    instance.record_deletion()
    if instance.externi_odkazy_zdroje:
        for eo in instance.externi_odkazy_zdroje.all():
            eo.delete()
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    if instance.soubory and instance.soubory.pk:
        instance.soubory.delete()
