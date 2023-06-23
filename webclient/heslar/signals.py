import logging

from django.db.models.signals import post_save
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
    """
    Funkce pro uložení metadat okresu.
    """
    instance.save_metadata()
