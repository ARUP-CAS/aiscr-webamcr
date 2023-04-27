import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from dal import autocomplete
from django import forms
from django.db import utils
from django.forms import HiddenInput
from django.utils.translation import gettext as _
from django.utils.safestring import mark_safe
from django.db.models import Value, IntegerField
from crispy_forms.bootstrap import AppendedText

from core.constants import COORDINATE_SYSTEM, D_STAV_ARCHIVOVANY, D_STAV_ODESLANY
from dokument.models import Dokument, DokumentCast, DokumentExtraData, Let, Tvar
from heslar.hesla import (
    ALLOWED_DOKUMENT_TYPES,
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_ULOZENI,
    HESLAR_JAZYK,
    HESLAR_LETFOTO_TVAR,
    HESLAR_POSUDEK_TYP,
    MODEL_3D_DOKUMENT_TYPES,
)
from heslar.models import Heslar
from uzivatel.models import Osoba

logger = logging.getLogger(__name__)


class AutoriField(forms.models.ModelMultipleChoiceField):
    def clean(self, value):
        qs = super().clean(value)
        if value:
            i = 1
            logger.debug("dokument.forms.AutoriField.clean", extra={"value": value})
            for item in value:
                part_qs = qs.filter(pk=item).annotate(qs_order=Value(i, IntegerField()))
                if i ==1:
                    new_qs = part_qs
                else:
                    new_qs = part_qs.union(new_qs)
                i = i+1
            qs = new_qs.order_by("qs_order")
        return qs


class CoordinatesDokumentForm(forms.Form):
    detector_system_coordinates = forms.ChoiceField(
        label=_("Souř. systém"),
        choices=COORDINATE_SYSTEM,
        required=False,
        help_text=_("dokument.form.coordinates.detector.tooltip"),
    )
    detector_coordinates_x = forms.CharField(
        label=_("Šířka (N / Y)"),
        required=False,
        help_text=_("dokument.form.coordinates.cor_x.tooltip"),
    )
    detector_coordinates_y = forms.CharField(
        label=_("Délka (E / X)"),
        required=False,
        help_text=_("dokument.form.coordinates.cor_y.tooltip"),
    )

    coordinate_wgs84_x = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_wgs84_y = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_sjtsk_x = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_sjtsk_y = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_system = forms.CharField(
        required=False, widget=HiddenInput(), initial="wgs84"
    )


class EditDokumentExtraDataForm(forms.ModelForm):
    rada = forms.CharField(label="Řada", required=False, help_text=_("dokument.form.dokumentExtraData.rada.tooltip"),)

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
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "nahrada": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "format": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "zeme": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "udalost_typ": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "meritko": forms.TextInput(),
            "cislo_objektu": forms.TextInput(),
            "region": forms.TextInput(),
            "udalost": forms.TextInput(),
            "odkaz": forms.TextInput(),
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
        help_texts = {
            "datum_vzniku": _("dokument.form.dokumentExtraData.datum_vzniku.tooltip"),
            "zachovalost": _("dokument.form.dokumentExtraData.zachovalost.tooltip"),
            "nahrada": _("dokument.form.dokumentExtraData.nahrada.tooltip"),
            "pocet_variant_originalu": _(
                "dokument.form.dokumentExtraData.pocet_variant_originalu.tooltip"
            ),
            "odkaz": _("dokument.form.dokumentExtraData.odkaz.tooltip"),
            "format": _("dokument.form.dokumentExtraData.format.tooltip"),
            "meritko": _("dokument.form.dokumentExtraData.meritko.tooltip"),
            "vyska": _("dokument.form.dokumentExtraData.vyska.tooltip"),
            "sirka": _("dokument.form.dokumentExtraData.sirka.tooltip"),
            "cislo_objektu": _("dokument.form.dokumentExtraData.cislo_objektu.tooltip"),
            "zeme": _("dokument.form.dokumentExtraData.zeme.tooltip"),
            "region": _("dokument.form.dokumentExtraData.region.tooltip"),
            "udalost": _("dokument.form.dokumentExtraData.udalost.tooltip"),
            "udalost_typ": _("dokument.form.dokumentExtraData.udalost_typ.tooltip"),
            "rok_od": _("dokument.form.dokumentExtraData.rok_od.tooltip"),
            "rok_do": _("dokument.form.dokumentExtraData.rok_do.tooltip"),
            "duveryhodnost": _("dokument.form.dokumentExtraData.duveryhodnost.tooltip"),
        }

    def __init__(
        self, *args, readonly=False, required=None, required_next=None, **kwargs
    ):
        rada = kwargs.pop("rada", None)
        let = kwargs.pop("let", "")
        dok_osoby = kwargs.pop("dok_osoby", None)
        edit_prohibited = kwargs.pop("edit", True)
        super(EditDokumentExtraDataForm, self).__init__(*args, **kwargs)
        try:
            self.fields["dokument_osoba"] = forms.MultipleChoiceField(
                choices=Osoba.objects.all().values_list("id", "vypis_cely"),
                label="Dokumentované osoby",
                required=False,
                widget=autocomplete.Select2Multiple(url="heslar:osoba-autocomplete-choices"),
                help_text=_("dokument.form.dokumentExtraData.dokument_osoba.tooltip"),
            )
            self.fields["let"] = forms.ChoiceField(
                choices=tuple(
                    [("", "")] + list(Let.objects.all().values_list("id", "ident_cely"))
                ),
                label="Let",
                required=False,
                widget=forms.Select(
                    attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
                ),
                help_text=_("dokument.form.dokumentExtraData.let.tooltip"),
            )
        except utils.ProgrammingError:
            self.fields["dokument_osoba"] = forms.MultipleChoiceField(
                choices=tuple(("", "")),
                label="Dokumentované osoby",
                required=False,
                widget=autocomplete.Select2Multiple(url="heslar:osoba-autocomplete-choices"),
            )
            self.fields["let"] = forms.ChoiceField(
                choices=tuple(("", "")),
                label="Let",
                required=False,
                widget=forms.Select(
                    attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
                ),
            )
        if readonly:
            dok_osoby_div = Div(
                "dokument_osoba",
                css_class="col-sm-2",
            )
        else:
            dok_osoby_div = Div(
                AppendedText(
                    "dokument_osoba",
                    mark_safe('<button id="create-dok-osoba" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'),
                ),
                css_class="col-sm-2 input-osoba select2-input",
            )
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
                dok_osoby_div,
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
                    if key == "let":
                        self.fields[key].widget.url = "#"
                    elif key == "dokument_osoba":
                        self.fields[key].widget = forms.widgets.SelectMultiple()
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
            if required:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(
                        self.fields[key].widget.attrs["class"]
                    ) + (" required-next" if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"] = (
                        "required-next" if key in required_next else ""
                    )
        self.fields["rada"].disabled = edit_prohibited


class EditDokumentForm(forms.ModelForm):
    autori = AutoriField(Osoba.objects.all(), widget=autocomplete.Select2Multiple(
                url="heslar:osoba-autocomplete-choices",
            ),
            help_text= _("dokument.form.createDokument.autori.tooltip"),
            label = _("Autoři"),)
    region = forms.ChoiceField(choices=[("C-",_("dokument.create.regionCech.text")),("M-",_("dokument.create.regionMorava.text"))],
                label=_("dokument.form.createDokument.region.label"),
                required=False,
                widget=forms.Select(
                    attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
                ),
                help_text= _("dokument.form.createDokument.region.tooltip"),)
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
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true", "required": ""}
            ),
            "material_originalu": forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "pristupnost": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "ulozeni_originalu": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "jazyky": forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "posudky": forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "oznaceni_originalu": forms.TextInput(),
            "licence": forms.TextInput(),
            "popis": forms.TextInput(),
            "poznamka": forms.TextInput(),
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
        help_texts = {
            "organizace": _("dokument.form.createDokument.organizace.tooltip"),
            "rok_vzniku": _("dokument.form.createDokument.rok_vzniku.tooltip"),
            "material_originalu": _(
                "dokument.form.createDokument.material_originalu.tooltip"
            ),
            "typ_dokumentu": _("dokument.form.createDokument.typ_dokumentu.tooltip"),
            "popis": _("dokument.form.createDokument.popis.tooltip"),
            "poznamka": _("dokument.form.createDokument.poznamka.tooltip"),
            "ulozeni_originalu": _(
                "dokument.form.createDokument.ulozeni_originalu.tooltip"
            ),
            "oznaceni_originalu": _(
                "dokument.form.createDokument.oznaceni_originalu.tooltip"
            ),
            "pristupnost": _("dokument.form.createDokument.pristupnost.tooltip"),
            "datum_zverejneni": _(
                "dokument.form.createDokument.datum_zverejneni.tooltip"
            ),
            "licence": _("dokument.form.createDokument.licence.tooltip"),
            "jazyky": _("dokument.form.createDokument.jazyky.tooltip"),
            "posudky": _("dokument.form.createDokument.posudky.tooltip"),
        }

    def __init__(
        self, *args, readonly=False, required=None, required_next=None, **kwargs
    ):
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
        if not readonly:
            self.fields["typ_dokumentu"].choices = [("", "")] + list(
                Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP)
                .filter(id__in=ALLOWED_DOKUMENT_TYPES)
                .values_list("id", "heslo")
            )
            autori_div = Div(
                AppendedText(
                    "autori",
                    mark_safe('<button id="create-autor" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'),
                ),
                css_class="col-sm-2 input-osoba select2-input",
            )
        else:
            autori_div = Div(
                "autori",
                css_class="col-sm-2",
            )
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
                autori_div,
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
                Div("region", style="display: none"),
                css_class="row",
            ),
        )
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                if key == "autori":
                    self.fields[key].empty_label = None
                else:
                    self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    if key == "autori":
                        self.fields[key].widget = forms.widgets.SelectMultiple()
                        self.fields[key].widget.attrs.update(
                            {"name_id": str(key) + ";" + str(self.instance)}
                        )
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
                self.fields[key].required = False
            if required:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(
                        self.fields[key].widget.attrs["class"]
                    ) + (" required-next" if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"] = (
                        "required-next" if key in required_next else ""
                    )
        self.fields["datum_zverejneni"].disabled = True
        self.fields["autori"].widget.choices = list(Osoba.objects.filter(
            dokumentautor__dokument=self.instance
        ).order_by("dokumentautor__poradi").values_list("id","vypis_cely"))


class CreateModelDokumentForm(forms.ModelForm):
    autori = AutoriField(Osoba.objects.all(), widget=autocomplete.Select2Multiple(
                url="heslar:osoba-autocomplete-choices",
            ),)
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
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "autori": autocomplete.Select2Multiple(
                url="heslar:osoba-autocomplete-choices",
            ),
            "oznaceni_originalu": forms.TextInput(),
            "popis": forms.TextInput(),
            "poznamka": forms.TextInput(),
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
        help_texts = {
            "typ_dokumentu": _("dokument.form.createModel.typ_dokumentu.tooltip"),
            "organizace": _("dokument.form.createModel.organizace.tooltip"),
            "oznaceni_originalu": _(
                "dokument.form.createModel.oznaceni_originalu.tooltip"
            ),
            "popis": _("dokument.form.createModel.popis.tooltip"),
            "poznamka": _("dokument.form.createModel.poznamka.tooltip"),
            "autori": _("dokument.form.createModel.autori.tooltip"),
            "rok_vzniku": _("dokument.form.createModel.rok_vzniku.tooltip"),
        }

    def __init__(
        self, *args, readonly=False, required=None, required_next=None, **kwargs
    ):
        super(CreateModelDokumentForm, self).__init__(*args, **kwargs)
        self.fields["popis"].widget.attrs["rows"] = 1
        self.fields["poznamka"].widget.attrs["rows"] = 1
        self.fields["typ_dokumentu"].choices = [("", "")] + list(
            Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP)
            .filter(id__in=MODEL_3D_DOKUMENT_TYPES)
            .values_list("id", "heslo")
        )
        self.fields["rok_vzniku"].required = True
        if readonly:
            autori_div = Div(
                "autori",
                css_class="col-sm-6",
            )
        else:
            autori_div = Div(
                AppendedText(
                    "autori",
                    mark_safe('<button id="create-autor" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'),
                ),
                css_class="col-sm-6 input-osoba select2-input",
            )
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div("typ_dokumentu", css_class="col-sm-4"),
            Div("organizace", css_class="col-sm-4"),
            Div("rok_vzniku", css_class="col-sm-4"),
            Div("oznaceni_originalu", css_class="col-sm-6"),
            autori_div,
            Div("popis", css_class="col-sm-12"),
            Div("poznamka", css_class="col-sm-12"),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                if key == "autori":
                    self.fields[key].empty_label = None
                else:
                    self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    if key == "autori":
                        self.fields[key].widget = forms.widgets.Select()
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
                self.fields[key].required = False
            if required:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(
                        self.fields[key].widget.attrs["class"]
                    ) + (" required-next" if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"] = (
                        "required-next" if key in required_next else ""
                    )


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
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "region": forms.TextInput(),
            "duveryhodnost": forms.NumberInput(attrs={"max": "100", "min": "0"}),
            "odkaz": forms.TextInput(),
            "zeme": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
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
        help_texts = {
            "format": _("dokument.form.modelExtraData.format.tooltip"),
            "duveryhodnost": _("dokument.form.modelExtraData.duveryhodnost.tooltip"),
            "odkaz": _("dokument.form.modelExtraData.odkaz.tooltip"),
            "zeme": _("dokument.form.modelExtraData.zeme.tooltip"),
            "region": _("dokument.form.modelExtraData.region.tooltip"),
            "vyska": _("dokument.form.modelExtraData.vyska.tooltip"),
            "sirka": _("dokument.form.modelExtraData.sirka.tooltip"),
        }

    def __init__(
        self, *args, readonly=False, required=None, required_next=None, **kwargs
    ):
        super(CreateModelExtraDataForm, self).__init__(*args, **kwargs)
        # self.fields["format"].required = True
        # Disabled hodnoty se neposilaji na server
        self.fields["vyska"].widget.attrs["disabled"] = "disabled"
        self.fields["sirka"].widget.attrs["disabled"] = "disabled"
        self.fields["format"].choices = [("", "")] + list(
            Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT)
            .filter(heslo__startswith="3D")
            .values_list("id", "heslo")
        )
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
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
                self.fields[key].required = False
            if required:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(
                        self.fields[key].widget.attrs["class"]
                    ) + (" required-next" if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"] = (
                        "required-next" if key in required_next else ""
                    )


class PripojitDokumentForm(forms.Form):
    def __init__(self, projekt=None, *args, **kwargs):
        super(PripojitDokumentForm, self).__init__(projekt, *args, **kwargs)
        self.fields["dokument"] = forms.MultipleChoiceField(
            label=_("Vyberte dokument k připojení"),
            choices=list(
                Dokument.objects.filter(
                    stav__in=(D_STAV_ARCHIVOVANY, D_STAV_ODESLANY)
                ).values_list("id", "ident_cely")
            ),
            widget=autocomplete.Select2Multiple(
                url="dokument:dokument-autocomplete-bez-zapsanych"
            ),
            help_text=_("dokument.form.pripojitDokument.tooltip")
        )
        self.fields["dokument"].required = True
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class DokumentCastForm(forms.ModelForm):
    poznamka = forms.CharField(
        help_text=_("dokument.form.castDokumentu.poznamka.tooltip"),
        label=_("dokument.form.castDokumentu.poznamka.label"),
        required=False,
    )
    class Meta:
        model = DokumentCast
        fields = ("poznamka",)

    def __init__(self, readonly=False, *args, **kwargs):
        super(DokumentCastForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
                self.fields[key].required = False


class DokumentCastCreateForm(forms.Form):
    poznamka = forms.CharField(
        help_text=_("dokument.form.castDokumentu.poznamka.tooltip"),
        label=_("dokument.form.castDokumentu.poznamka.label"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(DokumentCastCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False


# Will subclass this function so that I can pass choices to formsets in formsetfactory call as arguments
def create_tvar_form(not_readonly=True):
    class TvarForm(forms.ModelForm):
        class Meta:
            model = Tvar
            fields = ["tvar", "poznamka"]
            labels = {"tvar": _("Tvar"), "poznamka": _("Poznámka")}
            widgets = {
                "poznamka": forms.TextInput(),
                "tvar": forms.Select(
                    attrs={
                        "class": "selectpicker",
                        "data-multiple-separator": "; ",
                        "data-live-search": "true",
                    },
                ),
            }
            help_texts = {
                "tvar": _("tvar.form.tvar.tooltip"),
                "poznamka": _("tvar.form.poznamka.tooltip"),
            }

        def __init__(self, *args, **kwargs):
            super(TvarForm, self).__init__(*args, **kwargs)
            self.fields["tvar"].required = True
            self.fields["tvar"].choices = [("", "")] + list(
                Heslar.objects.filter(nazev_heslare=HESLAR_LETFOTO_TVAR).values_list(
                    "id", "heslo"
                )
            )
            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if self.fields[key].disabled == True:
                    if isinstance(self.fields[key].widget, forms.widgets.Select):
                        self.fields[
                            key
                        ].widget.template_name = "core/select_to_text.html"
                    self.fields[key].help_text = ""

    return TvarForm


class TvarFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "inline_formset.html"
        self.form_tag = False
        self.form_id = "tvar"