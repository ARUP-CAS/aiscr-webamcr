from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from notifikace_projekty.models import Pes


@receiver(post_save, sender=Pes)
def pes_save(sender, instance: Pes, **kwargs):
    if instance.user:
        transaction = instance.user.save_metadata()
        if transaction:
            transaction.mark_transaction_as_closed()


@receiver(pre_delete, sender=Pes)
def pes_delete(sender, instance: Pes, **kwargs):
    if instance.user:
        transaction = instance.user.save_metadata()
        if transaction:
            transaction.mark_transaction_as_closed()

