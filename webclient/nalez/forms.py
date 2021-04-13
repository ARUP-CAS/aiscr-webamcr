from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
)
from heslar.views import heslar_12
from nalez.models import NalezObjekt, NalezPredmet


class NalezFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "bootstrap4/table_inline_formset.html"
        self.form_tag = False


class CreateNalezObjektForm(forms.ModelForm):
    class Meta:
        model = NalezObjekt

        fields = ("druh", "specifikace", "pocet", "poznamka")

        labels = {"pocet": _("Počet"), "poznamka": _("Poznámka")}

        widgets = {
            "poznamka": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "pocet": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }

    def __init__(self, *args, **kwargs):
        super(CreateNalezObjektForm, self).__init__(*args, **kwargs)
        druh_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
        specifikace_choices = heslar_12(
            HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT
        )
        self.fields["druh"] = TwoLevelSelectField(
            label=_("Druh"),
            widget=forms.Select(
                choices=druh_choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.fields["specifikace"] = TwoLevelSelectField(
            label=_("Specifikace"),
            widget=forms.Select(
                choices=specifikace_choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )


class CreateNalezPredmetForm(forms.ModelForm):
    class Meta:
        model = NalezPredmet

        fields = ("druh", "specifikace", "pocet", "poznamka")

        labels = {
            "pocet": _("Počet"),
            "poznamka": _("Poznámka"),
            "specifikace": _("Specifikace"),
        }

        widgets = {
            "poznamka": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "pocet": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }

    def __init__(self, *args, **kwargs):
        super(CreateNalezPredmetForm, self).__init__(*args, **kwargs)
        druh_choices = heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)
        self.fields["druh"] = TwoLevelSelectField(
            label=_("Druh"),
            widget=forms.Select(
                choices=druh_choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
