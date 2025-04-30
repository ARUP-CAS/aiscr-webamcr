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
    maintenance = get_set_maintenance_in_cache()
    if maintenance:
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
    logger.error(
        "core.template_tags.get_settings.missing_settings", extra={"item_group": item_group, "item_id": item_id}
    )
    return ""


@register.simple_tag
def message_top(forloop_counter):
    # 65px is the height of the message incl. margin
    return forloop_counter * 65 + 15


@register.simple_tag
def get_datetime_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@register.simple_tag
def get_test_env():
    return settings.TEST_ENV
