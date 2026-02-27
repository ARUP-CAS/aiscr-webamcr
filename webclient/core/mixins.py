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
        """Provádí funkci ``ManyToManyRestrictedClassMixin.has_connections`` v rámci modulu ``webclient.core.mixins``."""
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
        """Provádí funkci ``IPWhitelistMixin.dispatch`` v rámci modulu ``webclient.core.mixins``."""
        ALLOWED_IPS = settings.ALLOWED_HOSTS + ["127.0.0.1", "10.0.0.2"]
        client_ip = request.META.get("REMOTE_ADDR", "")  # Get client IP
        if client_ip not in ALLOWED_IPS and "*" not in ALLOWED_IPS:  # Ověří, že je IP adresa povolena.
            logger.error("healthcheck.views.IPWhitelistMixin", extra={"ip": client_ip})
            return HttpResponseForbidden("Access denied: Your IP is not allowed.")  # Deny access
        return super().dispatch(request, *args, **kwargs)  # Jinak pokračuje zpracování pohledu.
