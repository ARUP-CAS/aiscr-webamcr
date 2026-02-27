import logging

from arch_z.signals import invalidate_arch_z_related_models
from core.repository_connector import FedoraTransaction
from dj.models import DokumentacniJednotka
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from dokument.models import DokumentCast
from komponenta.models import Komponenta

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Komponenta, weak=False)
def komponenta_save(sender, instance: Komponenta, **kwargs):
    """Provádí operaci komponenta save.

    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek provedené operace."""
    logger.debug("komponenta.signals.komponenta_save.start", extra={"pk": instance.pk})
    if instance.suppress_signal:
        logger.debug("komponenta.signals.komponenta_save.suppress_signal", extra={"pk": instance.pk})
        return
    invalidate_arch_z_related_models()
    fedora_transaction = instance.active_transaction
    close_transaction = instance.close_active_transaction_when_finished
    if instance.komponenta_vazby.navazany_objekt:
        navazany_objekt = instance.komponenta_vazby.navazany_objekt
        if isinstance(navazany_objekt, DokumentCast):
            if close_transaction:
                transaction.on_commit(
                    lambda: navazany_objekt.dokument.save_metadata(fedora_transaction, close_transaction=True)
                )
            else:
                navazany_objekt.dokument.save_metadata(fedora_transaction)
        elif isinstance(navazany_objekt, DokumentacniJednotka):
            if close_transaction:
                transaction.on_commit(
                    lambda: navazany_objekt.archeologicky_zaznam.save_metadata(
                        fedora_transaction, close_transaction=True
                    )
                )
            else:
                navazany_objekt.archeologicky_zaznam.save_metadata(fedora_transaction)
    logger.debug(
        "komponenta.signals.komponenta_save.end",
        extra={"transaction": getattr(fedora_transaction, "uid", None), "pk": instance.pk},
    )


@receiver(post_delete, sender=Komponenta, weak=False)
def komponenta_delete(sender, instance: Komponenta, **kwargs):
    """Provádí operaci komponenta delete.

    :param sender: Vstupní hodnota ``sender`` pro danou operaci.
    :param instance: Vstupní hodnota ``instance`` pro danou operaci.
    :param kwargs: Dodatečné pojmenované argumenty předané voláním.
    :return: Vrací výsledek provedené operace."""
    logger.debug("komponenta.signals.komponenta_delete.start", extra={"pk": instance.pk})
    if instance.suppress_signal:
        logger.debug("komponenta.signals.komponenta_delete.suppress_signal", extra={"pk": instance.pk})
        return
    invalidate_arch_z_related_models()
    fedora_transaction: FedoraTransaction = instance.active_transaction
    close_transaction = instance.close_active_transaction_when_finished
    if instance.komponenta_vazby.navazany_objekt:
        navazany_objekt = instance.komponenta_vazby.navazany_objekt

        def save_metadata():
            """Uloží metadata.

            :return: Vrací výsledek provedené operace."""
            if isinstance(navazany_objekt, DokumentCast):
                navazany_objekt.dokument.save_metadata(fedora_transaction, skip_container_check=True)
            elif isinstance(navazany_objekt, DokumentacniJednotka):
                navazany_objekt.archeologicky_zaznam.save_metadata(fedora_transaction, skip_container_check=True)
            if close_transaction:
                fedora_transaction.mark_transaction_as_closed()

        if close_transaction:
            transaction.on_commit(save_metadata)
        else:
            save_metadata()
    logger.debug(
        "komponenta.signals.komponenta_delete.end",
        extra={"transaction": getattr(fedora_transaction, "uid", None), "pk": instance.pk},
    )
