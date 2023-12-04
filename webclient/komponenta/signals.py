import logging

from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from dj.models import DokumentacniJednotka
from dokument.models import DokumentCast
from komponenta.models import KomponentaVazby, Komponenta

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=KomponentaVazby)
def delete_komponenta_vazby(sender, instance: KomponentaVazby, **kwargs):
    """
    Náhrada triggeru delete_connected_komponenta_vazby_relations.
    """
    logger.debug("komponenta.signals.delete_komponenta_vazby.start")
    Komponenta.objects.filter(komponenta_vazby=instance.id).delete()
    logger.debug("komponenta.signals.delete_komponenta_vazby.end")


@receiver(post_save, sender=Komponenta)
def komponenta_save(sender, instance: Komponenta, **kwargs):
    if instance.komponenta_vazby.navazany_objekt:
        navazany_objekt = instance.komponenta_vazby.navazany_objekt
        if isinstance(navazany_objekt, DokumentCast):
            navazany_objekt.dokument.save_metadata()
        elif isinstance(navazany_objekt, DokumentacniJednotka):
            navazany_objekt.archeologicky_zaznam.save_metadata()


@receiver(pre_delete, sender=Komponenta)
def komponenta_delete(sender, instance: Komponenta, **kwargs):
    if instance.komponenta_vazby.navazany_objekt:
        navazany_objekt = instance.komponenta_vazby.navazany_objekt
        if isinstance(navazany_objekt, DokumentCast):
            navazany_objekt.dokument.save_metadata()
        elif isinstance(navazany_objekt, DokumentacniJednotka):
            navazany_objekt.archeologicky_zaznam.save_metadata()
