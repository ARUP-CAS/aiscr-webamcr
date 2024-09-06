import logging
import logstash

from adb.models import Adb, VyskovyBod
from crispy_forms.bootstrap import AppendedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from core.coordTransform import convertToJTSK
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from dal import autocomplete

from uzivatel.models import Osoba

logger = logging.getLogger(__name__)


class AdbReadOnlyTextInput(forms.TextInput):
    def format_value(self, value):
        if value:
            osoba_query = Osoba.objects.filter(pk=value)
            if osoba_query.count():
                return osoba_query.first().vypis_cely
        return ""


class CreateADBForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení ADB.
    """
    class Meta:
        model = Adb
        fields = (
            "typ_sondy",
            "uzivatelske_oznaceni_sondy",
            "trat",
            "cislo_popisne",
            "parcelni_cislo",
            "podnet",
            "stratigraficke_jednotky",
            "autor_popisu",
            "rok_popisu",
            "autor_revize",
            "rok_revize",
            "poznamka",
        )

        labels = {
            "typ_sondy": _("adb.forms.createAdbForm.label.typ_sondy"),
            "uzivatelske_oznaceni_sondy": _("adb.forms.createAdbForm.label.uzivatelske_oznaceni_sondy"),
            "trat": _("adb.forms.createAdbForm.label.trat"),
            "cislo_popisne": _("adb.forms.createAdbForm.label.cislo_popisne"),
            "parcelni_cislo": _("adb.forms.createAdbForm.label.parcelni_cislo"),
            "podnet": _("adb.forms.createAdbForm.label.podnet"),
            "stratigraficke_jednotky": _("adb.forms.createAdbForm.label.stratigraficke_jednotky"),
            "autor_popisu": _("adb.forms.createAdbForm.label.autor_popisu"),
            "rok_popisu": _("adb.forms.createAdbForm.label.rok_popisu"),
            "autor_revize": _("adb.forms.createAdbForm.label.autor_revize"),
            "rok_revize": _("adb.forms.createAdbForm.label.rok_revize"),
            "poznamka": _("adb.forms.createAdbForm.label.poznamka"),
        }
        widgets = {
            "typ_sondy": forms.Select(attrs={"class": "selectpicker", "data-multiple-separator": "; ",
                                             "data-live-search": "true"}),
            "podnet": forms.Select(attrs={"class": "selectpicker", "data-multiple-separator": "; ",
                                          "data-live-search": "true"}),
            "uzivatelske_oznaceni_sondy": forms.TextInput(),
            "trat": forms.TextInput(),
            "cislo_popisne": forms.TextInput(),
            "parcelni_cislo": forms.TextInput(),
            "stratigraficke_jednotky": forms.TextInput(),
            "poznamka": forms.TextInput(),
            "autor_popisu": autocomplete.ModelSelect2(url="heslar:osoba-autocomplete"),
            "autor_revize": autocomplete.ModelSelect2(url="heslar:osoba-autocomplete"),
            "rok_popisu": forms.DateInput(attrs={
                "class": "dateinput form-control date_roky",
            }),
            "rok_revize": forms.DateInput(attrs={
                "class": "dateinput form-control date_roky",
            }),
        }

        help_texts = {
            "typ_sondy": _("adb.forms.createAdbForm.tooltip.typSondy"),
            "uzivatelske_oznaceni_sondy": _(
                "adb.forms.createAdbForm.tooltip.uzivatelske_oznaceni_sondy"
            ),
            "trat": _("adb.forms.createAdbForm.tooltip.trat"),
            "cislo_popisne": _("adb.forms.createAdbForm.tooltip.cislo_popisne"),
            "parcelni_cislo": _("adb.forms.createAdbForm.tooltip.parcelni_cislo"),
            "podnet": _("adb.forms.createAdbForm.tooltip.podnet"),
            "stratigraficke_jednotky": _("adb.forms.createAdbForm.tooltip.stratigraficke_jednotky"),
            "autor_popisu": _("adb.forms.createAdbForm.tooltip.autor_popisu"),
            "rok_popisu": _("adb.forms.createAdbForm.tooltip.rok_popisu"),
            "autor_revize": _("adb.forms.createAdbForm.tooltip.autor_revize"),
            "rok_revize": _("adb.forms.createAdbForm.tooltip.rok_revize"),
            "poznamka": _("adb.forms.createAdbForm.tooltip.poznamka"),
        }

    def __init__(self, *args, readonly=False, **kwargs):
        """
        Init metóda pro vytvoření formuláře.
        Args:
            readonly (boolean): nastavuje formulář na readonly.
        """
        super(CreateADBForm, self).__init__(*args, **kwargs)
        self.fields["uzivatelske_oznaceni_sondy"].required = False
        self.fields["autor_revize"].required = False
        self.fields["rok_revize"].required = False
        self.helper = FormHelper(self)
        if readonly:
            self.fields["autor_popisu"].widget = AdbReadOnlyTextInput(attrs={"readonly": "readonly"})
            self.fields["autor_revize"].widget = AdbReadOnlyTextInput(attrs={"readonly": "readonly"})
            self.helper.layout = Layout(
                Div(
                    Div("typ_sondy", css_class="col-sm-2"),
                    Div("podnet", css_class="col-sm-2"),
                    Div("uzivatelske_oznaceni_sondy", css_class="col-sm-2"),
                    Div("trat", css_class="col-sm-2"),
                    Div("cislo_popisne", css_class="col-sm-2"),
                    Div("parcelni_cislo", css_class="col-sm-2"),
                    Div("stratigraficke_jednotky", css_class="col-sm-2"),
                    Div(css_class="col-sm-2"),
                    Div("autor_popisu", css_class="col-sm-2"),
                    Div("rok_popisu", css_class="col-sm-2"),
                    Div("autor_revize", css_class="col-sm-2"),
                    Div("rok_revize", css_class="col-sm-2"),
                    Div("poznamka", css_class="col-sm-12"),
                    css_class="row",
                ),
            )
        else:
            self.helper.layout = Layout(
                Div(
                    Div("typ_sondy", css_class="col-sm-2"),
                    Div("podnet", css_class="col-sm-2"),
                    Div("uzivatelske_oznaceni_sondy", css_class="col-sm-2"),
                    Div("trat", css_class="col-sm-2"),
                    Div("cislo_popisne", css_class="col-sm-2"),
                    Div("parcelni_cislo", css_class="col-sm-2"),
                    Div("stratigraficke_jednotky", css_class="col-sm-2"),
                    Div(css_class="col-sm-2"),
                    Div(
                        AppendedText(
                            "autor_popisu",
                            mark_safe('<button id="create-autor-popisu" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'),
                        ),
                        css_class="col-sm-2 input-osoba select2-input",
                    ),
                    # Div("autor_popisu", css_class="col-sm-2"),
                    Div("rok_popisu", css_class="col-sm-2"),
                    Div(
                        AppendedText(
                            "autor_revize",
                            mark_safe('<button id="create-autor-revize" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'),
                        ),
                        css_class="col-sm-2 input-osoba select2-input",
                    ),
                    # Div("autor_revize", css_class="col-sm-2"),
                    Div("rok_revize", css_class="col-sm-2"),
                    Div("poznamka", css_class="col-sm-12"),
                    css_class="row",
                ),
            )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if self.fields[key].disabled == True:
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"
                self.fields[key].help_text = ""


class VyskovyBodFormSetHelper(FormHelper):
    """
    Form helper pro správne vykreslení formuláře výškovího bodu.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "inline_formset.html"
        self.form_tag = False
        self.form_id = "vb"


def create_vyskovy_bod_form(pian=None, niveleta=None, not_readonly=True):
    """
    Funkce která vrací formulář VB pro formset.

    Args:
        pian (pian): pian objeckt.

        niveleta (niveleta): niveleta objekt.
        
        not_readonly (boolean): nastavuje formulář na readonly.
    
    Returns:
        CreateVysovyBodForm: django model formulář VB
    """
    
    class CreateVyskovyBodForm(forms.ModelForm):
        """
        Hlavní formulář pro vytvoření, editaci a zobrazení VB.
        """
        northing = forms.FloatField(
            label=_("adb.forms.createVyskovyBodForm.label.northing"),
            help_text=_("adb.forms.createVyskovyBodForm.tooltip.northing"),
            min_value=-905000.0, max_value=-400000.0,
        )
        easting = forms.FloatField(
            label=_("adb.forms.createVyskovyBodForm.label.easting"),
            help_text=_("adb.forms.createVyskovyBodForm.tooltip.easting"),
             min_value=-1230000.0, max_value=-930000.0,
        )
        niveleta = forms.FloatField(
            label=_("adb.forms.createVyskovyBodForm.label.niveleta"),
            help_text=_("adb.forms.createVyskovyBodForm.tooltip.niveleta"),
            min_value=100.0, max_value=1610.0,
        )

        class Meta:
            model = VyskovyBod

            fields = ("ident_cely", "typ", "northing", "easting", "niveleta")

            labels = {
                "ident_cely": _("adb.forms.createVyskovyBodForm.label.ident_cely"),
                "typ": _("adb.forms.createVyskovyBodForm.label.typ"),
                "niveleta": _("adb.forms.createVyskovyBodForm.label.niveleta"),
                "northing": _("adb.forms.createVyskovyBodForm.label.northing"),
                "easting": _("adb.forms.createVyskovyBodForm.label.easting"),
            }

            widgets = {
                "ident_cely": forms.TextInput(),
                "typ": forms.Select(attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}),
            }
            help_texts = {
                "ident_cely": _("adb.forms.createVyskovyBodForm.tooltip.ident_cely"),
                "typ": _("adb.forms.createVyskovyBodForm.tooltip.typ"),
                "niveleta": _("adb.forms.createVyskovyBodForm.tooltip.niveleta"),
                "northing": _("adb.forms.createVyskovyBodForm.tooltip.northing"),
                "easting": _("adb.forms.createVyskovyBodForm.tooltip.easting"),
            }

        def _has_initial_values(self):
            """
            Metóda která vrací či ma formulář vyplnená initial hodnota
            Args:
            pian (pian): pian objeckt.
            niveleta (niveleta): niveleta objekt
            Returns:
            has_initial_values: boolean jestli formulář má initial hodnotu nebo ne.
            """
            cleaned_data = self.cleaned_data
            has_initial_values = False
            if pian:
                [x, y] = convertToJTSK(pian.geom.centroid.x, pian.geom.centroid.y)
                has_initial_values = cleaned_data.get("northing", None) == round(x, 2) and cleaned_data.get("easting", None) == round(y, 2)
                logger.debug("adb.forms.create_vyskovy_bod_form.pian",
                             extra={"cleaned_data": cleaned_data, "x": x, "y": y,
                                      "has_initial_values": has_initial_values})
            if has_initial_values and niveleta:
                has_initial_values = cleaned_data.get("niveleta", None) == niveleta
                logger.debug("adb.forms.create_vyskovy_bod_form.has_initial_values", extra={
                    "cleaned_data": cleaned_data, "niveleta": niveleta,
                    "has_initial_values": has_initial_values})
            elif "niveleta" in cleaned_data:
                has_initial_values = False
            if "typ" in cleaned_data and cleaned_data["typ"] is not None:
                has_initial_values = False
            return has_initial_values

        def is_valid(self):
            """
            Metóda která vrací či je formulář správne vyplněn, zakomponována metóda na vyplnení initial hodnoty.
            """
            parent_is_valid = super().is_valid()
            if self._has_initial_values():
                return True
            return parent_is_valid

        def save(self, commit=True):
            """
            Metóda která ukladá formulář do modelu, zakomponována metóda na vyplnení initial hodnoty.
            """
            if self._has_initial_values():
                return None
            return super().save(commit)

        def __init__(self, *args, **kwargs):
            """
            Init metóda pro vytvoření formuláře.
            Args:
            not_readonly (boolean): nastavuje formulář na readonly.
            """
            super(CreateVyskovyBodForm, self).__init__(*args, **kwargs)
            self.fields["ident_cely"].required = False

            if self.instance.northing is not None and self.instance.easting is not None:
                self.fields["northing"].initial = self.instance.northing
                self.fields["easting"].initial = self.instance.easting
            elif pian:
                [x, y] = convertToJTSK(pian.geom.centroid.x, pian.geom.centroid.y)
                self.fields["northing"].initial = round(x, 2)
                self.fields["easting"].initial = round(y, 2)

            if self.instance.niveleta is not None:
                self.fields["niveleta"].initial = self.instance.niveleta
            elif niveleta:
                self.fields["niveleta"].initial = niveleta

            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if self.fields[key].disabled == True:
                    if isinstance(self.fields[key].widget, forms.widgets.Select):
                        self.fields[
                            key
                        ].widget.template_name = "core/select_to_text.html"
                    self.fields[key].help_text = ""
            self.fields["ident_cely"].disabled = True

    return CreateVyskovyBodForm
