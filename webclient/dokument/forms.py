import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from dal import autocomplete
from django import forms
from django.db import utils
from django.forms import HiddenInput
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.db.models import Value, IntegerField
from crispy_forms.bootstrap import AppendedText

from core.constants import COORDINATE_SYSTEM, D_STAV_ARCHIVOVANY, D_STAV_ODESLANY
from dokument.models import Dokument, DokumentCast, DokumentExtraData, Let, Tvar
from heslar.hesla import (
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_ULOZENI,
    HESLAR_JAZYK,
    HESLAR_LETFOTO_TVAR,
    HESLAR_POSUDEK_TYP, HESLAR_LICENCE,
)
from heslar.hesla_dynamicka import (
    ALLOWED_DOKUMENT_TYPES,
    MODEL_3D_DOKUMENT_TYPES,
    JAZYK_CS,
    PRIMARNE_DIGITALNI,
)
from heslar.models import Heslar
from uzivatel.models import Osoba
from core.forms import BaseFilterForm

logger = logging.getLogger(__name__)


class AutoriField(forms.models.ModelMultipleChoiceField):
    """
    Třída pro správne zaobcházení s autormi, tak aby jejich uložení pořadí bylo stejné jako zadané uživatelem.
    """
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
    """
    Hlavní formulář pro editaci souřadnic v modelu 3D a PAS.
    """
    visible_ss_combo = forms.ChoiceField(
        label=_("pas.forms.coordinates.detector.label"),
        choices=COORDINATE_SYSTEM,
        required=False,
        help_text=_("pas.forms.coordinates.detector.tooltip"),
    )
    visible_x1 = forms.CharField(
        label=_("pas.forms.coordinates.cor_x1.label"),
        required=False,
        help_text=_("pas.forms.coordinates.cor_x1.tooltip"),
    )
    visible_x2 = forms.CharField(
        label=_("pas.forms.coordinates.cor_x2.label"),
        required=False,
        help_text=_("pas.forms.coordinates.cor_x2.tooltip"),
    )

    coordinate_wgs84_x1 = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_wgs84_x2 = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_sjtsk_x1 = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_sjtsk_x2 = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_system = forms.CharField(
        required=False, widget=HiddenInput(), initial="4326"
    )


class EditDokumentExtraDataForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení Extra dat u dokumentu a modelu 3D.
    """
    rada = forms.CharField(label=_("dokument.forms.editDokumentExtraDataForm.rada.label"), required=False, help_text=_("dokument.forms.editDokumentExtraDataForm.rada.tooltip"),)

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
            "region_extra",
            "udalost",
            "udalost_typ",
            "rok_od",
            "rok_do",
            "duveryhodnost",
        )
        widgets = {
            "zachovalost": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true",
                       "data-container": ".content-with-table-responsive-container",}
            ),
            "nahrada": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true",
                       "data-container": ".content-with-table-responsive-container",}
            ),
            "format": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true",
                       "data-container": ".content-with-table-responsive-container",}
            ),
            "zeme": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true",
                       "data-container": ".content-with-table-responsive-container",}
            ),
            "udalost_typ": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true",
                       "data-container": ".content-with-table-responsive-container",}
            ),
            "meritko": forms.TextInput(),
            "cislo_objektu": forms.TextInput(),
            "region_extra": forms.TextInput(),
            "udalost": forms.TextInput(),
            "odkaz": forms.TextInput(),
            "rok_od":forms.DateInput(attrs={"class": "dateinput form-control date_roky",}),
            "rok_do":forms.DateInput(attrs={"class": "dateinput form-control date_roky",}),
        }
        labels = {
            "datum_vzniku": _("dokument.forms.editDokumentExtraDataForm.datumVzniku.label"),
            "zachovalost": _("dokument.forms.editDokumentExtraDataForm.zachovalost.label"),
            "nahrada": _("dokument.forms.editDokumentExtraDataForm.nahrada.label"),
            "pocet_variant_originalu": _("dokument.forms.editDokumentExtraDataForm.pocetVariantOriginalu.label"),
            "odkaz": _("dokument.forms.editDokumentExtraDataForm.odkaz.label"),
            "format": _("dokument.forms.editDokumentExtraDataForm.format.label"),
            "meritko": _("dokument.forms.editDokumentExtraDataForm.meritko.label"),
            "vyska": _("dokument.forms.editDokumentExtraDataForm.vyska.label"),
            "sirka": _("dokument.forms.editDokumentExtraDataForm.sirka.label"),
            "cislo_objektu": _("dokument.forms.editDokumentExtraDataForm.cisloObjektu.label"),
            "zeme": _("dokument.forms.editDokumentExtraDataForm.zeme.label"),
            "region_extra": _("dokument.forms.editDokumentExtraDataForm.region.label"),
            "udalost": _("dokument.forms.editDokumentExtraDataForm.udalost.label"),
            "udalost_typ": _("dokument.forms.editDokumentExtraDataForm.typUdalosti.label"),
            "rok_od": _("dokument.forms.editDokumentExtraDataForm.rokOd.label"),
            "rok_do": _("dokument.forms.editDokumentExtraDataForm.rokDo.label"),
            "duveryhodnost": _("dokument.forms.editDokumentExtraDataForm.duveryhodnost.label"),
        }
        help_texts = {
            "datum_vzniku": _("dokument.forms.editDokumentExtraDataForm.datumVzniku.tooltip"),
            "zachovalost": _("dokument.forms.editDokumentExtraDataForm.zachovalost.tooltip"),
            "nahrada": _("dokument.forms.editDokumentExtraDataForm.nahrada.tooltip"),
            "pocet_variant_originalu": _(
                "dokument.forms.editDokumentExtraDataForm.pocetVariantOriginalu.tooltip"
            ),
            "odkaz": _("dokument.forms.editDokumentExtraDataForm.odkaz.tooltip"),
            "format": _("dokument.forms.editDokumentExtraDataForm.format.tooltip"),
            "meritko": _("dokument.forms.editDokumentExtraDataForm.meritko.tooltip"),
            "vyska": _("dokument.forms.editDokumentExtraDataForm.vyska.tooltip"),
            "sirka": _("dokument.forms.editDokumentExtraDataForm.sirka.tooltip"),
            "cislo_objektu": _("dokument.forms.editDokumentExtraDataForm.cisloObjektu.tooltip"),
            "zeme": _("dokument.forms.editDokumentExtraDataForm.zeme.tooltip"),
            "region_extra": _("dokument.forms.editDokumentExtraDataForm.region.tooltip"),
            "udalost": _("dokument.forms.editDokumentExtraDataForm.udalost.tooltip"),
            "udalost_typ": _("dokument.forms.editDokumentExtraDataForm.udalostTyp.tooltip"),
            "rok_od": _("dokument.forms.editDokumentExtraDataForm.rokOd.tooltip"),
            "rok_do": _("dokument.forms.editDokumentExtraDataForm.rokDo.tooltip"),
            "duveryhodnost": _("dokument.forms.editDokumentExtraDataForm.duveryhodnost.tooltip"),
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
            self.fields["dokument_osoba"] = forms.ModelMultipleChoiceField(
                queryset=Osoba.objects.all(),
                label=_("dokument.forms.editDokumentExtraDataForm.dokumentovaneOsoby.label"),
                required=False,
                widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
                help_text=_("dokument.forms.editDokumentExtraDataForm.dokumentOsoba.tooltip"),
            )
            self.fields["let"] = forms.ChoiceField(
                choices=tuple(
                    [("", "")] + list(Let.objects.all().values_list("id", "ident_cely"))
                ),
                label=_("dokument.forms.editDokumentExtraDataForm.let.label"),
                required=False,
                widget=forms.Select(
                    attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
                ),
                help_text=_("dokument.forms.editDokumentExtraDataForm.let.tooltip"),
            )
        except utils.ProgrammingError:
            self.fields["dokument_osoba"] = forms.ModelMultipleChoiceField(
                queryset=Osoba.objects.none(),
                label=_("dokument.forms.editDokumentExtraDataForm.osoby.label"),
                required=False,
                widget=autocomplete.ModelSelect2Multiple(url="heslar:osoba-autocomplete"),
            )
            self.fields["let"] = forms.ChoiceField(
                choices=tuple(("", "")),
                label=_("dokument.forms.editDokumentExtraDataForm.let.label"),
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
        self.fields["region_extra"].widget.attrs["rows"] = 1
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
                Div("region_extra", css_class="col-sm-2"),
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
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení Dokumentu.
    """
    autori = AutoriField(Osoba.objects.all(), widget=autocomplete.Select2Multiple(
                url="heslar:osoba-autocomplete",
            ),
            help_text= _("dokument.forms.editDokumentForm.autori.tooltip"),
            label = _("dokument.forms.editDokumentForm.autori.label"),)
    region = forms.ChoiceField(choices=[(None,""),("C-",_("dokument.forms.editDokumentForm.region.C.option")),("M-",_("dokument.forms.editDokumentForm.region.M.option"))],
                label=_("dokument.forms.editDokumentForm.region.label"),
                widget=forms.Select(
                    attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
                ),
                help_text= _("dokument.forms.editDokumentForm.region.tooltip"),)
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
            "licence":  forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "popis": forms.TextInput(),
            "poznamka": forms.TextInput(),
            "rok_vzniku":forms.DateInput(attrs={
                "class": "dateinput form-control date_roky",
            }),
        }
        labels = {
            "organizace": _("dokument.forms.editDokumentForm.organizace.label"),
            "rok_vzniku": _("dokument.forms.editDokumentForm.rokVzniku.label"),
            "material_originalu": _("dokument.forms.editDokumentForm.materialOriginalu.label"),
            "typ_dokumentu": _("dokument.forms.editDokumentForm.typDokumentu.label"),
            "popis": _("dokument.forms.editDokumentForm.popis.label"),
            "poznamka": _("dokument.forms.editDokumentForm.poznamka.label"),
            "ulozeni_originalu": _("dokument.forms.editDokumentForm.ulozeniOriginalu.label"),
            "oznaceni_originalu": _("dokument.forms.editDokumentForm.oznaceniOriginalu.label"),
            "pristupnost": _("dokument.forms.editDokumentForm.pristupnost.label"),
            "datum_zverejneni": _("dokument.forms.editDokumentForm.datumZverejneni.label"),
            "licence": _("dokument.forms.editDokumentForm.licence.label"),
            "jazyky": _("dokument.forms.editDokumentForm.jazyky.label"),
            "posudky": _("dokument.forms.editDokumentForm.posudky.label"),
        }
        help_texts = {
            "organizace": _("dokument.forms.editDokumentForm.organizace.tooltip"),
            "rok_vzniku": _("dokument.forms.editDokumentForm.rokVzniku.tooltip"),
            "material_originalu": _(
                "dokument.forms.editDokumentForm.materialOriginalu.tooltip"
            ),
            "typ_dokumentu": _("dokument.forms.editDokumentForm.typDokumentu.tooltip"),
            "popis": _("dokument.forms.editDokumentForm.popis.tooltip"),
            "poznamka": _("dokument.forms.editDokumentForm.poznamka.tooltip"),
            "ulozeni_originalu": _(
                "dokument.forms.editDokumentForm.ulozeniOriginalu.tooltip"
            ),
            "oznaceni_originalu": _(
                "dokument.forms.editDokumentForm.oznaceniOriginalu.tooltip"
            ),
            "pristupnost": _("dokument.forms.editDokumentForm.pristupnost.tooltip"),
            "datum_zverejneni": _(
                "dokument.forms.editDokumentForm.datumZverejneni.tooltip"
            ),
            "licence": _("dokument.forms.editDokumentForm.licence.tooltip"),
            "jazyky": _("dokument.forms.editDokumentForm.jazyky.tooltip"),
            "posudky": _("dokument.forms.editDokumentForm.posudky.tooltip"),
        }

    def __init__(
        self, *args, readonly=False, required=None, required_next=None, can_edit_datum_zverejneni=False,**kwargs
    ):
        create = kwargs.pop("create", None)
        region_not_required = kwargs.pop("region_not_required", None)
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
                Heslar.objects.get(nazev_heslare=HESLAR_JAZYK, id=JAZYK_CS).pk
            ]
            self.fields["ulozeni_originalu"].initial = [
                Heslar.objects.get(
                    nazev_heslare=HESLAR_DOKUMENT_ULOZENI,
                    id=PRIMARNE_DIGITALNI,
                ).pk
            ]
            self.fields["licence"].initial = (Heslar.objects.filter(nazev_heslare=HESLAR_LICENCE)
                                                  .order_by("razeni").first())
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
        if not can_edit_datum_zverejneni:
            self.fields["datum_zverejneni"].disabled = True
        self.fields["autori"].widget.choices = list(Osoba.objects.filter(
            dokumentautor__dokument__pk=self.instance.pk
        ).order_by("dokumentautor__poradi").values_list("id","vypis_cely"))
        if region_not_required is True:
            self.fields["region"].required = False
        elif create:
            self.fields["region"].required = True


class CreateModelDokumentForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení modelu 3D.
    """
    autori = AutoriField(Osoba.objects.all(), widget=autocomplete.Select2Multiple(
                url="heslar:osoba-autocomplete",
            ),
            help_text= _("dokument.forms.createModelDokumentForm.autori.tooltip"),
            label = _("dokument.forms.createModelDokumentForm.autori.label"),)
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
            "oznaceni_originalu": forms.TextInput(),
            "popis": forms.TextInput(),
            "poznamka": forms.TextInput(),
            "rok_vzniku":forms.DateInput(attrs={
                "class": "dateinput form-control date_roky",
            }),
        }
        labels = {
            "typ_dokumentu": _("dokument.forms.createModelDokumentForm.typDokumentu.label"),
            "organizace": _("dokument.forms.createModelDokumentForm.organizace.label"),
            "oznaceni_originalu": _("dokument.forms.createModelDokumentForm.oznaceniOriginalu.label"),
            "popis": _("dokument.forms.createModelDokumentForm.popis.label"),
            "poznamka": _("dokument.forms.createModelDokumentForm.poznamka.label"),
            "rok_vzniku": _("dokument.forms.createModelDokumentForm.rokVzniku.label"),
        }
        help_texts = {
            "typ_dokumentu": _("dokument.forms.createModelDokumentForm.typDokumentu.tooltip"),
            "organizace": _("dokument.forms.createModelDokumentForm.organizace.tooltip"),
            "oznaceni_originalu": _(
                "dokument.forms.createModelDokumentForm.oznaceniOriginalu.tooltip"
            ),
            "popis": _("dokument.forms.createModelDokumentForm.popis.tooltip"),
            "poznamka": _("dokument.forms.createModelDokumentForm.poznamka.tooltip"),
            "rok_vzniku": _("dokument.forms.createModelDokumentForm.rokVzniku.tooltip"),
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
        self.fields["autori"].widget.choices = list(Osoba.objects.filter(
            dokumentautor__dokument__pk=self.instance.pk
        ).order_by("dokumentautor__poradi").values_list("id","vypis_cely"))


class CreateModelExtraDataForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení extra dat modelu 3D.
    """
    coordinate_wgs84_x1 = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_wgs84_x2 = forms.FloatField(required=False, widget=HiddenInput())

    visible_x1 = forms.CharField(
        label=_("dokument.forms.createModelExtraDataForm.cor_x1.label"),
        required=False,
        help_text=_("dokument.forms.createModelExtraDataForm.cor_x1.tooltip"),
    )
    visible_x2 = forms.CharField(
        label=_("dokument.forms.createModelExtraDataForm.cor_x2.label"),
        required=False,
        help_text=_("dokument.forms.createModelExtraDataForm.cor_x2.tooltip"),
    )

    class Meta:
        model = DokumentExtraData
        fields = (
            "format",
            "duveryhodnost",
            "odkaz",
            "zeme",
            "region_extra",
        )
        widgets = {
            "format": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "region_extra": forms.TextInput(),
            "duveryhodnost": forms.NumberInput(attrs={"max": "100", "min": "0"}),
            "odkaz": forms.TextInput(),
            "zeme": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
        }
        labels = {
            "format": _("dokument.forms.createModelExtraDataForm.format.label"),
            "duveryhodnost": _("dokument.forms.createModelExtraDataForm.duveryhodnost.label"),
            "odkaz": _("dokument.forms.createModelExtraDataForm.odkaz.label"),
            "zeme": _("dokument.forms.createModelExtraDataForm.zeme.label"),
            "region_extra": _("dokument.forms.createModelExtraDataForm.region_extra.label"),
        }
        help_texts = {
            "format": _("dokument.forms.createModelExtraDataForm.format.tooltip"),
            "duveryhodnost": _("dokument.forms.createModelExtraDataForm.duveryhodnost.tooltip"),
            "odkaz": _("dokument.forms.createModelExtraDataForm.odkaz.tooltip"),
            "zeme": _("dokument.forms.createModelExtraDataForm.zeme.tooltip"),
            "region_extra": _("dokument.forms.createModelExtraDataForm.region_extra.tooltip"),
        }

    def __init__(
        self, *args, readonly=False, required=None, required_next=None, **kwargs
    ):
        super(CreateModelExtraDataForm, self).__init__(*args, **kwargs)
        # self.fields["format"].required = True
        # Disabled hodnoty se neposilaji na server
        self.fields["visible_x1"].widget.attrs["disabled"] = "disabled"
        self.fields["visible_x2"].widget.attrs["disabled"] = "disabled"
        self.fields["format"].choices = [("", "")] + list(
            Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT)
            .filter(heslo__startswith="3D")
            .values_list("id", "heslo")
        )
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
    """
    Hlavní formulář připojení dokumentu do projektu nebo arch záznamu.
    """
    def __init__(self, projekt=None, *args, **kwargs):
        super(PripojitDokumentForm, self).__init__(projekt, *args, **kwargs)
        self.fields["dokument"] = forms.MultipleChoiceField(
            label=_("dokument.forms.pripojitDokumentForm.dokument.label"),
            choices=list(
                Dokument.objects.filter(
                    stav__in=(D_STAV_ARCHIVOVANY, D_STAV_ODESLANY)
                ).values_list("id", "ident_cely")
            ),
            widget=autocomplete.Select2Multiple(
                url=reverse("dokument:dokument-autocomplete")
            ),
            help_text=_("dokument.forms.pripojitDokumentForm.dokument.tooltip")
        )
        self.fields["dokument"].required = True
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class DokumentCastForm(forms.ModelForm):
    """
    Hlavní formulář pro zobrazení Dokument části.
    """
    poznamka = forms.CharField(
        help_text=_("dokument.forms.dokumentCastForm.poznamka.tooltip"),
        label=_("dokument.forms.dokumentCastForm.poznamka.label"),
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
    """
    Hlavní formulář pro vytvoření, editaci Dokument části.
    """
    poznamka = forms.CharField(
        help_text=_("dokument.forms.dokumentCastCreateForm.poznamka.tooltip"),
        label=_("dokument.forms.dokumentCastCreateForm.poznamka.label"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(DokumentCastCreateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False


def create_tvar_form(not_readonly=True):
    """
    Funkce která vrací formulář Tvar pro formset.
    Pomocí ní je možné předat výběr formuláři.
    """
    class TvarForm(forms.ModelForm):
        class Meta:
            model = Tvar
            fields = ["tvar", "poznamka"]
            labels = {"tvar": _("dokument.forms.tvarForm.tvar.label"), "poznamka": _("dokument.forms.tvarForm.poznamka.label")}
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
                "tvar": _("dokument.forms.tvarForm.tvar.tooltip"),
                "poznamka": _("dokument.forms.tvarForm.poznamka.tooltip"),
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
    """
    Form helper pro správne vykreslení formuláře tvarů.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "inline_formset.html"
        self.form_tag = False
        self.form_id = "tvar"

class DokumentFilterForm(BaseFilterForm):
    list_to_check = ["historie_datum_zmeny_od","datum_vzniku","let_datum","datum_zverejneni"]
