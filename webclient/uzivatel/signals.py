import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver
from uzivatel.models import AuthUser

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=AuthUser)
def create_ident_cely(sender, instance, **kwargs):
    if instance.pk is None:
        logger.debug("Running create_ident_cely receiver ...")
        if not instance.ident_cely:
            users = AuthUser.objects.all().order_by("-ident_cely")
            if users.count() > 0:
                last_user = users.first()
                dash_index = last_user.ident_cely.rfind("-")
                number = int(last_user.ident_cely[dash_index + 1 :]) + 1
                instance.ident_cely = "U-" + "{0}".format(str(number)).zfill(6)
            else:
                instance.ident_cely = "U-000001"
