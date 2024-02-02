import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver

from arch_z.models import ArcheologickyZaznam, ExterniOdkaz, Akce
from core.constants import ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE
from cron.tasks import update_single_redis_snapshot
from dokument.models import DokumentCast
from historie.models import HistorieVazby
from xml_generator.models import UPDATE_REDIS_SNAPSHOT, check_if_task_queued

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ArcheologickyZaznam)
def create_arch_z_vazby(sender, instance, **kwargs):
    """
        Metóda pro vytvoření historických vazeb arch záznamu.
        Metóda se volá pred uložením arch záznamu.
    """
    logger.debug("arch_z.signals.create_arch_z_vazby.start")
    if instance.pk is None:
        logger.debug(
            "arch_z.create_arch_z_vazby", extra={"instance": str(instance)})
        hv = HistorieVazby(typ_vazby=ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        logger.debug("arch_z.signals.create_arch_z_vazby.created_vazby", extra={"hv_pk": hv.pk})
    logger.debug("arch_z.signals.create_arch_z_vazby.end", extra={"record_pk": instance.pk})


@receiver(post_save, sender=ArcheologickyZaznam)
def create_arch_z_metadata(sender, instance: ArcheologickyZaznam, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    logger.debug("arch_z.signals.create_arch_z_metadata.start", extra={"record_pk": instance.pk})
    transaction = None
    if not instance.suppress_signal:
        transaction = instance.save_metadata()
        try:
            if instance.akce and instance.akce.projekt:
                instance.akce.projekt.save_metadata(transaction)
        except ObjectDoesNotExist as err:
            logger.debug("arch_z.signals.create_arch_z_metadata.no_akce",
                         extra={"record_ident_cely": instance.ident_cely, "err": err})
    if instance.initial_pristupnost is not None and instance.pristupnost.id != instance.initial_pristupnost.id:
        for dok_jednotka in instance.dokumentacni_jednotky_akce.all():
            if dok_jednotka.pian:
                initial_pristupnost \
                    = dok_jednotka.pian.evaluate_pristupnost_change(instance.initial_pristupnost.id, instance.id)
                pristupnost = dok_jednotka.pian.evaluate_pristupnost_change(instance.pristupnost.id, instance.id)
                if initial_pristupnost.id != pristupnost.id and dok_jednotka.pian:
                    logger.debug("arch_z.signals.create_arch_z_metadata.update_pian_metadata",
                                 extra={"pian": dok_jednotka.pian.ident_cely,
                                        "initial_pripustnost": initial_pristupnost.pk, "pripustnost": pristupnost.pk})
                    dok_jednotka.pian.save_metadata(transaction)
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("arch_z.signals.create_arch_z_metadata.end", extra={"record_pk": instance.pk,
                                                                     "transaction": transaction})


@receiver(post_save, sender=Akce)
def update_akce_snapshot(sender, instance: Akce, **kwargs):
    logger.debug("arch_z.signals.update_akce_snapshot.start", extra={"record_pk": instance.pk})
    if not check_if_task_queued("Akce", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["Akce", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    logger.debug("arch_z.signals.update_akce_snapshot.end", extra={"record_pk": instance.pk})


@receiver(post_save, sender=ExterniOdkaz)
def create_externi_odkaz_metadata(sender, instance: ExterniOdkaz, **kwargs):
    """
        Funkce pro aktualizaci metadat externího odkazu.
    """
    logger.debug("arch_z.signals.create_externi_odkaz_metadata.start", extra={"record_pk": instance.pk})
    transaction = None
    if instance.archeologicky_zaznam is not None:
        transaction = instance.archeologicky_zaznam.save_metadata()
    if instance.externi_zdroj is not None:
        if not transaction:
            instance.externi_zdroj.save_metadata(transaction)
        else:
            transaction = instance.externi_zdroj.save_metadata()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("arch_z.signals.create_externi_odkaz_metadata.end", extra={"record_pk": instance.pk,
                                                                            "transaction": transaction})


@receiver(pre_delete, sender=ArcheologickyZaznam)
def delete_arch_z_repository_container_and_connections(sender, instance: ArcheologickyZaznam, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    logger.debug("arch_z.signals.delete_arch_z_repository_container_and_connections.start",
                 extra={"record_ident_cely": instance.ident_cely})
    transaction = instance.record_deletion()
    try:
        if instance.akce and instance.akce.projekt is not None:
            instance.akce.projekt.save_metadata(transaction)
    except ObjectDoesNotExist as err:
        logger.debug("arch_z.signals.delete_arch_z_repository_container_and_connections.no_akce",
                     extra={"record_ident_cely": instance.ident_cely, "err": err})
    if instance.historie and instance.historie.pk:
        instance.historie.delete()
    komponenty_jednotek_vazby = []
    for dj in instance.dokumentacni_jednotky_akce.all():
        if dj.komponenty:
            komponenty_jednotek_vazby.append(dj.komponenty)
    for komponenta_vazba in komponenty_jednotek_vazby:
        komponenta_vazba.delete()
    if instance.externi_odkazy:
        for eo in instance.externi_odkazy.all():
            eo.suppress_signal_arch_z = True
            eo.delete()
    transaction.mark_transaction_as_closed()
    logger.debug("arch_z.signals.delete_arch_z_repository_container_and_connections.end",
                 extra={"record_ident_cely": instance.ident_cely, "transaction": transaction})


@receiver(pre_delete, sender=ArcheologickyZaznam)
def delete_arch_z_repository_update_connected_records(sender, instance: ArcheologickyZaznam, **kwargs):
    logger.debug("arch_z.signals.delete_arch_z_repository_update_connected_records.start",
                 extra={"record_ident": instance.ident_cely})
    transaction = None
    for item in instance.casti_dokumentu.all():
        item: DokumentCast
        if not transaction:
            transaction = item.dokument.save_metadata()
        else:
            item.dokument.save_metadata(transaction)
        transaction.mark_transaction_as_closed()
    logger.debug("arch_z.signals.delete_arch_z_repository_update_connected_records.end",
                 extra={"record_ident": instance.ident_cely, "transaction": transaction})


@receiver(post_delete, sender=ExterniOdkaz)
def delete_externi_odkaz_repository_container(sender, instance: ExterniOdkaz, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    logger.debug("arch_z.signals.delete_externi_odkaz_repository_container.start",
                 extra={"record_pk": instance.pk, "suppress_signal_arch_z": instance.suppress_signal_arch_z})
    if instance.suppress_signal_arch_z is False and instance.archeologicky_zaznam is not None:
        transaction = instance.archeologicky_zaznam.save_metadata()
    else:
        transaction = None
    if instance.externi_zdroj is not None:
        if transaction:
            instance.externi_zdroj.save_metadata(transaction)
        else:
            transaction = instance.externi_zdroj.save_metadata()
    if transaction:
        transaction.mark_transaction_as_closed()
    logger.debug("arch_z.signals.delete_externi_odkaz_repository_container.end",
                 extra={"record_pk": instance.pk, "suppress_signal_arch_z": instance.suppress_signal_arch_z,
                        "transaction": transaction})
