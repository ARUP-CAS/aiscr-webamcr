import asyncio
import inspect
import logging
from typing import Optional

from cacheops import invalidate_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver

from adb.models import Adb
from arch_z.models import ArcheologickyZaznam, ExterniOdkaz, Akce, ExterniZdroj
from core.constants import ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE
from core.repository_connector import FedoraTransaction
from cron.tasks import update_single_redis_snapshot
from dj.models import DokumentacniJednotka
from historie.models import HistorieVazby, Historie
from komponenta.models import KomponentaVazby, Komponenta
from nalez.models import NalezPredmet, NalezObjekt
from pian.models import Pian
from projekt.models import Projekt
from xml_generator.models import UPDATE_REDIS_SNAPSHOT, check_if_task_queued

logger = logging.getLogger(__name__)


def invalidate_arch_z_related_models():
    invalidate_model(Akce)
    invalidate_model(ArcheologickyZaznam)
    invalidate_model(Historie)
    invalidate_model(Adb)
    invalidate_model(Pian)
    invalidate_model(NalezPredmet)
    invalidate_model(NalezObjekt)
    invalidate_model(DokumentacniJednotka)
    invalidate_model(Komponenta)
    invalidate_model(Projekt)


@receiver(pre_save, sender=ArcheologickyZaznam, weak=False)
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


@receiver(post_save, sender=ArcheologickyZaznam, weak=False)
def create_arch_z_metadata(sender, instance: ArcheologickyZaznam, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    logger.debug("arch_z.signals.create_arch_z_metadata.start", extra={"record_pk": instance.pk})

    invalidate_arch_z_related_models()
    fedora_transaction = instance.active_transaction
    if instance.initial_pristupnost is not None and instance.pristupnost.id != instance.initial_pristupnost.id:
        dj_list = list(instance.dokumentacni_jednotky_akce.all())
    else:
        dj_list = []
    if instance.initial_stav != instance.stav:
        adb_list = [x.adb for x in instance.dokumentacni_jednotky_akce.all() if x.has_adb()]
    else:
        adb_list = []
    async def run_save_metadata_tasks():
        tasks = []
        if not instance.suppress_signal:
            if instance.initial_pristupnost is not None and instance.pristupnost.id != instance.initial_pristupnost.id:
                for dok_jednotka in dj_list:
                    dok_jednotka: DokumentacniJednotka
                    if dok_jednotka.pian:
                        initial_pristupnost \
                            = dok_jednotka.pian.evaluate_pristupnost_change(instance.initial_pristupnost.id, instance.id)
                        pristupnost = dok_jednotka.pian.evaluate_pristupnost_change(instance.pristupnost.id, instance.id)
                        if initial_pristupnost.id != pristupnost.id and dok_jednotka.pian:
                            logger.debug("arch_z.signals.create_arch_z_metadata.update_pian_metadata",
                                         extra={"pian": dok_jednotka.pian.ident_cely,
                                                "initial_pripustnost": initial_pristupnost.pk,
                                                "pripustnost": pristupnost.pk})
                            tasks.append(dok_jednotka.pian.save_metadata(fedora_transaction))
                    if dok_jednotka.has_adb() and (instance.initial_stav != instance.stav
                                                   or instance.initial_pristupnost != instance.pristupnost):
                        tasks.append(dok_jednotka.adb.save_metadata(fedora_transaction))
            if instance.initial_stav != instance.stav:
                for adb in adb_list:
                    tasks.append(adb.save_metadata(fedora_transaction))
            try:
                if (instance.akce and instance.akce.projekt and
                        (instance.akce.initial_projekt is None or
                         instance.akce.projekt.ident_cely != instance.initial_projekt.ident_cely)):
                    tasks.append(instance.akce.projekt.save_metadata(fedora_transaction))
            except (ObjectDoesNotExist, AttributeError) as err:
                logger.debug("arch_z.signals.create_arch_z_metadata.no_akce",
                             extra={"record_ident_cely": instance.ident_cely, "err": err})
        await asyncio.gather(*tasks)
    close_transaction = instance.close_active_transaction_when_finished

    def save_metadata(inner_close_transaction=False):
        asyncio.run(run_save_metadata_tasks())
        asyncio.run(instance.save_metadata(fedora_transaction, close_transaction=inner_close_transaction))
    if close_transaction:
        transaction.on_commit(lambda: save_metadata(True))
    else:
        save_metadata()
    logger.debug("arch_z.signals.create_arch_z_metadata.end", extra={"record_pk": instance.pk,
                                                                     "transaction": fedora_transaction.uid})


@receiver(post_save, sender=Akce, weak=False)
def update_akce_snapshot(sender, instance: Akce, **kwargs):
    logger.debug("arch_z.signals.update_akce_snapshot.start", extra={"record_pk": instance.pk})
    if not check_if_task_queued("Akce", instance.pk, "update_single_redis_snapshot"):
        update_single_redis_snapshot.apply_async(["Akce", instance.pk], countdown=UPDATE_REDIS_SNAPSHOT)
    invalidate_arch_z_related_models()
    if not instance.suppress_signal:
        fedora_transaction: Optional[FedoraTransaction, None] = instance.active_transaction
        if instance.projekt is not None and instance.initial_projekt is None:
            instance.projekt.save_metadata(fedora_transaction)
        if instance.projekt is None and instance.initial_projekt is not None:
            instance.initial_projekt.save_metadata(fedora_transaction)
        if (instance.projekt is not None and instance.initial_projekt is not None
                and instance.projekt.ident_cely != instance.initial_projekt.ident_cely):
            instance.projekt.save_metadata(fedora_transaction)
            instance.initial_projekt.save_metadata(fedora_transaction)
        if instance.close_active_transaction_when_finished:
            fedora_transaction.mark_transaction_as_closed()
    logger.debug("arch_z.signals.update_akce_snapshot.end", extra={"record_pk": instance.pk})


@receiver(post_save, sender=ExterniOdkaz, weak=False)
def create_externi_odkaz_metadata(sender, instance: ExterniOdkaz, **kwargs):
    """
        Funkce pro aktualizaci metadat externího odkazu.
    """
    logger.debug("arch_z.signals.create_externi_odkaz_metadata.start", extra={"record_pk": instance.pk})
    invalidate_arch_z_related_models()
    if not instance.suppress_signal:
        fedora_transaction: FedoraTransaction = instance.active_transaction
        if instance.archeologicky_zaznam is not None:
            instance.archeologicky_zaznam.save_metadata(fedora_transaction)
        if instance.externi_zdroj is not None:
            instance.externi_zdroj.save_metadata(fedora_transaction)
        close_transaction = instance.close_active_transaction_when_finished
        if close_transaction:
            fedora_transaction.mark_transaction_as_closed()
        logger.debug("arch_z.signals.create_externi_odkaz_metadata.end", extra={"record_pk": instance.pk,
                                                                                "transaction": fedora_transaction})


@receiver(pre_delete, sender=ArcheologickyZaznam, weak=False)
def delete_arch_z_repository_container_and_connections(sender, instance: ArcheologickyZaznam, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    logger.debug("arch_z.signals.delete_arch_z_repository_container_and_connections.start",
                 extra={"record_ident_cely": instance.ident_cely})
    komponenty_jednotek_vazby = []
    for dj in instance.dokumentacni_jednotky_akce.all():
        dj: DokumentacniJednotka
        dj.suppress_signal = True
        if dj.komponenty:
            komponenty_jednotek_vazby.append(dj.komponenty)
    for komponenta_vazba in komponenty_jednotek_vazby:
        komponenta_vazba: KomponentaVazby
        for item in komponenta_vazba.komponenty.all():
            item.active_transaction = instance.active_transaction
            item.delete()
        komponenta_vazba.suppress_komponenta_signal = True
        komponenta_vazba.delete()
    logger.debug("arch_z.signals.delete_arch_z_repository_container_and_connections.end",
                 extra={"record_ident_cely": instance.ident_cely})


@receiver(post_delete, sender=ArcheologickyZaznam, weak=False)
def delete_arch_z_repository_update_connected_records(sender, instance: ArcheologickyZaznam, **kwargs):
    logger.debug("arch_z.signals.delete_arch_z_repository_update_connected_records.start",
                 extra={"record_ident": instance.ident_cely})
    fedora_transaction: FedoraTransaction = instance.active_transaction

    def save_metadata(close_transaction=False):
        invalidate_arch_z_related_models()
        try:
            if instance.akce and instance.akce.projekt is not None:
                instance.akce.projekt.save_metadata(fedora_transaction)
        except ObjectDoesNotExist as err:
            logger.debug("arch_z.signals.delete_arch_z_repository_container_and_connections.no_akce",
                         extra={"record_ident_cely": instance.ident_cely, "err": err})
        instance.record_deletion(fedora_transaction, close_transaction=close_transaction)

    if instance.close_active_transaction_when_finished:
        transaction.on_commit(lambda: save_metadata(True))
    else:
        save_metadata()
    logger.debug("arch_z.signals.delete_arch_z_repository_update_connected_records.end",
                 extra={"record_ident": instance.ident_cely, "transaction": transaction})


@receiver(post_delete, sender=ExterniOdkaz, weak=False)
def delete_externi_odkaz_repository_container(sender, instance: ExterniOdkaz, **kwargs):
    """
        Funkce pro aktualizaci metadat archeologického záznamu.
    """
    logger.debug("arch_z.signals.delete_externi_odkaz_repository_container.start",
                 extra={"record_pk": instance.pk, "suppress_signal_arch_z": instance.suppress_signal_arch_z})
    fedora_transaction = instance.active_transaction
    invalidate_model(ExterniZdroj)
    invalidate_arch_z_related_models()

    def save_metadata(inner_close_transaction=False):
        if instance.suppress_signal_arch_z is False and instance.archeologicky_zaznam is not None:
            instance.archeologicky_zaznam.save_metadata(fedora_transaction)
        if instance.externi_zdroj is not None:
            instance.externi_zdroj.save_metadata(fedora_transaction)
        if inner_close_transaction:
            fedora_transaction.mark_transaction_as_closed()
    close_transaction = instance.close_active_transaction_when_finished
    if close_transaction:
        transaction.on_commit(lambda: save_metadata(True))
    else:
        save_metadata()
    logger.debug("arch_z.signals.delete_externi_odkaz_repository_container.end",
                 extra={"record_pk": instance.pk, "suppress_signal_arch_z": instance.suppress_signal_arch_z,
                        "transaction": fedora_transaction.uid})
