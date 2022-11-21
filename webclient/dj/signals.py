import logging

from core.constants import DOKUMENT_RELATION_TYPE, PIAN_POTVRZEN
from core.models import SouborVazby
from django.db.models.signals import pre_save
from django.dispatch import receiver

from dj.models import DokumentacniJednotka
from historie.models import HistorieVazby
from pian.models import Pian

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=DokumentacniJednotka)
def create_dokumentacni_jednotka(sender, instance, created, **kwargs):
    instance: DokumentacniJednotka
    if created and instance.pian is None:
        ruian_katastr = instance.archeologicky_zaznam.hlavni_katastr
        if ruian_katastr.pian is not None:
            pian = ruian_katastr.pian

        else:
            pian = Pian(stav=PIAN_POTVRZEN, zm10=ruian_katastr.definicni_bod)
            pian.save()
        instance.pian = pian
        instance.save()
