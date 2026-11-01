"""Šablonové tagy pro překlad zpráv s pojmenovanými zástupnými znaky."""

from core.translation import format_message
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


# Přeloží ID zprávy a dosadí do překladu pojmenované parametry.
@register.simple_tag
def translate_format(message_id, **params):
    """
    Vrátí přeloženou zprávu s dosazenými pojmenovanými zástupnými znaky.

    Šablona předává hodnoty jako pojmenované argumenty, takže překlad drží celou větu
    a pořadí slov určuje překladatel. Nahrazuje skládání klíče a proměnných uvnitř
    ``blocktranslate``, kde se do ID zprávy vlepují názvy zástupných znaků.

    :param message_id: Překladové ID zprávy.
    :param params: Hodnoty pro pojmenované zástupné znaky v překladu.

        :return: Vrací přeloženou zprávu označenou jako bezpečný HTML.
    """
    return mark_safe(format_message(message_id, **params))
