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
    logger.debug("dj.signals.create_dokumentacni_jednotka.start")
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
        if instance.pian is not None:
            instance.pian.save_metadata()
        if instance.initial_pian is not None:
            instance.initial_pian.save_metadata()
    instance.archeologicky_zaznam.save_metadata()


@receiver(pre_delete, sender=DokumentacniJednotka)
def delete_dokumentacni_jednotka(sender, instance: DokumentacniJednotka, **kwargs):
    logger.debug("dj.signals.delete_dokumentacni_jednotka.start")
    pian: Pian = instance.pian
    if not pian:
        logger.debug("dj.signals.delete_dokumentacni_jednotka.no_pian", extra={"ident_cely": instance.ident_cely})
        return
    dj_query = DokumentacniJednotka.objects.filter(pian=pian).filter(~Q(ident_cely=instance.ident_cely))
    if pian.ident_cely.startswith("N-") and not dj_query.exists():
        logger.debug("dj.signals.delete_dokumentacni_jednotka.delete", extra={"ident_cely": pian.ident_cely})
        if hasattr(instance, "deleted_by_user") and instance.deleted_by_user is not None:
            pian.deleted_by_user = instance.deleted_by_user
        pian.delete()
    instance.archeologicky_zaznam.save_metadata()
    logger.debug("dj.signals.delete_dokumentacni_jednotka.end")
