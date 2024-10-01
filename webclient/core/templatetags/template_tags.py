import logging

from datetime import datetime, date, timedelta

import core.message_constants as mc

from django import template
from django.utils.safestring import mark_safe
from django.template import Node, TemplateSyntaxError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.html import escape
from django.utils.http import urlencode

from django_tables2.templatetags.django_tables2 import (
    token_kwargs,
    context_processor_error_msg,
)

from core.models import OdstavkaSystemu, CustomAdminSettings
from django.core.cache import cache

register = template.Library()
logger = logging.getLogger(__name__)


# to get message constant for auto logout
@register.simple_tag
def get_message(message):
    return mark_safe("'%s'" % str(getattr(mc, message, "Message constant not found")))


class QuerystringNodeMulti(Node):
    def __init__(self, updates, removals, asvar=None):
        super().__init__()
        self.updates = updates
        self.removals = removals
        self.asvar = asvar

    def render(self, context):
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
                        if (
                            val == value
                            or val == str("-" + value)
                            or str("-" + val) == str(value)
                        ):
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
    Creates a URL (containing only the query string [including "?"]) derived
    from the current URL's query string, by updating it with the provided
    keyword arguments.
    Example (imagine URL is ``/abc/?gender=male&name=Brad``)::
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

    # ``bits`` should now be empty of a=b pairs, it should either be empty, or
    # have ``without`` arguments.
    if bits and bits.pop(0) != "without":
        raise TemplateSyntaxError("Malformed arguments to '%s'" % tag)
    removals = [parser.compile_filter(bit) for bit in bits]
    return QuerystringNodeMulti(updates, removals, asvar=asvar)


# To get info about maintenance
@register.simple_tag
def get_maintenance():
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
            cache.set("last_maintenance", False, 600)
    if last_maintenance is not None:
        if last_maintenance.datum_odstavky != date.today():
            return True
        elif last_maintenance.cas_odstavky > datetime.now().time():
            return True
    return False


@register.simple_tag
def get_server_domain():
    return settings.EMAIL_SERVER_DOMAIN_NAME


@register.simple_tag
def get_site_url():
    return settings.SITE_URL


@register.simple_tag
def get_settings(item_group, item_id):
    settings_query = CustomAdminSettings.objects.filter(item_group=item_group, item_id=item_id)
    if settings_query.count() > 0:
        return settings_query.last().value
    logger.error("core.template_tags.get_settings.missing_settings",
                 extra={"item_group": item_group, "item_id": item_id})
    return ""
