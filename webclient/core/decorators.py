import logging
from datetime import datetime
from functools import wraps

import pytz
from core.utils import get_set_maintenance_in_cache
from django.shortcuts import render

logger = logging.getLogger(__name__)


def allowed_user_groups(allowed_groups):
    """
    Dekorátor funkce použitý nad pohledem, na kontrolu práv uživatele na daný pohled.
    Na vstupe je list povolených uživatelských skupin.
    Jestli uživatel nemá jesnou z daných skupin jako hlavní tak funkce vráti exception PermissionError a nezobrazí formulár.
    """

    @wraps(allowed_groups)
    def _method_wrapper(func):
        @wraps(func)
        def _arguments_wrapper(request, *args, **kwargs):
            hlavni_role = request.user.hlavni_role
            if hlavni_role.id not in allowed_groups:
                raise PermissionError("Nepovolená uživatelská role")
            return func(request, *args, **kwargs)

        return _arguments_wrapper

    return _method_wrapper


def odstavka_in_progress(view_func):
    """
    Dekorátor funkce použitý nad pohledem, na zobrazení stránky o odstávke místo stránky oznámení a prihlášení pokud je nastavená odstívka.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        maintenance = get_set_maintenance_in_cache()
        if maintenance:
            if pytz.timezone("Europe/Prague").localize(
                datetime.combine(maintenance.datum_odstavky, maintenance.cas_odstavky)
            ) <= datetime.now(pytz.timezone("Europe/Prague")):
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
