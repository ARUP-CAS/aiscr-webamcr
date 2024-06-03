import logging
from datetime import datetime, timedelta
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.db.utils import OperationalError
from core.models import Permissions
from core.message_constants import NEPRODUKCNI_PROSTREDI_INFO
from core.repository_connector import FedoraError

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
            if not "autocomplete" in resolver.route:
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
                    tested.append(
                        concrete_permission.check_concrete_permission(
                            request.user, ident, typ
                        )
                    )
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
            return render(request, 'fedora_error.html', context, status=500)

        if isinstance(exception, OperationalError) and "canceling statement due to statement timeout" in str(exception):
            context = {"exception": exception}
            return render(request, 'db_timeout_error.html', context, status=500)
           
           
class TestEnvPopupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        if getattr(settings, "TEST_ENV") and request.user.is_authenticated:
            cache_name = f"test_env_{request.user.pk}"
            last_test_env_popup = cache.get(cache_name)
            if last_test_env_popup is None:
                now = datetime.now()
                midnight = (now + timedelta(days=1)).replace(hour=0, minute = 0, second=0)
                cache.set(cache_name,True,(midnight - now).seconds)
                messages.add_message(
                                request, messages.WARNING, NEPRODUKCNI_PROSTREDI_INFO, 'notclosing'
                            )