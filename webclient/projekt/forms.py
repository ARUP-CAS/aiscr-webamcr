import logging

from django.urls import reverse

from crispy_forms.bootstrap import AppendedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from dal import autocomplete
from django import forms
from django.forms import HiddenInput
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from arch_z import validators
from historie.models import Historie
from oznameni.forms import DateRangeField, DateRangeWidget
from projekt.models import Projekt
from core.constants import PROJEKT_STAV_ARCHIVOVANY, PROJEKT_STAV_ZAHAJENY_V_TERENU, PROJEKT_STAV_ZRUSENY
from heslar.hesla_dynamicka import TYP_PROJEKTU_PRUZKUM_ID
from core.forms import BaseFilterForm

logger_s = logging.getLogger(__name__)

class CreateProjektForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření projektu.
    """
    coordinate_x1 = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_x2 = forms.FloatField(required=False, widget=HiddenInput())
    planovane_zahajeni = DateRangeField(
        required=True,
        label=_("projekt.forms.createProjekt.planovaneZahajeni.label"),
        widget=DateRangeWidget(attrs={"rows": 1, "cols": 40, "autocomplete": "off"}),
        help_text=_("projekt.forms.createProjekt.planovaneZahajeni.tooltip"),
    )

    class Meta:
        model = Projekt
        fields = (
            "typ_projektu",
            "hlavni_katastr",
            "katastry",  # optional
            "planovane_zahajeni",
            "podnet",
            "lokalizace",
            "parcelni_cislo",
            "oznaceni_stavby",  # optional
        )
        widgets = {
            "typ_projektu": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "podnet": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "lokalizace": forms.TextInput(),
            "parcelni_cislo": forms.TextInput(),
            "oznaceni_stavby": forms.TextInput(),
            "hlavni_katastr": forms.TextInput(
                attrs={"readonly": "readonly"}
            ),
            "katastry": autocomplete.ModelSelect2Multiple(
                url="heslar:katastr-autocomplete"
            ),
        }
        labels = {
            "typ_projektu": _("projekt.forms.createProjekt.typProjektu.label"),
            "hlavni_katastr": _("projekt.forms.createProjekt.hlavniKatastr.label"),
            "katastry": _("projekt.forms.createProjekt.katastry.label"),
            "podnet": _("projekt.forms.createProjekt.podnet.label"),
            "lokalizace": _("projekt.forms.createProjekt.lokalizace.label"),
            "parcelni_cislo": _("projekt.forms.createProjekt.parcelniCislo.label"),
            "oznaceni_stavby": _("projekt.forms.createProjekt.oznaceniStavby.label"),
        }
        error_messages = {
            "hlavni_katastr": {"required": _("projekt.forms.createProjekt.hlavniKatastr.error")}
        }
        help_texts = {
            "typ_projektu": _("projekt.forms.createProjekt.typProjektu.tooltip"),
            "hlavni_katastr": _("projekt.forms.createProjekt.hlavniKatastr.tooltip"),
            "katastry": _("projekt.forms.createProjekt.katastry.tooltip"),
            "podnet": _("projekt.forms.createProjekt.podnet.tooltip"),
            "lokalizace": _("projekt.forms.createProjekt.lokalizace.tooltip"),
            "parcelni_cislo": _("projekt.forms.createProjekt.parcelniCislo.tooltip"),
            "oznaceni_stavby": _("projekt.forms.createProjekt.oznaceniStavby.tooltip"),
        }

    def __init__(self, *args,required=None,required_next=None, **kwargs):
        super(CreateProjektForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
        self.fields["katastry"].readonly = True
        self.fields["podnet"].required = True
        self.fields["lokalizace"].required = True
        self.fields["parcelni_cislo"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("projekt.forms.createProjekt.cardHeader.detail")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div(
                            Div(
                                Div("typ_projektu", css_class="col-md-6 col-lg-3"),
                                Div("hlavni_katastr", css_class="col-md-6 col-lg-3"),
                                Div("katastry", css_class="col-md-12 col-lg-6"),
                                Div("podnet", css_class="col-sm-12"),
                                Div("lokalizace", css_class="col-sm-12"),
                                Div("parcelni_cislo", css_class="col-sm-12"),
                                Div("oznaceni_stavby", css_class="col-sm-6"),
                                Div("planovane_zahajeni", css_class="col-sm-3"),
                                Div("coordinate_x1", css_class="hidden"),
                                Div("coordinate_x2", css_class="hidden"),
                                css_class="row",
                            ),
                            css_class="col-md-6 col-12",
                        ),
                        Div(
                            Div(id="projectMap"),
                            css_class="col-md-6 col-12",
                        ),
                        css_class="row",
                    ),
                    css_class="card-body",
                ),
                css_class="card app-card-form",
            )
        )
        self.fields[
            "hlavni_katastr"
        ].widget.template_name = "core/select_to_text.html"
        self.helper.form_tag = False
        for key in self.fields.keys():
            if required or required_next:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"]= str(self.fields[key].widget.attrs["class"]) + (' required-next' if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"]= 'required-next' if key in required_next else ""
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
            if self.fields[key].disabled == True:
                self.fields[key].help_text = ""

    def clean(self):
        cleaned_data = super().clean()

        coordinate_x1 = cleaned_data.get('coordinate_x1')
        coordinate_x2 = cleaned_data.get('coordinate_x2')

        if not coordinate_x1 or not coordinate_x2:
            raise forms.ValidationError(_("projekt.forms.CreateProjektForm.clean.missing_coords"))
        return cleaned_data



class EditProjektForm(forms.ModelForm):
    """
    Hlavní formulář pro editaci projektu.
    """
    coordinate_x1 = forms.FloatField(required=False, widget=HiddenInput())
    coordinate_x2 = forms.FloatField(required=False, widget=HiddenInput())
    planovane_zahajeni = DateRangeField(
        required=True,
        label=_("projekt.forms.editProjekt.planovaneZahajeni.label"),
        widget=DateRangeWidget(attrs={"rows": 1, "cols": 40, "autocomplete": "off"}),
        help_text=_("projekt.forms.editProjekt.planovaneZahajeni.tooltip"),
    )
    datum_zahajeni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        widget=forms.DateInput(
            attrs={"data-provide": "datepicker", "autocomplete": "off"}
        ),
        help_text=_("projekt.forms.editProjekt.datumZahajeni.tooltip"),
    )
    datum_ukonceni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        widget=forms.DateInput(
            attrs={"data-provide": "datepicker", "autocomplete": "off"}
        ),
        help_text=_("projekt.forms.editProjekt.datumUkonceni.tooltip"),
    )

    class Meta:
        model = Projekt
        fields = (
            "typ_projektu",
            "hlavni_katastr",
            "planovane_zahajeni",
            "podnet",
            "lokalizace",
            "parcelni_cislo",
            "oznaceni_stavby",
            "vedouci_projektu",
            "organizace",
            "kulturni_pamatka",
            "kulturni_pamatka_cislo",
            "kulturni_pamatka_popis",
            "datum_zahajeni",
            "datum_ukonceni",
            "uzivatelske_oznaceni",
            "katastry",
            "termin_odevzdani_nz",
        )
        widgets = {
            "typ_projektu": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "podnet": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "lokalizace": forms.TextInput(),
            "parcelni_cislo": forms.TextInput(),
            "oznaceni_stavby": forms.TextInput(),
            "kulturni_pamatka_cislo": forms.TextInput(),
            "kulturni_pamatka_popis": forms.TextInput(),
            "uzivatelske_oznaceni": forms.TextInput(),
            "hlavni_katastr": forms.TextInput(
                attrs=
                    {"readonly": "readonly"}
                ,
            ),
            "katastry": autocomplete.ModelSelect2Multiple(
                url="heslar:katastr-autocomplete"
            ),
            "vedouci_projektu": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "termin_odevzdani_nz": forms.DateInput(
                attrs={"data-provide": "datepicker", "autocomplete": "off"}
            ),
            "kulturni_pamatka": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
        }
        labels = {
            "typ_projektu": _("projekt.forms.editProjekt.typProjektu.label"),
            "hlavni_katastr": _("projekt.forms.editProjekt.hlavniKatastr.label"),
            "katastry": _("projekt.forms.editProjekt.katastry.label"),
            "podnet": _("projekt.forms.editProjekt.podnet.label"),
            "lokalizace": _("projekt.forms.editProjekt.lokalizace.label"),
            "parcelni_cislo": _("projekt.forms.editProjekt.parcelniCislo.label"),
            "oznaceni_stavby": _("projekt.forms.editProjekt.oznaceniStavby.label"),
            "vedouci_projektu": _("projekt.forms.editProjekt.vedouciProjektu.label"),
            "organizace": _("projekt.forms.editProjekt.organizace.label"),
            "kulturni_pamatka": _("projekt.forms.editProjekt.kulturniPamatka.label"),
            "kulturni_pamatka_cislo": _("projekt.forms.editProjekt.kulturniPamatkaCislo.label"),
            "kulturni_pamatka_popis": _("projekt.forms.editProjekt.kulturniPamatkaPopis.label"),
            "uzivatelske_oznaceni": _("projekt.forms.editProjekt.uzivatelskeOznaceni.label"),
            "datum_zahajeni": _("projekt.forms.editProjekt.datumZahajeni.label"),
            "datum_ukonceni": _("projekt.forms.editProjekt.datumUkonceni.label"),
            "termin_odevzdani_nz": _("projekt.forms.editProjekt.terminOdevzdani.label"),
        }
        help_texts = {
            "typ_projektu": _("projekt.forms.editProjekt.typProjektu.tooltip"),
            "hlavni_katastr": _("projekt.forms.editProjekt.hlavniKatastr.tooltip"),
            "katastry": _("projekt.forms.editProjekt.katastry.tooltip"),
            "podnet": _("projekt.forms.editProjekt.podnet.tooltip"),
            "lokalizace": _("projekt.forms.editProjekt.lokalizace.tooltip"),
            "parcelni_cislo": _("projekt.forms.editProjekt.parcelniCislo.tooltip"),
            "oznaceni_stavby": _("projekt.forms.editProjekt.oznaceniStavby.tooltip"),
            "vedouci_projektu": _("projekt.forms.editProjekt.vedouciProjektu.tooltip"),
            "organizace": _("projekt.forms.editProjekt.organizace.tooltip"),
            "kulturni_pamatka": _("projekt.forms.editProjekt.kulturniPamatka.tooltip"),
            "kulturni_pamatka_cislo": _(
                "projekt.forms.editProjekt.kulturniPamatkaCislo.tooltip"
            ),
            "kulturni_pamatka_popis": _(
                "projekt.forms.editProjekt.kulturniPamatkaPopis.tooltip"
            ),
            "uzivatelske_oznaceni": _(
                "projekt.forms.editProjekt.uzivatelskeOznaceni.tooltip"
            ),
            "datum_zahajeni": _("projekt.forms.editProjekt.datumZahajeni.tooltip"),
            "datum_ukonceni": _("projekt.forms.editProjekt.datumUkonceni.tooltip"),
            "termin_odevzdani_nz": _(
                "projekt.forms.editProjekt.terminOdevzdani.tooltip"
            ),
        }

    def __init__(self, *args, required=None, required_next=None, edit_fields=None, **kwargs):
        super(EditProjektForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
        self.helper = FormHelper(self)
        self.fields[
            "hlavni_katastr"
        ].widget.template_name = "core/select_to_text.html"
        for key in self.fields.keys():
            if edit_fields:
                if key not in edit_fields:
                    self.fields[key].disabled = True
            if required or required_next:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"]= str(self.fields[key].widget.attrs["class"]) + (' required-next' if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"]= 'required-next' if key in required_next else ""
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
        if self.fields["vedouci_projektu"].disabled is True:
            helper_vedouci_projektu = Div("vedouci_projektu",css_class="col-sm-4")
        else:
            helper_vedouci_projektu = Div(
                            AppendedText("vedouci_projektu", mark_safe('<button id="create-osoba" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>')),
                            css_class="col-sm-4 input-osoba",
            )
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("projekt.forms.editProjekt.cardHeader.editace")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div(
                            Div(
                                Div("typ_projektu", css_class="col-sm-3"),
                                Div("hlavni_katastr", css_class="col-sm-3"),
                                Div("katastry", css_class="col-sm-6"),
                                Div("podnet", css_class="col-sm-12"),
                                Div("lokalizace", css_class="col-sm-12"),
                                Div("parcelni_cislo", css_class="col-sm-12"),
                                Div("oznaceni_stavby", css_class="col-sm-6"),
                                Div("planovane_zahajeni", css_class="col-sm-3"),
                                css_class="row",
                            ),
                            css_class="col-sm-9",
                        ),
                        Div(
                            Div(id="projectMap"),
                            css_class="col-sm-3",
                        ),
                        css_class="row",
                    ),
                    Div(
                        Div(
                            HTML('<span class="app-divider-label">'),
                            HTML(
                                _("projekt.forms.editProjekt.prihlaseni.divider")
                                ),
                            HTML('</span>'),
                            HTML('<hr class="mt-0" />'),
                            css_class="col-sm-12",
                        ),
                        helper_vedouci_projektu,
                        Div("organizace", css_class="col-sm-4"),
                        Div("uzivatelske_oznaceni", css_class="col-sm-4"),
                        Div("kulturni_pamatka", css_class="col-sm-3"),
                        Div("kulturni_pamatka_cislo", css_class="col-sm-3"),
                        Div("kulturni_pamatka_popis", css_class="col-sm-6"),
                        Div("coordinate_x1", css_class="hidden"),
                        Div("coordinate_x2", css_class="hidden"),
                        Div(
                            HTML('<span class="app-divider-label">'),
                            HTML(_("projekt.forms.editProjekt.terenniCast.divider")),
                            HTML('</span>'),
                            HTML('<hr class="mt-0" />'),
                            css_class="col-sm-12",
                        ),
                        Div("datum_zahajeni", css_class="col-sm-3"),
                        Div(css_class="col-sm-1"),
                        Div("datum_ukonceni", css_class="col-sm-3"),
                        Div(css_class="col-sm-1"),
                        Div("termin_odevzdani_nz", css_class="col-sm-3"),
                        css_class="row",
                    ),
                    css_class="card-body",
                ),
                css_class="card app-card-form",
            )
        )
        self.helper.form_tag = False

    def clean(self):
        """
        Kontrola datumu zahájení a ukončení pri validaci formuláře.
        """
        cleaned_data = super().clean()
        if {"datum_zahajeni", "datum_ukonceni"} <= cleaned_data.keys():
            if cleaned_data.get("datum_zahajeni") and cleaned_data.get(
                "datum_ukonceni"
            ):
                if cleaned_data.get("datum_zahajeni") > cleaned_data.get(
                    "datum_ukonceni"
                ):
                    raise forms.ValidationError(
                        "Datum zahájení nemůže být po datu ukončení"
                    )
        return self.cleaned_data


class NavrhnoutZruseniProjektForm(forms.Form):
    """
    Formulář pro navržení zrušení projektu.
    """
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())
    CHOICES = [
        ("option1", _("projekt.forms.navrhzruseni.duvod1.text")),
        ("option2", _("projekt.forms.navrhzruseni.duvod2.text")),
        ("option3", _("projekt.forms.navrhzruseni.duvod3.text")),
        ("option4", _("projekt.forms.navrhzruseni.duvod4.text")),
        ("option5", _("projekt.forms.navrhzruseni.duvod5.text")),
        ("option6", _("projekt.forms.navrhzruseni.duvod6.text")),
    ]

    reason = forms.ChoiceField(
        label=_("projekt.forms.navrhzruseni.duvod.label"),
        choices=CHOICES,
        widget=forms.RadioSelect,
        help_text=_("projekt.forms.navrhzruseni.duvod.tooltip"),
    )
    projekt_id = forms.CharField(
        label=_("projekt.forms.navrhzruseni.projektId.label"),
        required=False,
        help_text=_("projekt.forms.navrhZruseniProj.projektId.tooltip"),
    )
    reason_text = forms.CharField(
        label=_("projekt.forms.navrhzruseni.vlastniduvod.label"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "cols": 80}),
        help_text=_("projekt.forms.navrhZruseniProj.reasonText.tooltip"),
    )
    enable_submit = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                "reason",
                css_class="form-check",
                ),
            Div(
                "reason_text",
                css_class="col-sm-12",
            ),
            Div("projekt_id", css_class="col-sm-12"),
            Div("old_stav"),        
        )

    def clean(self):
        """
        Metóda na kontrolu obsahu důvodu pro zrušení.
        """
        cleaned_data = super().clean()
        if cleaned_data.get("reason") == "option1":
            if not cleaned_data.get("projekt_id"):
                raise forms.ValidationError(
                    _("projekt.forms.navrhzruseni.validation.projektId.text")
                )
        elif cleaned_data.get("reason") == "option6":
            if not cleaned_data.get("reason_text"):
                raise forms.ValidationError(
                    _("projekt.forms.navrhzruseni.validation.vlastniDuvod.text")
                )
        return self.cleaned_data


class PrihlaseniProjektForm(forms.ModelForm):
    """
    Hlavní formulář pro prihlášení projektu.
    """
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    class Meta:
        model = Projekt
        fields = (
            "vedouci_projektu",
            "organizace",
            "kulturni_pamatka",
            "kulturni_pamatka_cislo",
            "kulturni_pamatka_popis",
            "uzivatelske_oznaceni",
        )
        widgets = {
            "kulturni_pamatka_popis": forms.TextInput(),
            "kulturni_pamatka_cislo": forms.TextInput(),
            "uzivatelske_oznaceni": forms.TextInput(),
            "vedouci_projektu": forms.Select(
                attrs={"class": "selectpicker required-next", "data-live-search": "true"}
            ),
            "kulturni_pamatka": forms.Select(
                attrs={"class": "selectpicker required-next", "data-live-search": "true"}
            ),
            "organizace": forms.Select(
                attrs={"class": "selectpicker required-next", "data-live-search": "true", "size":"7"}
            ),
        }
        labels = {
            "vedouci_projektu": _("projekt.forms.prihlaseniProj.vedouciProjektu.label"),
            "organizace": _("projekt.forms.prihlaseniProj.organizace.label"),
            "kulturni_pamatka": _("projekt.forms.prihlaseniProj.kulturniPamatka.label"),
            "kulturni_pamatka_cislo": _("projekt.forms.prihlaseniProj.kulturniPamatkaCislo.label"),
            "kulturni_pamatka_popis": _("projekt.forms.prihlaseniProj.kulturniPamatkaPopis.label"),
            "uzivatelske_oznaceni": _("projekt.forms.prihlaseniProj.uzivatelskeOznaceni.label"),
        }
        help_texts = {
            "vedouci_projektu": _(
                "projekt.forms.prihlaseniProj.vedouciProjektu.tooltip"
            ),
            "kulturni_pamatka": _(
                "projekt.forms.prihlaseniProj.kulturniPamatka.tooltip"
            ),
            "organizace": _("projekt.forms.prihlaseniProj.organizace.tooltip"),
            "kulturni_pamatka_cislo": _(
                "projekt.forms.prihlaseniProj.kulturniPamatkaCislo.tooltip"
            ),
            "kulturni_pamatka_popis": _(
                "projekt.forms.prihlaseniProj.kulturniPamatkaPopis.tooltip"
            ),
            "uzivatelske_oznaceni": _(
                "projekt.forms.prihlaseniProj.uzivatelskeOznaceni.tooltip"
            ),
        }

    def __init__(self, *args, **kwargs):
        archivar = kwargs.pop("archivar", False)
        super(PrihlaseniProjektForm, self).__init__(*args, **kwargs)
        self.fields["vedouci_projektu"].required = True
        self.fields["kulturni_pamatka"].required = True
        self.fields["organizace"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    AppendedText("vedouci_projektu", mark_safe('<button id="create-osoba" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>')),
                    css_class="col-sm-4 input-osoba",
                    ),
                Div("organizace", css_class="col-sm-4"),
                Div("uzivatelske_oznaceni", css_class="col-sm-4"),
                Div("kulturni_pamatka", css_class="col-sm-4"),
                Div("kulturni_pamatka_cislo", css_class="col-sm-4"),
                Div("kulturni_pamatka_popis", css_class="col-sm-4"),
                Div("old_stav"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False

        for key in self.fields.keys():
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
        if archivar:
            self.fields["organizace"].disabled = True
            self.fields["organizace"].widget.template_name = "core/select_to_text.html"


class ZahajitVTerenuForm(forms.ModelForm):
    """
    Formulář pro zahájení projektu v terénu.
    """
    datum_zahajeni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        help_text=_("projekt.forms.zahajitVTerenu.datumZahajeni.tooltip"),
        label=_("projekt.forms.zahajitVTerenu.datumZahajeni.label")
    )
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    class Meta:
        model = Projekt
        fields = ("datum_zahajeni",)
        labels = {
            "datum_zahajeni": _("projekt.forms.zahajitVTerenu.datumZahajeni.label"),
        }
        help_texts = {
            "datum_zahajeni": _("projekt.forms.zahajitVTerenu.datumZahajeni.tooltip")
        }

    def __init__(self, *args, **kwargs):
        super(ZahajitVTerenuForm, self).__init__(*args, **kwargs)
        self.fields["datum_zahajeni"].required = True
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("datum_zahajeni", css_class="col-sm-4"),
                Div("old_stav"),
                css_class="row",
                ),
        )


class UkoncitVTerenuForm(forms.ModelForm):
    """
    Formulář pro ukončení projektu v terénu.
    """
    datum_ukonceni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        help_text=_("projekt.forms.ukoncitVTerenu.datumUkonceni.tooltip"),
        label=_("projekt.forms.ukoncitVTerenu.datumUkonceni.label")
    )
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    class Meta:
        model = Projekt
        fields = ("datum_ukonceni",)
        labels = {
            "datum_ukonceni": _("projekt.forms.ukoncitVTerenu.datumUkonceni.label"),
        }
        help_texts = {
            "datum_ukonceni": _("projekt.forms.ukoncitVTerenu.datumUkonceni.tooltip"),
        }

    def __init__(self, *args, **kwargs):
        super(UkoncitVTerenuForm, self).__init__(*args, **kwargs)
        self.fields["datum_ukonceni"].required = True
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("datum_ukonceni", css_class="col-sm-4"),
                Div("old_stav"),
                css_class="row",
                ),
        )

    def clean(self):
        """
        Metóda pro kontrolu datumu ukončení.
        """
        cleaned_data = super().clean()
        if {"datum_ukonceni"} <= cleaned_data.keys():
            if self.instance.datum_zahajeni > cleaned_data.get("datum_ukonceni"):
                raise forms.ValidationError(
                    "Datum ukončení nemůže být pred datem zahájení (%s)"
                    % self.instance.datum_zahajeni.strftime("%d. %m. %Y")
                )
        return self.cleaned_data


class ZruseniProjektForm(forms.Form):
    """
    Formulář pro zrušení projektu.
    """
    reason_text = forms.CharField(
        label=_("projekt.forms.zruseni.duvod.label"),
        required=True,
        widget=forms.Textarea(attrs={"rows": 2, "cols": 80}),
        help_text=_("projekt.forms.zruseni.duvod.tooltip"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    "reason_text",
                    css_class="col-sm-12",
                    title="projekt.forms.zruseni.duvodTooltip.text",
                ),
                css_class="row",
            ),
        )


class GenerovatNovePotvrzeniForm(forms.Form):
    """
    Formulář pro vygenerování nového potvrzení projektu.
    """
    odeslat_oznamovateli = forms.BooleanField(label=_("projekt.forms.GenerovatExpertniListForm.odeslatOznamovateli.label"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        "odeslat_oznamovateli",
                        css_class="col-sm-12",
                        title="projekt.form.GenerovatExpertniListForm.odeslatOznamovateli.tooltip",
                    ),
                    css_class="row",
                ),
            ),
        )


TYP_VYZKUMU_CHOICES = [
    ("predstihovy", _("projekt.forms.GenerovatExpertniListForm.predstihovy.typ_vyzkumu.text")),
    ("zachranny", _("projekt.forms.GenerovatExpertniListForm.zachranny.typ_vyzkumu.text")),
    ("dohled", _("projekt.forms.GenerovatExpertniListForm.dohled.typ_vyzkumu.text")),
]
VYSLEDEK_CHOICES = [
    ("pozitivni", _("projekt.forms.GenerovatExpertniListForm.vysledek.pozitivni.text")),
    ("negativni", _("projekt.forms.GenerovatExpertniListForm.vysledek.negativni.text")),
    ("jine", _("projekt.forms.GenerovatExpertniListForm.vysledek.jine.text")),
]

class GenerovatExpertniListForm(forms.Form):
    """
    Formulář pro generování expertního listu projektu.
    """
    cislo_jednaci = forms.CharField(label=_("projekt.forms.GenerovatExpertniListForm.cislo_jednaci.label"),
                                    required=False,
                                    help_text=_("projekt.forms.GenerovatExpertniListForm.cislo_jednaci.tooltip"), )
    typ_vyzkumu = forms.ChoiceField(
        label=_("projekt.forms.GenerovatExpertniListForm.typ_vyzkumu.label"),
        choices=TYP_VYZKUMU_CHOICES,
        widget=forms.Select,
        help_text=_("projekt.forms.GenerovatExpertniListForm.typ_vyzkumu.tooltip"),
    )
    vysledek = forms.ChoiceField(
        label=_("projekt.forms.GenerovatExpertniListForm.vysledek.label"),
        choices=VYSLEDEK_CHOICES,
        widget=forms.Select,
        help_text=_("projekt.forms.GenerovatExpertniListForm.vysledek.tooltip"),
    )
    poznamka_popis = forms.CharField(
        label=_("projekt.forms.GenerovatExpertniListForm.poznamka_popis.label"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "cols": 80}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.fields["poznamka_popis"].disabled = True
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        "cislo_jednaci",
                        css_class="col-sm-12",
                    ),
                    Div(
                        "typ_vyzkumu",
                        css_class="col-sm-12",
                    ),
                    Div(
                        "vysledek",
                        css_class="col-sm-12",
                    ),
                    Div(
                        "poznamka_popis",
                        css_class="col-sm-12",
                    ),
                    css_class="row",
                ),
            ),
        )

class PripojitProjektForm(forms.Form):
    """
    Formulář pro pripojení projektu do akce nebo dokumentu.
    """
    def __init__(self,dok=False, *args, **kwargs):
        super(PripojitProjektForm, self).__init__(*args, **kwargs)
        if dok:
            new_choices = list(
                Projekt.objects.filter(stav__gte=PROJEKT_STAV_ZAHAJENY_V_TERENU,stav__lte=PROJEKT_STAV_ARCHIVOVANY)
                .filter(typ_projektu__id=TYP_PROJEKTU_PRUZKUM_ID)
                .values_list("id", "ident_cely")
            )
            typ = "dokument"
        else:
            new_choices = list(
                Projekt.objects.filter(stav__gte=PROJEKT_STAV_ZAHAJENY_V_TERENU,stav__lte=PROJEKT_STAV_ARCHIVOVANY)
                .exclude(typ_projektu__id=TYP_PROJEKTU_PRUZKUM_ID)
                .values_list("id", "ident_cely")
            )
            typ= "archz"
        self.fields["projekt"] = forms.ChoiceField(
            label=_("projekt.forms.projektPripojit.projekt.label"),
            choices=new_choices,
            widget=autocomplete.ListSelect2(
                url=reverse("projekt:projekt-autocomplete-bez-zrusenych", kwargs={"typ": typ})
            ),
            help_text=_("projekt.forms.projektPripojit.projekt.tooltip"),
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    "projekt",
                    css_class="col-sm-8",
                ),
                css_class="row",
            ),
        )

class ProjektFilterForm(BaseFilterForm):
    list_to_check = ["historie_datum_zmeny_od","planovane_zahajeni", "termin_odevzdani_nz","datum_ukonceni","datum_zahajeni","akce_datum_zahajeni","akce_datum_ukonceni"]

class ZadostUdajeOznamovatelForm(forms.Form):
    reason = forms.CharField(
        label=_("projekt.forms.zadostUdajeOznamovatel.duvod.label"),
        required=True,
        help_text=_("projekt.forms.zadostUdajeOznamovatel.duvod.tooltip"),
        widget = forms.Textarea(attrs={"rows": 5, "cols": 40})
    )

    def __init__(self, *args, **kwargs):
        super(ZadostUdajeOznamovatelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class UpravitDatumOznameniForm(forms.ModelForm):
    datum_oznameni = forms.DateField(
        label=_("projekt.forms.upravitDatumOznameni.datumOznameni.label"),
        widget=forms.DateInput(
            attrs={"data-provide": "datepicker", "autocomplete": "off"}
        ),
        help_text=_("projekt.forms.upravitDatumOznameni.datumOznameni.tooltip"),
    )

    cas_oznameni = forms.TimeField(
        label=_("projekt.forms.upravitDatumOznameni.casOznameni.label"),
        widget=forms.TimeInput(format='%H:%M', attrs={"type": "time", "autocomplete": "off"}),  # Type "time" provides a time picker
        help_text=_("projekt.forms.upravitDatumOznameni.casOznameni.tooltip"),
    )

    class Meta:
        model = Historie
        fields = ("datum_oznameni", "cas_oznameni", "poznamka")
        help_texts = {
            "poznamka": _("projekt.forms.upravitDatumOznameni.poznamka.tooltip"),
        }
        labels = {"poznamka": _("projekt.forms.upravitDatumOznameni.poznamka.label"),}

    def __init__(self, *args, **kwargs):
        super(UpravitDatumOznameniForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div("datum_oznameni", css_class="col-sm-6"),
                        Div("cas_oznameni", css_class="col-sm-6"),
                        Div("poznamka", css_class="col-sm-12"),
                        css_class="row",
                    ),
                    css_class="card-body",
                ),
                css_class="card app-card-form",
            )
        )
        self.helper.form_tag = False
