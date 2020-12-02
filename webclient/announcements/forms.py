from django import forms
from django.utils.translation import gettext_lazy as _

from webclient.validators import validate_phone_number


class AnnouncementForm(forms.Form):
    # Announcer part
    phone = forms.CharField(label=_('Telefon'), max_length=15, required=True, validators=[validate_phone_number])
    email = forms.EmailField(label=_('Email'), required=True)
    representative = forms.CharField(label=_('Zástupce'), max_length=100, required=True)
    person = forms.CharField(label=_('Osoba realizující stavební či jiný záměr'), max_length=100, required=True)
    # Time schedule part
    expected_start_date = forms.DateField(label=_('Předpokládaný datum zahájení prací'), required=True)
    expected_end_date = forms.DateField(label=_('Předpokládaný datum ukončení prací'), required=True)
    # Intention description part
    localization = forms.CharField(label=_('Lokalizace'), required=True)
    parcel_number = forms.CharField(label=_('Parcelní číslo'), required=True)
    stimul = forms.CharField(label=_('Podnět'), required=True)
    cadastre = forms.ChoiceField(label=_('Katastr'), required=True)
    other_cadastres = forms.MultipleChoiceField(label=_('Další katastry'))
