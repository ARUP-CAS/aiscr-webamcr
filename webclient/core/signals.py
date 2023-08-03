import logging

from core.models import Soubor
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from dokument.models import Dokument, Let
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Soubor)
def soubor_save_update_record_metadata(sender, instance: Soubor, **kwargs):
    if instance.vazba is not None and isinstance(instance.vazba.navazany_objekt, ModelWithMetadata) \
            and instance.suppress_signal is False:
        instance.vazba.navazany_objekt.save_metadata()


@receiver(post_delete, sender=Soubor)
def soubor_save_update_record_metadata(sender, instance: Soubor, **kwargs):
    if instance.vazba is not None and isinstance(instance.vazba.navazany_objekt, ModelWithMetadata):
        instance.vazba.navazany_objekt.save_metadata()
