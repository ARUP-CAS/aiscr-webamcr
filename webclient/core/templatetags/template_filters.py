import logging

from django import template

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
def last_x_letters(value, x):
    if len(value) > x:
        return value[-x:]
    else:
        return value
