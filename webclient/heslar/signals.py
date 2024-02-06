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
    if not instance.ident_cely and not instance.pk:
        instance.ident_cely = get_heslar_ident()


@receiver(post_save, sender=Heslar)
def save_metadata_heslar(sender, instance: Heslar, **kwargs):
    """
    Funkce pro uložení metadat hesláře.
    """
    instance.save_metadata()


@receiver(post_save, sender=RuianKatastr)
def save_metadata_katastr(sender, instance: RuianKatastr, **kwargs):
    """
    Funkce pro uložení metadat katastru.
    """
    instance.save_metadata()


@receiver(post_save, sender=RuianKraj)
def save_metadata_kraj(sender, instance: RuianKraj, **kwargs):
    """
    Funkce pro uložení metadat kraje.
    """
    instance.save_metadata()


@receiver(post_save, sender=RuianOkres)
def save_metadata_okres(sender, instance: RuianOkres, **kwargs):
    instance.save_metadata()


@receiver(post_save, sender=HeslarHierarchie)
def save_metadata_heslar_hierarchie(sender, instance: HeslarHierarchie, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.
    """
    if hasattr(instance, "heslo_podrazene") and instance.heslo_podrazene:
        instance.heslo_podrazene.save_metadata()
    if hasattr(instance, "heslo_nadrazene") and instance.heslo_nadrazene:
        instance.heslo_nadrazene.save_metadata()
    if (hasattr(instance, "initial_heslo_nadrazene") and instance.initial_heslo_nadrazene
            and instance.heslo_nadrazene.pk != instance.initial_heslo_nadrazene.pk):
        instance.initial_heslo_nadrazene.save_metadata()
    if (hasattr(instance, "initial_heslo_podrazene") and instance.initial_heslo_podrazene
            and instance.heslo_podrazene.pk != instance.initial_heslo_podrazene.pk):
        instance.initial_heslo_podrazene.save_metadata()


@receiver(post_save, sender=HeslarDatace)
def save_metadata_heslar_hierarchie(sender, instance: HeslarDatace, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.
    """
    instance.obdobi.save_metadata()
    if (hasattr(instance, "initial_obdobi") and
            instance.initial_obdobi and instance.initial_obdobi != instance.obdobi):
        instance.initial_obdobi.save_metadata()

@receiver(post_save, sender=HeslarDokumentTypMaterialRada)
def save_metadata_heslar_dokument_typ_material_rada(sender, instance: HeslarDokumentTypMaterialRada, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - hierarchie.
    """
    if created:
        instance.dokument_rada.save_metadata()
        instance.dokument_typ.save_metadata()
        instance.dokument_material.save_metadata()


@receiver(post_save, sender=HeslarOdkaz)
def save_metadata_heslar_odkaz(sender, instance: HeslarOdkaz, created, **kwargs):
    """
    Funkce pro uložení metadat heslář - odkaz.
    """
    instance.heslo.save_metadata()
    if hasattr(instance, "initial_heslo") and instance.initial_heslo != instance.heslo:
        heslo = Heslar.objects.get(pk=instance.initial_heslo.pk)
        heslo.save_metadata()


@receiver(pre_delete, sender=Heslar)
def heslar_delete_repository_container(sender, instance: Heslar, **kwargs):
    instance.record_deletion()


@receiver(pre_delete, sender=RuianKatastr)
def ruian_katastr_delete_repository_container(sender, instance: RuianKatastr, **kwargs):
    instance.record_deletion()


@receiver(pre_delete, sender=RuianKraj)
def ruian_kraj_delete_repository_container(sender, instance: RuianKraj, **kwargs):
    instance.record_deletion()


@receiver(pre_delete, sender=RuianOkres)
def ruian_okres_delete_repository_container(sender, instance: RuianOkres, **kwargs):
    instance.record_deletion()


@receiver(post_delete, sender=HeslarHierarchie)
def delete_uppdate_related_heslar_hierarchie(sender, instance: HeslarHierarchie, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - hierarchie.
    """
    instance.heslo_podrazene.save_metadata()
    instance.heslo_nadrazene.save_metadata()


@receiver(post_delete, sender=HeslarDokumentTypMaterialRada)
def delete_uppdate_related_heslar_dokument_typ_material_rada(sender, instance: HeslarDokumentTypMaterialRada, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - dokument typ materiál řada.
    """
    instance.dokument_rada.save_metadata()
    instance.dokument_typ.save_metadata()
    instance.dokument_material.save_metadata()


@receiver(post_delete, sender=HeslarOdkaz)
def delete_uppdate_related_heslar_odkaz(sender, instance: HeslarOdkaz, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - odkaz.
    """
    instance.heslo.save_metadata()


@receiver(post_delete, sender=HeslarDatace)
def delete_uppdate_related_heslar_datace(sender, instance: HeslarDatace, **kwargs):
    """
    Funkce pro uložení metadat navázaného hesláře při smazání heslář - datace.
    """
    instance.obdobi.save_metadata()
