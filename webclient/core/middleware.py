import logging
import re
from datetime import datetime, timedelta

from core.connectors import RedisConnector
from core.message_constants import NEPRODUKCNI_PROSTREDI_INFO, ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_USPESNE_EDITOVAN
from core.models import Permissions
from core.repository_connector import FedoraError, FedoraTransaction, FedoraTransactionResult
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.utils import OperationalError
from django.shortcuts import render
from django.utils.translation import gettext_lazy

logger = logging.getLogger(__name__)


class PermissionMiddleware:
    """
    Middleware třída užívaná pro kontrolu oprávnení.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Metóda pro kontrolu oprvávnení pro každý view.
        """
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
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, FedoraError):
            context = {"exception": exception}
            return render(request, "fedora_error.html", context, status=500)

        if isinstance(exception, OperationalError) and "canceling statement due to statement timeout" in str(exception):
            context = {"exception": exception}
            return render(request, "db_timeout_error.html", context, status=504)


class TestEnvPopupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if settings.TEST_ENV and request.user.is_authenticated:
            cache_name = f"test_env_{request.user.pk}"
            last_test_env_popup = cache.get(cache_name)
            if last_test_env_popup is None:
                now = datetime.now()
                midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                cache.set(cache_name, True, (midnight - now).seconds)
                messages.add_message(request, messages.WARNING, NEPRODUKCNI_PROSTREDI_INFO, "notclosing")


class StatusMessageMiddleware:
    pattern = re.compile(r"[\w-]+\d+[A-Z]?")

    def __init__(self, get_response):
        self.get_response = get_response
        r = RedisConnector()
        self.redis_connection = r.get_connection()

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def _show_message(self, value, request, redis_key):
        value = int(value.decode("utf-8"))
        if value == FedoraTransactionResult.COMMITED.value:
            success_message = self.redis_connection.hget(redis_key, "success_message")
            if success_message:
                success_message = gettext_lazy(success_message.decode("utf-8"))
            else:
                success_message = ZAZNAM_USPESNE_EDITOVAN
            messages.add_message(request, messages.SUCCESS, success_message)
        else:
            error_message = self.redis_connection.hget(redis_key, "error_message")
            if error_message:
                error_message = gettext_lazy(error_message)
            else:
                error_message = ZAZNAM_SE_NEPOVEDLO_EDITOVAT
            messages.add_message(request, messages.ERROR, error_message)
        self.redis_connection.delete(redis_key)

    def process_view(self, request, view_func, view_args, view_kwargs):
        regex_result = self.pattern.findall(request.path)
        for item in regex_result:
            redis_key = FedoraTransaction.get_transaction_redis_key(item, request.user.id)
            status = self.redis_connection.hget(redis_key, "status")
            if status:
                self._show_message(status, request, redis_key)
                break
