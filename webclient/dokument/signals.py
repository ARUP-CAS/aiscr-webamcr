import logging

from arch_z.models import ArcheologickyZaznam
from core.constants import DOKUMENT_CAST_RELATION_TYPE, DOKUMENT_RELATION_TYPE
from core.models import SouborVazby
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from dokument.models import Dokument, DokumentAutor, DokumentCast, Let, Tvar
from historie.models import HistorieVazby
from komponenta.models import KomponentaVazby

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Dokument)
def create_dokument_vazby(sender, instance: Dokument, **kwargs):
    """
    Metóda pro vytvoření historických vazeb dokumentu.
    Metóda se volá pred uložením záznamu.
    """
    if instance.pk is None:
        logger.debug("dokument.signals.create_dokument_vazby.creating_history_for_dokument",
                     extra={"instance": instance})
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


@receiver(pre_save, sender=DokumentCast)
def create_dokument_cast_vazby(sender, instance: DokumentCast, **kwargs):
        """
        Metóda pro vytvoření komponent vazeb dokument části.
        Metóda se volá pred uložením dokument části.
        """   
        if instance.pk is None:
            logger.debug("Creating child komponenty for dokument cast" + str(instance))
            k = KomponentaVazby(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
            k.save()
            instance.komponenty = k


@receiver(post_save, sender=Dokument)
def dokument_save_metadata(sender, instance: Dokument, **kwargs):
    if not instance.suppress_signal:
        instance.save_metadata()
    instance.set_snapshots()


@receiver(post_save, sender=Let)
def let_save_metadata(sender, instance: Let, **kwargs):
    if not instance.suppress_signal:
        instance.save_metadata()


@receiver(pre_delete, sender=Dokument)
def dokument_delete_repository_container(sender, instance: Dokument, **kwargs):
    instance.record_deletion()
    for item in instance.casti.all():
        item: DokumentCast
        if item.archeologicky_zaznam is not None:
            item.archeologicky_zaznam.save_metadata()
        if item.projekt is not None:
            item.projekt.save_metadata()
    if instance.let:
        instance.let.save_metadata()


@receiver(pre_delete, sender=Let)
def let_delete_repository_container(sender, instance: Let, **kwargs):
    instance.record_deletion()


@receiver(post_save, sender=DokumentCast)
def dokument_cast_save_metadata(sender, instance: DokumentCast, created, **kwargs):
    if created:
        instance.dokument.save_metadata()
        if instance.archeologicky_zaznam is not None:
            instance.archeologicky_zaznam.save_metadata()
        if instance.projekt is not None:
            instance.projekt.save_metadata()


@receiver(post_save, sender=Tvar)
def tvar_save(sender, instance: Tvar, created, **kwargs):
    if instance.dokument:
        instance.dokument.save_metadata()


@receiver(pre_delete, sender=Tvar)
def tvar_delete(sender, instance: Tvar, created, **kwargs):
    if instance.dokument:
        instance.dokument.save_metadata()
