import logging

from core.constants import SAMOSTATNY_NALEZ_RELATION_TYPE
from django.core.exceptions import ObjectDoesNotExist
from core.models import SouborVazby
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from historie.models import HistorieVazby, Historie
from pas.models import SamostatnyNalez, UzivatelSpoluprace

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=SamostatnyNalez)
def create_dokument_vazby(sender, instance, **kwargs):
    """
    Metóda pro vytvoření historických a souborových vazeb samostatnýho náleze.
    Metóda se volá pred uložením záznamu.
    """
    if instance.pk is None:
        logger.debug("Creating history records for SN " + str(instance))
        hv = HistorieVazby(typ_vazby=SAMOSTATNY_NALEZ_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        logger.debug("Creating child file and soubory for SN " + str(instance))
        sv = SouborVazby(typ_vazby=SAMOSTATNY_NALEZ_RELATION_TYPE)
        sv.save()
        instance.soubory = sv


@receiver(post_save, sender=SamostatnyNalez)
def save_metadata_samostatny_nalez(sender, instance: SamostatnyNalez, **kwargs):
    instance.save_metadata()
    instance.projekt.save_metadata()


@receiver(pre_delete, sender=SamostatnyNalez)
def dokument_delete_soubor_vazby(sender, instance: SamostatnyNalez, **kwargs):
    try:
        instance.soubory.delete()
    except ObjectDoesNotExist:
        logger.debug("pas.signals.dokument_delete_soubor_vazby.not_exist", extra={"ident_cely": instance.ident_cely})

@receiver(pre_delete, sender=SamostatnyNalez)
def samostatny_nalez_okres_delete_repository_container(sender, instance: SamostatnyNalez, **kwargs):
    instance.record_deletion()


@receiver(pre_save, sender=UzivatelSpoluprace)
def save_uzivatel_spoluprce(sender, instance: UzivatelSpoluprace, **kwargs):
    instance.vedouci.save_metadata(use_celery=False)
    instance.spolupracovnik.save_metadata(use_celery=False)


@receiver(post_delete, sender=UzivatelSpoluprace)
def delete_uzivatel_spoluprce(sender, instance: UzivatelSpoluprace, **kwargs):
    Historie.save_record_deletion_record(record=instance)
    instance.vedouci.save_metadata(use_celery=False)
    instance.spolupracovnik.save_metadata(use_celery=False)
