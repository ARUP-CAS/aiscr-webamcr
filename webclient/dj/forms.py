from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from dal import autocomplete
from dj.models import DokumentacniJednotka
from django import forms
from django.utils.translation import gettext as _


class MyAutocompleteWidget(autocomplete.ModelSelect2):
    def media(self):
        return ()


class CreateDJForm(forms.ModelForm):
    class Meta:
        model = DokumentacniJednotka
        fields = ("typ", "negativni_jednotka", "nazev", "pian")

        labels = {
            "typ": _("Typ"),
            "negativni_jednotka": _("Negativní zjištění"),
            "nazev": _("Název"),
            "pian": _("Pian"),
        }

        widgets = {
            "nazev": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "pian": MyAutocompleteWidget(url="pian:pian-autocomplete"),
        }

    def __init__(
        self,
        *args,
        not_readonly=True,
        **kwargs,
    ):
        super(CreateDJForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("typ", css_class="col-sm-3"),
                Div("nazev", css_class="col-sm-3"),
                Div("negativni_jednotka", css_class="col-sm-3"),
                Div("pian", css_class="col-sm-3"),
                css_class="row align-items-end",
            ),
        )
        if not not_readonly:
            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"
