from core.forms import HeslarChoiceFieldField, TwoLevelSelectField
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _
from nalez.models import NalezObjekt, NalezPredmet


class NalezFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "bootstrap4/table_inline_formset.html"
        self.form_tag = False


# Will subclass this function so that I can pass choices to formsets in formsetfactory call as arguments
def create_nalez_objekt_form(druh_obj_choices, spec_obj_choices, not_readonly=True):
    class CreateNalezObjektForm(forms.ModelForm):
        class Meta:
            model = NalezObjekt
            fields = ("druh", "specifikace", "pocet", "poznamka")
            labels = {"pocet": _("Počet"), "poznamka": _("Poznámka")}
            widgets = {
                "poznamka": forms.Textarea(attrs={"rows": 1, "cols": 40}),
                "pocet": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            }

        def __init__(
            self,
            druh_objekt_choices=druh_obj_choices,
            specifikace_objekt_choices=spec_obj_choices,
            *args,
            **kwargs
        ):
            super(CreateNalezObjektForm, self).__init__(*args, **kwargs)
            self.fields["druh"] = TwoLevelSelectField(
                label=_("Druh"),
                widget=forms.Select(
                    choices=druh_objekt_choices,
                    attrs={"class": "selectpicker", "data-live-search": "true"},
                ),
            )
            self.fields["specifikace"] = TwoLevelSelectField(
                label=_("Specifikace"),
                widget=forms.Select(
                    choices=specifikace_objekt_choices,
                    attrs={"class": "selectpicker", "data-live-search": "true"},
                ),
            )
            self.fields["specifikace"].required = False

            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if self.fields[key].disabled == True:
                    if isinstance(self.fields[key].widget, forms.widgets.Select):
                        self.fields[
                            key
                        ].widget.template_name = "core/select_to_text.html"

    return CreateNalezObjektForm


def create_nalez_predmet_form(
    druh_projekt_choices, specifikce_predmetu_choices, not_readonly=True
):
    class CreateNalezPredmetForm(forms.ModelForm):
        class Meta:
            model = NalezPredmet

            fields = ("druh", "specifikace", "pocet", "poznamka")

            labels = {
                "pocet": _("Počet"),
                "poznamka": _("Poznámka"),
            }

            widgets = {
                "poznamka": forms.Textarea(attrs={"rows": 1, "cols": 40}),
                "pocet": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            }

        def __init__(self, *args, **kwargs):
            super(CreateNalezPredmetForm, self).__init__(*args, **kwargs)
            self.fields["druh"] = TwoLevelSelectField(
                label=_("Druh"),
                widget=forms.Select(
                    choices=druh_projekt_choices,
                    attrs={"class": "selectpicker", "data-live-search": "true"},
                ),
            )
            self.fields["specifikace"] = HeslarChoiceFieldField(
                label=_("Specifikace"),
                choices=[("", "")] + specifikce_predmetu_choices,
            )
            self.fields["specifikace"].widget.attrs = {
                "class": "selectpicker",
                "data-live-search": "true",
            }
            self.fields["specifikace"].required = True

            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if self.fields[key].disabled == True:
                    if isinstance(self.fields[key].widget, forms.widgets.Select):
                        self.fields[
                            key
                        ].widget.template_name = "core/select_to_text.html"

    return CreateNalezPredmetForm
