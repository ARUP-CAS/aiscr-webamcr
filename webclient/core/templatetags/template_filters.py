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
    display = str()
    for katastr in value:
        display += (katastr.__str__()) + ", "
    return display


@register.filter
def hesla_to_list(value):
    list_hesla = ", ".join(value.values_list("heslo", flat=True))
    return list_hesla


@register.filter
def osoby_to_list(value):
    list_hesla = "; ".join(value.values_list("vypis_cely", flat=True))
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


@register.filter(name="ifinlist")
def ifinlist(widget_optgroups, list):
    string = ""
    for group_name, group_choices, group_index in widget_optgroups:
        for option in group_choices:
            if str(option["value"]) in list:
                if string == "":
                    string = str(option["label"])
                else:
                    string += " ," + str(option["label"])
    return string
