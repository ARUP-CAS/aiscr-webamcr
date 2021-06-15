from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.contrib.gis.forms import OSMWidget
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
)
from heslar.views import heslar_12
from pas.models import SamostatnyNalez


class CreateSamostatnyNalezForm(forms.ModelForm):
    class Meta:
        model = SamostatnyNalez
        fields = (
            "projekt",
            "nalezce",
            "datum_nalezu",
            "lokalizace",
            "okolnosti",
            "hloubka",
            "geom",
            "obdobi",
            "druh_nalezu",
            "pocet",
            "presna_datace",
            "specifikace",  # material
            "poznamka",
        )
        widgets = {
            "projekt": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "nalezce": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "okolnosti": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "specifikace": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "geom": OSMWidget(
                attrs={"default_lat": 50.05, "default_lon": 14.05, "default_zoom": 6}
            ),
        }
        labels = {
            "projekt": _("Projekt"),
            "nalezce": _("Nálezce"),
            "datum_nalezu": _("Datum nálezu"),
            "lokalizace": _("Lokalizace"),
            "okolnosti": _("Nálezové okolnosti"),
            "hloubka": _("Hloubka (cm)"),
            "geom": _("Poloha"),
            "obdobi": _("Období"),
            "druh_nalezu": _("Nález"),
            "pocet": _("Počet"),
            "presna_datace": _("Přesná datace"),
            "specifikace": _("Materiál"),
            "poznamka": _("Poznámka / bližší popis"),
        }

    def __init__(self, *args, readonly=False, **kwargs):
        super(CreateSamostatnyNalezForm, self).__init__(*args, **kwargs)
        self.fields["lokalizace"].widget.attrs["rows"] = 1
        self.fields["pocet"].widget.attrs["rows"] = 1
        self.fields["presna_datace"].widget.attrs["rows"] = 1
        self.fields["poznamka"].widget.attrs["rows"] = 1
        self.fields["lokalizace"].required = True
        self.fields["datum_nalezu"].required = True
        self.fields["okolnosti"].required = True
        self.fields["specifikace"].required = True
        self.fields["geom"].required = True
        self.fields["geom"].widget.template_name = "dokument/openlayers-osm.html"
        self.fields["druh_nalezu"] = TwoLevelSelectField(
            label=_("Druh nálezu"),
            widget=forms.Select(
                choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT),
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.fields["obdobi"] = TwoLevelSelectField(
            label=_("Období"),
            widget=forms.Select(
                choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT),
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("projekt", css_class="col-sm-4"),
                Div("nalezce", css_class="col-sm-4"),
                Div("datum_nalezu", css_class="col-sm-4"),
                Div("lokalizace", css_class="col-sm-12"),
                Div("okolnosti", css_class="col-sm-6"),
                Div("hloubka", css_class="col-sm-6"),
                Div("geom", css_class="col-sm-12"),
                Div("obdobi", css_class="col-sm-4"),
                Div("druh_nalezu", css_class="col-sm-4"),
                Div("pocet", css_class="col-sm-4"),
                Div("presna_datace", css_class="col-sm-4"),
                Div("specifikace", css_class="col-sm-4"),
                Div("poznamka", css_class="col-sm-4"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
