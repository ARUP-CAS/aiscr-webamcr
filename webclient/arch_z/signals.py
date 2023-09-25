import logging

from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
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
    if instance.initial_pristupnost is not None and instance.pristupnost.id != instance.initial_pristupnost.id:
        for dok_jednotka in instance.dokumentacni_jednotky_akce.all():
            initial_pristupnost \
                = dok_jednotka.pian.evaluate_pristupnost_change(instance.initial_pristupnost.id, instance.id)
            pristupnost = dok_jednotka.pian.evaluate_pristupnost_change(instance.pristupnost.id, instance.id)
            if initial_pristupnost.id != pristupnost.id:
                dok_jednotka.pian.save_metadata()


@receiver(post_save, sender=ExterniOdkaz)
def create_externi_odkaz_metadata(sender, instance: ExterniOdkaz, **kwargs):
    """
        Funkce pro aktualizaci metadat externího odkazu.
    """
    if instance.archeologicky_zaznam is not None:
        instance.archeologicky_zaznam.save_metadata()
    if instance.externi_zdroj is not None:
        instance.externi_zdroj.save_metadata()


@receiver(post_delete, sender=ArcheologickyZaznam)
def delete_arch_z_repository_container(sender, instance: ArcheologickyZaznam, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    instance.record_deletion()


@receiver(post_delete, sender=ExterniOdkaz)
def delete_externi_odkaz_repository_container(sender, instance: ExterniOdkaz, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    if instance.archeologicky_zaznam is not None:
        instance.archeologicky_zaznam.save_metadata()
    if instance.externi_zdroj is not None:
        instance.externi_zdroj.save_metadata()
