import logging
from django.core.exceptions import PermissionDenied

from core.models import Permissions


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
