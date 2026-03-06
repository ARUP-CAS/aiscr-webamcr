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
    """
    Vrátí bezpečně escapovaný text konstanty podle jejího názvu.

    :param message: Textová zpráva ``message`` používaná pro hlášení stavu nebo chyby.
    """
    return mark_safe("'%s'" % str(getattr(mc, message, "Message constant not found")))


class QuerystringNodeMulti(Node):
    """Implementuje komponentu ``QuerystringNodeMulti`` v rámci aplikace."""

    def __init__(self, updates, removals, asvar=None):
        """
        Inicializuje instanci třídy.

        :param updates: Časový údaj ``updates`` použitý při filtrování nebo výpočtu.
        :param removals: Kolekce nebo datová struktura `removals` zpracovávaná touto funkcí.
        :param asvar: Číselná nebo geometrická hodnota `asvar` použitá při výpočtu nebo transformaci.
        """
        super().__init__()
        self.updates = updates
        self.removals = removals
        self.asvar = asvar

    def render(self, context):
        """
        Vyrenderuje hodnotu. v aplikaci.

        :param context: Kontextová data používaná při serializaci nebo renderování.
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
    """
    Provádí operaci querystring multi.

    :param parser: Typová nebo konfigurační hodnota `parser` určující cílovou logiku.
    :param token: Textový nebo strukturální vstup `token` používaný při sestavení nebo zpracování obsahu.
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
    """Vrací maintenance. v aplikaci."""
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
    """
    Vrací settings. v aplikaci.

    :param item_group: Doménový objekt `item_group`, se kterým funkce pracuje.
    :param item_id: Identifikátor objektu ``item``.
    """
    settings_query = CustomAdminSettings.objects.filter(item_group=item_group, item_id=item_id)
    if settings_query.count() > 0:
        return settings_query.last().value
    logger.error("core.template_tags.get_settings.missing_settings", extra={"group": item_group, "pk": item_id})
    return ""


@register.simple_tag
def message_top(forloop_counter):
    """
    Vypočítá vertikální offset pro vykreslení systémových zpráv.

    :param forloop_counter: Číselná nebo geometrická hodnota `forloop_counter` použitá při výpočtu nebo transformaci.
    """
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
