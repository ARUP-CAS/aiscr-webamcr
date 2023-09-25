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
            permission_set = Permissions.objects.filter(
                main_role=request.user.hlavni_role,
                address_in_app=request.resolver_match.route,
            )
            if permission_set.count() > 0:
                tested = []
                for concrete_permission in permission_set:
                    tested.append(
                        concrete_permission.check_concrete_permission(
                            resolver.kwargs, request.user
                        )
                    )
                if any(tested):
                    return
                else:
                    raise PermissionDenied
