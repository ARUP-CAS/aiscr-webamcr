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
        if "oznameni" in request.path:
            response = render(
                request,
                "/vol/web/nginx/data/"
                + request.LANGUAGE_CODE
                + "/oznameni/custom_50x.html",
            )
        else:
            response = render(
                request,
                "/vol/web/nginx/data/" + request.LANGUAGE_CODE + "/custom_50x.html",
            )
        if last_maintenance is None:
            odstavka = OdstavkaSystemu.objects.filter(
                info_od__lte=datetime.today(),
                datum_odstavky__gte=datetime.today(),
                status=True,
            ).order_by("-datum_odstavky", "-cas_odstavky")
            if odstavka:
                last_maintenance = odstavka[0]
                cache.set("last_maintenance", last_maintenance, 600)
        if last_maintenance.datum_odstavky == date.today():
            if last_maintenance.cas_odstavky > datetime.now():
                return response
        elif last_maintenance.datum_odstavky > date.today():
            return response
        return False

    return wrapper