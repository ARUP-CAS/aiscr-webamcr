"""Sdílené dekorátory pro řízení přístupu a režimu odstávky."""

import logging
from functools import wraps

from core.utils import get_set_maintenance_in_cache, is_maintenance_in_progress
from django.shortcuts import render

logger = logging.getLogger(__name__)


def allowed_user_groups(allowed_groups):
    """
    Omezí přístup k pohledu pouze na vybrané hlavní uživatelské role.

    Args:
    allowed_groups: Seznam ID rolí, které mohou pohled vykonat.

    :param allowed_groups: Popis parametru ``allowed_groups``.
    """

    @wraps(allowed_groups)
    def _method_wrapper(func):
        """Obalí cílovou funkci kontrolou hlavní role uživatele."""

        @wraps(func)
        def _arguments_wrapper(request, *args, **kwargs):
            """
            Provádí operaci arguments wrapper.

            :param request: Django HTTP požadavek použitý při zpracování.
            :param args: Dodatečné poziční argumenty předané voláním.
            :param kwargs: Dodatečné pojmenované argumenty předané voláním.
            :return: Vrací výsledek provedené operace.
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

    :param view_func: Popis parametru ``view_func``.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """
        Rozhodne, zda vrátit stránku odstávky, nebo vykonat původní pohled.

        :param request: Popis parametru ``request``.
        :param args: Popis parametru ``args``.
        :param kwargs: Popis parametru ``kwargs``.
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
                    )
                return render(
                    request,
                    "/vol/web/nginx/data/" + language + "/custom_503.html",
                )
        return view_func(request, *args, **kwargs)

    return wrapper
