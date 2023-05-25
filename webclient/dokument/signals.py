import logging

from core.constants import DOKUMENT_CAST_RELATION_TYPE, DOKUMENT_RELATION_TYPE
from core.models import SouborVazby
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from dokument.models import Dokument, DokumentAutor, DokumentCast
from historie.models import HistorieVazby
from komponenta.models import KomponentaVazby

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Dokument)
def create_dokument_vazby(sender, instance, **kwargs):
    """
    Metóda pro vytvoření historických vazeb dokumentu.
    Metóda se volá pred uložením záznamu.
    """
    if instance.pk is None:
        logger.debug("dokument.signals.create_dokument_vazby.creating_history_for_dokument",
                     extra={"instance": instance})
        hv = HistorieVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        hv.save()
        instance.historie = hv
        sv = SouborVazby(typ_vazby=DOKUMENT_RELATION_TYPE)
        sv.save()
        instance.soubory = sv

@receiver(pre_save, sender=DokumentCast)
def create_dokument_cast_vazby(sender, instance, **kwargs):     
        """
        Metóda pro vytvoření komponent vazeb dokument části.
        Metóda se volá pred uložením dokument části.
        """   
        logger.debug("Creating child komponenty for dokument cast" + str(instance))
        k = KomponentaVazby(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
        k.save()
        instance.komponenty = k

