"""Šablonové tagy pro překlad zpráv s pojmenovanými zástupnými znaky."""

from core.translation import format_message
from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_noop

register = template.Library()

# Registry překladových ID, která se používají jen v šablonách přes ``translate_format``.
# ``makemessages`` je z ``{% translate_format %}`` neumí extrahovat, takže jsou zde obalená
# v ``gettext_noop``; bez toho by je další běh ``makemessages`` označil za nepoužité a překlad
# by z katalogu vypadl.
TEMPLATE_ONLY_MESSAGE_IDS = (
    gettext_noop("oznameni.templates.components.uvod.collapsed.text"),
    gettext_noop("pas.templates.potvrdit_spolupraci.question"),
    gettext_noop("pas.templates.potvrdit_spolupraci.already_active"),
)


# Přeloží ID zprávy a dosadí do překladu pojmenované parametry.
@register.simple_tag
def translate_format(message_id, **params):
    """
    Vrátí přeloženou zprávu s dosazenými pojmenovanými zástupnými znaky.

    Hodnoty z šablony se escapují, takže je nelze vložit jako HTML; bezpečný zůstává jen text
    překladu z katalogu. Hodnota označená jako bezpečná (``mark_safe`` nebo filtr ``safe``)
    se ponechá beze změny, takže volající může výjimku povolit explicitně.

    :param message_id: Překladové ID zprávy.
    :param params: Hodnoty pro pojmenované zástupné znaky v překladu.

    :return: Vrací přeloženou zprávu označenou jako bezpečný HTML.
    """
    safe_params = {key: conditional_escape(value) for key, value in params.items()}
    return mark_safe(format_message(message_id, **safe_params))
