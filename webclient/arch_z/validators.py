import datetime

from django import forms
from django.utils.translation import gettext as _


def datum_max_1_mesic_v_budoucnosti(value):
    """
    Metóda pro validaci dátumu měsíc do budoucnosti.
    """
    if value > datetime.date.today() + datetime.timedelta(days=30):
        raise forms.ValidationError(_("arch_z.validators.maxDatum.error"))
    return value
