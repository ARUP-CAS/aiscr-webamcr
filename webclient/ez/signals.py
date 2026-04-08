import logging

from cacheops import invalidate_model
from core.constants import EXTERNI_ZDROJ_RELATION_TYPE
from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from historie.models import HistorieVazby

from .models import ExterniZdroj

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ExterniZdroj, weak=False)
def create_ez_vazby(sender, instance: ExterniZdroj, **kwargs):
    """
    Metoda pro vytvoření historických vazeb externího zdroje.

    Metoda se volá pred uložením záznamu.

    :param sender: Třída modelu, který signál vyslal (ExterniZdroj).
    :param instance: Instance externího zdroje, pro niž se vytváří historická vazba při prvním uložení.
    :param kwargs: Dodatečné argumenty předávané signálem Django.
    """
    logger.debug("ez.signals.create_ez_vazby.start", extra={"ident_cely": instance.ident_cely})
    if instance.pk is None:
        logger.debug("ez.signals.create_ez_vazby", extra={"instance": instance})
        hv = HistorieVazby(typ_vazby=EXTERNI_ZDROJ_RELATION_TYPE)
        hv.save()
        instance.historie = hv
    try:
        instance.set_snapshots()
    except ValueError as err:
        logger.debug("ez.signals.create_ez_vazby.type_error", extra={"ident_cely": instance.ident_cely, "error": err})
    else:
        logger.debug("ez.signals.create_ez_vazby.end", extra={"ident_cely": instance.ident_cely})


@receiver(post_save, sender=ExterniZdroj, weak=False)
def externi_zdroj_save_metadata(sender, instance: ExterniZdroj, **kwargs):
    """
    Po uložení externího zdroje invaliduje cache a uloží metadata do Fedory, pokud není potlačen signál.

    :param sender: Třída modelu, který signál vyslal (ExterniZdroj).
    :param instance: Uložená instance externího zdroje, jejíž metadata se synchronizují s úložištěm.
    :param kwargs: Dodatečné argumenty předávané signálem Django.
    """
    logger.debug("ez.signals.externi_zdroj_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    invalidate_model(ExterniZdroj)
    if not instance.suppress_signal:
        fedora_transaction = instance.active_transaction
        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        else:
            instance.save_metadata(fedora_transaction)
        logger.debug(
            "ez.signals.externi_zdroj_save_metadata.save_medata",
            extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)},
        )
    logger.debug("ez.signals.externi_zdroj_save_metadata.end", extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=ExterniZdroj, weak=False)
def delete_externi_zdroj_repository_container(sender, instance: ExterniZdroj, **kwargs):
    """
    Odstraní externi zdroj repository container.

    :param sender: Třída modelu, který signál vyslal (ExterniZdroj).
    :param instance: Instance externího zdroje, který je před smazáním odstraněn z úložiště Fedora spolu s jeho externími odkazy a historií.
    :param kwargs: Dodatečné argumenty předávané signálem Django.
    """
    logger.debug(
        "ez.signals.delete_externi_zdroj_repository_container.start", extra={"ident_cely": instance.ident_cely}
    )
    fedora_transaction = instance.active_transaction
    invalidate_model(ExterniZdroj)
    instance.record_deletion(close_transaction=instance.close_active_transaction_when_finished)
    if instance.externi_odkazy_zdroje:
        for eo in instance.externi_odkazy_zdroje.all():
            eo.delete()
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    logger.debug(
        "ez.signals.delete_externi_zdroj_repository_container.end",
        extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)},
    )
