import logging

from cacheops import invalidate_model
from django.db import transaction
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from arch_z.models import ArcheologickyZaznam
from core.constants import DOKUMENTACNI_JEDNOTKA_RELATION_TYPE, DOKUMENT_CAST_RELATION_TYPE
from core.repository_connector import FedoraTransaction
from dj.models import DokumentacniJednotka
from dokument.models import DokumentCast, Dokument
from komponenta.models import KomponentaVazby, Komponenta

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=KomponentaVazby)
def delete_komponenta_vazby(sender, instance: KomponentaVazby, **kwargs):
    """
    Náhrada triggeru delete_connected_komponenta_vazby_relations.
    """
    logger.debug("komponenta.signals.delete_komponenta_vazby.start")
    Komponenta.objects.filter(komponenta_vazby=instance.id).delete()
    logger.debug("komponenta.signals.delete_komponenta_vazby.end")


@receiver(post_save, sender=Komponenta)
def komponenta_save(sender, instance: Komponenta, **kwargs):
    logger.debug("komponenta.signals.komponenta_save.start", extra={"pk": instance.pk})
    if instance.komponenta_vazby.typ_vazby == DOKUMENTACNI_JEDNOTKA_RELATION_TYPE:
        invalidate_model(ArcheologickyZaznam)
    elif instance.komponenta_vazby.typ_vazby == DOKUMENT_CAST_RELATION_TYPE:
        invalidate_model(Dokument)
    fedora_transaction = instance.active_transaction
    close_transaction = instance.close_active_transaction_when_finished
    if instance.komponenta_vazby.navazany_objekt:
        navazany_objekt = instance.komponenta_vazby.navazany_objekt
        if isinstance(navazany_objekt, DokumentCast):
            navazany_objekt.dokument.save_metadata(fedora_transaction, close_transaction=close_transaction)
        elif isinstance(navazany_objekt, DokumentacniJednotka):
            navazany_objekt.archeologicky_zaznam.save_metadata(fedora_transaction, close_transaction=close_transaction)
    logger.debug("komponenta.signals.komponenta_save.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None), "pk": instance.pk})


@receiver(pre_delete, sender=Komponenta)
def komponenta_delete(sender, instance: Komponenta, **kwargs):
    logger.debug("komponenta.signals.komponenta_delete.start", extra={"pk": instance.pk})
    if instance.komponenta_vazby.typ_vazby == DOKUMENTACNI_JEDNOTKA_RELATION_TYPE:
        invalidate_model(ArcheologickyZaznam)
    elif instance.komponenta_vazby.typ_vazby == DOKUMENT_CAST_RELATION_TYPE:
        invalidate_model(Dokument)
    fedora_transaction: FedoraTransaction = instance.active_transaction
    close_transaction = instance.close_active_transaction_when_finished
    if instance.komponenta_vazby.navazany_objekt:
        navazany_objekt = instance.komponenta_vazby.navazany_objekt
        def save_metadata():
            if isinstance(navazany_objekt, DokumentCast):
                navazany_objekt.dokument.save_metadata(fedora_transaction)
            elif isinstance(navazany_objekt, DokumentacniJednotka):
                navazany_objekt.archeologicky_zaznam.save_metadata(fedora_transaction)
            if close_transaction:
                fedora_transaction.mark_transaction_as_closed()

        if close_transaction:
            transaction.on_commit(save_metadata)
        else:
            save_metadata()
    logger.debug("komponenta.signals.komponenta_delete.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None), "pk": instance.pk})
