import logging

from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _

from core.ident_cely import get_heslar_ident
from core.repository_connector import FedoraTransaction, FedoraRepositoryConnector, FedoraError
from .models import Heslar, RuianKatastr, RuianKraj, RuianOkres, HeslarDatace, HeslarHierarchie, \
    HeslarDokumentTypMaterialRada, HeslarOdkaz

logger = logging.getLogger(__name__)


def get_or_create_transaction(instance):
    if instance.active_transaction:
        return instance.active_transaction
    else:
        return FedoraTransaction()


@receiver(pre_save, sender=Heslar)
def save_ident_cely(sender, instance: Heslar, **kwargs):
    """
    Funkce pro uložení metadat hesláře.
    """
    logger.debug("heslo.signals.save_ident_cely.start")
    if not instance.ident_cely and not instance.pk:
        instance.ident_cely = get_heslar_ident()
        if not FedoraRepositoryConnector.check_container_deleted_or_not_exists(instance.ident_cely, "heslar"):
            raise Exception(_("heslo.signals.save_ident_cely.fedora_container_deleted_or_not_exists"))
        logger.debug("heslo.signals.save_ident_cely.ident_cely", extra={"ident_cely": instance.ident_cely})
    logger.debug("heslo.signals.save_ident_cely.end")


@receiver(post_save, sender=Heslar)
def save_metadata_heslar(sender, instance: Heslar, **kwargs):
    """
    Funkce pro uložení metadat hesláře.
    """
    logger.debug("heslo.signals.save_metadata_heslar.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug("heslo.signals.save_metadata_heslar.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_save, sender=RuianKatastr)
def save_metadata_katastr(sender, instance: RuianKatastr, **kwargs):
    """
    Funkce pro uložení metadat katastru.
    """
    logger.debug("heslo.signals.save_metadata_katastr.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug("heslo.signals.save_metadata_katastr.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_save, sender=RuianKraj)
def save_metadata_kraj(sender, instance: RuianKraj, **kwargs):
    """
    Funkce pro uložení metadat kraje.
    """
    logger.debug("heslo.signals.save_metadata_kraj.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug("heslo.signals.save_metadata_kraj.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_save, sender=RuianOkres)
def save_metadata_okres(sender, instance: RuianOkres, **kwargs):
    logger.debug("heslo.signals.save_metadata_okres.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        logger.debug("heslo.signals.save_metadata_okres.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_save, sender=HeslarHierarchie)
def save_metadata_heslar_hierarchie(sender, instance: HeslarHierarchie, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.
    """
    logger.debug("heslo.signals.save_metadata_heslar_hierarchie.start")

    if not instance.suppress_signal:

        def save_metadata():
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
            logger.debug("heslo.signals.save_metadata_heslar_hierarchie.end",
                         extra={"transaction": getattr(fedora_transaction, "uid", None)})
        transaction.on_commit(save_metadata)


@receiver(post_save, sender=HeslarDatace)
def save_metadata_heslar_hierarchie(sender, instance: HeslarDatace, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.
    """
    logger.debug("heslo.signals.save_metadata_heslar_hierarchie.start")
    if not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()

        def save_metadata():
            if instance.initial_obdobi and instance.initial_obdobi != instance.obdobi:
                instance.initial_obdobi.save_metadata(fedora_transaction)
                logger.debug("heslo.signals.save_metadata_heslar_hierarchie.save_metadata",
                             extra={"transaction": fedora_transaction})
            instance.obdobi.save_metadata(fedora_transaction, close_transaction=True)
        transaction.on_commit(save_metadata)
        logger.debug("heslo.signals.save_metadata_heslar_hierarchie.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_save, sender=HeslarDokumentTypMaterialRada)
def save_metadata_heslar_dokument_typ_material_rada(sender, instance: HeslarDokumentTypMaterialRada, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.
    """
    logger.debug("heslo.signals.save_metadata_heslar_dokument_typ_material_rada.start")
    if not instance.suppress_signal:
        if created:
            def save_metadata():
                fedora_transaction = FedoraTransaction()
                instance.dokument_typ.save_metadata(fedora_transaction)
                instance.dokument_material.save_metadata(fedora_transaction)
                instance.dokument_rada.save_metadata(fedora_transaction, close_transaction=True)
                logger.debug("heslo.signals.save_metadata_heslar_dokument_typ_material_rada.save_metadata",
                             extra={"transaction": getattr(fedora_transaction, "uid", None)})
            transaction.on_commit(save_metadata)
    logger.debug("heslo.signals.save_metadata_heslar_dokument_typ_material_rada.end")


@receiver(post_save, sender=HeslarOdkaz)
def save_metadata_heslar_odkaz(sender, instance: HeslarOdkaz, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - odkaz.
    """
    logger.debug("heslo.signals.save_metadata_heslar_odkaz.start")
    if not instance.suppress_signal:
        def save_metadata():
            fedora_transaction = FedoraTransaction()
            if instance.initial_heslo and instance.initial_heslo != instance.heslo:
                heslo = Heslar.objects.get(pk=instance.initial_heslo.pk)
                heslo.save_metadata(fedora_transaction)
            heslo = Heslar.objects.get(pk=instance.heslo.pk)
            heslo.save_metadata(fedora_transaction)
            fedora_transaction.mark_transaction_as_closed()
            logger.debug("heslo.signals.save_metadata_heslar_odkaz.save_medata",
                         extra={"transaction": getattr(fedora_transaction, "uid", None),
                                "initial_heslo": getattr(instance.initial_heslo, "ident_cely", None),
                                "heslo": getattr(instance.initial_heslo, "ident_cely", None)})
        transaction.on_commit(save_metadata)
        logger.debug("heslo.signals.save_metadata_heslar_odkaz.end")


@receiver(pre_delete, sender=Heslar)
def heslar_delete_repository_container(sender, instance: Heslar, **kwargs):
    logger.debug("heslo.signals.heslar_delete_repository_container.start")
    fedora_transaction = FedoraTransaction()
    transaction.on_commit(lambda: instance.record_deletion(fedora_transaction, close_transaction=True))
    logger.debug("heslo.signals.heslar_delete_repository_container.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(pre_delete, sender=RuianKatastr)
def ruian_katastr_delete_repository_container(sender, instance: RuianKatastr, **kwargs):
    logger.debug("heslo.signals.ruian_katastr_delete_repository_container.start")
    fedora_transaction = get_or_create_transaction(instance)
    transaction.on_commit(lambda: instance.record_deletion(fedora_transaction, close_transaction=True))
    logger.debug("heslo.signals.ruian_katastr_delete_repository_container.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(pre_delete, sender=RuianKraj)
def ruian_kraj_delete_repository_container(sender, instance: RuianKraj, **kwargs):
    logger.debug("heslo.signals.ruian_kraj_delete_repository_container.start")
    fedora_transaction = get_or_create_transaction(instance)
    transaction.on_commit(lambda: instance.record_deletion(fedora_transaction, close_transaction=True))
    logger.debug("heslo.signals.ruian_kraj_delete_repository_container.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(pre_delete, sender=RuianOkres)
def ruian_okres_delete_repository_container(sender, instance: RuianOkres, **kwargs):
    logger.debug("heslo.signals.ruian_okres_delete_repository_container.start")

    def save_metadata():
        fedora_transaction = get_or_create_transaction(instance)
        instance.record_deletion(fedora_transaction, close_transaction=True)
        logger.debug("heslo.signals.ruian_okres_delete_repository_container.end",
                     extra={"transaction": getattr(fedora_transaction, "uid", None)})
    transaction.on_commit(save_metadata)


@receiver(post_delete, sender=HeslarHierarchie)
def delete_uppdate_related_heslar_hierarchie(sender, instance: HeslarHierarchie, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - hierarchie.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_hierarchie.start")
    fedora_transaction = FedoraTransaction()

    def save_metadata():
        instance.heslo_podrazene.save_metadata(fedora_transaction)
        instance.heslo_nadrazene.save_metadata(fedora_transaction, close_transaction=True)
    transaction.on_commit(save_metadata)
    logger.debug("heslo.signals.delete_uppdate_related_heslar_hierarchie.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_delete, sender=HeslarDokumentTypMaterialRada)
def delete_uppdate_related_heslar_dokument_typ_material_rada(sender, instance: HeslarDokumentTypMaterialRada, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - dokument typ materiál řada.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_dokument_typ_material_rada.start")
    fedora_transaction = FedoraTransaction()

    def save_metadata():
        instance.dokument_rada.save_metadata(fedora_transaction)
        instance.dokument_typ.save_metadata(fedora_transaction)
        instance.dokument_material.save_metadata(fedora_transaction, close_transaction=True)

    transaction.on_commit(save_metadata)
    logger.debug("heslo.signals.delete_uppdate_related_heslar_dokument_typ_material_rada.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_delete, sender=HeslarOdkaz)
def delete_uppdate_related_heslar_odkaz(sender, instance: HeslarOdkaz, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - odkaz.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_odkaz.start")
    fedora_transaction = FedoraTransaction()
    transaction.on_commit(lambda: instance.heslo.save_metadata(fedora_transaction, close_transaction=True))
    logger.debug("heslo.signals.delete_uppdate_related_heslar_odkaz.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None)})


@receiver(post_delete, sender=HeslarDatace)
def delete_uppdate_related_heslar_datace(sender, instance: HeslarDatace, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - datace.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_datace.start")
    fedora_transaction = FedoraTransaction()
    heslo_obdobi = instance.obdobi

    def save_metadata():
        heslo_obdobi.datace_obdobi = None
        heslo_obdobi.save_metadata(fedora_transaction, close_transaction=True)
    transaction.on_commit(save_metadata)
    logger.debug("heslo.signals.delete_uppdate_related_heslar_datace.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None)})
