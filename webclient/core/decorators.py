import logging
from datetime import date, datetime
from functools import wraps

from core.models import OdstavkaSystemu
from django.core.cache import cache
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
        last_maintenance = cache.get("last_maintenance")
        if last_maintenance is None:
            odstavka = OdstavkaSystemu.objects.filter(
                info_od__lte=datetime.today(),
                datum_odstavky__lte=datetime.today(),
                status=True,
            ).order_by("-datum_odstavky", "-cas_odstavky")
            if odstavka.count():
                last_maintenance = odstavka[0]
                cache.set("last_maintenance", last_maintenance, 600)
            else:
                cache.set("last_maintenance", False, 600)
        if last_maintenance is not None and last_maintenance is not False:
            if (
                last_maintenance.datum_odstavky == date.today()
                and datetime.now().time() > last_maintenance.cas_odstavky
            ) or date.today() > last_maintenance.datum_odstavky:
                try:
                    language = request.LANGUAGE_CODE
                except Exception:
                    language = "cs"
                if "oznameni" in request.path:
                    return render(
                        request,
                        "/vol/web/nginx/data/" + language + "/oznameni/custom_50x.html",
                    )
                return render(
                    request,
                    "/vol/web/nginx/data/" + language + "/custom_50x.html",
                )
        return view_func(request, *args, **kwargs)

    return wrapper
