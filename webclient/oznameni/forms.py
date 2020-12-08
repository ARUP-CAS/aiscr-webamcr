from django import forms
from projekt.models import Projekt

from .models import Oznamovatel

# from webclient.validators import validate_phone_number


class OznamovatelForm(forms.ModelForm):
    class Meta:
        model = Oznamovatel
        fields = ("telefon", "email", "odpovedna_osoba", "oznamovatel", "adresa")


class ProjektOznameniForm(forms.ModelForm):
    class Meta:
        model = Projekt
        fields = ("planovane_zahajeni",)
