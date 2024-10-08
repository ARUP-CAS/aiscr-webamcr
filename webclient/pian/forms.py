from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.contrib.gis.forms import HiddenInput
from django.utils.translation import gettext_lazy as _
from pian.models import Pian


class PianCreateForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení pianu.
    """

    class Meta:
        model = Pian
        fields = ("presnost", "geom", "geom_sjtsk", "geom_system")
        labels = {"presnost": _("pian.forms.pianCreateForm.presnost.label")}
        help_texts = {
            "presnost": _("pian.forms.pianCreateForm.presnost.tooltip"),
        }
        widgets = {
            "geom": HiddenInput(),
            "geom_sjtsk": HiddenInput(),
            "geom_system": HiddenInput(),
            "presnost": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
        }

    def __init__(self, presnost=None, *args, **kwargs):
        super(PianCreateForm, self).__init__(*args, **kwargs)
        if presnost:
            self.fields["presnost"].initial = presnost
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.fields["geom_system"].initial = "4326"
        self.helper.layout = Layout(
            Div(
                Div(
                    "presnost",
                    css_class="col-sm-2",
                ),
                Div("geom", css_class="col-sm-2"),
                Div("geom_sjtsk", css_class="col-sm-2"),
                Div("geom_system", css_class="col-sm-2"),
                css_class="row",
            ),
        )
