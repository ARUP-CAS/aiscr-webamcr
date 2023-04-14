import logging

from arch_z.models import ArcheologickyZaznam
from core.constants import ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE
from django.db.models.signals import pre_save
from django.dispatch import receiver
from historie.models import HistorieVazby

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ArcheologickyZaznam)
def create_arch_z_vazby(sender, instance, **kwargs):
    """
        Metóda pro vytvoření historických vazeb arch záznamu.
        metóda se volá pred uložením arch záznamu.
    """
    if instance.pk is None:
        logger.debug(
            "Creating history records for archaeological record " + str(instance)
        )
        hv = HistorieVazby(typ_vazby=ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE)
        hv.save()
        instance.historie = hv
