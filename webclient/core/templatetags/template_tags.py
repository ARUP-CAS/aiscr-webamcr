import logging
from datetime import datetime

import core.message_constants as mc
from core.setting_models import CustomAdminSettings
from core.utils import get_set_maintenance_in_cache
from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import Node, TemplateSyntaxError
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django_tables2.templatetags.django_tables2 import context_processor_error_msg, token_kwargs

register = template.Library()
logger = logging.getLogger(__name__)


# Získá textovou konstantu zprávy pro automatické odhlášení.
@register.simple_tag
def get_message(message):
    """Vrátí bezpečně escapovaný text konstanty podle jejího názvu."""
    return mark_safe("'%s'" % str(getattr(mc, message, "Message constant not found")))


class QuerystringNodeMulti(Node):
    """Zapouzdřuje chování třídy ``QuerystringNodeMulti`` pro modul ``webclient.core.templatetags.template_tags``."""
    def __init__(self, updates, removals, asvar=None):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param updates: Vstupní hodnota parametru ``updates`` použitého při zpracování.
        :param removals: Vstupní hodnota parametru ``removals`` použitého při zpracování.
        :param asvar: Vstupní hodnota parametru ``asvar`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__()
        self.updates = updates
        self.removals = removals
        self.asvar = asvar

    def render(self, context):
        """Zajišťuje logiku funkce ``render``.
        
        :param context: Vstupní hodnota parametru ``context`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if "request" not in context:
            raise ImproperlyConfigured(context_processor_error_msg % "querystring")

        params = dict(context["request"].GET)
        old_params = {}
        for key, value in self.updates.items():
            if isinstance(key, str):
                if key in params and key == "sort":
                    old_params[key] = list(params[key])
                    for index, val in enumerate(params[key]):
                        if val == value or val == str("-" + value):
                            old_params[key].pop(index)
                params[key] = value
                continue
            key = key.resolve(context)
            value = value.resolve(context)

            if key not in ("", None):
                if key in params and key == "sort":
                    old_params[key] = list(params[key])
                    for index, val in enumerate(params[key]):
                        if val == value or val == str("-" + value) or str("-" + val) == str(value):
                            old_params[key].pop(index)
                params[key] = value

        for removal in self.removals:
            params.pop(removal.resolve(context), None)
        value = escape("?" + urlencode(params, doseq=True))
        if old_params:
            value = value + escape("&" + urlencode(old_params, doseq=True))

        if self.asvar:
            context[str(self.asvar)] = value
            return ""
        else:
            return value


@register.tag
def querystring_multi(parser, token):
    """Sestaví query string z aktuální URL a upraví jej podle parametrů tagu.

    Příklad (pokud je URL ``/abc/?gender=male&name=Brad``)::
        # {% querystring "name"="abc" "age"=15 %}
        ?name=abc&gender=male&age=15
        {% querystring "name"="Ayers" "age"=20 %}
        ?name=Ayers&gender=male&age=20
        {% querystring "name"="Ayers" without "gender" %}
        ?name=Ayers
    """
    bits = token.split_contents()
    tag = bits.pop(0)
    updates = token_kwargs(bits, parser)

    asvar_key = None
    for key in updates:
        if str(key) == "as":
            asvar_key = key

    if asvar_key is not None:
        asvar = updates[asvar_key]
        del updates[asvar_key]
    else:
        asvar = None

    # V této fázi by ``bits`` nemělo obsahovat páry a=b; buď je prázdné,
    # nebo obsahuje argumenty za klíčovým slovem ``without``.
    if bits and bits.pop(0) != "without":
        raise TemplateSyntaxError("Malformed arguments to '%s'" % tag)
    removals = [parser.compile_filter(bit) for bit in bits]
    return QuerystringNodeMulti(updates, removals, asvar=asvar)


# Vrátí informaci o zapnutém režimu údržby.
@register.simple_tag
def get_maintenance():
    """Zajišťuje logiku funkce ``get_maintenance``.
    
    :return: Návratová hodnota funkce po zpracování vstupních dat.
    """
    if get_set_maintenance_in_cache():
        return True
    return False


@register.simple_tag
def get_server_domain():
    """Vrátí doménu používanou pro e-mailové odkazy."""
    return settings.EMAIL_SERVER_DOMAIN_NAME


@register.simple_tag
def get_site_url():
    """Vrátí základní URL adresu aplikace."""
    return settings.SITE_URL


@register.simple_tag
def get_settings(item_group, item_id):
    """Načte hodnotu konfigurační položky z administrátorského nastavení."""
    settings_query = CustomAdminSettings.objects.filter(item_group=item_group, item_id=item_id)
    if settings_query.count() > 0:
        return settings_query.last().value
    logger.error("core.template_tags.get_settings.missing_settings", extra={"group": item_group, "pk": item_id})
    return ""


@register.simple_tag
def message_top(forloop_counter):
    """Vypočítá vertikální offset pro vykreslení systémových zpráv."""
    # 65 px je výška jedné zprávy včetně okrajů.
    return forloop_counter * 65 + 15


@register.simple_tag
def get_datetime_now():
    """Vrátí aktuální datum a čas ve formátu používaném v šablonách."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@register.simple_tag
def get_test_env():
    """Vrátí příznak testovacího prostředí."""
    return settings.TEST_ENV
