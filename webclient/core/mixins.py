import ipaddress
import logging

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
        """Určí, zda connections.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
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
    """
    Mixin pro filtrování IP adres. Používá se pro PrometheusMetrics a HealthCheck.
    Dovolí přístup pouze z lokálních adres.
    """

    def dispatch(self, request, *args, **kwargs):
        """Ověří, že požadavek pochází z lokální IP adresy (loopback, privátní nebo link-local).

        :param request: Objekt požadavku Django.
        :param args: Poziční argumenty view.
        :param kwargs: Pojmenované argumenty view.
        :return: ``HttpResponseForbidden`` při neoprávněném přístupu, jinak výsledek nadřazené metody ``dispatch``.
        """
        client_ip = None
        try:
            client_ip = ipaddress.ip_address(request.META.get("REMOTE_ADDR", ""))  # Get client IP
            allowed = client_ip.is_loopback or client_ip.is_private or client_ip.is_link_local
        except ValueError:
            allowed = False
        if not allowed:
            logger.error("core.mixins.IPWhitelistMixin", extra={"ip": client_ip})
            return HttpResponseForbidden("Access denied: Your IP is not allowed.")  # Deny access
        return super().dispatch(request, *args, **kwargs)
