from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from dal import autocomplete
from dj.models import DokumentacniJednotka
from django import forms
from django.utils.translation import gettext as _


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
            "pian": autocomplete.ModelSelect2(url="pian:pian-autocomplete"),
        }

    def __init__(self, *args, **kwargs):
        super(CreateDJForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(
                            HTML(_("Detail")),
                            css_class="app-fx app-left",
                        ),
                        css_class="card-header",
                    ),
                    Div(
                        Div(
                            Div("typ", css_class="col-sm-3"),
                            Div("negativni_jednotka", css_class="col-sm-3"),
                            Div("nazev", css_class="col-sm-3"),
                            Div("pian", css_class="col-sm-3"),
                            css_class="row",
                        ),
                        css_class="card-body",
                    ),
                ),
                css_class="card app-card-form",
            )
        )
