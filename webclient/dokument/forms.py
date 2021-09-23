from core.constants import COORDINATE_SYSTEM
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.forms import HiddenInput
from django.utils.translation import gettext as _
from dokument.models import Dokument, DokumentExtraData, Let
from heslar.hesla import (
    ALLOWED_DOKUMENT_TYPES,
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_ULOZENI,
    HESLAR_JAZYK,
    HESLAR_POSUDEK_TYP,
    MODEL_3D_DOKUMENT_TYPES,
)
from heslar.models import Heslar
from uzivatel.models import Osoba


class CoordinatesDokumentForm(forms.Form):
    detector_system_coordinates = forms.ChoiceField(
        label=_("Souř. systém"), choices=COORDINATE_SYSTEM, required=False
    )
    detector_coordinates_x = forms.CharField(label=_("Šířka (N / Y)"), required=False)
    detector_coordinates_y = forms.CharField(label=_("Délka (E / X)"), required=False)


class EditDokumentExtraDataForm(forms.ModelForm):
    rada = forms.CharField(label="Řada", required=False)
    let = forms.ChoiceField(
        label="Let",
        required=False,
        choices=tuple(
            [("", "")] + list(Let.objects.all().values_list("id", "ident_cely"))
        ),
        widget=forms.Select(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )
    dokument_osoba = forms.MultipleChoiceField(
        label="Dokumentované osoby",
        required=False,
        choices=Osoba.objects.all().values_list("id", "vypis_cely"),
        widget=forms.SelectMultiple(
            attrs={"class": "selectpicker", "data-live-search": "true"}
        ),
    )

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
            "meritko": forms.TextInput(),
            "cislo_objektu": forms.TextInput(),
            "region": forms.TextInput(),
            "udalost": forms.TextInput(),
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

    def __init__(self, *args, readonly=False, **kwargs):
        rada = kwargs.pop("rada", None)
        let = kwargs.pop("let", "")
        dok_osoby = kwargs.pop("dok_osoby", None)
        edit_prohibited = kwargs.pop("edit", True)
        super(EditDokumentExtraDataForm, self).__init__(*args, **kwargs)
        self.fields["odkaz"].widget.attrs["rows"] = 1
        self.fields["meritko"].widget.attrs["rows"] = 1
        self.fields["cislo_objektu"].widget.attrs["rows"] = 1
        self.fields["region"].widget.attrs["rows"] = 1
        self.fields["udalost"].widget.attrs["rows"] = 1
        self.helper = FormHelper(self)
        self.fields["rada"].initial = rada
        self.fields["let"].initial = let
        self.fields["dokument_osoba"].initial = dok_osoby
        self.helper.layout = Layout(
            Div(
                Div("rada", css_class="col-sm-2"),
                Div("let", css_class="col-sm-2"),
                Div("datum_vzniku", css_class="col-sm-2"),
                Div("zachovalost", css_class="col-sm-2"),
                Div("nahrada", css_class="col-sm-2"),
                Div("pocet_variant_originalu", css_class="col-sm-2"),
                Div("format", css_class="col-sm-2"),
                Div("meritko", css_class="col-sm-2"),
                Div("vyska", css_class="col-sm-2"),
                Div("sirka", css_class="col-sm-2"),
                Div("cislo_objektu", css_class="col-sm-4"),
                Div("zeme", css_class="col-sm-2"),
                Div("region", css_class="col-sm-2"),
                Div("udalost", css_class="col-sm-2"),
                Div("udalost_typ", css_class="col-sm-2"),
                Div("rok_od", css_class="col-sm-2"),
                Div("rok_do", css_class="col-sm-2"),
                Div("duveryhodnost", css_class="col-sm-2"),
                Div("dokument_osoba", css_class="col-sm-2"),
                Div("odkaz", css_class="col-sm-8"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
        self.fields["rada"].disabled = edit_prohibited


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
            "autori",
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
            "autori": forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "oznaceni_originalu": forms.TextInput(),
            "licence": forms.TextInput(),
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
            "autori": _("Autoři"),
        }

    def __init__(self, *args, readonly=False, **kwargs):
        create = kwargs.pop("create", None)
        super(EditDokumentForm, self).__init__(*args, **kwargs)
        self.fields["popis"].widget.attrs["rows"] = 1
        self.fields["poznamka"].widget.attrs["rows"] = 1
        self.fields["jazyky"].choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_JAZYK).values_list("id", "heslo")
        )
        self.fields["posudky"].choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_POSUDEK_TYP).values_list(
                "id", "heslo"
            )
        )
        self.fields["posudky"].required = False
        self.fields["typ_dokumentu"].choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP)
            .filter(id__in=ALLOWED_DOKUMENT_TYPES)
            .values_list("id", "heslo")
        ) + [("", "")]
        self.fields["ulozeni_originalu"].required = True
        self.fields["rok_vzniku"].required = True
        self.fields["licence"].required = True
        self.fields["popis"].required = True
        self.fields["poznamka"].required = False
        if create:
            self.fields["jazyky"].initial = [
                Heslar.objects.get(nazev_heslare=HESLAR_JAZYK, heslo="CS").pk
            ]
            self.fields["ulozeni_originalu"].initial = [
                Heslar.objects.get(
                    nazev_heslare=HESLAR_DOKUMENT_ULOZENI,
                    heslo="primárně digitální dokument",
                ).pk
            ]
            self.fields["licence"].initial = "CC-BY-NC 4.0"
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("autori", css_class="col-sm-2"),
                Div("rok_vzniku", css_class="col-sm-2"),
                Div("organizace", css_class="col-sm-2"),
                Div("typ_dokumentu", css_class="col-sm-2"),
                Div("material_originalu", css_class="col-sm-2"),
                Div("jazyky", css_class="col-sm-2"),
                Div("popis", css_class="col-sm-12"),
                Div("poznamka", css_class="col-sm-12"),
                Div("ulozeni_originalu", css_class="col-sm-2"),
                Div("oznaceni_originalu", css_class="col-sm-2"),
                Div("posudky", css_class="col-sm-2"),
                Div("pristupnost", css_class="col-sm-2"),
                Div("licence", css_class="col-sm-2"),
                Div("datum_zverejneni", css_class="col-sm-2"),
                css_class="row",
            ),
        )

        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
        self.fields["datum_zverejneni"].disabled = True


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
            "rok_vzniku",
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
            "rok_vzniku": _("Rok vzniku"),
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
        self.fields["rok_vzniku"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("typ_dokumentu", css_class="col-sm-4"),
                Div("organizace", css_class="col-sm-4"),
                Div("rok_vzniku", css_class="col-sm-4"),
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
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"


class CreateModelExtraDataForm(forms.ModelForm):
    coordinate_x = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_y = forms.FloatField(required=False, widget=HiddenInput())

    class Meta:
        model = DokumentExtraData
        fields = (
            "format",
            "duveryhodnost",
            "odkaz",
            "zeme",
            "region",
            "vyska",
            "sirka",
        )
        widgets = {
            "format": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "region": forms.TextInput(),
        }
        labels = {
            "format": _("Formát"),
            "duveryhodnost": _("Důvěryhodnost"),
            "odkaz": _("Odkaz na úložiště modelu (např. Sketchfab)"),
            "zeme": _("Země"),
            "region": _("Region"),
            "vyska": _("Délka"),
            "sirka": _("Šířka"),
        }

    def __init__(self, *args, readonly=False, **kwargs):
        super(CreateModelExtraDataForm, self).__init__(*args, **kwargs)
        self.fields["odkaz"].widget.attrs["rows"] = 1
        self.fields["format"].required = True
        # Disabled hodnoty se neposilaji na server
        self.fields["vyska"].widget.attrs["disabled"] = "disabled"
        self.fields["sirka"].widget.attrs["disabled"] = "disabled"
        self.fields["format"].choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT)
            .filter(heslo__startswith="3D")
            .values_list("id", "heslo")
        ) + [("", "")]
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("format", css_class="col-sm-6"),
                Div("duveryhodnost", css_class="col-sm-6"),
                Div("odkaz", css_class="col-sm-12"),
                Div("zeme", css_class="col-sm-3"),
                Div("region", css_class="col-sm-3"),
                Div("vyska", css_class="col-sm-3"),
                Div("sirka", css_class="col-sm-3"),
                Div("coordinate_x", css_class="hidden"),
                Div("coordinate_y", css_class="hidden"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
