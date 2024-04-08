import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver

from arch_z.models import ArcheologickyZaznam
from core.repository_connector import FedoraTransaction
from dj.models import DokumentacniJednotka
from dokument.models import DokumentCast, Dokument
from nalez.models import NalezObjekt, NalezPredmet

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=NalezObjekt)
def delete_nalez_objekt(sender, instance: NalezObjekt, **kwargs):
    logger.debug("nalez.signals.delete_nalez_objekt.start", extra={"pk": instance.pk})
    fedora_transaction: FedoraTransaction = instance.active_transaction
    if isinstance(instance.komponenta.komponenta_vazby.navazany_objekt, DokumentacniJednotka):
        logger.debug("nalez.signals.delete_nalez_objekt.dokumentacni_jednotka",
                     extra={"pk": instance.pk, "transaction": fedora_transaction.uid,
                            "close_transaction": instance.close_active_transaction_when_finished})
        arch_z = instance.komponenta.komponenta_vazby.navazany_objekt.archeologicky_zaznam
        arch_z: ArcheologickyZaznam
        arch_z.save_metadata(fedora_transaction, close_transaction=instance.close_active_transaction_when_finished)
    if isinstance(instance.komponenta.komponenta_vazby.navazany_objekt, DokumentCast):
        logger.debug("nalez.signals.delete_nalez_objekt.dokument_cast",
                     extra={"pk": instance.pk, "transaction": fedora_transaction.uid,
                            "close_transaction": instance.close_active_transaction_when_finished})
        navazany_objekt = instance.komponenta.komponenta_vazby.navazany_objekt
        if navazany_objekt.dokument:
            navazany_objekt.dokument.save_metadata(fedora_transaction,
                                                   close_transaction=instance.close_active_transaction_when_finished)
    logger.debug("nalez.signals.delete_nalez_objekt.start",
                 extra={"pk": instance.pk, "transaction": fedora_transaction.uid})


@receiver(post_delete, sender=NalezPredmet)
def delete_nalez_predmet(sender, instance: NalezObjekt, **kwargs):
    logger.debug("nalez.signals.delete_nalez_predmet.start", extra={"pk": instance.pk})
    fedora_transaction: FedoraTransaction = instance.active_transaction
    if isinstance(instance.komponenta.komponenta_vazby.navazany_objekt, DokumentacniJednotka):
        logger.debug("nalez.signals.delete_nalez_predmet.dokumentacni_jednotka",
                     extra={"pk": instance.pk, "transaction": fedora_transaction.uid,
                            "close_transaction": instance.close_active_transaction_when_finished})
        arch_z = instance.komponenta.komponenta_vazby.navazany_objekt.archeologicky_zaznam
        arch_z: ArcheologickyZaznam
        arch_z.save_metadata(fedora_transaction, close_transaction=instance.close_active_transaction_when_finished)
    if isinstance(instance.komponenta.komponenta_vazby.navazany_objekt, DokumentCast):
        logger.debug("nalez.signals.delete_nalez_predmet.dokument_cast",
                     extra={"pk": instance.pk, "transaction": fedora_transaction.uid,
                            "close_transaction": instance.close_active_transaction_when_finished})
        navazany_objekt = instance.komponenta.komponenta_vazby.navazany_objekt
        if navazany_objekt.dokument:
            navazany_objekt.dokument.save_metadata(fedora_transaction,
                                                   close_transaction=instance.close_active_transaction_when_finished)
    logger.debug("nalez.signals.delete_nalez_predmet.start",
                 extra={"pk": instance.pk, "transaction": fedora_transaction.uid})