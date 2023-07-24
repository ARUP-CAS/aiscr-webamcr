import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Heslar, RuianKatastr, RuianKraj, RuianOkres

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Heslar)
def save_metadata_heslar(sender, instance: Heslar, **kwargs):
    """
    Funkce pro uložení metadat hesláře.
    """
    instance.save_metadata()


@receiver(post_save, sender=RuianKatastr)
def save_metadata_katastr(sender, instance: RuianKatastr, **kwargs):
    """
    Funkce pro uložení metadat katastru.
    """
    instance.save_metadata()


@receiver(post_save, sender=RuianKraj)
def save_metadata_kraj(sender, instance: RuianKraj, **kwargs):
    """
    Funkce pro uložení metadat kraje.
    """
    instance.save_metadata()


@receiver(post_save, sender=RuianOkres)
def save_metadata_okres(sender, instance: RuianOkres, **kwargs):
    instance.save_metadata()


@receiver(post_delete, sender=Heslar)
def heslar_delete_repository_container(sender, instance: Heslar, **kwargs):
    instance.record_deletion()


@receiver(post_delete, sender=RuianKatastr)
def ruian_katastr_delete_repository_container(sender, instance: RuianKatastr, **kwargs):
    instance.record_deletion()


@receiver(post_delete, sender=RuianKraj)
def ruian_kraj_delete_repository_container(sender, instance: RuianKraj, **kwargs):
    instance.record_deletion()


@receiver(post_delete, sender=RuianOkres)
def ruian_okres_delete_repository_container(sender, instance: RuianOkres, **kwargs):
    instance.record_deletion()
