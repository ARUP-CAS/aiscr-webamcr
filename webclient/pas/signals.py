import logging

from core.constants import SAMOSTATNY_NALEZ_RELATION_TYPE
from cron.tasks import update_single_redis_snapshot
from core.models import SouborVazby
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from historie.models import HistorieVazby, Historie
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from xml_generator.models import check_if_task_queued, UPDATE_REDIS_SNAPSHOT

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=SamostatnyNalez)
def create_dokument_vazby(sender, instance, **kwargs):
    """
    Metóda pro vytvoření historických a souborových vazeb samostatnýho náleze.
    Metóda se volá pred uložením záznamu.
    """
    logger.debug("pas.signals.create_dokument_vazby.start", extra={"ident_cely": instance.ident_cely})
    if instance.pk is None:
        hv = HistorieVazby(typ_vazby=SAMOSTATNY_NALEZ_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        sv = SouborVazby(typ_vazby=SAMOSTATNY_NALEZ_RELATION_TYPE)
        sv.save()
        instance.soubory = sv
    logger.debug("pas.signals.create_dokument_vazby.end", extra={"ident_cely": instance.ident_cely})


@receiver(post_save, sender=SamostatnyNalez)
def save_metadata_samostatny_nalez(sender, instance: SamostatnyNalez, created, **kwargs):
    logger.debug("pas.signals.save_metadata_samostatny_nalez.start", extra={"ident_cely": instance.ident_cely})
    fedora_transaction = instance.active_transaction
    if (created or instance.initial_pristupnost != instance.pristupnost) and instance.projekt:
        instance.projekt.save_metadata(fedora_transaction)
    instance.save_metadata(fedora_transaction, close_transaction=instance.close_active_transaction_when_finished)
    if not check_if_task_queued("SamostatnyNalez", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["SamostatnyNalez", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    logger.debug("pas.signals.save_metadata_samostatny_nalez.end", extra={"ident_cely": instance.ident_cely,
                                                                          "transaction": fedora_transaction})


@receiver(pre_delete, sender=SamostatnyNalez)
def dokument_delete_container_soubor_vazby(sender, instance: SamostatnyNalez, **kwargs):
    logger.debug("pas.signals.dokument_delete_container_soubor_vazby.start",
                 extra={"ident_cely": instance.ident_cely})
    fedora_transaction = instance.active_transaction
    if instance.projekt:
        instance.projekt.save_metadata(fedora_transaction)
    transaction = instance.record_deletion(fedora_transaction,
                                           close_transaction=instance.close_active_transaction_when_finished)
    if instance.soubory and instance.soubory.pk:
        instance.soubory.delete()
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    logger.debug("pas.signals.dokument_delete_container_soubor_vazby.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": transaction})


@receiver(post_save, sender=UzivatelSpoluprace)
def save_uzivatel_spoluprce(sender, instance: UzivatelSpoluprace, **kwargs):
    logger.debug("pas.signals.save_uzivatel_spoluprce.start", extra={"pk": instance.pk})
    fedora_transaction = instance.active_transaction
    instance.vedouci.save_metadata(fedora_transaction)
    instance.spolupracovnik.save_metadata(fedora_transaction,
                                          close_transaction=instance.close_activate_transaction_when_finished)
    logger.debug("pas.signals.save_uzivatel_spoluprce.end", extra={"pk": instance.pk})


@receiver(pre_delete, sender=UzivatelSpoluprace)
def delete_uzivatel_spoluprce_connections(sender, instance: UzivatelSpoluprace, **kwargs):
    logger.debug("pas.signals.delete_uzivatel_spoluprce_connections.start", extra={"pk": instance.pk})
    fedora_transaction = instance.active_transaction
    instance.vedouci.save_metadata(fedora_transaction)
    instance.spolupracovnik.save_metadata(fedora_transaction,
                                          close_transaction=instance.close_activate_transaction_when_finished)
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    logger.debug("pas.signals.delete_uzivatel_spoluprce_connections.end",
                 extra={"pk": instance.pk,  "transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_delete, sender=UzivatelSpoluprace)
def delete_uzivatel_spoluprce(sender, instance: UzivatelSpoluprace, **kwargs):
    logger.debug("pas.signals.delete_uzivatel_spoluprce.start", extra={"pk": instance.pk})
    Historie.save_record_deletion_record(record=instance)
    fedora_transaction = instance.active_transaction
    instance.vedouci.save_metadata(fedora_transaction)
    instance.spolupracovnik.save_metadata(fedora_transaction,
                                          close_transaction=instance.close_activate_transaction_when_finished)
    if not check_if_task_queued("UzivatelSpoluprace", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["UzivatelSpoluprace", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    logger.debug("pas.signals.delete_uzivatel_spoluprce.end",
                 extra={"pk": instance.pk, "transaction": getattr(fedora_transaction, "uid", None)})
