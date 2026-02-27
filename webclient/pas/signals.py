import logging

from cacheops import invalidate_model
from core.constants import SAMOSTATNY_NALEZ_RELATION_TYPE
from core.models import SouborVazby
from cron.tasks import update_single_redis_snapshot
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from historie.models import Historie, HistorieVazby
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from projekt.models import Projekt
from xml_generator.models import UPDATE_REDIS_SNAPSHOT, check_if_task_queued

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=SamostatnyNalez, weak=False)
def create_dokument_vazby(sender, instance, **kwargs):
    """
    Metoda pro vytvoření historických a souborových vazeb samostatnýho náleze.
    Metoda se volá pred uložením záznamu.
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


@receiver(post_save, sender=SamostatnyNalez, weak=False)
def save_metadata_samostatny_nalez(sender, instance: SamostatnyNalez, created, **kwargs):
    """Uloží metadata samostatny nalez.

    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param created: Vstupní hodnota ``created`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek provedené operace."""
    logger.debug("pas.signals.save_metadata_samostatny_nalez.start", extra={"ident_cely": instance.ident_cely})
    invalidate_model(SamostatnyNalez)
    invalidate_model(Projekt)
    fedora_transaction = None
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction

        def save_metadata(close_transaction=False):
            """Uloží metadata.

            :param close_transaction: Vstupní hodnota ``close_transaction`` pro danou operaci.
            :return: Vrací výsledek provedené operace."""
            if (created or instance.initial_pristupnost != instance.pristupnost) and instance.projekt:
                instance.projekt.set_pristupnost()
                instance.projekt.active_transaction = fedora_transaction
                instance.projekt.save()
            instance.save_metadata(fedora_transaction, close_transaction=close_transaction)

        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: save_metadata(True))
        else:
            save_metadata(False)
    if not check_if_task_queued("SamostatnyNalez", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["SamostatnyNalez", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    logger.debug(
        "pas.signals.save_metadata_samostatny_nalez.end",
        extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction},
    )


@receiver(pre_delete, sender=SamostatnyNalez, weak=False)
def dokument_delete_container_soubor_vazby(sender, instance: SamostatnyNalez, **kwargs):
    """Provádí operaci dokument delete container soubor vazby.

    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek provedené operace."""
    logger.debug("pas.signals.dokument_delete_container_soubor_vazby.start", extra={"ident_cely": instance.ident_cely})
    invalidate_model(SamostatnyNalez)
    invalidate_model(Projekt)
    fedora_transaction = instance.active_transaction

    def save_metadata(close_transaction=False):
        """Uloží metadata.

        :param close_transaction: Vstupní hodnota ``close_transaction`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if instance.projekt:
            instance.projekt.save_metadata(fedora_transaction)
        instance.record_deletion(fedora_transaction, close_transaction=close_transaction)

    if instance.close_active_transaction_when_finished:
        transaction.on_commit(lambda: save_metadata(True))
    else:
        save_metadata(False)
    if instance.soubory and instance.soubory.pk:
        for item in instance.soubory.soubory.all():
            item.suppress_signal = True
            item.delete()
        instance.soubory.delete()
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    logger.debug(
        "pas.signals.dokument_delete_container_soubor_vazby.end",
        extra={"ident_cely": instance.ident_cely, "transaction": transaction},
    )


@receiver(post_save, sender=UzivatelSpoluprace, weak=False)
def save_uzivatel_spoluprce(sender, instance: UzivatelSpoluprace, **kwargs):
    """Uloží uzivatel spoluprce.

    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek provedené operace."""
    logger.debug("pas.signals.save_uzivatel_spoluprce.start", extra={"pk": instance.pk})
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction

        def save_metadata(close_transaction=False):
            """Uloží metadata.

            :param close_transaction: Vstupní hodnota ``close_transaction`` pro danou operaci.
            :return: Vrací výsledek provedené operace."""
            instance.vedouci.save_metadata(fedora_transaction)
            instance.spolupracovnik.save_metadata(fedora_transaction, close_transaction=close_transaction)

        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: save_metadata(True))
        else:
            save_metadata()
    logger.debug("pas.signals.save_uzivatel_spoluprce.end", extra={"pk": instance.pk})


@receiver(post_delete, sender=UzivatelSpoluprace, weak=False)
def delete_uzivatel_spoluprce_connections(sender, instance: UzivatelSpoluprace, **kwargs):
    """Odstraní uzivatel spoluprce connections.

    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek operace odstranění."""
    logger.debug("pas.signals.delete_uzivatel_spoluprce_connections.start", extra={"pk": instance.pk})
    fedora_transaction = instance.active_transaction

    def save_metadata(close_transaction=False):
        """Uloží metadata.

        :param close_transaction: Vstupní hodnota ``close_transaction`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        Historie.save_record_deletion_record(record=instance)
        instance.vedouci.save_metadata(fedora_transaction)
        if instance.historie and instance.historie.pk:
            instance.historie.delete()
        instance.spolupracovnik.save_metadata(fedora_transaction, close_transaction=close_transaction)

    if instance.close_active_transaction_when_finished:
        transaction.on_commit(lambda: save_metadata(True))
    else:
        save_metadata()
    logger.debug(
        "pas.signals.delete_uzivatel_spoluprce_connections.end",
        extra={"pk": instance.pk, "transaction": getattr(fedora_transaction, "uid", None)},
    )
