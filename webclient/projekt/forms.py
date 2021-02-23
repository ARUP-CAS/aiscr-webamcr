import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from django.contrib.gis import forms
from django.utils.translation import gettext as _
from projekt.models import Projekt

logger = logging.getLogger(__name__)


class ProjektForm(forms.ModelForm):
    latitude = forms.FloatField(required=True)
    longitude = forms.FloatField(required=True)

    class Meta:
        model = Projekt
        fields = ("ident_cely", "lokalizace", "parcelni_cislo", "latitude", "longitude")
        widgets = {
            "ident_cely": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "lokalizace": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }
        labels = {
            "ident_cely": _("ident_cely"),
            "lokalizace": _("Lokalizace"),
            "parcelni_cislo": _("Parcelní číslo"),
        }
        help_texts = {
            "lokalizace": _("Prosím zadeje lokalizaci."),
            "parcelni_cislo": _("Prosím zadejte parcelní číslo."),
        }

    def save(self, commit=True):
        # do something with self.cleaned_data['id']
        return super(ProjektForm, self).save(commit=commit)

    def __init__(self, *args, **kwargs):
        super(ProjektForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Projekt")),
                    css_class="card-header",
                ),
                Div(
                    "ident_cely",
                    "lokalizace",
                    "parcelni_cislo",
                    Div(
                        #Div("latitude", css_class="col-sm-6,"),
                        #Div("longitude", css_class="col-sm-6"),
                         Div("latitude", css_class="hidden"),
                         Div("longitude", css_class="hidden"),
                        css_class="row",
                    ),
                    css_class="card-body",
                ),
                css_class="card",
            )
        )
        self.helper.form_tag = False
