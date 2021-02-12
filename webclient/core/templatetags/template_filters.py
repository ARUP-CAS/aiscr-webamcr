import logging

from django import template

register = template.Library()

logger = logging.getLogger(__name__)


@register.filter
def url_to_classes(value):
    classes = value.replace("/", " app-")
    return classes
