import logging



from django.db.models.signals import post_save
from django.dispatch import receiver

from dj.models import DokumentacniJednotka
from heslar.models import RuianKatastr
from pian.models import vytvor_pian
from heslar.hesla import TYP_DJ_KATASTR

logger = logging.getLogger(__name__)


@receiver(post_save, sender=DokumentacniJednotka)
def create_dokumentacni_jednotka(sender, instance, created, **kwargs):
    logger.debug("dj.signals.create_dokumentacni_jednotka.start")
    instance: DokumentacniJednotka
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
