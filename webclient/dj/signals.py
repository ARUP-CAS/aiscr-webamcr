import logging

import structlog
from django.core.exceptions import ObjectDoesNotExist

from core.constants import DOKUMENT_RELATION_TYPE, PIAN_POTVRZEN, KLADYZM10, KLADYZM50, PIAN_PRESNOST_KATASTR
from core.models import SouborVazby
from django.db.models.signals import post_save
from django.dispatch import receiver

from dj.models import DokumentacniJednotka
from heslar.hesla import GEOMETRY_PLOCHA
from heslar.models import RuianKatastr, Heslar
from historie.models import HistorieVazby
from pian.models import Pian, Kladyzm

logger = logging.getLogger(__name__)
logger_s = structlog.get_logger(__name__)


@receiver(post_save, sender=DokumentacniJednotka)
def create_dokumentacni_jednotka(sender, instance, created, **kwargs):
    logger_s.debug("dj.signals.create_dokumentacni_jednotka.start")
    instance: DokumentacniJednotka
    if created and instance.pian is None:
        logger_s.debug("dj.signals.create_dokumentacni_jednotka.not_localized")
        ruian_katastr: RuianKatastr = instance.archeologicky_zaznam.hlavni_katastr
        if ruian_katastr.pian is not None:
            pian = ruian_katastr.pian
            instance.pian = pian
            instance.save()
            logger_s.debug("dj.signals.create_dokumentacni_jednotka.finined", dj_pk=instance.pk)
        else:
            zm10s = (
                Kladyzm.objects.filter(kategorie=KLADYZM10)
                .filter(the_geom__contains=ruian_katastr.definicni_bod)
            )
            zm50s = (
                Kladyzm.objects.filter(kategorie=KLADYZM50)
                .filter(the_geom__contains=ruian_katastr.definicni_bod)
            )
            if len(zm10s) == 0:
                logger_s.error("dj.signals.create_dokumentacni_jednotka.zm10s.not_found")
                return
            if len(zm50s) == 0:
                logger_s.error("dj.signals.create_dokumentacni_jednotka.zm50s.not_found")
                return
            zm10s = zm10s.first()
            zm50s = zm50s.first()
            try:
                geom = ruian_katastr.hranice
                presnost = Heslar.objects.get(pk=PIAN_PRESNOST_KATASTR)
                typ = Heslar.objects.get(pk=GEOMETRY_PLOCHA)
                pian = Pian(stav=PIAN_POTVRZEN, zm10=zm10s, zm50=zm50s, typ=typ, presnost=presnost, geom=geom)
                pian.set_permanent_ident_cely()
                pian.save()
                ruian_katastr.pian = pian.pk
                ruian_katastr.save()
                instance.pian = pian
                instance.save()
                logger_s.debug("dj.signals.create_dokumentacni_jednotka.finined", dj_pk=instance.pk)
            except ObjectDoesNotExist as err:
                logger_s.error("dj.signals.create_dokumentacni_jednotka.ObjectDoesNotExist", err=err)
