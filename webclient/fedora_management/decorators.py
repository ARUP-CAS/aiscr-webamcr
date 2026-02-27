import logging
from functools import wraps

from core.repository_connector import FedoraError
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)


def handle_fedora_error(view_func=None, additional_exceptions=tuple()):
    """Funkce `handle_fedora_error` v modulu `webclient.fedora_management.decorators`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param view_func: Vstupní hodnota používaná při zpracování.
    :param additional_exceptions: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    def decorator(func):
        """Funkce `decorator` v modulu `webclient.fedora_management.decorators`.
        
        Zajišťuje dílčí aplikační logiku pro tento modul.
        
        :param func: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        @wraps(func)
        def _wrapped(*args, **kwargs):
            """Funkce `_wrapped` v modulu `webclient.fedora_management.decorators`.
            
            Zajišťuje dílčí aplikační logiku pro tento modul.
            
            :param args: Vstupní hodnota používaná při zpracování.
            :param kwargs: Vstupní hodnota používaná při zpracování.
            :return: Výsledek odpovídající účelu volání.
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
