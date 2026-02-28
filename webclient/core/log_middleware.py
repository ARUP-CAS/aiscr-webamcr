import json
import logging
import threading
import time

from core.setting_models import CustomAdminSettings
from django.urls import Resolver404, resolve

log_request_data = threading.local()
logger = logging.getLogger("request.timer")


def get_slow_request_settings():
    """Vrací slow request settings."""
    try:
        settings_query = CustomAdminSettings.objects.filter(item_group="settings", item_id="variables")
        return json.loads(settings_query.last().value)["SLOW_REQUEST_THRESHOLD"]
    except Exception:
        return 2.0


# práh pro „pomalé“ požadavky (v sekundách)
SLOW_REQUEST_THRESHOLD = get_slow_request_settings()


def _resolve_view_info(request) -> dict:
    """Vrátí dict s informacemi o view: view_name, view_module, kwargs."""
    try:
        match = resolve(request.path_info)
        view_func = match.func
        view_name = getattr(match, "view_name", None)
        view_module = getattr(view_func, "__module__", None)
        return {
            "view_name": view_name,
            "view_module": view_module,
            "url_kwargs": str(match.kwargs or {}),
        }
    except Resolver404:
        return {
            "view_name": None,
            "view_module": None,
            "url_kwargs": "",
        }


class LogMiddleware:
    """
    Middleware, který: v aplikaci.

    - ukládá do thread-local: url, user_id
    - měří duration a zapisuje strukturovaný log po odpovědi
    """

    def __init__(self, get_response):
        """
        Inicializuje instanci třídy.

        :param get_response: Vstupní hodnota ``get_response`` pro danou operaci.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Provádí operaci call.

        :param request: Django HTTP požadavek použitý při zpracování.
        """
        start = time.monotonic()
        log_request_data.url = request.get_full_path()
        log_request_data.user_id = (
            request.user.ident_cely if request.user.is_authenticated else "anonymous"
        )  # slouží také pro zaznamenání ve Fedoře
        try:
            response = self.get_response(request)
            status = getattr(response, "status_code", None)
            duration = time.monotonic() - start
            if duration >= SLOW_REQUEST_THRESHOLD or status == 504:
                view_info = _resolve_view_info(request)
                payload = {
                    "method": request.method,
                    "status_code": status,
                    "duration_s": round(duration, 6),
                    "view_name": view_info["view_name"],
                    "view_module": view_info["view_module"],
                    "url_kwargs": view_info["url_kwargs"],
                }
                logger.warning("core.log_middleware.LogMiddleware.slow_request", extra=payload)
            return response
        except Exception:
            duration = time.monotonic() - start
            view_info = _resolve_view_info(request)
            payload = {
                "method": request.method,
                "duration_s": round(duration, 6),
                "view_name": view_info["view_name"],
                "view_module": view_info["view_module"],
                "url_kwargs": view_info["url_kwargs"],
            }
            logger.error("core.log_middleware.LogMiddleware.request_error", exc_info=True, extra=payload)
            raise
        finally:
            for attr in ("url", "user_id"):
                try:
                    delattr(log_request_data, attr)
                except AttributeError:
                    pass

    @staticmethod
    def get_request_url():
        """Vrací request url."""
        return getattr(log_request_data, "url", None)

    @staticmethod
    def get_user_id():
        """Vrací user id."""
        return getattr(log_request_data, "user_id", "anonymous")
