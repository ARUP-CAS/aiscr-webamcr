import logging

from django.contrib.auth.models import Group

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.dispatch import receiver

from services.mailer import Mailer
from uzivatel.models import User
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def create_ident_cely(sender, instance, **kwargs):
    """
    Přidelení identu celý pro usera.
    """
    if not kwargs['update_fields'] and instance.id:
        # Save it, so it can be used in post_save
        database_user_query = User.objects.filter(id=instance.id)
        if database_user_query.count() > 0:
            instance.old = database_user_query.first()
        else:
            instance.old = None
    if instance.pk is None:
        instance.model_is_updated = False
        logger.debug("uzivatel.signals.create_ident_cely.running_create_ident_cely_receiver")
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
def user_post_save_method(sender, instance: User, **kwargs):
    send_deactivation_email(sender, instance, **kwargs)
    send_new_user_email_to_admin(sender, instance, **kwargs)
    send_account_confirmed_email(sender, instance, **kwargs)
    # Create or change token when user changed.
    try:
        old_token = Token.objects.get(user=instance)
    except Token.DoesNotExist:
        Token.objects.create(user=instance)
    else:
        old_token.delete()
        Token.objects.create(user=instance)



def send_deactivation_email(sender, instance: User, **kwargs):
    """
    Signál pro poslání deaktivačního emailu uživately.
    """
    if not kwargs.get('update_fields') and hasattr(instance, 'old') and instance.old is not None:
        kwargs['update_fields'] = []
        if instance.is_active != instance.old.is_active:
            kwargs['update_fields'].append('is_active')
    if kwargs['update_fields']:
        if 'is_active' in kwargs['update_fields'] and instance.is_active is False:
            Mailer.send_eu03(user=instance)


def send_new_user_email_to_admin(sender, instance: User, **kwargs):
    """
    Signál pro zaslání info o nově registrovaném uživately adminovy.
    """
    if kwargs.get('created') is True and instance.created_from_admin_panel is False:
        Mailer.send_eu04(user=instance)


def send_account_confirmed_email(sender, instance: User, **kwargs):
    """
    signál pro zaslání emailu uživately o jeho konfirmaci.
    """
    if kwargs.get('created') is True and instance.created_from_admin_panel is True:
        Mailer.send_eu02(user=instance)


@receiver(post_delete, sender=User)
def delete_profile(sender, instance, *args, **kwargs):
    """
    Signál pro zaslání emailu uživately o jeho smazání.
    """
    Mailer.send_eu03(user=instance)
