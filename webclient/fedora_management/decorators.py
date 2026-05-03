import logging
from functools import wraps

from core.message_constants import CHYBA_SPOJENI_REPOZITAR
from core.repository_connector import FedoraError, FedoraNoResponseError
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
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
        Obalí pohledovou funkci obsluhou chyb Fedory a přesměrováním při výjimce.

        :param func: Funkce, která je obalena nebo volána wrapperem.

            :return: Vrací proměnná ``_wrapped``.
        """

        @wraps(func)
        def _wrapped(*args, **kwargs):
            """
            Zavolá obalenou funkci a při výjimce FedoraError nastaví uzavření transakce na rollback a přesměruje uživatele.
            Při výjimce FedoraNoResponseError (nedostupný repozitář) zobrazí uživateli chybovou zprávu.

            :param args: Poziční argumenty předané obalené funkci.
            :param kwargs: Klíčové argumenty předané obalené funkci.
            :return: Výstup funkce odpovídající implementované logice.
            """
            try:
                return func(*args, **kwargs)
            except (FedoraError,) + additional_exceptions as err:
                logger.info("fedora_management.decorators.handle_fedora_error", extra={"error": err})
                fedora_transaction = getattr(err, "fedora_transaction", None)
                if fedora_transaction:
                    try:
                        fedora_transaction.rollback_transaction()
                    except Exception as rollback_err:
                        logger.warning(
                            "fedora_management.decorators.handle_fedora_error.rollback_failed",
                            extra={"error": err, "rollback_error": rollback_err},
                        )
                transaction.set_rollback(True)
                if isinstance(err, FedoraNoResponseError):
                    request = args[0]
                    messages.add_message(request, messages.ERROR, CHYBA_SPOJENI_REPOZITAR)
                    if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                        return JsonResponse({"error": "connection_failed"}, status=503)
                    if err.ident_cely:
                        return redirect(reverse("core:redirect_ident", kwargs={"ident_cely": err.ident_cely}))
                    return redirect(reverse("core:home"))
                redirect_url = getattr(err, "redirect_url", None)
                ident_cely = getattr(err, "ident_cely", None)
                if getattr(err, "redirect", None) or redirect_url:
                    if redirect_url:
                        return redirect(redirect_url)
                    if ident_cely:
                        return redirect(reverse("core:redirect_ident", kwargs={"ident_cely": ident_cely}))
                    return redirect(reverse("core:home"))
                raise

        return _wrapped

    if view_func is None:
        return decorator
    return decorator(view_func)
