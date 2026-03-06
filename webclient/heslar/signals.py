import logging

from core.ident_cely import get_heslar_ident
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from .models import (
    Heslar,
    HeslarDatace,
    HeslarDokumentTypMaterialRada,
    HeslarHierarchie,
    HeslarOdkaz,
    RuianKatastr,
    RuianKraj,
    RuianOkres,
)

logger = logging.getLogger(__name__)


def get_or_create_transaction(instance):
    """
    Vrací or create transaction.

    :param instance: Parametr ``instance`` pracuje se s atributy ``active_transaction``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, výsledek volání ``FedoraTransaction()``.
    """
    if instance.active_transaction:
        return instance.active_transaction
    else:
        return FedoraTransaction()


@receiver(pre_save, sender=Heslar, weak=False)
def save_ident_cely(sender, instance: Heslar, **kwargs):
    """
    Funkce pro uložení metadat hesláře.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_ident_cely``.
    :param instance: Parametr ``instance`` předává se do volání ``check_container_deleted_or_not_exists()``, ``debug()``, pracuje se s atributy ``ident_cely``, ``pk``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_ident_cely``.

        :raises Exception: Vyvolá se při splnění podmínky ``not FedoraRepositoryConnector.check_container_deleted_or_not_exists(instance.ident_cely, 'heslar')``.
    """
    logger.debug("heslo.signals.save_ident_cely.start")
    if not instance.ident_cely and not instance.pk:
        instance.ident_cely = get_heslar_ident()
        if not FedoraRepositoryConnector.check_container_deleted_or_not_exists(instance.ident_cely, "heslar"):
            raise Exception(_("heslo.signals.save_ident_cely.fedora_container_deleted_or_not_exists"))
        logger.debug("heslo.signals.save_ident_cely.ident_cely", extra={"ident_cely": instance.ident_cely})
    logger.debug("heslo.signals.save_ident_cely.end")


@receiver(post_save, sender=Heslar, weak=False)
def save_metadata_heslar(sender, instance: Heslar, **kwargs):
    """
    Funkce pro uložení metadat hesláře.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar``.
    :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar``.
    """
    logger.debug("heslo.signals.save_metadata_heslar.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug(
            "heslo.signals.save_metadata_heslar.end", extra={"transaction": getattr(fedora_transaction, "uid", None)}
        )


@receiver(post_save, sender=RuianKatastr, weak=False)
def save_metadata_katastr(sender, instance: RuianKatastr, **kwargs):
    """
    Funkce pro uložení metadat katastru.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_katastr``.
    :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_katastr``.
    """
    logger.debug("heslo.signals.save_metadata_katastr.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug(
            "heslo.signals.save_metadata_katastr.end", extra={"transaction": getattr(fedora_transaction, "uid", None)}
        )


@receiver(post_save, sender=RuianKraj, weak=False)
def save_metadata_kraj(sender, instance: RuianKraj, **kwargs):
    """
    Funkce pro uložení metadat kraje.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_kraj``.
    :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_kraj``.
    """
    logger.debug("heslo.signals.save_metadata_kraj.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug(
            "heslo.signals.save_metadata_kraj.end", extra={"transaction": getattr(fedora_transaction, "uid", None)}
        )


@receiver(post_save, sender=RuianOkres, weak=False)
def save_metadata_okres(sender, instance: RuianOkres, **kwargs):
    """
    Uloží metadata okres.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_okres``.
    :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_okres``.
    """
    logger.debug("heslo.signals.save_metadata_okres.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug(
            "heslo.signals.save_metadata_okres.end", extra={"transaction": getattr(fedora_transaction, "uid", None)}
        )


@receiver(post_save, sender=HeslarHierarchie, weak=False)
def save_metadata_heslar_hierarchie(sender, instance: HeslarHierarchie, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_hierarchie``.
    :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
    :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_hierarchie``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_hierarchie``.
    """
    logger.debug("heslo.signals.save_metadata_heslar_hierarchie.start")

    if not instance.suppress_signal:

        def save_metadata():
            """
                       Uloží metadata.

            Výsledek provedené změny nad cílovým objektem.
            """
            fedora_transaction = FedoraTransaction()
            if instance.heslo_podrazene:
                instance.heslo_podrazene.save_metadata(fedora_transaction)
            if instance.heslo_nadrazene:
                instance.heslo_nadrazene.save_metadata(fedora_transaction)
            if instance.initial_heslo_nadrazene and instance.heslo_nadrazene.pk != instance.initial_heslo_nadrazene.pk:
                instance.initial_heslo_nadrazene.save_metadata(fedora_transaction)
            if instance.initial_heslo_podrazene and instance.heslo_podrazene.pk != instance.initial_heslo_podrazene.pk:
                instance.initial_heslo_podrazene.save_metadata(fedora_transaction)
            fedora_transaction.mark_transaction_as_closed()
            logger.debug(
                "heslo.signals.save_metadata_heslar_hierarchie.end",
                extra={"transaction": getattr(fedora_transaction, "uid", None)},
            )

        transaction.on_commit(save_metadata)


@receiver(post_save, sender=HeslarDatace, weak=False)
def save_metadata_heslar_datace(sender, instance: HeslarDatace, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_datace``.
    :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
    :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_datace``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_datace``.
    """
    logger.debug("heslo.signals.save_metadata_heslar_hierarchie.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()

        def save_metadata():
            """
                       Uloží metadata.

            Výsledek provedené změny nad cílovým objektem.
            """
            if instance.initial_obdobi and instance.initial_obdobi != instance.obdobi:
                instance.initial_obdobi.save_metadata(fedora_transaction)
                logger.debug(
                    "heslo.signals.save_metadata_heslar_hierarchie.save_metadata",
                    extra={"transaction": fedora_transaction},
                )
            instance.obdobi.save_metadata(fedora_transaction, close_transaction=True)

        transaction.on_commit(save_metadata)
        logger.debug(
            "heslo.signals.save_metadata_heslar_hierarchie.end",
            extra={"transaction": getattr(fedora_transaction, "uid", None)},
        )


@receiver(post_save, sender=HeslarDokumentTypMaterialRada, weak=False)
def save_metadata_heslar_dokument_typ_material_rada(sender, instance: HeslarDokumentTypMaterialRada, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_dokument_typ_material_rada``.
    :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
    :param created: Parametr ``created`` ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_dokument_typ_material_rada``.
    """
    logger.debug("heslo.signals.save_metadata_heslar_dokument_typ_material_rada.start")
    if not instance.suppress_signal:
        if created:

            def save_metadata():
                """
                               Uloží metadata.

                Výsledek provedené změny nad cílovým objektem.
                """
                fedora_transaction = FedoraTransaction()
                instance.dokument_typ.save_metadata(fedora_transaction)
                instance.dokument_material.save_metadata(fedora_transaction)
                instance.dokument_rada.save_metadata(fedora_transaction, close_transaction=True)
                logger.debug(
                    "heslo.signals.save_metadata_heslar_dokument_typ_material_rada.save_metadata",
                    extra={"transaction": getattr(fedora_transaction, "uid", None)},
                )

            transaction.on_commit(save_metadata)
    logger.debug("heslo.signals.save_metadata_heslar_dokument_typ_material_rada.end")


@receiver(post_save, sender=HeslarOdkaz, weak=False)
def save_metadata_heslar_odkaz(sender, instance: HeslarOdkaz, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - odkaz.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_odkaz``.
    :param instance: Parametr ``instance`` pracuje se s atributy ``suppress_signal``, ovlivňuje větvení podmínek.
    :param created: Parametr ``created`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_odkaz``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata_heslar_odkaz``.
    """
    logger.debug("heslo.signals.save_metadata_heslar_odkaz.start")
    if not instance.suppress_signal:

        def save_metadata():
            """
                       Uloží metadata.

            Výsledek provedené změny nad cílovým objektem.
            """
            fedora_transaction = FedoraTransaction()
            if instance.initial_heslo and instance.initial_heslo != instance.heslo:
                heslo = Heslar.objects.get(pk=instance.initial_heslo.pk)
                heslo.save_metadata(fedora_transaction)
            heslo = Heslar.objects.get(pk=instance.heslo.pk)
            heslo.save_metadata(fedora_transaction)
            fedora_transaction.mark_transaction_as_closed()
            logger.debug(
                "heslo.signals.save_metadata_heslar_odkaz.save_medata",
                extra={
                    "transaction": getattr(fedora_transaction, "uid", None),
                    "initial": getattr(instance.initial_heslo, "ident_cely", None),
                    "data": getattr(instance.initial_heslo, "ident_cely", None),
                },
            )

        transaction.on_commit(save_metadata)
        logger.debug("heslo.signals.save_metadata_heslar_odkaz.end")


@receiver(pre_delete, sender=Heslar, weak=False)
def heslar_delete_repository_container(sender, instance: Heslar, **kwargs):
    """
    Provádí operaci heslar delete repository container.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``heslar_delete_repository_container``.
    :param instance: Parametr ``instance`` předává se do volání ``on_commit()``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``heslar_delete_repository_container``.
    """
    logger.debug("heslo.signals.heslar_delete_repository_container.start")
    fedora_transaction = FedoraTransaction()
    transaction.on_commit(lambda: instance.record_deletion(fedora_transaction, close_transaction=True))
    logger.debug(
        "heslo.signals.heslar_delete_repository_container.end",
        extra={"transaction": getattr(fedora_transaction, "uid", None)},
    )


@receiver(pre_delete, sender=RuianKatastr, weak=False)
def ruian_katastr_delete_repository_container(sender, instance: RuianKatastr, **kwargs):
    """
    Provádí operaci ruian katastr delete repository container.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``ruian_katastr_delete_repository_container``.
    :param instance: Parametr ``instance`` předává se do volání ``get_or_create_transaction()``, ``on_commit()``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``ruian_katastr_delete_repository_container``.
    """
    logger.debug("heslo.signals.ruian_katastr_delete_repository_container.start")
    fedora_transaction = get_or_create_transaction(instance)
    transaction.on_commit(lambda: instance.record_deletion(fedora_transaction, close_transaction=True))
    logger.debug(
        "heslo.signals.ruian_katastr_delete_repository_container.end",
        extra={"transaction": getattr(fedora_transaction, "uid", None)},
    )


@receiver(pre_delete, sender=RuianKraj, weak=False)
def ruian_kraj_delete_repository_container(sender, instance: RuianKraj, **kwargs):
    """
    Provádí operaci ruian kraj delete repository container.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``ruian_kraj_delete_repository_container``.
    :param instance: Parametr ``instance`` předává se do volání ``get_or_create_transaction()``, ``on_commit()``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``ruian_kraj_delete_repository_container``.
    """
    logger.debug("heslo.signals.ruian_kraj_delete_repository_container.start")
    fedora_transaction = get_or_create_transaction(instance)
    transaction.on_commit(lambda: instance.record_deletion(fedora_transaction, close_transaction=True))
    logger.debug(
        "heslo.signals.ruian_kraj_delete_repository_container.end",
        extra={"transaction": getattr(fedora_transaction, "uid", None)},
    )


@receiver(pre_delete, sender=RuianOkres, weak=False)
def ruian_okres_delete_repository_container(sender, instance: RuianOkres, **kwargs):
    """
    Provádí operaci ruian okres delete repository container.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``ruian_okres_delete_repository_container``.
    :param instance: Parametr ``instance`` slouží jako vstup pro logiku funkce ``ruian_okres_delete_repository_container``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``ruian_okres_delete_repository_container``.
    """
    logger.debug("heslo.signals.ruian_okres_delete_repository_container.start")

    def save_metadata():
        """Uloží metadata. v aplikaci."""
        fedora_transaction = get_or_create_transaction(instance)
        instance.record_deletion(fedora_transaction, close_transaction=True)
        logger.debug(
            "heslo.signals.ruian_okres_delete_repository_container.end",
            extra={"transaction": getattr(fedora_transaction, "uid", None)},
        )

    transaction.on_commit(save_metadata)


@receiver(post_delete, sender=HeslarHierarchie, weak=False)
def delete_uppdate_related_heslar_hierarchie(sender, instance: HeslarHierarchie, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - hierarchie.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_hierarchie``.
    :param instance: Parametr ``instance`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_hierarchie``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_hierarchie``.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_hierarchie.start")
    fedora_transaction = FedoraTransaction()

    def save_metadata():
        """Uloží metadata. v aplikaci."""
        instance.heslo_podrazene.save_metadata(fedora_transaction)
        instance.heslo_nadrazene.save_metadata(fedora_transaction, close_transaction=True)

    transaction.on_commit(save_metadata)
    logger.debug(
        "heslo.signals.delete_uppdate_related_heslar_hierarchie.end",
        extra={"transaction": getattr(fedora_transaction, "uid", None)},
    )


@receiver(post_delete, sender=HeslarDokumentTypMaterialRada, weak=False)
def delete_uppdate_related_heslar_dokument_typ_material_rada(sender, instance: HeslarDokumentTypMaterialRada, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - dokument typ materiál řada.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_dokument_typ_material_rada``.
    :param instance: Parametr ``instance`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_dokument_typ_material_rada``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_dokument_typ_material_rada``.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_dokument_typ_material_rada.start")
    fedora_transaction = FedoraTransaction()

    def save_metadata():
        """Uloží metadata. v aplikaci."""
        instance.dokument_rada.save_metadata(fedora_transaction)
        instance.dokument_typ.save_metadata(fedora_transaction)
        instance.dokument_material.save_metadata(fedora_transaction, close_transaction=True)

    transaction.on_commit(save_metadata)
    logger.debug(
        "heslo.signals.delete_uppdate_related_heslar_dokument_typ_material_rada.end",
        extra={"transaction": getattr(fedora_transaction, "uid", None)},
    )


@receiver(post_delete, sender=HeslarOdkaz, weak=False)
def delete_uppdate_related_heslar_odkaz(sender, instance: HeslarOdkaz, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - odkaz.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_odkaz``.
    :param instance: Parametr ``instance`` předává se do volání ``on_commit()``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_odkaz``.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_odkaz.start")
    fedora_transaction = FedoraTransaction()
    transaction.on_commit(lambda: instance.heslo.save_metadata(fedora_transaction, close_transaction=True))
    logger.debug(
        "heslo.signals.delete_uppdate_related_heslar_odkaz.end",
        extra={"transaction": getattr(fedora_transaction, "uid", None)},
    )


@receiver(post_delete, sender=HeslarDatace, weak=False)
def delete_uppdate_related_heslar_datace(sender, instance: HeslarDatace, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - datace.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_datace``.
    :param instance: Parametr ``instance`` pracuje se s atributy ``obdobi``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_uppdate_related_heslar_datace``.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_datace.start")
    fedora_transaction = FedoraTransaction()
    heslo_obdobi = instance.obdobi

    def save_metadata():
        """Uloží metadata. v aplikaci."""
        heslo_obdobi.datace_obdobi = None
        heslo_obdobi.save_metadata(fedora_transaction, close_transaction=True)

    transaction.on_commit(save_metadata)
    logger.debug(
        "heslo.signals.delete_uppdate_related_heslar_datace.end",
        extra={"transaction": getattr(fedora_transaction, "uid", None)},
    )
