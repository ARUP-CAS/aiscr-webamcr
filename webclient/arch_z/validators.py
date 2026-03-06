import datetime

from django import forms
from django.utils.translation import gettext as _


def datum_max_1_mesic_v_budoucnosti(value):
    """
    Metoda pro validaci dátumu měsíc do budoucnosti.

    :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
    """
    if value > datetime.date.today() + datetime.timedelta(days=30):
        raise forms.ValidationError(_("arch_z.validators.maxDatum.error"))
    return value
