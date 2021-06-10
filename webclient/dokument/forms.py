from core.constants import OBLAST_CHOICES
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.contrib.gis.forms import OSMWidget
from django.utils.translation import gettext as _
from dokument.models import Dokument, DokumentExtraData
from heslar.hesla import (
    ALLOWED_DOKUMENT_TYPES,
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_DOKUMENT_TYP,
    HESLAR_JAZYK,
    HESLAR_POSUDEK_TYP,
    MODEL_3D_DOKUMENT_TYPES,
)
from heslar.models import Heslar


class EditDokumentExtraDataForm(forms.ModelForm):
    class Meta:
        model = DokumentExtraData
        fields = (
            "datum_vzniku",
            "zachovalost",
            "nahrada",
            "pocet_variant_originalu",
            "odkaz",
            "format",
            "meritko",
            "vyska",
            "sirka",
            "cislo_objektu",
            "zeme",
            "region",
            "udalost",
            "udalost_typ",
            "rok_od",
            "rok_do",
            "duveryhodnost",
        )
        widgets = {
            "zachovalost": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "nahrada": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "format": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "zeme": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "udalost_typ": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        }
        labels = {
            "datum_vzniku": _("Datum vzniku"),
            "zachovalost": _("Zachovalost"),
            "nahrada": _("Náhrada"),
            "pocet_variant_originalu": _("Počet variant originálu"),
            "odkaz": _("Odkaz"),
            "format": _("Formát plánu/foto"),
            "meritko": _("Měřítko plánu"),
            "vyska": _("Výška plánu"),
            "sirka": _("Šířka plánu"),
            "cislo_objektu": _("Objekt/kontext"),
            "zeme": _("Země"),
            "region": _("Region"),
            "udalost": _("Událost"),
            "udalost_typ": _("Typ události"),
            "rok_od": _("Rok od"),
            "rok_do": _("Rok do"),
            "duveryhodnost": _("Důvěryhodnost"),
        }

    def __init__(self, *args, **kwargs):
        super(EditDokumentExtraDataForm, self).__init__(*args, **kwargs)
        self.fields["odkaz"].widget.attrs["rows"] = 1
        self.fields["meritko"].widget.attrs["rows"] = 1
        self.fields["cislo_objektu"].widget.attrs["rows"] = 1
        self.fields["region"].widget.attrs["rows"] = 1
        self.fields["udalost"].widget.attrs["rows"] = 1
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("datum_vzniku", css_class="col-sm-4"),
                Div("zachovalost", css_class="col-sm-4"),
                Div("nahrada", css_class="col-sm-4"),
                Div("pocet_variant_originalu", css_class="col-sm-4"),
                Div("odkaz", css_class="col-sm-12"),
                Div("format", css_class="col-sm-4"),
                Div("meritko", css_class="col-sm-4"),
                Div("vyska", css_class="col-sm-4"),
                Div("sirka", css_class="col-sm-4"),
                Div("cislo_objektu", css_class="col-sm-4"),
                Div("zeme", css_class="col-sm-4"),
                Div("region", css_class="col-sm-4"),
                Div("udalost", css_class="col-sm-4"),
                Div("udalost_typ", css_class="col-sm-4"),
                Div("rok_od", css_class="col-sm-4"),
                Div("rok_do", css_class="col-sm-4"),
                Div("duveryhodnost", css_class="col-sm-4"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False


class EditDokumentForm(forms.ModelForm):
    class Meta:
        model = Dokument
        fields = (
            "typ_dokumentu",
            "material_originalu",
            "organizace",
            "rok_vzniku",
            "pristupnost",
            "popis",
            "poznamka",
            "ulozeni_originalu",
            "oznaceni_originalu",
            "datum_zverejneni",
            "licence",
            "jazyky",
            "posudky",
            "osoby",
        )
        widgets = {
            "typ_dokumentu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "material_originalu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "pristupnost": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "ulozeni_originalu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "jazyky": forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "posudky": forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "osoby": forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        }
        labels = {
            "organizace": _("Organizace"),
            "rok_vzniku": _("Rok vzniku"),
            "material_originalu": _("Materiál originálu"),
            "typ_dokumentu": _("Typ dokumentu"),
            "popis": _("Popis"),
            "poznamka": _("Poznámka"),
            "ulozeni_originalu": _("Uložení originálu"),
            "oznaceni_originalu": _("Označení originálu"),
            "pristupnost": _("Přístupnost"),
            "datum_zverejneni": _("Datum zveřejnění"),
            "licence": _("Licence"),
        }

    def __init__(self, *args, **kwargs):
        super(EditDokumentForm, self).__init__(*args, **kwargs)
        self.fields["popis"].widget.attrs["rows"] = 1
        self.fields["poznamka"].widget.attrs["rows"] = 1
        self.fields["oznaceni_originalu"].widget.attrs["rows"] = 1
        self.fields["licence"].widget.attrs["rows"] = 1
        self.fields["jazyky"].required = False
        self.fields["jazyky"].choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_JAZYK).values_list("id", "heslo")
        )
        self.fields["posudky"].required = False
        self.fields["posudky"].choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_POSUDEK_TYP).values_list(
                "id", "heslo"
            )
        )
        self.fields["typ_dokumentu"].choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP)
            .filter(id__in=ALLOWED_DOKUMENT_TYPES)
            .values_list("id", "heslo")
        ) + [("", "")]
        self.fields["osoby"].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("typ_dokumentu", css_class="col-sm-4"),
                Div("material_originalu", css_class="col-sm-4"),
                Div("organizace", css_class="col-sm-4"),
                Div("rok_vzniku", css_class="col-sm-4"),
                Div("pristupnost", css_class="col-sm-4"),
                Div("datum_zverejneni", css_class="col-sm-4"),
                Div("popis", css_class="col-sm-12"),
                Div("poznamka", css_class="col-sm-12"),
                Div("oznaceni_originalu", css_class="col-sm-12"),
                Div("ulozeni_originalu", css_class="col-sm-4"),
                Div("licence", css_class="col-sm-4"),
                Div("jazyky", css_class="col-sm-4"),
                Div("posudky", css_class="col-sm-4"),
                Div("osoby", css_class="col-sm-4"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False


class CreateDokumentForm(EditDokumentForm):

    identifikator = forms.ChoiceField(choices=OBLAST_CHOICES, required=True)

    def __init__(self, *args, **kwargs):
        super(CreateDokumentForm, self).__init__(*args, **kwargs)
        self.fields["identifikator"].widget.attrs = {
            "class": "selectpicker",
            "data-live-search": "true",
        }
        self.helper.layout = Layout(
            Div(
                Div("identifikator", css_class="col-sm-4"),
                Div("typ_dokumentu", css_class="col-sm-4"),
                Div("material_originalu", css_class="col-sm-4"),
                Div("organizace", css_class="col-sm-4"),
                Div("rok_vzniku", css_class="col-sm-4"),
                Div("pristupnost", css_class="col-sm-4"),
                Div("popis", css_class="col-sm-12"),
                Div("poznamka", css_class="col-sm-12"),
                Div("oznaceni_originalu", css_class="col-sm-12"),
                Div("ulozeni_originalu", css_class="col-sm-4"),
                Div("licence", css_class="col-sm-4"),
                Div("jazyky", css_class="col-sm-4"),
                Div("posudky", css_class="col-sm-4"),
                Div("osoby", css_class="col-sm-4"),
                Div("datum_zverejneni", css_class="col-sm-4"),
                css_class="row",
            ),
        )


class CreateModelDokumentForm(forms.ModelForm):
    class Meta:
        model = Dokument
        fields = (
            "typ_dokumentu",
            "organizace",
            "oznaceni_originalu",
            "popis",
            "poznamka",
            "autori",
        )
        widgets = {
            "typ_dokumentu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "autori": forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        }
        labels = {
            "typ_dokumentu": _("Typ dokumentu"),
            "organizace": _("Organizace"),
            "oznaceni_originalu": _("Označení originálu"),
            "popis": _("Popis"),
            "poznamka": _("Poznámka"),
            "autori": _("Autoři"),
        }

    def __init__(self, *args, readonly=False, **kwargs):
        super(CreateModelDokumentForm, self).__init__(*args, **kwargs)
        self.fields["popis"].widget.attrs["rows"] = 1
        self.fields["popis"].required = True
        self.fields["poznamka"].widget.attrs["rows"] = 1
        self.fields["oznaceni_originalu"].widget.attrs["rows"] = 1
        self.fields["typ_dokumentu"].choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP)
            .filter(id__in=MODEL_3D_DOKUMENT_TYPES)
            .values_list("id", "heslo")
        ) + [("", "")]
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("typ_dokumentu", css_class="col-sm-6"),
                Div("organizace", css_class="col-sm-6"),
                Div("oznaceni_originalu", css_class="col-sm-6"),
                Div("autori", css_class="col-sm-6"),
                Div("popis", css_class="col-sm-12"),
                Div("poznamka", css_class="col-sm-12"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly


class CreateModelExtraDataForm(forms.ModelForm):
    class Meta:
        model = DokumentExtraData
        fields = ("format", "datum_vzniku", "duveryhodnost", "geom", "odkaz")
        widgets = {
            "format": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "geom": OSMWidget(
                attrs={"default_lat": 50.05, "default_lon": 14.05, "default_zoom": 6}
            ),
        }
        labels = {
            "datum_vzniku": _("Datum vzniku"),
            "format": _("Formát"),
            "duveryhodnost": _("Důvěryhodnost"),
            "geom": _("Lokalizace (Vyberte prosím polohu)"),
            "odkaz": _("Odkaz na úložiště modelu (např. Sketchfab)"),
        }

    def __init__(self, *args, readonly=False, **kwargs):
        super(CreateModelExtraDataForm, self).__init__(*args, **kwargs)
        self.fields["odkaz"].widget.attrs["rows"] = 1
        self.fields["datum_vzniku"].required = True
        self.fields["geom"].required = True
        self.fields["geom"].widget.template_name = "dokument/openlayers-osm.html"
        self.fields["format"].required = True
        self.fields["format"].choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT)
            .filter(heslo__startswith="3D")
            .values_list("id", "heslo")
        ) + [("", "")]
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("datum_vzniku", css_class="col-sm-4"),
                Div("format", css_class="col-sm-4"),
                Div("duveryhodnost", css_class="col-sm-4"),
                Div("odkaz", css_class="col-sm-12"),
                Div("geom", css_class="col-sm-12"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
