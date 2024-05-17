import logging

from cacheops import invalidate_model, invalidate_all
from django.contrib.auth import user_logged_in
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed, pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from core.repository_connector import FedoraTransaction, FedoraRepositoryConnector
from heslar.signals import get_or_create_transaction
from historie.models import Historie
from services.mailer import Mailer
from uzivatel.models import Organizace, Osoba, User, UzivatelPrihlaseniLog
from rest_framework.authtoken.models import Token
from core.ident_cely import get_uzivatel_ident

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Organizace)
def orgnaizace_save_metadata(sender, instance: Organizace, **kwargs):
    logger.debug("uzivatel.signals.orgnaizace_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    fedora_transaction = get_or_create_transaction(instance)
    instance.save_metadata(fedora_transaction, close_transaction=True)
    logger.debug("uzivatel.signals.orgnaizace_save_metadata.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction})


@receiver(post_save, sender=Osoba)
def osoba_save_metadata(sender, instance: Osoba, **kwargs):
    logger.debug("uzivatel.signals.osoba_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    fedora_transaction = get_or_create_transaction(instance)
    instance.save_metadata(fedora_transaction, close_transaction=True)
    logger.debug("uzivatel.signals.osoba_save_metadata.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction})


@receiver(pre_save, sender=User)
def create_ident_cely(sender, instance: User, **kwargs):
    """
    Přidelení identu celý pro usera.
    """
    logger.debug("uzivatel.signals.create_ident_cely.start")
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
            instance.ident_cely = get_uzivatel_ident()
        if not FedoraRepositoryConnector.check_container_deleted_or_not_exists(instance.ident_cely, "uzivatel"):
            raise ValidationError(_("uzivatel.models.User.save.check_container_deleted_or_not_exists.invalid"))
        if not instance.active_transaction:
            instance.active_transaction = FedoraTransaction()
            instance.close_active_transaction_when_finished = True
            logger.debug("uzivatel.signals.create_ident_cely.create_transaction",
                         extra={"transaction": instance.active_transaction.uid})
    if kwargs["update_fields"] and len(kwargs["update_fields"]) == 1 and "last_login" in kwargs["update_fields"]:
        instance.suppress_signal = True
    logger.debug("uzivatel.signals.create_ident_cely.end", extra={"ident_cely": instance.ident_cely})


@receiver(post_save, sender=User)
def user_post_save_method(sender, instance: User, created: bool, **kwargs):
    invalidate_all()
    fedora_transaction = instance.active_transaction
    logger.debug("uzivatel.signals.user_post_save_method.start",
                 extra={"user": instance.ident_cely, "suppress_signal": instance.suppress_signal,
                        "transaction": getattr(fedora_transaction, "uid", None)})
    if not instance.suppress_signal:
        send_deactivation_email(sender, instance, **kwargs)
        send_account_confirmed_email(sender, instance, created)
        # Create or change token when user changed.
        try:
            old_token = Token.objects.get(user=instance)
        except Token.DoesNotExist:
            Token.objects.create(user=instance)
        else:
            old_token.delete()
            Token.objects.create(user=instance)
        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        else:
            instance.save_metadata(fedora_transaction)
        logger.debug("uzivatel.signals.user_post_save_method.end",
                     extra={"user": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)})


def send_deactivation_email(sender, instance: User, **kwargs):
    """
    Signál pro poslání deaktivačního emailu uživately.
    """
    logger.debug("uzivatel.signals.send_deactivation_email.start", extra={"user": instance.ident_cely})
    if not kwargs.get('update_fields') and hasattr(instance, 'old') and instance.old is not None:
        kwargs['update_fields'] = []
        if instance.is_active != instance.old.is_active:
            kwargs['update_fields'].append('is_active')
    if kwargs['update_fields']:
        if 'is_active' in kwargs['update_fields'] and instance.is_active is False:
            Mailer.send_eu03(user=instance)
    logger.debug("uzivatel.signals.send_deactivation_email.end", extra={"user": instance.ident_cely})


def send_account_confirmed_email(sender, instance: User, created):
    """
    signál pro zaslání emailu uživately o jeho konfirmaci.
    """
    logger.debug("uzivatel.signals.send_account_confirmed_email.start",
                 extra={"user": instance.ident_cely,"user_created": created,
                        "created_from_admin_panel": instance.created_from_admin_panel})
    if created is True and instance.created_from_admin_panel is True:
        Mailer.send_eu02(user=instance)
    logger.debug("uzivatel.signals.send_account_confirmed_email.end", extra={"user": instance.ident_cely})


@receiver(pre_delete, sender=User)
def delete_user_connections(sender, instance, *args, **kwargs):
    logger.debug("uzivatel.signals.delete_user_connections.start", extra={"ident_cely": instance.ident_cely})
    Historie.save_record_deletion_record(record=instance)
    fedora_transaction = FedoraTransaction()
    instance.save_metadata(fedora_transaction)
    if instance.history_vazba and instance.history_vazba.pk:
        instance.history_vazba.delete()
    instance.record_deletion(fedora_transaction)
    fedora_transaction.mark_transaction_as_closed()
    logger.debug("uzivatel.signals.delete_user_connections.end", extra={"ident_cely": instance.ident_cely,
                                                                        "transaction": fedora_transaction.uid})


@receiver(post_delete, sender=User)
def delete_profile(sender, instance: User, *args, **kwargs):
    """
    Signál pro zaslání emailu uživately o jeho smazání.
    """
    logger.debug("uzivatel.signals.delete_profile.start", extra={"ident_cely": instance.ident_cely})
    Mailer.send_eu03(user=instance)
    logger.debug("uzivatel.signals.delete_profile.end", extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=Osoba)
def osoba_delete_repository_container(sender, instance: Osoba, **kwargs):
    logger.debug("uzivatel.signals.osoba_delete_repository_container.start",
                 extra={"ident_cely": instance.ident_cely})
    fedora_transaction = get_or_create_transaction(instance)
    instance.record_deletion(fedora_transaction, close_transaction=True)
    logger.debug("uzivatel.signals.osoba_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": transaction})


@receiver(pre_delete, sender=Organizace)
def organizace_delete_repository_container(sender, instance: Organizace, **kwargs):
    logger.debug("uzivatel.signals.organizace_delete_repository_container.start",
                 extra={"ident_cely": instance.ident_cely})
    fedora_transaction = get_or_create_transaction(instance)
    instance.record_deletion(fedora_transaction, close_transaction=True)
    logger.debug("uzivatel.signals.organizace_delete_repository_container.end",
                 extra={"ident_cely": instance.ident_cely, "transaction": transaction})


@receiver(user_logged_in)
def log_user_signin(sender, user, request, **kwargs):
    # Get the IP address from the request object
    ip_address = request.META.get('REMOTE_ADDR', None)
    UzivatelPrihlaseniLog.objects.create(user=user, ip_adresa=ip_address)
