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
    Před smazáním samostatného nálezu označí záznam ve Fedoře jako smazaný a odstraní jeho soubory a historii v DB.

    Zápis do Fedory probíhá hned (uvnitř DB transakce), aby chyba Fedory (např. 409 při souběžném
    zápisu jiné transakce) vedla k rollbacku smazání v DB. Metadata projektu se zapisují až
    v ``samostatny_nalez_delete_update_projekt`` po smazání řádku, aby už nález neobsahovala.

    :param sender: Model, který signál vyvolal (``SamostatnyNalez``).
    :param instance: Mazaný samostatný nález; používá se jeho ``active_transaction``, ``soubory`` a ``historie``.
    :param kwargs: Dodatečné argumenty předané Django signálem.
    """
    logger.debug("pas.signals.dokument_delete_container_soubor_vazby.start", extra={"ident_cely": instance.ident_cely})
    invalidate_model(SamostatnyNalez)
    invalidate_model(Projekt)
    instance.record_deletion(instance.active_transaction)
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


@receiver(post_delete, sender=SamostatnyNalez, weak=False)
def samostatny_nalez_delete_update_projekt(sender, instance: SamostatnyNalez, **kwargs):
    """
    Po smazání samostatného nálezu přegeneruje metadata projektu ve Fedoře a případně uzavře transakci.

    Metadata projektu se zapisují ještě uvnitř DB transakce, takže konflikt ve Fedoře (409 při souběžném
    mazání jiného nálezu téhož projektu) se projeví výjimkou ve view a smazání v DB se odroluje.
    Do ``transaction.on_commit`` se odkládá jen commit Fedora transakce (#4437). Selhání samotného
    commitu Fedory po commitu DB tím pokryté není; zaloguje se jako ERROR s ``ident_cely``
    (``core_repository_connector.FedoraTransaction.commit_transaction.failed``).

    :param sender: Model, který signál vyvolal (``SamostatnyNalez``).
    :param instance: Smazaný samostatný nález; používá se jeho ``projekt``, ``active_transaction``
        a ``close_active_transaction_when_finished``.
    :param kwargs: Dodatečné argumenty předané Django signálem.
    """
    fedora_transaction = instance.active_transaction
    logger.debug(
        "pas.signals.samostatny_nalez_delete_update_projekt.start",
        extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)},
    )
    if instance.projekt:
        instance.projekt.save_metadata(fedora_transaction)
    if instance.close_active_transaction_when_finished:
        transaction.on_commit(fedora_transaction.mark_transaction_as_closed)
    logger.debug(
        "pas.signals.samostatny_nalez_delete_update_projekt.end",
        extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)},
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
    # Zápisy do DB i Fedory uvnitř DB transakce, aby chyba Fedory vedla k rollbacku smazání (#4437).
    Historie.save_record_deletion_record(record=instance)
    instance.vedouci.save_metadata(fedora_transaction)
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    instance.spolupracovnik.save_metadata(fedora_transaction)
    # User.save_metadata s close_transaction=True commitne Fedoru hned (na rozdíl od ModelWithMetadata),
    # proto se commit Fedora transakce plánuje explicitně až po commitu DB.
    if instance.close_active_transaction_when_finished:
        transaction.on_commit(fedora_transaction.mark_transaction_as_closed)
    logger.debug(
        "pas.signals.delete_uzivatel_spoluprce_connections.end",
        extra={"pk": instance.pk, "transaction": getattr(fedora_transaction, "uid", None)},
    )
