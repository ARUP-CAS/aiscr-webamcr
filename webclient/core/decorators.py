import logging
from functools import wraps

logger = logging.getLogger(__name__)

# not used, created more complex logic in core.models
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
