import logging
import re

from core.connectors import RedisConnector
from core.message_constants import ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_USPESNE_EDITOVAN
from core.repository_connector import FedoraError, FedoraTransaction, FedoraTransactionResult
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.utils import OperationalError
from django.shortcuts import render
from django.utils.translation import gettext_lazy

from redis import ResponseError

logger = logging.getLogger(__name__)


class PermissionMiddleware:
    """Middleware třída užívaná pro kontrolu oprávnení."""

    def __init__(self, get_response):
        """
        Inicializuje instanci třídy.

        :param get_response: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Provádí operaci call.

        :param request: Parametr ``request`` předává se do volání ``get_response()``.

            :return: Vrací proměnná ``response``.
        """
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Metoda pro kontrolu oprvávnení pro každý view.

        :param request: Parametr ``request`` se předává do volání ``append()``, ``check_concrete_permission()``, pracuje se s atributy ``user``, ``resolver_match``, ovlivňuje větvení podmínek.
        :param view_func: View funkce obalená dekorátorem nebo middlewarem.
        :param view_args: Dodatečné argumenty předané voláním.
        :param view_kwargs: Dodatečné argumenty předané voláním.

            :raises PermissionDenied: Vyvolá se při splnění podmínky ``any(tested)``.
        """
        from core.models import Permissions

        if request.user.is_authenticated:
            resolver = request.resolver_match
            filter = {
                "main_role": request.user.hlavni_role,
                "address_in_app": resolver.route,
            }
            i = 0
            typ = None
            if "typ_vazby" in resolver.route:
                filter.update({"action__endswith": resolver.kwargs.get("typ_vazby")})
                i = 1
            if "model_name" in resolver.route:
                i = 1
            if "nalez/smazat" in resolver.route:
                i = 2
                typ = resolver.kwargs.get("typ")
            if "autocomplete" not in resolver.route:
                permission_set = Permissions.objects.filter(**filter)
            else:
                permission_set = Permissions.objects.none()
            logger.debug("Permissions to check: %s for url: %s", permission_set, resolver.route)
            if permission_set.count() > 0:
                tested = []
                if len(resolver.kwargs) > 0:
                    ident = list(resolver.kwargs.values())[i]
                else:
                    ident = None
                for concrete_permission in permission_set:
                    tested.append(concrete_permission.check_concrete_permission(request.user, ident, typ))
                if any(tested):
                    return
                else:
                    raise PermissionDenied


class ErrorMiddleware:
    """Implementuje komponentu ``ErrorMiddleware`` v rámci aplikace."""

    def __init__(self, get_response):
        """
        Inicializuje instanci třídy.

        :param get_response: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Provádí operaci call.

        :param request: Parametr ``request`` předává se do volání ``get_response()``.

            :return: Vrací proměnná ``response``.
        """
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Provádí operaci process exception.

        :param request: Parametr ``request`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
        :param exception: Číselná hodnota ``exception`` použitá při výpočtu nebo transformaci.

            :return: Vrací výsledek volání ``render()``.
        """
        if isinstance(exception, FedoraError):
            context = {"exception": exception}
            return render(request, "fedora_error.html", context, status=500)

        if isinstance(exception, OperationalError) and "canceling statement due to statement timeout" in str(exception):
            context = {"exception": exception}
            return render(request, "db_timeout_error.html", context, status=504)


class StatusMessageMiddleware:
    """Implementuje komponentu ``StatusMessageMiddleware`` v rámci aplikace."""

    pattern = re.compile(r"[\w-]+\d+[A-Z]?")

    def __init__(self, get_response):
        """
        Inicializuje instanci třídy.

        :param get_response: Textový nebo strukturální vstup `get_response` používaný při sestavení nebo zpracování obsahu.
        """
        self.get_response = get_response
        r = RedisConnector()
        self.redis_connection = r.get_connection()

    def __call__(self, request):
        """
        Provádí operaci call.

        :param request: Parametr ``request`` předává se do volání ``get_response()``.

            :return: Vrací proměnná ``response``.
        """
        response = self.get_response(request)
        return response

    def _show_message(self, value, request, redis_key):
        """
               Provádí operaci show message.

               :param value: Parametr ``value`` předává se do volání ``int()``, pracuje se s atributy ``decode``, ovlivňuje větvení podmínek.
               :param request: Parametr ``request`` předává se do volání ``add_message()``.
               :param redis_key: Textový název nebo klíč ``redis_key`` používaný v rámci operace.
        :return: Výstup funkce odpovídající implementované logice.
        """
        value = int(value.decode("utf-8"))
        if value == FedoraTransactionResult.COMMITED.value:
            try:
                success_message = self.redis_connection.hget(redis_key, "success_message")
            except ResponseError as err:
                logger.warning("core.middleware._show_message.success.error", extra={"error": err})
                success_message = None
            if success_message:
                success_message = gettext_lazy(success_message.decode("utf-8"))
            else:
                success_message = ZAZNAM_USPESNE_EDITOVAN
            messages.add_message(request, messages.SUCCESS, success_message)
        else:
            try:
                error_message = self.redis_connection.hget(redis_key, "error_message")
            except ResponseError as err:
                logger.warning("core.middleware._show_message.error.error", extra={"error": err})
                error_message = None
            if error_message:
                error_message = gettext_lazy(error_message.decode("utf-8"))
            else:
                error_message = ZAZNAM_SE_NEPOVEDLO_EDITOVAT
            messages.add_message(request, messages.ERROR, error_message)
        self.redis_connection.delete(redis_key)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Provádí operaci process view.

        :param request: Parametr ``request`` předává se do volání ``findall()``, ``get_transaction_redis_key()``, pracuje se s atributy ``path``, ``user``.
        :param view_func: View funkce obalená dekorátorem nebo middlewarem.
        :param view_args: Dodatečné argumenty předané voláním.
        :param view_kwargs: Dodatečné argumenty předané voláním.
        """
        regex_result = self.pattern.findall(request.path)
        for item in regex_result:
            redis_key = FedoraTransaction.get_transaction_redis_key(item, request.user.id)
            try:
                status = self.redis_connection.hget(redis_key, "status")
            except ResponseError as err:
                logger.warning("core.middleware.process_view.status.error", extra={"error": err})
                status = None
            if status:
                self._show_message(status, request, redis_key)
                break
