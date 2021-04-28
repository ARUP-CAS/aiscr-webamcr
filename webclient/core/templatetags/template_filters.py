import datetime
import logging

from django import template
from psycopg2._range import DateRange

register = template.Library()

logger = logging.getLogger(__name__)


@register.filter
def url_to_classes(value):
    if value == "/":
        return "app-home"
    if value.endswith("/"):
        value = value[:-1]
    classes = value.replace("/", " app-")
    return classes


@register.filter
def katastry_to_list(value):
    list_katastry = ", ".join(value.values_list("nazev", flat=True))
    return list_katastry


@register.filter
def hesla_to_list(value):
    list_hesla = ", ".join(value.values_list("heslo", flat=True))
    return list_hesla


@register.filter
def render_daterange(value):
    if value == "" or value is None:
        return None
    if isinstance(value, DateRange):
        if value.lower and value.upper:
            return (
                value.lower.strftime("%d.%m.%Y")
                + " - "
                + (value.upper - datetime.timedelta(days=1)).strftime("%d.%m.%Y")
            )
    return str(value)


@register.filter
def last_x_letters(value, x):
    if len(value) > x:
        return value[-x:]
    else:
        return value
