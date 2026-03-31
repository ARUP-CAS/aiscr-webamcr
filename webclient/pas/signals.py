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

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_dokument_vazby``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``pk``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``create_dokument_vazby``.
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
    """
    Uloží metadata samostatny nalez.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_samostatny_nalez``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``check_if_task_queued()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
    :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_samostatny_nalez``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_samostatny_nalez``.
    """
    logger.debug("pas.signals.save_metadata_samostatny_nalez.start", extra={"ident_cely": instance.ident_cely})
    invalidate_model(SamostatnyNalez)
    invalidate_model(Projekt)
    fedora_transaction = None
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction

        def save_metadata(close_transaction=False):
            """
                       Uloží metadata.

                       :param close_transaction: Parametr ``close_transaction`` předává se do volání ``save_metadata()``.
            Výsledek provedené změny nad cílovým objektem.
            """
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
    """
    Provádí operaci dokument delete container soubor vazby.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``dokument_delete_container_soubor_vazby``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``dokument_delete_container_soubor_vazby``.
    """
    logger.debug("pas.signals.dokument_delete_container_soubor_vazby.start", extra={"ident_cely": instance.ident_cely})
    invalidate_model(SamostatnyNalez)
    invalidate_model(Projekt)
    fedora_transaction = instance.active_transaction

    def save_metadata(close_transaction=False):
        """
        Uloží metadata. v aplikaci.

        :param close_transaction: Parametr ``close_transaction`` předává se do volání ``record_deletion()``.
        """
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
    """
    Uloží uzivatel spoluprce.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_uzivatel_spoluprce``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_uzivatel_spoluprce``.
    """
    logger.debug("pas.signals.save_uzivatel_spoluprce.start", extra={"pk": instance.pk})
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction

        def save_metadata(close_transaction=False):
            """
                       Uloží metadata.

                       :param close_transaction: Parametr ``close_transaction`` předává se do volání ``save_metadata()``.
            Výsledek provedené změny nad cílovým objektem.
            """
            instance.vedouci.save_metadata(fedora_transaction)
            instance.spolupracovnik.save_metadata(fedora_transaction, close_transaction=close_transaction)

        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: save_metadata(True))
        else:
            save_metadata()
    logger.debug("pas.signals.save_uzivatel_spoluprce.end", extra={"pk": instance.pk})


@receiver(post_delete, sender=UzivatelSpoluprace, weak=False)
def delete_uzivatel_spoluprce_connections(sender, instance: UzivatelSpoluprace, **kwargs):
    """
    Odstraní uzivatel spoluprce connections.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uzivatel_spoluprce_connections``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``pk``, ``active_transaction``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uzivatel_spoluprce_connections``.
    """
    logger.debug("pas.signals.delete_uzivatel_spoluprce_connections.start", extra={"pk": instance.pk})
    fedora_transaction = instance.active_transaction

    def save_metadata(close_transaction=False):
        """
        Uloží metadata. v aplikaci.

        :param close_transaction: Parametr ``close_transaction`` předává se do volání ``save_metadata()``.
        """
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
