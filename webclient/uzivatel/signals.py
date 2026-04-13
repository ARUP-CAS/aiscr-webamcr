import logging

from core.constants import ROLE_BADATEL_ID
from core.ident_cely import get_uzivatel_ident
from core.log_middleware import LogMiddleware
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
from django.contrib.auth import user_logged_in
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from heslar.signals import get_or_create_transaction
from historie.models import Historie
from rest_framework.authtoken.models import Token
from services.mailer import Mailer
from uzivatel.models import NotificationsLog, Organizace, Osoba, User, UzivatelPrihlaseniLog

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Organizace, weak=False)
def orgnaizace_save_metadata(sender, instance: Organizace, **kwargs):
    """
    Provádí operaci orgnaizace save metadata.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``orgnaizace_save_metadata``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``get_or_create_transaction()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``orgnaizace_save_metadata``.
    """
    logger.debug("uzivatel.signals.orgnaizace_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    if not instance.suppress_signal:
        fedora_transaction = get_or_create_transaction(instance)
        instance.save_metadata(fedora_transaction, close_transaction=True)
        logger.debug(
            "uzivatel.signals.orgnaizace_save_metadata.end",
            extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction},
        )


@receiver(post_save, sender=Osoba, weak=False)
def osoba_save_metadata(sender, instance: Osoba, **kwargs):
    """
    Provádí operaci osoba save metadata.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``osoba_save_metadata``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``get_or_create_transaction()``, pracuje se s atributy ``ident_cely``, ``suppress_signal``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``osoba_save_metadata``.
    """
    logger.debug("uzivatel.signals.osoba_save_metadata.start", extra={"ident_cely": instance.ident_cely})
    if not instance.suppress_signal:
        fedora_transaction = get_or_create_transaction(instance)
        instance.save_metadata(fedora_transaction, close_transaction=True)
        logger.debug(
            "uzivatel.signals.osoba_save_metadata.end",
            extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction},
        )


@receiver(pre_save, sender=User, weak=False)
def create_ident_cely(sender, instance: User, **kwargs):
    """
    Přidelení identu celý pro usera.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``create_ident_cely``.
    :param instance: Parametr ``instance`` předává se do volání ``filter()``, ``check_container_deleted_or_not_exists()``, pracuje se s atributy ``id``, ``old``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` se předává do volání ``len()``, ovlivňuje větvení podmínek.

        :raises ValidationError: Vyvolá se při splnění podmínky ``not FedoraRepositoryConnector.check_container_deleted_or_not_exists(instance.ident_cely, 'uzivatel')``.
    """
    logger.debug("uzivatel.signals.create_ident_cely.start")
    if not kwargs["update_fields"] and instance.id:
        # Uloží jej, aby šel použít v `post_save`.
        database_user_query = User.objects.filter(id=instance.id)
        if database_user_query.count() > 0:
            instance.old = database_user_query.first()
        else:
            instance.old = None
    if instance.pk is None:
        instance.model_is_being_created = True
        logger.debug("uzivatel.signals.create_ident_cely.running_create_ident_cely_receiver")
        if not instance.ident_cely:
            instance.ident_cely = get_uzivatel_ident()
        if not FedoraRepositoryConnector.check_container_deleted_or_not_exists(instance.ident_cely, "uzivatel"):
            raise ValidationError(_("uzivatel.models.User.save.check_container_deleted_or_not_exists.invalid"))
        if not instance.active_transaction:
            instance.active_transaction = FedoraTransaction()
            instance.close_active_transaction_when_finished = True
            logger.debug(
                "uzivatel.signals.create_ident_cely.create_transaction",
                extra={"transaction": instance.active_transaction.uid},
            )
    if kwargs["update_fields"] and len(kwargs["update_fields"]) == 1 and "last_login" in kwargs["update_fields"]:
        instance.suppress_signal = True
    logger.debug("uzivatel.signals.create_ident_cely.end", extra={"ident_cely": instance.ident_cely})


@receiver(post_save, sender=User, weak=False)
def user_post_save_method(sender, instance: User, created: bool, **kwargs):
    """
    Provádí operaci user post save method.

    :param sender: Parametr ``sender`` se předává do volání ``send_deactivation_email()``, ``send_account_confirmed_email()``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``send_deactivation_email()``, pracuje se s atributy ``active_transaction``, ``ident_cely``, ovlivňuje větvení podmínek.
    :param created: Parametr ``created`` předává se do volání ``send_account_confirmed_email()``.
    :param kwargs: Parametr ``kwargs`` se předává do volání ``send_deactivation_email()``.
    """
    fedora_transaction = instance.active_transaction
    logger.debug(
        "uzivatel.signals.user_post_save_method.start",
        extra={
            "ident_cely": instance.ident_cely,
            "signal": instance.suppress_signal,
            "transaction": getattr(fedora_transaction, "uid", None),
        },
    )
    if instance.model_is_being_created and not instance.is_active:
        group = Group.objects.get(pk=ROLE_BADATEL_ID)
        instance.groups.set([group], clear=True)
    if not instance.suppress_signal:

        def check_password_change():
            """
            Ověří password change.

            :return: Vrací výsledek ověření nebo validačního pravidla.
            """
            if created:
                return False
            try:
                old_instance = User.objects.get(pk=instance.pk)
            except ObjectDoesNotExist:
                return False
            return not check_password(instance.password, old_instance.password)

        send_deactivation_email(sender, instance, **kwargs)
        send_account_confirmed_email(sender, instance, created)
        # Vytvoří nebo změní token při změně uživatele.
        try:
            old_token = Token.objects.get(user=instance)
        except Token.DoesNotExist:
            Token.objects.create(user=instance)
        else:
            old_token.delete()
            Token.objects.create(user=instance)
        if instance.active_transaction is None and check_password_change():
            instance.active_transaction = FedoraTransaction()
            instance.close_active_transaction_when_finished = True
        if instance.close_active_transaction_when_finished:
            transaction.on_commit(lambda: instance.save_metadata(fedora_transaction, close_transaction=True))
        else:
            instance.save_metadata(fedora_transaction)
        logger.debug(
            "uzivatel.signals.user_post_save_method.end",
            extra={"ident_cely": instance.ident_cely, "transaction": getattr(fedora_transaction, "uid", None)},
        )


def send_deactivation_email(sender, instance: User, **kwargs):
    """
    Signál pro poslání deaktivačního emailu uživately.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``send_deactivation_email``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``hasattr()``, pracuje se s atributy ``ident_cely``, ``old``, ovlivňuje větvení podmínek.
    :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``, ovlivňuje větvení podmínek.
    """
    logger.debug("uzivatel.signals.send_deactivation_email.start", extra={"ident_cely": instance.ident_cely})
    if not kwargs.get("update_fields") and hasattr(instance, "old") and instance.old is not None:
        kwargs["update_fields"] = []
        if instance.is_active != instance.old.is_active:
            kwargs["update_fields"].append("is_active")
    if kwargs["update_fields"]:
        if "is_active" in kwargs["update_fields"] and instance.is_active is False:
            Mailer.send_eu03(user=instance)
    logger.debug("uzivatel.signals.send_deactivation_email.end", extra={"ident_cely": instance.ident_cely})


def send_account_confirmed_email(sender, instance: User, created):
    """
    signál pro zaslání emailu uživately o jeho konfirmaci.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``send_account_confirmed_email``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``send_eu02()``, pracuje se s atributy ``ident_cely``, ``created_from_admin_panel``, ovlivňuje větvení podmínek.
    :param created: Parametr ``created`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.
    """
    logger.debug(
        "uzivatel.signals.send_account_confirmed_email.start",
        extra={
            "ident_cely": instance.ident_cely,
            "custom_created": created,
            "option": instance.created_from_admin_panel,
        },
    )
    if created is True and instance.created_from_admin_panel is True:
        Mailer.send_eu02(user=instance)
    logger.debug("uzivatel.signals.send_account_confirmed_email.end", extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=User, weak=False)
def delete_user_connections(sender, instance, *args, **kwargs):
    """
    Odstraní user connections.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_user_connections``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``save_record_deletion_record()``, pracuje se s atributy ``ident_cely``, ``deleted_by_user``, ovlivňuje větvení podmínek.
    :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``delete_user_connections``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_user_connections``.
    """
    logger.debug("uzivatel.signals.delete_user_connections.start", extra={"ident_cely": instance.ident_cely})
    instance.deleted_by_user = User.objects.filter(ident_cely=LogMiddleware.get_user_id()).first()
    Historie.save_record_deletion_record(record=instance)
    transaction_created = False
    if instance.active_transaction:
        fedora_transaction = instance.active_transaction
    else:
        fedora_transaction = FedoraTransaction()
        instance.active_transaction = fedora_transaction
        transaction_created = True
    instance.save_metadata(fedora_transaction)
    if transaction_created:
        instance.close_active_transaction_when_finished = True
    logger.debug(
        "uzivatel.signals.delete_user_connections.end",
        extra={"ident_cely": instance.ident_cely},
    )


@receiver(post_delete, sender=User, weak=False)
def delete_profile(sender, instance: User, *args, **kwargs):
    """
    Signál pro zaslání emailu uživately o jeho smazání.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``delete_profile``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``send_eu03()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ovlivňuje větvení podmínek.
    :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``delete_profile``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``delete_profile``.
    """
    logger.debug("uzivatel.signals.delete_profile.start", extra={"ident_cely": instance.ident_cely})
    Mailer.send_eu03(user=instance)
    NotificationsLog.objects.filter(user=instance).update(user=None)
    fedora_transaction = instance.active_transaction
    if instance.history_vazba and instance.history_vazba.pk:
        instance.history_vazba.delete()
    instance.record_deletion(fedora_transaction)
    if instance.close_active_transaction_when_finished:
        transaction.on_commit(lambda: fedora_transaction.mark_transaction_as_closed())
    logger.debug("uzivatel.signals.delete_profile.end", extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=Osoba, weak=False)
def osoba_delete_repository_container(sender, instance: Osoba, **kwargs):
    """
    Zaznamená smazání osoby v repozitáři před odstraněním záznamu z databáze.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``osoba_delete_repository_container``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ``close_active_transaction_when_finished``, ``record_deletion``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``osoba_delete_repository_container``.
    """
    logger.debug("uzivatel.signals.osoba_delete_repository_container.start", extra={"ident_cely": instance.ident_cely})
    if instance.active_transaction:
        fedora_transaction = instance.active_transaction
    else:
        fedora_transaction = FedoraTransaction()
        instance.active_transaction = fedora_transaction
        instance.close_active_transaction_when_finished = True
    instance.record_deletion(fedora_transaction)
    logger.debug(
        "uzivatel.signals.osoba_delete_repository_container.end",
        extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction.uid},
    )


@receiver(post_delete, sender=Osoba, weak=False)
def osoba_close_repository_transaction(sender, instance: Osoba, **kwargs):
    """
    Uzavře Fedora transakci po potvrzení smazání osoby v databázi.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``osoba_close_repository_transaction``.
    :param instance: Parametr ``instance`` pracuje se s atributy ``ident_cely``, ``close_active_transaction_when_finished``, ``active_transaction``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``osoba_close_repository_transaction``.
    """
    logger.debug("uzivatel.signals.osoba_close_repository_transaction.start", extra={"ident_cely": instance.ident_cely})
    if instance.close_active_transaction_when_finished:
        fedora_transaction = instance.active_transaction
        transaction.on_commit(lambda: fedora_transaction.mark_transaction_as_closed())
    logger.debug("uzivatel.signals.osoba_close_repository_transaction.end", extra={"ident_cely": instance.ident_cely})


@receiver(pre_delete, sender=Organizace, weak=False)
def organizace_delete_repository_container(sender, instance: Organizace, **kwargs):
    """
    Zaznamená smazání organizace v repozitáři před odstraněním záznamu z databáze.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``organizace_delete_repository_container``.
    :param instance: Parametr ``instance`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``active_transaction``, ``close_active_transaction_when_finished``, ``record_deletion``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``organizace_delete_repository_container``.
    """
    logger.debug(
        "uzivatel.signals.organizace_delete_repository_container.start", extra={"ident_cely": instance.ident_cely}
    )
    if instance.active_transaction:
        fedora_transaction = instance.active_transaction
    else:
        fedora_transaction = FedoraTransaction()
        instance.active_transaction = fedora_transaction
        instance.close_active_transaction_when_finished = True
    instance.record_deletion(fedora_transaction)
    logger.debug(
        "uzivatel.signals.organizace_delete_repository_container.end",
        extra={"ident_cely": instance.ident_cely, "transaction": fedora_transaction.uid},
    )


@receiver(post_delete, sender=Organizace, weak=False)
def organizace_close_repository_transaction(sender, instance: Organizace, **kwargs):
    """
    Uzavře Fedora transakci po potvrzení smazání organizace v databázi.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``organizace_close_repository_transaction``.
    :param instance: Parametr ``instance`` pracuje se s atributy ``ident_cely``, ``close_active_transaction_when_finished``, ``active_transaction``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``organizace_close_repository_transaction``.
    """
    logger.debug(
        "uzivatel.signals.organizace_close_repository_transaction.start", extra={"ident_cely": instance.ident_cely}
    )
    if instance.close_active_transaction_when_finished:
        fedora_transaction = instance.active_transaction
        transaction.on_commit(lambda: fedora_transaction.mark_transaction_as_closed())
    logger.debug(
        "uzivatel.signals.organizace_close_repository_transaction.end", extra={"ident_cely": instance.ident_cely}
    )


@receiver(user_logged_in, weak=False)
def log_user_signin(sender, user, request, **kwargs):
    # Získá IP adresu z objektu request.
    """
    Provádí operaci log user signin.

    :param sender: Parametr ``sender`` slouží jako vstup pro logiku funkce ``log_user_signin``.
    :param user: Parametr ``user`` se předává do volání ``create()``.
    :param request: Parametr ``request`` pracuje se s atributy ``META``.
    :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``log_user_signin``.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0]
    else:
        ip_address = request.META.get("REMOTE_ADDR")
    UzivatelPrihlaseniLog.objects.create(user=user, ip_adresa=ip_address)
