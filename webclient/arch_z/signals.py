import logging

from arch_z.models import ArcheologickyZaznam, ExterniZdroj
from core.constants import ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from historie.models import HistorieVazby

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ArcheologickyZaznam)
def create_arch_z_vazby(sender, instance, **kwargs):
    """
        Metóda pro vytvoření historických vazeb arch záznamu.
        Metóda se volá pred uložením arch záznamu.
    """
    if instance.pk is None:
        logger.debug(
            "arch_z.create_arch_z_vazby", extra={"instance": str(instance)})
        hv = HistorieVazby(typ_vazby=ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE)
        hv.save()
        instance.historie = hv

@receiver(post_save, sender=ArcheologickyZaznam)
def create_arch_z_metadata(sender, instance: ArcheologickyZaznam, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    if not instance.suppress_signal:
        instance.save_metadata()


@receiver(post_save, sender=ExterniZdroj)
def create_externi_zdroj_metadata(sender, instance: ExterniZdroj, **kwargs):
    """
        Funkce pro aktualizaci metadat externího odkazu.
    """
    instance.archeologicky_zaznam.save_metadata()
    instance.externi_zdroj.save_metadata()


@receiver(post_delete, sender=ArcheologickyZaznam)
def delete_arch_z_repository_container(sender, instance: ArcheologickyZaznam, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    instance.record_deletion()


@receiver(post_delete, sender=ExterniZdroj)
def delete_externi_zdroj_repository_container(sender, instance: ExterniZdroj, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    instance.record_deletion()
