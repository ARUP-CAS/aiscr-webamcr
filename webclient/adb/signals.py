import logging

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from adb.models import Adb, VyskovyBod

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Adb)
def adb_save_metadata(sender, instance: Adb, **kwargs):
    if not instance.suppress_signal:
        instance.save_metadata()
        instance.dokumentacni_jednotka.archeologicky_zaznam.save_metadata()


@receiver(pre_delete, sender=Adb)
def adb_delete_repository_container(sender, instance: Adb, **kwargs):
    instance.record_deletion()
    instance.dokumentacni_jednotka.archeologicky_zaznam.save_metadata()


@receiver(pre_delete, sender=VyskovyBod)
def vyskovy_bod_delete_repository_container(sender, instance: VyskovyBod, **kwargs):
    instance.adb.save_metadata()

