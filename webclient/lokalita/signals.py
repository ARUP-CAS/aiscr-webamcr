from django.db.models.signals import pre_save
from django.dispatch import receiver

from lokalita.models import Lokalita


@receiver(pre_save, sender=Lokalita)
def create_ez_vazby(sender, instance: Lokalita, **kwargs):
    instance.set_snapshots()
