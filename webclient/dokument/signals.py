import logging

from arch_z.models import ArcheologickyZaznam
from core.constants import DOKUMENT_CAST_RELATION_TYPE, DOKUMENT_RELATION_TYPE
from core.models import SouborVazby
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from dokument.models import Dokument, DokumentAutor, DokumentCast, Let
from historie.models import HistorieVazby
from komponenta.models import KomponentaVazby

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Dokument)
def create_dokument_vazby(sender, instance, **kwargs):
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


@receiver(pre_save, sender=DokumentCast)
def create_dokument_cast_vazby(sender, instance, **kwargs):     
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


@receiver(post_save, sender=Let)
def let_save_metadata(sender, instance: Let, **kwargs):
    if not instance.suppress_signal:
        instance.save_metadata()


@receiver(post_delete, sender=Dokument)
def dokument_delete_repository_container(sender, instance: Dokument, **kwargs):
    instance.record_deletion()


@receiver(post_delete, sender=Let)
def let_delete_repository_container(sender, instance: Let, **kwargs):
    instance.record_deletion()


@receiver(post_save, sender=DokumentCast)
def let_save_metadata(sender, instance: DokumentCast, created, **kwargs):
    if created:
        instance.dokument.save_metadata()
        if instance.archeologicky_zaznam is not None:
            instance.archeologicky_zaznam.save_metadata()
        if instance.projekt is not None:
            instance.projekt.save_metadata()
