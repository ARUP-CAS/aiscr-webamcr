import logging
import re

from core.connectors import RedisConnector
from core.message_constants import ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_USPESNE_EDITOVAN
from core.repository_connector import FedoraError, FedoraTransaction, FedoraTransactionResult
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.utils import OperationalError
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy

from redis import ResponseError

logger = logging.getLogger(__name__)


class PermissionMiddleware:
    """Middleware třída užívaná pro kontrolu oprávnění."""

    def __init__(self, get_response):
        """
        Inicializuje instanci třídy.

        :param get_response: Callable ze WSGI řetězce middleware, který vrátí response.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Zpracovává příchozí HTTP požadavek a kontroluje oprávnění uživatele.

        :param request: HTTP požadavek ze strany klienta.
        :return: HTTP response vygenerovaná aplikací.
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
    """Implementuje komponentu pro zachycení a zpracování chyb (ErrorMiddleware) v rámci aplikace."""

    def __init__(self, get_response):
        """
        Inicializuje instanci třídy.

        :param get_response: Callable ze WSGI řetězce middleware, který vrátí response.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Zpracovává příchozí HTTP požadavek.

        :param request: HTTP požadavek ze strany klienta.
        :return: HTTP response vygenerovaná aplikací.
        """
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Zachycuje a zpracovává Fedora a databázové výjimky během zpracování požadavku.

        :param request: HTTP požadavek pro vykreslení chybové stránky.
        :param exception: Vyvolená výjimka během zpracování požadavku.
        :return: HTML error response nebo None pokud jde o neznámou výjimku.
        """
        if isinstance(exception, FedoraError):
            context = {"exception": exception}
            return render(request, "fedora_error.html", context, status=500)

        if isinstance(exception, OperationalError) and "canceling statement due to statement timeout" in str(exception):
            context = {"exception": exception}
            return render(request, "db_timeout_error.html", context, status=504)


class InactiveUserMiddleware:
    """
    Middleware zachytávající ``ValidationError`` s kódem ``inactive``,
    která může vzniknout při vyhodnocení ``request.user`` u deaktivovaného
    uživatele s stále aktivní session.

    Pokud k této chybě dojde, session se zruší a uživatel je přesměrován
    na přihlašovací stránku s varovnou hláškou.
    """

    def __init__(self, get_response):
        """
        Inicializuje middleware.

        :param get_response: Callable z middleware řetězce,
                             který zpracuje požadavek a vrátí response.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Obalí zpracování požadavku a zachytí ``ValidationError`` s kódem
        ``inactive``, která může vzniknout při vyhodnocení ``request.user``.

        Pokud je chyba zachycena, session se zruší a uživatel je
        přesměrován na přihlašovací stránku.

        :param request: Instance ``HttpRequest``.
        :return: Standardní ``response`` nebo přesměrování na login.
        """
        try:
            return self.get_response(request)

        except ValidationError as e:
            if getattr(e, "code", None) == "inactive" or any(
                err.code == "inactive" for err in getattr(e, "error_list", [])
            ):
                request.session.flush()
                messages.warning(request, str(e))
                return redirect("django_authentication_login")

            raise


class StatusMessageMiddleware:
    """Middleware pro zobrazení stavových zpráv z Fedora transakcí skrze Redis."""

    pattern = re.compile(r"[\w-]+\d+[A-Z]?")

    def __init__(self, get_response):
        """
        Inicializuje instanci třídy.

        :param get_response: Callable ze WSGI řetězce middleware, který vrátí response.
        """
        self.get_response = get_response
        r = RedisConnector()
        self.redis_connection = r.get_connection()

    def __call__(self, request):
        """
        Zpracovává příchozí HTTP požadavek.

        :param request: HTTP požadavek ze strany klienta.
        :return: HTTP response vygenerovaná aplikací.
        """
        response = self.get_response(request)
        return response

    def _show_message(self, value, request, redis_key):
        """
        Zobrazí stavovou zprávu uživateli na základě výsledku Fedora transakce.

        :param value: Kódová hodnota stavu transakce z Redis (COMMITED nebo FAILED).
        :param request: HTTP požadavek pro přidání zprávy do session.
        :param redis_key: Klíč v Redis pro načtení stavových zpráv a smazání záznamu.
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
        Detekuje a zobrazuje stavové zprávy Fedora transakcí pro AMČR identifikátory v URL.

        :param request: HTTP požadavek obsahující cestu s potenciálním AMČR identifikátorem.
        :param view_func: View funkce, kterou se chystá aplikace volat.
        :param view_args: Poziční argumenty pro view funkci.
        :param view_kwargs: Pojmenované argumenty pro view funkci.
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
