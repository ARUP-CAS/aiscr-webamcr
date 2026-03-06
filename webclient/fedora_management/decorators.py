import logging
from functools import wraps

from core.repository_connector import FedoraError
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)


def handle_fedora_error(view_func=None, additional_exceptions=tuple()):
    """
    Zpracuje fedora error.

    :param view_func: View funkce obalená dekorátorem nebo middlewarem.
    :param additional_exceptions: Číselná hodnota ``additional_exceptions`` použitá při výpočtu nebo transformaci.

        :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``decorator``, výsledek volání ``decorator()``.
    """

    def decorator(func):
        """
        Provádí operaci decorator.

        :param func: Funkce, která je obalena nebo volána wrapperem.

            :return: Vrací proměnná ``_wrapped``.
        """

        @wraps(func)
        def _wrapped(*args, **kwargs):
            """
                       Provádí operaci wrapped.

                       :param args: Parametr ``args`` se předává do volání ``func()``, vstupuje do návratové hodnoty.
                       :param kwargs: Parametr ``kwargs`` se předává do volání ``func()``, vstupuje do návratové hodnoty.
            :return: Výstup funkce odpovídající implementované logice.
            """
            try:
                return func(*args, **kwargs)
            except (FedoraError,) + additional_exceptions as err:
                logger.info("fedora_management.decorators.handle_fedora_error", extra={"error": err})
                if err.fedora_transaction:
                    err.fedora_transaction.rollback_transaction()
                transaction.set_rollback(True)
                if err.redirect or err.redirect_url:
                    if err.redirect_url:
                        return redirect(err.redirect_url)
                    if err.ident_cely:
                        return redirect(reverse("core:redirect_ident", kwargs={"ident_cely": err.ident_cely}))

        return _wrapped

    if view_func is None:
        return decorator
    return decorator(view_func)
