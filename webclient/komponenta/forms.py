from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
)
from heslar.views import heslar_12
from komponenta.models import Komponenta


class CreateKomponentaForm(forms.ModelForm):
    class Meta:
        model = Komponenta
        fields = (
            "presna_datace",
            "poznamka",
            "jistota",
            "aktivity",
        )

        labels = {
            "presna_datace": _("Přesná datace"),
            "poznamka": _("Poznámka"),
            "jistota": _("Jistota"),
            "aktivity": _("Aktivity"),
        }

        widgets = {}

    def __init__(self, *args, **kwargs):
        super(CreateKomponentaForm, self).__init__(*args, **kwargs)
        obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
        areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
        self.fields["obdobi"] = forms.CharField(
            label=_("Období"),
            widget=forms.Select(
                choices=obdobi_choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.fields["areal"] = forms.CharField(
            label=_("Areál"),
            widget=forms.Select(
                choices=areal_choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False
