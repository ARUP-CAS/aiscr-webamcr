from django import forms
from django.utils.translation import gettext_lazy as _
from webclient.webclient.validators import validate_phone_number


class AnnouncementForm(forms.Form):
    # Announcer part
    phone = forms.CharField(label=_('Telefon'), max_length=15, required=True, validators=[validate_phone_number])
    email = forms.EmailField(label=_('Email'), required=True)
    representative = forms.CharField(label=_('Zástupce'), max_length=100, required=True)
    person = forms.CharField(label=_('Osoba realizující stavební či jiný záměr'), max_length=100, required=True)
