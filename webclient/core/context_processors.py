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

    if "SESSION_TIME" in options:
        ctx["seconds_until_session_end"] = seconds_until_session_end(
            request, options["SESSION_TIME"], current_time
        )

    if "IDLE_TIME" in options:
        ctx["seconds_until_idle_end"] = seconds_until_idle_time_end(
            request, options["IDLE_TIME"], current_time
        )

    if options.get("REDIRECT_TO_LOGIN_IMMEDIATELY"):
        ctx["redirect_to_login_immediately"] = mark_safe(
            "window.location.href = '/accounts/logout/?autologout=true'"
        )
    else:
        ctx["redirect_to_login_immediately"] = mark_safe(
            "$('#time').html('%s');" % _("nav.autologout.expired.text")
        )

    return ctx
