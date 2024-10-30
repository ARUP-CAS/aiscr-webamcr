import logging
import time
from io import StringIO

from core.mixins import IPWhitelistMixin
from django.core import management
from django.http import JsonResponse
from django.views import View

logger = logging.getLogger(__name__)


def check_status():
    io_out = StringIO()
    io_out_db = StringIO()
    try:
        management.call_command("check", stdout=io_out)
        management.call_command("check", "--database", "default", stdout=io_out_db)
        ret_code = 0
    except Exception:
        io_out.write("Django checks failed.\n")
        ret_code = 1
    return ret_code, io_out.getvalue(), io_out_db.getvalue()


class HealthCheckView(IPWhitelistMixin, View):
    def get(self, request):
        status = "healthy"
        r_code, msg, msg_db = check_status()
        status = ("healthy", 200) if r_code == 0 else ("unhealthy", 500)
        return JsonResponse(
            {
                "status": f"{status[0]}",
                "django_check_default": f"{msg}",
                "django_check_db": f"{msg_db}",
                "exit-code": f"{r_code}",
                "time": f"{time.strftime('%Y-%m-%d %H:%M:%S')}",
            },
            status=status[1],
        )
