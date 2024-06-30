import logging

from cacheops import invalidate_model
from django.db import transaction

from core.constants import PROJEKT_RELATION_TYPE, PROJEKT_STAV_ZAPSANY
from core.models import SouborVazby
from core.repository_connector import FedoraTransaction
from cron.tasks import update_single_redis_snapshot
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _

from dokument.models import Dokument
from historie.models import HistorieVazby, Historie
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from notifikace_projekty.tasks import check_hlidaci_pes
from arch_z.models import Akce, ArcheologickyZaznam
from xml_generator.models import UPDATE_REDIS_SNAPSHOT, check_if_task_queued

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Projekt)
def projekt_pre_save(sender, instance, **kwargs):
    """
        Metóda pro volání dílčích metod pro nastavení projektu pred uložením.
    """
    create_projekt_vazby(sender, instance)
    change_termin_odevzdani_NZ(sender, instance)
    
    if instance.stav == PROJEKT_STAV_ZAPSANY:
        if instance.pk is not None:
            instance.__original_stav = Projekt.objects.get(pk=instance.id).stav
        else:
            instance.__original_stav = None


def change_termin_odevzdani_NZ(sender, instance, **kwargs):
    """
        Metóda pro nastavení terminu odevzdání NZ.
    """
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
    """
        Metóda pro vytvoření historických vazeb projektu.
        Metóda se volá pred uložením projektu.
    """
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


@receiver(post_delete, sender=Projekt)
def projekt_pre_delete(sender, instance: Projekt, **kwargs):
    logger.debug("projekt.signals.projekt_pre_delete.start",
                 extra={"ident_cely": instance.ident_cely, "initial_dokumenty": instance.initial_dokumenty})
    if instance.soubory and instance.soubory.soubory.exists():
        raise Exception(_("projekt.signals.projekt_pre_delete.cannot_delete"))
    fedora_transaction = instance.active_transaction
    invalidate_model(Projekt)
    invalidate_model(Akce)
    invalidate_model(ArcheologickyZaznam)
    invalidate_model(SamostatnyNalez)
    invalidate_model(Historie)
    if not instance.suppress_signal:
        def save_metadata(close_transaction=False):
            if instance.soubory and instance.soubory.pk:
                instance.soubory.delete()
            for dokument_pk in instance.initial_dokumenty:
                dokument: Dokument = Dokument.objects.get(pk=dokument_pk)
                dokument.save_metadata(fedora_transaction)
            instance.record_deletion(fedora_transaction, close_transaction=close_transaction)
        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: save_metadata(True))
        else:
            save_metadata()
    logger.debug("projekt.signals.projekt_pre_delete.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_save, sender=Projekt)
def projekt_post_save(sender, instance: Projekt, **kwargs):
    """
        Metóda pro odeslání emailu hlídacího psa pri založení projektu.
    """
    # When projekt is created using the "oznameni" page, the metadata are saved directly without celery
    logger.debug("projekt.signals.projekt_post_save.start", extra={"ident_cely": instance.ident_cely})
    invalidate_model(Projekt)
    invalidate_model(Akce)
    invalidate_model(ArcheologickyZaznam)
    invalidate_model(SamostatnyNalez)
    invalidate_model(Historie)
    fedora_transaction = instance.active_transaction
    if getattr(instance, "suppress_signal", False) is not True:
        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        else:
            instance.save_metadata(fedora_transaction)
    if (instance.stav == PROJEKT_STAV_ZAPSANY and hasattr(instance, "__original_stav")
            and instance.stav != instance.__original_stav or instance.stav == PROJEKT_STAV_ZAPSANY
            and not hasattr(instance, "__original_stav")):
        logger.debug("projekt.signals.projekt_post_save.checked_hlidaci_pes",
                     extra={"instance": instance})
        check_hlidaci_pes.delay(instance.pk)
    if not check_if_task_queued("Projekt", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["Projekt", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    logger.debug("projekt.signals.projekt_post_save.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)})
