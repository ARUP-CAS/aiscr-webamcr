import logging
from functools import wraps
from datetime import datetime, date

from django.shortcuts import render

from core.models import OdstavkaSystemu
from django.core.cache import cache

logger = logging.getLogger(__name__)


def allowed_user_groups(allowed_groups):
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
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        last_maintenance = cache.get("last_maintenance")
        if "LANGUAGE_CODE" in request:
            language = request.LANGUAGE_CODE
        else:
            language = "cs"
        if "oznameni" in request.path:
            try:
                response = render(
                    request,
                    "/vol/web/nginx/data/" + language + "/oznameni/custom_50x.html",
                )
            except:
                pass
        else:
            try:
                response = render(
                    request,
                    "/vol/web/nginx/data/" + language + "/custom_50x.html",
                )
            except:
                pass
        if last_maintenance is None:
            odstavka = OdstavkaSystemu.objects.filter(
                info_od__lte=datetime.today(),
                datum_odstavky__gte=datetime.today(),
                status=True,
            ).order_by("-datum_odstavky", "-cas_odstavky")
            if odstavka:
                last_maintenance = odstavka[0]
                cache.set("last_maintenance", last_maintenance, 600)
        if last_maintenance is not None:
            if last_maintenance.datum_odstavky == date.today():
                if datetime.now().time() > last_maintenance.cas_odstavky:
                    return response
            elif date.today() > last_maintenance.datum_odstavky:
                return response
        return view_func(request, *args, **kwargs)

    return wrapper