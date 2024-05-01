import logging

from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from core.repository_connector import FedoraTransaction
from dj.models import DokumentacniJednotka
from heslar.models import RuianKatastr
from komponenta.models import Komponenta
from pian.models import vytvor_pian, Pian
from heslar.hesla_dynamicka import TYP_DJ_KATASTR

logger = logging.getLogger(__name__)


@receiver(post_save, sender=DokumentacniJednotka)
def save_dokumentacni_jednotka(sender, instance: DokumentacniJednotka, created, **kwargs):
    """
        Metóda pro vytvoření pianu z katastru arch záznamu.
        Metóda se volá po uložením DJ.
    """
    logger.debug("dj.signals.create_dokumentacni_jednotka.start", extra={"ident_cely": instance.ident_cely})
    fedora_transaction: FedoraTransaction = instance.active_transaction
    close_transaction = instance.close_active_transaction_when_finished
    if created and instance.typ.id == TYP_DJ_KATASTR and instance.pian is None:
        logger.debug("dj.signals.create_dokumentacni_jednotka.not_localized")
        ruian_katastr: RuianKatastr = instance.archeologicky_zaznam.hlavni_katastr
        if ruian_katastr.pian is not None:
            pian = ruian_katastr.pian
            instance.pian = pian
            instance.close_active_transaction_when_finished = False
            instance.save()
            logger.debug("dj.signals.create_dokumentacni_jednotka.finined",
                         extra={'dj_pk': instance.pk, "transaction": getattr(fedora_transaction, "uid", None)})
        else:
            try:
                instance.pian = vytvor_pian(ruian_katastr, fedora_transaction)
                instance.close_active_transaction_when_finished = False
                instance.save()
                logger.debug("dj.signals.create_dokumentacni_jednotka.finined",
                             extra={"dj_pk": instance.pk, "transaction": getattr(fedora_transaction, "uid", None)})
            except Exception as err:
                logger.debug("dj.signals.create_dokumentacni_jednotka.not_created",
                             extra={"err": err, "transaction": getattr(fedora_transaction, "uid", None)})
    elif instance.pian != instance.initial_pian:
        logger.debug("dj.signals.create_dokumentacni_jednotka.update_pian", extra={
            "pian_db": instance.initial_pian.ident_cely if instance.initial_pian else "None",
            "pian": instance.pian.ident_cely if instance.pian else "None",
            "transaction": fedora_transaction.uid
        })
        if instance.pian is not None:
            instance.pian.save_metadata(fedora_transaction)
        if instance.initial_pian is not None:
            instance.initial_pian.save_metadata(fedora_transaction)

    def arch_z_save_metadata(inner_close_transaction=False):
        instance.archeologicky_zaznam.save_metadata(fedora_transaction)
        if inner_close_transaction:
            fedora_transaction.mark_transaction_as_closed()
    if created or instance.tracker.changed():
        if close_transaction:
            transaction.on_commit(lambda: arch_z_save_metadata(True))
        else:
            arch_z_save_metadata()
    elif close_transaction:
        transaction.on_commit(lambda: fedora_transaction.mark_transaction_as_closed())
    logger.debug("dj.signals.create_dokumentacni_jednotka.end",
                 extra={"transaction": getattr(fedora_transaction, "uid", None),
                        "close_transaction": instance.close_active_transaction_when_finished})


@receiver(pre_delete, sender=DokumentacniJednotka)
def delete_dokumentacni_jednotka(sender, instance: DokumentacniJednotka, **kwargs):
    logger.debug("dj.signals.delete_dokumentacni_jednotka.start", extra={"ident_cely": instance.ident_cely})
    fedora_transaction = instance.active_transaction
    pian: Pian = instance.pian
    save_pian_metadata = False
    if not pian:
        logger.debug("dj.signals.delete_dokumentacni_jednotka.no_pian", extra={"ident_cely": instance.ident_cely})
    else:
        dj_query = DokumentacniJednotka.objects.filter(pian=pian).filter(~Q(ident_cely=instance.ident_cely))
        if pian.ident_cely.startswith("N-") and not dj_query.exists():
            logger.debug("dj.signals.delete_dokumentacni_jednotka.delete",
                         extra={"ident_cely": instance.ident_cely, "pian_ident_cely": pian.ident_cely})
            instance.pian = None
            instance.suppress_signal = True
            instance.save()
            instance.suppress_signal = False
            if hasattr(instance, "deleted_by_user") and instance.deleted_by_user is not None:
                pian.deleted_by_user = instance.deleted_by_user
            pian.suppress_signal = True
            pian.record_deletion(fedora_transaction)
            pian.delete()
        else:
            logger.debug("dj.signals.delete_dokumentacni_jednotka.update_pian_metadata",
                         extra={"ident_cely": instance.ident_cely, "pian_ident_cely": pian.ident_cely})
            save_pian_metadata = True
    if instance.komponenty:
        for komponenta in instance.komponenty.komponenty.all():
            komponenta: Komponenta
            for objekt in komponenta.objekty.all():
                objekt.active_transaction = fedora_transaction
                objekt.delete()
            for predmet in komponenta.predmety.all():
                predmet.active_transaction = fedora_transaction
                predmet.delete()
            komponenta.active_transaction = fedora_transaction
            komponenta.delete()
        instance.komponenty.delete()
    if instance.close_active_transaction_when_finished:
        def save_metadata():
            instance.archeologicky_zaznam.save_metadata(fedora_transaction)
            if save_pian_metadata:
                pian.save_metadata(fedora_transaction)
            fedora_transaction.mark_transaction_as_closed()

        transaction.on_commit(save_metadata)
    else:
        instance.archeologicky_zaznam.save_metadata(fedora_transaction)
    logger.debug("dj.signals.delete_dokumentacni_jednotka.end", extra={"ident_cely": instance.ident_cely,
                                                                       "transaction": fedora_transaction.uid})
