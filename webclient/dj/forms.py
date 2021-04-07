from crispy_forms.helper import FormHelper
from dj.models import DokumentacniJednotka
from django import forms
from django.utils.translation import gettext as _


class CreateDJForm(forms.ModelForm):
    class Meta:
        model = DokumentacniJednotka
        fields = (
            "typ",
            "negativni_jednotka",
            "nazev",
            # "pian"
        )

        labels = {
            "typ": _("Typ"),
            "negativni_jednotka": _("Negativní zjištění"),
            "nazev": _("Název"),
            # "pian": _("Pian")
        }

        widgets = {}

    def __init__(self, *args, **kwargs):
        super(CreateDJForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
