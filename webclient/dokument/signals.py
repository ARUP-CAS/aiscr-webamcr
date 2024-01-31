import logging

from arch_z.models import ArcheologickyZaznam
from core.constants import DOKUMENT_CAST_RELATION_TYPE, DOKUMENT_RELATION_TYPE
from core.models import SouborVazby
from cron.tasks import update_single_redis_snapshot
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from dokument.models import Dokument, DokumentAutor, DokumentCast, Let, Tvar
from historie.models import HistorieVazby
from komponenta.models import KomponentaVazby, Komponenta
from xml_generator.models import check_if_task_queued, UPDATE_REDIS_SNAPSHOT

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Dokument)
def create_dokument_vazby(sender, instance: Dokument, **kwargs):
    """
    Metóda pro vytvoření historických vazeb dokumentu.
    Metóda se volá pred uložením záznamu.
    """
    logger.debug("dokument.signals.create_dokument_vazby.start", extra={"ident_cely": instance.ident_cely})
    if instance.pk is None:
        logger.debug("dokument.signals.create_dokument_vazby.creating_history_for_dokument.create_history",
                     extra={"ident_cely": instance.ident_cely})
        hv = HistorieVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        sv = SouborVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        sv.save()
        instance.soubory = sv
        if instance.let is not None:
            instance.let.save_metadata()
    else:
        old_instance = Dokument.objects.get(pk=instance.pk)
        if not instance.suppress_signal:
            if old_instance.let is None and instance.let is not None:
                instance.let.save_metadata()
            elif old_instance.let is not None and instance.let is None:
                old_instance.let.save_metadata()
            elif old_instance.let is not None and instance.let is not None and old_instance.let != instance.let:
                old_instance.let.save_metadata()
                instance.let.save_metadata()
    try:
        instance.set_snapshots()
    except ValueError as err:
        logger.debug("dokument.signals.create_dokument_vazby.type_error", extra={"pk": instance.pk, "err": err})
    logger.debug("dokument.signals.create_dokument_vazby.end", extra={"ident_cely": instance.ident_cely})


@receiver(pre_save, sender=DokumentCast)
def create_dokument_cast_vazby(sender, instance: DokumentCast, **kwargs):
    """
    Metóda pro vytvoření komponent vazeb dokument části.
    Metóda se volá pred uložením dokument části.
    """
    logger.debug("dokument.signals.create_dokument_cast_vazby.start", extra={"pk": instance.pk})
    if instance.pk is None:
        logger.debug("Creating child komponenty for dokument cast" + str(instance))
        k = KomponentaVazby(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
        k.save()
        instance.komponenty = k
    logger.debug("dokument.signals.create_dokument_cast_vazby.end", extra={"pk": instance.pk})


@receiver(post_save, sender=Dokument)
def dokument_save_metadata(sender, instance: Dokument, **kwargs):
    logger.debug("dokument.signals.dokument_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    if not instance.suppress_signal:
        instance.save_metadata()
    if not check_if_task_queued("Dokument", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["Dokument", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    logger.debug("dokument.signals.dokument_save_metadata.end", extra={"ident_cely": instance.ident_cely})


@receiver(post_save, sender=Let)
def let_save_metadata(sender, instance: Let, **kwargs):
    logger.debug("dokument.signals.let_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    if not instance.suppress_signal:
        instance.save_metadata()
    logger.debug("dokument.signals.let_save_metadata.end", extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=Dokument)
def dokument_delete_repository_container(sender, instance: Dokument, **kwargs):
    logger.debug("dokument.signals.dokument_delete_repository_container.start",
                 extra={"ident_cely": instance.ident_cely})
    instance.record_deletion()
    for item in instance.casti.all():
        item: DokumentCast
        if item.archeologicky_zaznam is not None:
            item.archeologicky_zaznam.save_metadata()
        if item.projekt is not None:
            item.projekt.save_metadata()
    if instance.let:
        instance.let.save_metadata()
    for k in Komponenta.objects.filter(ident_cely__startswith=instance.ident_cely):
        logger.debug("dokument.signals.dokument_delete_repository_container.deleting",
                     extra={"ident_cely": k.ident_cely})
        k.delete()
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    if instance.soubory and instance.soubory.pk:
        instance.soubory.delete()
    logger.debug("dokument.signals.dokument_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=Let)
def let_delete_repository_container(sender, instance: Let, **kwargs):
    logger.debug("dokument.signals.let_delete_repository_container.start",
                 extra={"ident_cely": instance.ident_cely})
    instance.record_deletion()
    logger.debug("dokument.signals.let_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely})


@receiver(post_save, sender=DokumentCast)
def dokument_cast_save_metadata(sender, instance: DokumentCast, created, **kwargs):
    extra = {"dokument_cast": instance.pk, "signal_created": created}
    logger.debug("dokument.signals.dokument_cast_save_metadata.start", extra=extra)
    if (created or instance.initial_projekt != instance.projekt or
            instance.initial_archeologicky_zaznam != instance.archeologicky_zaznam):
        instance.dokument.save_metadata()
        if instance.archeologicky_zaznam is not None:
            instance.archeologicky_zaznam.save_metadata()
            extra.update({"archeologicky_zaznam": instance.archeologicky_zaznam.ident_cely})
        if instance.initial_archeologicky_zaznam is not None:
            instance.initial_archeologicky_zaznam.save_metadata()
            extra.update({"initial_archeologicky_zaznam": instance.initial_archeologicky_zaznam.ident_cely})
        if instance.projekt is not None:
            instance.projekt.save_metadata()
            extra.update({"projekt": instance.projekt.ident_cely})
        if instance.initial_projekt is not None:
            instance.initial_projekt.save_metadata()
            extra.update({"initial_projekt": instance.initial_projekt.ident_cely})
        logger.debug("dokument.signals.dokument_cast_save_metadata.changed", extra=extra)
    else:
        logger.debug("dokument.signals.dokument_cast_save_metadata.no_change", extra=extra)
    logger.debug("dokument.signals.dokument_cast_save_metadata.end", extra=extra)


@receiver(post_delete, sender=DokumentCast)
def dokument_cast_save_metadata(sender, instance: DokumentCast, **kwargs):
    logger.debug("dokument.signals.dokument_cast_save_metadata.start", extra={"pk": instance.pk})
    if instance.initial_archeologicky_zaznam is not None:
        instance.initial_archeologicky_zaznam.save_metadata()
    if instance.initial_projekt is not None:
        instance.initial_projekt.save_metadata()
    logger.debug("dokument.signals.dokument_cast_save_metadata.end", extra={"pk": instance.pk})


@receiver(post_save, sender=Tvar)
def tvar_save(sender, instance: Tvar, created, **kwargs):
    logger.debug("dokument.signals.tvar_save.start", extra={"pk": instance.pk})
    if instance.dokument:
        instance.dokument.save_metadata()
    logger.debug("dokument.signals.tvar_save.end", extra={"pk": instance.pk})


@receiver(pre_delete, sender=Tvar)
def tvar_delete(sender, instance: Tvar, **kwargs):
    logger.debug("dokument.signals.tvar_delete.start", extra={"pk": instance.pk})
    if instance.dokument:
        instance.dokument.save_metadata()
    logger.debug("dokument.signals.tvar_delete.end", extra={"pk": instance.pk})
