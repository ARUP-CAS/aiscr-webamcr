import logging

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from neidentakce.models import NeidentAkce


logger = logging.getLogger(__name__)


@receiver(post_save, sender=NeidentAkce)
def neident_akce_post_save(sender, instance: NeidentAkce, **kwargs):
    if instance.dokument_cast and instance.dokument_cast.dokument:
        instance.dokument_cast.dokument.save_metadata()


@receiver(pre_delete, sender=NeidentAkce)
def neident_akce_post_save(sender, instance: NeidentAkce, **kwargs):
    if instance.dokument_cast and instance.dokument_cast.dokument:
        instance.dokument_cast.dokument.save_metadata()
