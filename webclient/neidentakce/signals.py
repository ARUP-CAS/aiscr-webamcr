import logging

from core.repository_connector import FedoraTransaction
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from neidentakce.models import NeidentAkce

logger = logging.getLogger(__name__)


@receiver(post_save, sender=NeidentAkce, weak=False)
def neident_akce_post_save(sender, instance: NeidentAkce, **kwargs):
    """
    Provádí operaci neident akce post save.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``neident_akce_post_save``.
    :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``dokument_cast``, ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``neident_akce_post_save``.
    """
    if instance.dokument_cast and instance.dokument_cast.dokument and not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(
            lambda: instance.initial_dokument.save_metadata(fedora_transaction, close_transaction=True)
        )
        logger.debug(
            "neidentakce.signals.neident_akce_post_save.save_metadata.end",
            extra={"transaction": getattr(fedora_transaction, "uid", None)},
        )


@receiver(post_delete, sender=NeidentAkce, weak=False)
def neident_akce_post_delete(sender, instance: NeidentAkce, **kwargs):
    """
    Provádí operaci neident akce post delete.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``neident_akce_post_delete``.
    :param instance: Parametr ``instance`` předává se do volání ``on_commit()``, pracuje se s atributy ``dokument_cast``, ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``neident_akce_post_delete``.
    """
    if instance.dokument_cast and instance.dokument_cast.dokument and not instance.suppress_signal:
        fedora_transaction = FedoraTransaction()
        transaction.on_commit(
            lambda: instance.initial_dokument.save_metadata(fedora_transaction, close_transaction=True)
        )
        logger.debug(
            "neidentakce.signals.neident_akce_post_delete.save_metadata.end",
            extra={"transaction": getattr(fedora_transaction, "uid", None)},
        )
