from datetime import timedelta
import logging

from core.constants import PROJEKT_RELATION_TYPE, PROJEKT_STAV_ZAPSANY
from core.models import SouborVazby
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from historie.models import HistorieVazby
from projekt.models import Projekt
from notifikace_projekty.tasks import check_hlidaci_pes

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Projekt)
def projekt_pre_save(sender, instance, **kwargs):
    create_projekt_vazby(sender, instance)
    change_termin_odevzdani_NZ(sender, instance)
    if instance.pk is not None:
        if instance.stav == PROJEKT_STAV_ZAPSANY:
            instance.__original_stav = Projekt.objects.get(pk=instance.id).stav


def change_termin_odevzdani_NZ(sender, instance, **kwargs):
    try:
        instance_db = sender.objects.get(pk = instance.pk)
    except sender.DoesNotExist:
        instance_db = None
    if instance_db and instance.termin_odevzdani_nz == instance_db.termin_odevzdani_nz:
        if instance.datum_ukonceni != instance_db.datum_ukonceni and instance.datum_ukonceni:
            logger.debug("projekt.signals.change_termin_odevzdani_NZ.changed_automatic_date",
                         extra={"ident_cely": instance.ident_cely})
            instance.termin_odevzdani_nz = instance.datum_ukonceni
            instance.termin_odevzdani_nz = instance.termin_odevzdani_nz.replace(year=instance.termin_odevzdani_nz.year + 3)


def create_projekt_vazby(sender, instance, **kwargs):
    if instance.pk is None:
        logger.debug("projekt.signals.create_projekt_vazby.history_created",
                     extra={"instance": instance})
        hv = HistorieVazby(typ_vazby=PROJEKT_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        logger.debug("projekt.signals.create_projekt_vazby.child_file_created",
                     extra={"instance": instance})
        sv = SouborVazby(typ_vazby=PROJEKT_RELATION_TYPE)
        sv.save()
        instance.soubory = sv


@receiver(post_save, sender=Projekt)
def projekt_post_save(sender, instance: Projekt, **kwargs):
    instance.save_metadata()
    if instance.stav == PROJEKT_STAV_ZAPSANY and hasattr(instance, "__original_stav") \
            and instance.stav != instance.__original_stav:
        logger.debug("projekt.signals.projekt_post_save.checked_hlidaci_pes",
                     extra={"instance": instance})
        check_hlidaci_pes.delay(instance.pk)
