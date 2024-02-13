import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver

from core.ident_cely import get_heslar_ident
from .models import Heslar, RuianKatastr, RuianKraj, RuianOkres, HeslarDatace, HeslarHierarchie, \
    HeslarDokumentTypMaterialRada, HeslarOdkaz

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Heslar)
def save_ident_cely(sender, instance: Heslar, **kwargs):
    """
    Funkce pro uložení metadat hesláře.
    """
    logger.debug("heslo.signals.save_ident_cely.start")
    if not instance.ident_cely and not instance.pk:
        instance.ident_cely = get_heslar_ident()
        logger.debug("heslo.signals.save_ident_cely.ident_cely", extra={"ident_cely": instance.ident_cely})
    logger.debug("heslo.signals.save_ident_cely.end")


@receiver(post_save, sender=Heslar)
def save_metadata_heslar(sender, instance: Heslar, **kwargs):
    """
    Funkce pro uložení metadat hesláře.
    """
    logger.debug("heslo.signals.save_metadata_heslar.start")
    transaction = instance.save_metadata()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.save_metadata_heslar.end", extra={"transaction": transaction})


@receiver(post_save, sender=RuianKatastr)
def save_metadata_katastr(sender, instance: RuianKatastr, **kwargs):
    """
    Funkce pro uložení metadat katastru.
    """
    logger.debug("heslo.signals.save_metadata_katastr.start")
    transaction = instance.save_metadata()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.save_metadata_katastr.end", extra={"transaction": transaction})


@receiver(post_save, sender=RuianKraj)
def save_metadata_kraj(sender, instance: RuianKraj, **kwargs):
    """
    Funkce pro uložení metadat kraje.
    """
    logger.debug("heslo.signals.save_metadata_kraj.start")
    transaction = instance.save_metadata()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.save_metadata_kraj.end", extra={"transaction": transaction})


@receiver(post_save, sender=RuianOkres)
def save_metadata_okres(sender, instance: RuianOkres, **kwargs):
    logger.debug("heslo.signals.save_metadata_okres.start")
    transaction = instance.save_metadata()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.save_metadata_okres.end", extra={"transaction": transaction})


@receiver(post_save, sender=HeslarHierarchie)
def save_metadata_heslar_hierarchie(sender, instance: HeslarHierarchie, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.
    """
    logger.debug("heslo.signals.save_metadata_heslar_hierarchie.start")
    transaction = None
    if instance.heslo_podrazene:
        transaction = instance.heslo_podrazene.save_metadata(transaction)
    if instance.heslo_nadrazene:
        transaction = instance.heslo_nadrazene.save_metadata(transaction)
    if instance.initial_heslo_nadrazene and instance.heslo_nadrazene.pk != instance.initial_heslo_nadrazene.pk:
        transaction = instance.initial_heslo_nadrazene.save_metadata(transaction)
    if instance.initial_heslo_podrazene and instance.heslo_podrazene.pk != instance.initial_heslo_podrazene.pk:
        transaction = instance.initial_heslo_podrazene.save_metadata(transaction)
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.save_metadata_heslar_hierarchie.end", extra={"transaction": transaction})


@receiver(post_save, sender=HeslarDatace)
def save_metadata_heslar_hierarchie(sender, instance: HeslarDatace, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.
    """
    logger.debug("heslo.signals.save_metadata_heslar_hierarchie.start")
    transaction = instance.obdobi.save_metadata()
    if instance.initial_obdobi and instance.initial_obdobi != instance.obdobi:
        transaction = instance.initial_obdobi.save_metadata(transaction)
        logger.debug("heslo.signals.save_metadata_heslar_hierarchie.save_metadata",
                     extra={"transaction": transaction})
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.save_metadata_heslar_hierarchie.end")


@receiver(post_save, sender=HeslarDokumentTypMaterialRada)
def save_metadata_heslar_dokument_typ_material_rada(sender, instance: HeslarDokumentTypMaterialRada, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.
    """
    logger.debug("heslo.signals.save_metadata_heslar_dokument_typ_material_rada.start")
    if created:
        transaction = instance.dokument_rada.save_metadata()
        transaction = instance.dokument_typ.save_metadata(transaction)
        transaction = instance.dokument_material.save_metadata(transaction)
        if transaction:
            transaction.mark_transaction_as_closed()
        logger.debug("heslo.signals.save_metadata_heslar_dokument_typ_material_rada.save_metadata",
                     extra={"transaction": transaction})
    logger.debug("heslo.signals.save_metadata_heslar_dokument_typ_material_rada.end")


@receiver(post_save, sender=HeslarOdkaz)
def save_metadata_heslar_odkaz(sender, instance: HeslarOdkaz, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - odkaz.
    """
    logger.debug("heslo.signals.save_metadata_heslar_odkaz.start")
    transaction = instance.heslo.save_metadata()
    if instance.initial_heslo != instance.heslo:
        heslo = Heslar.objects.get(pk=instance.initial_heslo.pk)
        transaction = heslo.save_metadata(transaction)
        if transaction:
            transaction.mark_transaction_as_closed()
        logger.debug("heslo.signals.save_metadata_heslar_odkaz.save_medata", extra={"transaction": transaction})
    logger.debug("heslo.signals.save_metadata_heslar_odkaz.end")


@receiver(pre_delete, sender=Heslar)
def heslar_delete_repository_container(sender, instance: Heslar, **kwargs):
    logger.debug("heslo.signals.heslar_delete_repository_container.start")
    transaction = instance.record_deletion()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.heslar_delete_repository_container.end", extra={"transaction": transaction})


@receiver(pre_delete, sender=RuianKatastr)
def ruian_katastr_delete_repository_container(sender, instance: RuianKatastr, **kwargs):
    logger.debug("heslo.signals.ruian_katastr_delete_repository_container.start")
    transaction = instance.record_deletion()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.ruian_katastr_delete_repository_container.end", extra={"transaction": transaction})


@receiver(pre_delete, sender=RuianKraj)
def ruian_kraj_delete_repository_container(sender, instance: RuianKraj, **kwargs):
    logger.debug("heslo.signals.ruian_kraj_delete_repository_container.start")
    transaction = instance.record_deletion()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.ruian_kraj_delete_repository_container.end", extra={"transaction": transaction})


@receiver(pre_delete, sender=RuianOkres)
def ruian_okres_delete_repository_container(sender, instance: RuianOkres, **kwargs):
    logger.debug("heslo.signals.ruian_okres_delete_repository_container.start")
    transaction = instance.record_deletion()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.ruian_okres_delete_repository_container.end", extra={"transaction": transaction})


@receiver(post_delete, sender=HeslarHierarchie)
def delete_uppdate_related_heslar_hierarchie(sender, instance: HeslarHierarchie, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - hierarchie.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_hierarchie.start")
    transaction = instance.heslo_podrazene.save_metadata()
    instance.heslo_nadrazene.save_metadata(transaction)
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.delete_uppdate_related_heslar_hierarchie.end", extra={"transaction": transaction})


@receiver(post_delete, sender=HeslarDokumentTypMaterialRada)
def delete_uppdate_related_heslar_dokument_typ_material_rada(sender, instance: HeslarDokumentTypMaterialRada, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - dokument typ materiál řada.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_dokument_typ_material_rada.start")
    transaction = instance.dokument_rada.save_metadata()
    instance.dokument_typ.save_metadata(transaction)
    instance.dokument_material.save_metadata(transaction)
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.delete_uppdate_related_heslar_dokument_typ_material_rada.end",
                 extra={"transaction": transaction})


@receiver(post_delete, sender=HeslarOdkaz)
def delete_uppdate_related_heslar_odkaz(sender, instance: HeslarOdkaz, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - odkaz.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_odkaz.start")
    transaction = instance.heslo.save_metadata()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.delete_uppdate_related_heslar_odkaz.end", extra={"transaction": transaction})


@receiver(post_delete, sender=HeslarDatace)
def delete_uppdate_related_heslar_datace(sender, instance: HeslarDatace, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - datace.
    """
    logger.debug("heslo.signals.delete_uppdate_related_heslar_datace.start")
    transaction = instance.obdobi.save_metadata()
    transaction.mark_transaction_as_closed()
    logger.debug("heslo.signals.delete_uppdate_related_heslar_datace.end", extra={"transaction": transaction})
