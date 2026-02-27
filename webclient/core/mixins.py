import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden

logger = logging.getLogger(__name__)


class ManyToManyRestrictedClassMixin:
    """
    Třída pro model pro vytvoření property has_connections.
    Hledá jestli má model nejakou many to many vazbu.
    """

    @property
    def has_connections(self):
        """Zajišťuje logiku funkce ``has_connections``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        attr_list = []
        for attr in dir(self):
            if not attr.startswith("_") and attr not in ("has_connections", "objects"):
                try:
                    if hasattr(getattr(self, attr), "all"):
                        attr_list.append(attr)
                except ObjectDoesNotExist as err:
                    logger.debug(
                        "core.mixins.ManyToManyRestrictedClassMixin.has_connections.ObjectDoesNotExist",
                        extra={"error": err},
                    )
        attr_list = [attr for attr in attr_list if getattr(self, attr).all().count() > 0]
        return len(attr_list) > 0


class IPWhitelistMixin:
    """Zapouzdřuje chování třídy ``IPWhitelistMixin`` pro modul ``webclient.core.mixins``."""
    def dispatch(self, request, *args, **kwargs):
        """Zajišťuje logiku funkce ``dispatch``.
        
        :param request: HTTP požadavek zpracovávaný view funkcí nebo metodou.
        :param args: Poziční argumenty předané voláním.
        :param kwargs: Pojmenované argumenty předané voláním.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        ALLOWED_IPS = settings.ALLOWED_HOSTS + ["127.0.0.1", "10.0.0.2"]
        client_ip = request.META.get("REMOTE_ADDR", "")  # Get client IP
        if client_ip not in ALLOWED_IPS and "*" not in ALLOWED_IPS:  # Ověří, že je IP adresa povolena.
            logger.error("healthcheck.views.IPWhitelistMixin", extra={"ip": client_ip})
            return HttpResponseForbidden("Access denied: Your IP is not allowed.")  # Deny access
        return super().dispatch(request, *args, **kwargs)  # Jinak pokračuje zpracování pohledu.
