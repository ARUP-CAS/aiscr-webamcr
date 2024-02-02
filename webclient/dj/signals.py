import logging

from django.db.models import Q
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from dj.models import DokumentacniJednotka
from heslar.models import RuianKatastr
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
    transaction = None
    if created and instance.typ.id == TYP_DJ_KATASTR and instance.pian is None:
        logger.debug("dj.signals.create_dokumentacni_jednotka.not_localized")
        ruian_katastr: RuianKatastr = instance.archeologicky_zaznam.hlavni_katastr
        if ruian_katastr.pian is not None:
            pian = ruian_katastr.pian
            instance.pian = pian
            instance.save()
            logger.debug("dj.signals.create_dokumentacni_jednotka.finined", extra={'dj_pk': instance.pk})

        else:
            try:
                instance.pian = vytvor_pian(ruian_katastr)
                instance.save()
                logger.debug("dj.signals.create_dokumentacni_jednotka.finined", extra={"dj_pk": instance.pk})
            except Exception as e:
                logger.debug("pian not created")
    elif instance.pian != instance.initial_pian:
        logger.debug("dj.signals.create_dokumentacni_jednotka.update_pian", extra={
            "pian_db": instance.initial_pian.ident_cely if instance.initial_pian else "None",
            "pian": instance.pian.ident_cely if instance.pian else "None",
        })
        transaction = None
        if instance.pian is not None:
            transaction = instance.pian.save_metadata()
        if instance.initial_pian is not None:
            if transaction:
                instance.initial_pian.save_metadata(transaction)
            else:
                transaction = instance.initial_pian.save_metadata()
    if transaction:
        instance.archeologicky_zaznam.save_metadata(transaction)
    else:
        transaction = instance.archeologicky_zaznam.save_metadata()
    transaction.mark_transaction_as_closed()
    logger.debug("dj.signals.create_dokumentacni_jednotka.end", extra={"transaction": transaction})


@receiver(pre_delete, sender=DokumentacniJednotka)
def delete_dokumentacni_jednotka(sender, instance: DokumentacniJednotka, **kwargs):
    logger.debug("dj.signals.delete_dokumentacni_jednotka.start", extra={"ident_cely": instance.ident_cely})
    pian: Pian = instance.pian
    transaction = None
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
            pian.delete()
        else:
            logger.debug("dj.signals.delete_dokumentacni_jednotka.update_pian_metadata",
                         extra={"ident_cely": instance.ident_cely, "pian_ident_cely": pian.ident_cely})
            transaction = pian.save_metadata()
    if instance.komponenty:
        instance.komponenty.delete()
    if transaction:
        instance.archeologicky_zaznam.save_metadata(transaction)
    else:
        transaction = instance.archeologicky_zaznam.save_metadata()
    transaction.mark_transaction_as_closed()
    logger.debug("dj.signals.delete_dokumentacni_jednotka.end", extra={"ident_cely": instance.ident_cely,
                                                                       "transaction": transaction})
