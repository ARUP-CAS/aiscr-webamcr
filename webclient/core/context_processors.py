import logging
from datetime import datetime

import pytz
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
    ROLE_ADMIN_ID,
)
from core.utils import get_set_maintenance_in_cache
from django.conf import settings
from django.core.cache import cache
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_auto_logout.utils import now, seconds_until_idle_time_end, seconds_until_session_end

logger = logging.getLogger(__name__)


def constants_import(request):
    """
    Automatický import stavov projektú do kontextu všech template.
    """
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
    """
    Automatický import linkov na digitálni archiv zo settings do kontextov všech template.
    """
    return getattr(settings, "DIGI_LINKS")


def logout_next_url(request):
    logger.debug(f"request path: {request.path}")
    return {"logout_next_url": request.path}


# for autologout function redirect immediatelly
def auto_logout_client(request):
    """
    Automatický výpočet a import kontextu potrebného pro správne zobrzazení automatického logoutu na všech stránkach.
    """
    if request.user.is_anonymous:
        return {}

    options = getattr(settings, "AUTO_LOGOUT")
    if not options:
        return {}

    ctx = {}
    current_time = now()

    ctx["maintenance_logout_text"] = mark_safe("0")
    maintenance_logout = False
    maintenance = get_set_maintenance_in_cache()
    if maintenance:
        time_difference = int(
            (
                pytz.timezone("Europe/Prague").localize(
                    datetime.combine(maintenance.datum_odstavky, maintenance.cas_odstavky)
                )
                - datetime.now(pytz.timezone("Europe/Prague"))
            ).total_seconds()
        )
        if time_difference < 3601 and time_difference > 0:
            maintenance_logout = True

    if "SESSION_TIME" in options:
        ctx["seconds_until_session_end"] = seconds_until_session_end(request, options["SESSION_TIME"], current_time)
    if not maintenance_logout:
        if "IDLE_TIME" in options:
            ctx["seconds_until_idle_end"] = seconds_until_idle_time_end(request, options["IDLE_TIME"], current_time)
        if "IDLE_WARNING_TIME" in options:
            ctx["IDLE_WARNING_TIME"] = mark_safe(options["IDLE_WARNING_TIME"])

        if options.get("REDIRECT_TO_LOGIN_IMMEDIATELY"):
            ctx["redirect_to_login_immediately"] = "logoutFunction"
            ctx["extra_param"] = mark_safe({"logout_type": "autologout"})
        else:
            ctx["redirect_to_login_immediately"] = "showTimeToExpire"
            ctx["extra_param"] = mark_safe(_("core.context_processors.autologout.expired.text"))
        ctx["logout_warning_text"] = mark_safe("AUTOLOGOUT_EXPIRATION_WARNING")
    else:
        logger.debug("core.context_processors.auto_logout_client_maintenance_logout")
        ctx["seconds_until_idle_end"] = time_difference
        ctx["redirect_to_login_immediately"] = "logoutFunction"
        ctx["extra_param"] = mark_safe({"logout_type": "maintenance"})
        user_cache = str(request.user.id) + "logout_warning"
        if cache.get(user_cache, True) and time_difference < 605:
            cache.set(user_cache, False, 3600)
            ctx["IDLE_WARNING_TIME"] = ctx["seconds_until_idle_end"] - 5
            ctx["logout_warning_text"] = mark_safe("MAINTENANCE_LOGOUT_WARNING")
        ctx["maintenance"] = mark_safe("true")

    return ctx


def main_shows(request):
    main_show = {}
    if request.user.is_authenticated:
        if request.user.hlavni_role.id == ROLE_ADMIN_ID:
            main_show["show_administrace"] = True
        if request.user.is_archiver_or_more:
            main_show["show_projekt_schvalit"] = True
            main_show["show_projekt_archivovat"] = True
            main_show["show_projekt_zrusit"] = True
            main_show["show_samakce_archivovat"] = True
            main_show["show_lokalita_archivovat"] = True
            main_show["show_knihovna_archivovat"] = True
            main_show["show_dokumenty_archivovat"] = True
            main_show["show_pas_archivovat"] = True
            main_show["show_ez_archivovat"] = True
            main_show["show_dokumenty_zapsat"] = True
        if request.user.is_archeolog_or_more:
            main_show["show_pas_nase"] = True
            main_show["show_pas_potvrdit"] = True
            main_show["show_projekt"] = True
    return main_show
