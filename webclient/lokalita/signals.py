from django.db.models.signals import post_save
from django.dispatch import receiver

from lokalita.models import Lokalita


@receiver(post_save, sender=Lokalita)
def create_ez_vazby(sender, instance: Lokalita, **kwargs):
    instance.set_snapshots()
