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
