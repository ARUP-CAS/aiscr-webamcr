import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from services.mailer import Mailer
from uzivatel.models import User, UserNotificationType

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def create_ident_cely(sender, instance, **kwargs):
    # check if the updated fields exist and if you're not creating a new object
    if not kwargs['update_fields'] and instance.id:
        # Save it, so it can be used in post_save
        instance.old = User.objects.get(id=instance.id)
    if instance.pk is None:
        instance.model_is_updated = False
        logger.debug("Running create_ident_cely receiver ...")
        if not instance.ident_cely:
            users = User.objects.all().order_by("-ident_cely")
            if users.count() > 0:
                last_user = users.first()
                dash_index = last_user.ident_cely.rfind("-")
                number = int(last_user.ident_cely[dash_index + 1:]) + 1
                instance.ident_cely = "U-" + "{0}".format(str(number)).zfill(6)
            else:
                instance.ident_cely = "U-000001"


@receiver(post_save, sender=User)
def send_deactivation_email(sender, instance: User, **kwargs):
    if not kwargs.get('update_fields') and hasattr(instance, 'old'):
        kwargs['update_fields'] = []
        if (instance.is_active != instance.old.is_active):
            kwargs['update_fields'].append('is_active')
    if (kwargs['update_fields']):
        if 'is_active' in kwargs['update_fields'] and instance.is_active == False:
            Mailer.sendEU03(user=instance)


@receiver(post_save, sender=User)
def send_new_user_email_to_admin(sender, instance: User, **kwargs):
    if (kwargs.get('created') == True) and instance.created_from_admin_panel == False:
        Mailer.sendEU04(user=instance)


@receiver(post_save, sender=User)
def send_account_confirmed_email(sender, instance: User, **kwargs):
    if kwargs.get('created') == True and instance.created_from_admin_panel == True:
        Mailer.sendEU02(user=instance)


# @receiver(post_save, sender=User)
# def some(sender, instance: User, **kwargs):
#     old = instance.old
#     x = '777'
