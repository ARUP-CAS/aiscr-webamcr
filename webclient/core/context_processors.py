from core.constants import (
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
)
from django.conf import settings


from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_auto_logout.utils import (
    now,
    seconds_until_session_end,
    seconds_until_idle_time_end,
)
from django.core.cache import cache
from core.models import OdstavkaSystemu
from datetime import datetime, date, timedelta


def constants_import(request):
    constants_dict = {
        "PROJEKT_STAV_OZNAMENY": PROJEKT_STAV_OZNAMENY,
        "PROJEKT_STAV_ZAPSANY": PROJEKT_STAV_ZAPSANY,
        "PROJEKT_STAV_PRIHLASENY": PROJEKT_STAV_PRIHLASENY,
        "PROJEKT_STAV_ZAHAJENY_V_TERENU": PROJEKT_STAV_ZAHAJENY_V_TERENU,
        "PROJEKT_STAV_UKONCENY_V_TERENU": PROJEKT_STAV_UKONCENY_V_TERENU,
        "PROJEKT_STAV_UZAVRENY": PROJEKT_STAV_UZAVRENY,
        "PROJEKT_STAV_ARCHIVOVANY": PROJEKT_STAV_ARCHIVOVANY,
        "PROJEKT_STAV_NAVRZEN_KE_ZRUSENI": PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
        "PROJEKT_STAV_ZRUSENY": PROJEKT_STAV_ZRUSENY,
    }

    return constants_dict


def digi_links_from_settings(request):
    return getattr(settings, "DIGI_LINKS")


# for autologout function redirect immediatelly
def auto_logout_client(request):
    if request.user.is_anonymous:
        return {}

    options = getattr(settings, "AUTO_LOGOUT")
    if not options:
        return {}

    ctx = {}
    current_time = now()

    ctx["maintenance_logout_text"] = mark_safe("0")
    maintenance_logout = False
    last_maintenance = cache.get("last_maintenance")
    if last_maintenance is None:
        odstavka = OdstavkaSystemu.objects.filter(
            info_od__lte=datetime.today(),
            datum_odstavky__gte=datetime.today(),
            status=True,
        ).order_by("-datum_odstavky", "-cas_odstavky")
        if odstavka:
            last_maintenance = odstavka[0]
            cache.set("last_maintenance", last_maintenance, 600)
    else:
        if (
            last_maintenance.datum_odstavky == date.today()
            and last_maintenance.cas_odstavky
            < (datetime.now() + timedelta(hours=1)).time()
        ):
            maintenance_logout = True

    if "SESSION_TIME" in options:
        ctx["seconds_until_session_end"] = seconds_until_session_end(
            request, options["SESSION_TIME"], current_time
        )
    if not maintenance_logout:
        if "IDLE_TIME" in options:
            ctx["seconds_until_idle_end"] = seconds_until_idle_time_end(
                request, options["IDLE_TIME"], current_time
            )
        if "IDLE_WARNING_TIME" in options:
            ctx["IDLE_WARNING_TIME"] = mark_safe(options["IDLE_WARNING_TIME"])

        if options.get("REDIRECT_TO_LOGIN_IMMEDIATELY"):
            ctx["redirect_to_login_immediately"] = mark_safe(
                "window.location.href = '/accounts/logout/?autologout=true'"
            )
        else:
            ctx["redirect_to_login_immediately"] = mark_safe(
                "$('#time').html('%s');" % _("nav.autologout.expired.text")
            )
        ctx["logout_warning_text"] = mark_safe("AUTOLOGOUT_EXPIRATION_WARNING")
    else:
        ctx["seconds_until_idle_end"] = options["MAINTENANCE_LOGOUT_TIME"]
        ctx["IDLE_WARNING_TIME"] = options["MAINTENANCE_LOGOUT_TIME"] - 5
        ctx["redirect_to_login_immediately"] = mark_safe(
            "window.location.href = '/accounts/logout/?maintenance_logout=true'"
        )
        ctx["logout_warning_text"] = mark_safe("MAINTENANCE_LOGOUT_WARNING")
        ctx["maintenance"] = mark_safe("true")

    return ctx
