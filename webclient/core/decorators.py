"""Sdílené dekorátory pro řízení přístupu a režimu odstávky."""

import logging
from functools import wraps

from core.utils import get_set_maintenance_in_cache, is_maintenance_in_progress
from django.shortcuts import render

logger = logging.getLogger(__name__)


def allowed_user_groups(allowed_groups):
    """
    Omezí přístup k pohledu pouze na vybrané hlavní uživatelské role.

    Na vstupe je list povolených uživatelských skupin.
    Jestli uživatel nemá jesnou z daných skupin jako hlavní tak funkce vráti exception PermissionError a nezobrazí formulár.

    :param allowed_groups: Seznam nebo množina ID povolených hlavních rolí (skupin), jimž je přístup povolen.

        :return: Vrací proměnná ``_method_wrapper``.
    """

    @wraps(allowed_groups)
    def _method_wrapper(func):
        """
        Obalí cílovou funkci kontrolou hlavní role uživatele.

        :param func: View funkce, která má být chráněna kontrolou hlavní role.
        :return: Vrací proměnná ``_arguments_wrapper``.
        """

        @wraps(func)
        def _arguments_wrapper(request, *args, **kwargs):
            """
            Zkontroluje hlavní roli přihlášeného uživatele a buď vyvolá PermissionError, nebo předá řízení obalené funkci.

            :param request: HTTP požadavek, z jehož atributu ``user.hlavni_role`` se čte ID hlavní role.
            :param args: Další poziční argumenty předané obalené view funkci.
            :param kwargs: Klíčové argumenty předané obalené view funkci.

            :return: Výstup funkce odpovídající implementované logice.

            :raises PermissionError: Vyvolá se s textem "Nepovolená uživatelská role".
            """
            hlavni_role = request.user.hlavni_role
            if hlavni_role.id not in allowed_groups:
                raise PermissionError("Nepovolená uživatelská role")
            return func(request, *args, **kwargs)

        return _arguments_wrapper

    return _method_wrapper


def odstavka_in_progress(view_func):
    """
    Při aktivní odstávce vrátí stránku údržby namísto cílového pohledu.

    :param view_func: View funkce obalená dekorátorem nebo middlewarem.

        :return: Vrací proměnná ``wrapper``.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """
        Rozhodne, zda vrátit stránku odstávky, nebo vykonat původní pohled.

        :param request: Parametr ``request`` se předává do volání ``render()``, ``view_func()``, pracuje se s atributy ``LANGUAGE_CODE``, ``path``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param args: Parametr ``args`` se předává do volání ``view_func()``, vstupuje do návratové hodnoty.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``view_func()``, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render()``, výsledek volání ``view_func()``.
        """
        maintenance = get_set_maintenance_in_cache()
        if maintenance:
            if is_maintenance_in_progress():
                try:
                    language = request.LANGUAGE_CODE
                except Exception:
                    language = "cs"
                if "oznameni" in request.path:
                    return render(
                        request,
                        "/vol/web/nginx/data/" + language + "/oznameni/custom_503.html",
                        status=503,
                    )
                return render(
                    request,
                    "/vol/web/nginx/data/" + language + "/custom_503.html",
                    status=503,
                )
        return view_func(request, *args, **kwargs)

    return wrapper
