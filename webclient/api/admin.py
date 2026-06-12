from api.models import ApiRequestLog
from django.contrib import admin
from django.http.request import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


@admin.register(ApiRequestLog)
class ApiRequestLogAdmin(admin.ModelAdmin):
    """Třída admin panelu pro zobrazení logů API požadavků."""

    list_display = [
        "received_at_display",
        "finished_at_display",
        "user",
        "client_ip",
        "request_target",
        "status",
        "ident_cely",
        "filename",
        "file_size",
    ]

    @staticmethod
    def _format_datetime(value):
        """Naformátuje datetime jako ``RRRR-MM-DD HH:MM:SS.xx`` (setiny sekundy)."""
        if value is None:
            return ""
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime("%Y-%m-%d %H:%M:%S.") + f"{value.microsecond // 10000:02d}"

    @admin.display(description=_("api.model.apiRequestLog.receivedAt"), ordering="received_at")
    def received_at_display(self, obj):
        """
        Vrátí ``received_at`` ve formátu ``RRRR-MM-DD HH:MM:SS.xx``.

        :param obj: Záznam ``ApiRequestLog``, jehož ``received_at`` se formátuje.

        :return: Naformátovaný řetězec datumu a času, nebo prázdný řetězec při ``None``.
        """
        return self._format_datetime(obj.received_at)

    @admin.display(description=_("api.model.apiRequestLog.finishedAt"), ordering="finished_at")
    def finished_at_display(self, obj):
        """
        Vrátí ``finished_at`` ve formátu ``RRRR-MM-DD HH:MM:SS.xx``.

        :param obj: Záznam ``ApiRequestLog``, jehož ``finished_at`` se formátuje.

        :return: Naformátovaný řetězec datumu a času, nebo prázdný řetězec při ``None``.
        """
        return self._format_datetime(obj.finished_at)

    list_filter = ["status", "request_target"]
    search_fields = ["user__email", "client_ip", "ident_cely"]
    readonly_fields = [
        "user",
        "client_ip",
        "received_at",
        "finished_at",
        "request_target",
        "filename",
        "file_size",
        "status",
        "ident_cely",
        "samostatny_nalez",
        "errors",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Zakáže ruční vytváření záznamů — logy se vytvářejí pouze automaticky.

        :param request: HTTP požadavek od klienta.

        :return: Vždy ``False``.
        """
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        """
        Zakáže editaci záznamů — logy jsou pouze pro čtení.

        :param request: HTTP požadavek od klienta.
        :param obj: Volitelný objekt záznamu.

        :return: Vždy ``False``.
        """
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        """
        Zakáže mazání záznamů — logy jsou auditní záznamy určené k archivaci.

        :param request: HTTP požadavek od klienta.
        :param obj: Volitelný objekt záznamu.

        :return: Vždy ``False``.
        """
        return False
