import core.message_constants as mc

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# to get message constant for auto logout
@register.simple_tag
def get_message(message):
    return mark_safe("'%s'" % str(getattr(mc, message)))
