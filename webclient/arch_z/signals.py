import logging

from django.db.models import Q

from arch_z.models import ArcheologickyZaznam, ExterniOdkaz
from core.constants import ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver

from dokument.models import DokumentCast, Dokument
from historie.models import HistorieVazby, Historie

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
def delete_arch_z_connected_documents(sender, instance: ArcheologickyZaznam, **kwargs):
    """
        Trigger delete_connected_documents
    """
    logger.debug("arch_z.signals.delete_arch_z_repository_container.start", extra={"arch_z": instance.ident_cely})
    dokument_query = instance.casti_dokumentu.filter(~Q(dokument__ident_cely__startswith="X-"))
    if hasattr(instance, "deleted_by_user") and instance.deleted_by_user is not None:
        deleted_by_user = instance.deleted_by_user
    else:
        deleted_by_user = None
    for item in dokument_query:
        delete_dokument = True
        item: Dokument
        dokument_cast_query = DokumentCast.objects.filter(archeologicky_zaznam=instance).filter(dokument=item)
        for inner_item in dokument_cast_query:
            inner_item: DokumentCast
            if inner_item.filter(dokument=item).filter(~Q(archeologicky_zaznam=instance)).exists():
                delete_dokument = False
        if delete_dokument:
            item.deleted_by_user = deleted_by_user
            item.delete()
            logger.debug("arch_z.signals.delete_arch_z_repository_container.cast_dokumentu.delete.part_2",
                         extra={"arch_z": item.ident_cely})
        else:
            logger.debug("arch_z.signals.delete_arch_z_repository_container.cast_dokumentu.not_delete.part_2",
                         extra={"arch_z": item.ident_cely})

    for item in instance.casti_dokumentu.all():
        item: DokumentCast
        if item.komponenty.komponenty.exists():
            continue
        if item.neident_akce.exists():
            continue
        item.delete()
        logger.debug("arch_z.signals.delete_arch_z_repository_container.cast_dokumentu.delete.part_1",
                     extra={"arch_z": item.ident_cely})
    logger.debug("arch_z.signals.delete_arch_z_repository_container.end", extra={"arch_z": instance.ident_cely})


@receiver(pre_delete, sender=ArcheologickyZaznam)
def delete_arch_z_repository_container(sender, instance: ArcheologickyZaznam, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    instance.record_deletion()
    if instance.akce.projekt is not None:
        instance.akce.projekt.save_metadata()


@receiver(post_delete, sender=ExterniOdkaz)
def delete_externi_odkaz_repository_container(sender, instance: ExterniOdkaz, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    if instance.archeologicky_zaznam is not None:
        instance.archeologicky_zaznam.save_metadata()
    if instance.externi_zdroj is not None:
        instance.externi_zdroj.save_metadata()
