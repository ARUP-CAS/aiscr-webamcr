import logging

from django.urls import reverse

from crispy_forms.bootstrap import FormActions, AppendedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout, Submit
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import HiddenInput
from django.utils.translation import gettext as _
from django.utils.safestring import mark_safe

from arch_z import validators
from oznameni.forms import DateRangeField, DateRangeWidget
from projekt.models import Projekt
from core.constants import PROJEKT_STAV_ARCHIVOVANY, PROJEKT_STAV_ZAHAJENY_V_TERENU, PROJEKT_STAV_ZRUSENY
from heslar.hesla import TYP_PROJEKTU_PRUZKUM_ID

logger_s = logging.getLogger(__name__)

class CreateProjektForm(forms.ModelForm):
    latitude = forms.FloatField(required=False, widget=HiddenInput())
    longitude = forms.FloatField(required=False, widget=HiddenInput())
    planovane_zahajeni = DateRangeField(
        required=True,
        label=_("Plánované zahájení prací"),
        widget=DateRangeWidget(attrs={"rows": 1, "cols": 40, "autocomplete": "off"}),
        help_text=_("projekt.form.createProjekt.planovane_zahajeni.tooltip"),
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
            "typ_projektu": _("Typ projektu"),
            "hlavni_katastr": _("Hlavní katastr"),
            "katastry": _("Další katastry"),
            "podnet": _("Podnět"),
            "lokalizace": _("Lokalizace"),
            "parcelni_cislo": _("Parcelní číslo"),
            "oznaceni_stavby": _("Označení stavby"),
        }
        error_messages = {
            "hlavni_katastr": {"required": "Je třeba vybrat bod na mapě."}
        }
        help_texts = {
            "typ_projektu": _("projekt.form.createProjekt.typ_projektu.tooltip"),
            "hlavni_katastr": _("projekt.form.createProjekt.hlavni_katastr.tooltip"),
            "katastry": _("projekt.form.createProjekt.katastry.tooltip"),
            "podnet": _("projekt.form.createProjekt.podnet.tooltip"),
            "lokalizace": _("projekt.form.createProjekt.lokalizace.tooltip"),
            "parcelni_cislo": _("projekt.form.createProjekt.parcelni_cislo.tooltip"),
            "oznaceni_stavby": _("projekt.form.createProjekt.oznaceni_stavby.tooltip"),
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
                        HTML(_("Detail projektu")),
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
                                Div("latitude", css_class="hidden"),
                                Div("longitude", css_class="hidden"),
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


class EditProjektForm(forms.ModelForm):
    latitude = forms.FloatField(required=False, widget=HiddenInput())
    longitude = forms.FloatField(required=False, widget=HiddenInput())
    planovane_zahajeni = DateRangeField(
        required=True,
        label=_("Plánované zahájení prací"),
        widget=DateRangeWidget(attrs={"rows": 1, "cols": 40, "autocomplete": "off"}),
        help_text=_("projekt.form.editProjekt.planovane_zahajeni.tooltip"),
    )
    datum_zahajeni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        widget=forms.DateInput(
            attrs={"data-provide": "datepicker", "autocomplete": "off"}
        ),
        help_text=_("projekt.form.editProjekt.datum_zahajeni.tooltip"),
    )
    datum_ukonceni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        widget=forms.DateInput(
            attrs={"data-provide": "datepicker", "autocomplete": "off"}
        ),
        help_text=_("projekt.form.editProjekt.datum_ukonceni.tooltip"),
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
            "typ_projektu": _("Typ projektu"),
            "hlavni_katastr": _("Hlavní katastr"),
            "katastry": _("Další katastry"),
            "podnet": _("Podnět"),
            "lokalizace": _("Lokalizace"),
            "parcelni_cislo": _("Parcelní číslo"),
            "oznaceni_stavby": _("Označení stavby"),
            "vedouci_projektu": _("Vedoucí projektu"),
            "organizace": _("Organizace"),
            "kulturni_pamatka": _("Památková ochrana"),
            "kulturni_pamatka_cislo": _("Rejstříkové číslo USKP"),
            "kulturni_pamatka_popis": _("Název památky"),
            "uzivatelske_oznaceni": _("Uživatelské označení"),
            "datum_zahajeni": _("Datum zahájení výzkumu"),
            "datum_ukonceni": _("Datum ukončení výzkumu"),
            "termin_odevzdani_nz": _("Termín odevzdání"),
        }
        help_texts = {
            "typ_projektu": _("projekt.form.editProjekt.typ_projektu.tooltip"),
            "hlavni_katastr": _("projekt.form.editProjekt.hlavni_katastr.tooltip"),
            "katastry": _("projekt.form.editProjekt.katastry.tooltip"),
            "podnet": _("projekt.form.editProjekt.podnet.tooltip"),
            "lokalizace": _("projekt.form.editProjekt.lokalizace.tooltip"),
            "parcelni_cislo": _("projekt.form.editProjekt.parcelni_cislo.tooltip"),
            "oznaceni_stavby": _("projekt.form.editProjekt.oznaceni_stavby.tooltip"),
            "vedouci_projektu": _("projekt.form.editProjekt.vedouci_projektu.tooltip"),
            "organizace": _("projekt.form.editProjekt.organizace.tooltip"),
            "kulturni_pamatka": _("projekt.form.editProjekt.kulturni_pamatka.tooltip"),
            "kulturni_pamatka_cislo": _(
                "projekt.form.editProjekt.kulturni_pamatka_cislo.tooltip"
            ),
            "kulturni_pamatka_popis": _(
                "projekt.form.editProjekt.kulturni_pamatka_popis.tooltip"
            ),
            "uzivatelske_oznaceni": _(
                "projekt.form.editProjekt.uzivatelske_oznaceni.tooltip"
            ),
            "datum_zahajeni": _("projekt.form.editProjekt.datum_zahajeni.tooltip"),
            "datum_ukonceni": _("projekt.form.editProjekt.datum_ukonceni.tooltip"),
            "termin_odevzdani_nz": _(
                "projekt.form.editProjekt.termin_odevzdani_nz.tooltip"
            ),
        }

    def __init__(self, *args, required=None,required_next=None, **kwargs):
        super(EditProjektForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("Editace projektu")),
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
                            HTML(
                                _(
                                    '<span class="app-divider-label">Přihlášení projektu</span>'
                                )
                            ),
                            HTML(_('<hr class="mt-0" />')),
                            css_class="col-sm-12",
                        ),
                        Div(
                            AppendedText("vedouci_projektu", mark_safe('<button id="create-osoba" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>')),
                            css_class="col-sm-4 input-osoba",
                        ),
                        Div("organizace", css_class="col-sm-4"),
                        Div("uzivatelske_oznaceni", css_class="col-sm-4"),
                        Div("kulturni_pamatka", css_class="col-sm-3"),
                        Div("kulturni_pamatka_cislo", css_class="col-sm-3"),
                        Div("kulturni_pamatka_popis", css_class="col-sm-6"),
                        Div("latitude", css_class="hidden"),
                        Div("longitude", css_class="hidden"),
                        Div(
                            HTML(
                                _('<span class="app-divider-label">Terenní část</span>')
                            ),
                            HTML(_('<hr class="mt-0" />')),
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
        self.fields[
            "hlavni_katastr"
        ].widget.template_name = "core/select_to_text.html"
        for key in self.fields.keys():
            if required or required_next:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"]= str(self.fields[key].widget.attrs["class"]) + (' required-next' if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"]= 'required-next' if key in required_next else ""
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""

    def clean(self):
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
    reason = forms.CharField(
        label=_("Důvod návrhu zrušení"),
        required=True,
        help_text=_("projekt.form.navrhZruseniProj.reason.tooltip"),
    )
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())
    CHOICES = [
        ("option1", _("projekt.form.navrhzruseni.duvod1.text")),
        ("option2", _("projekt.form.navrhzruseni.duvod2.text")),
        ("option3", _("projekt.form.navrhzruseni.duvod3.text")),
        ("option4", _("projekt.form.navrhzruseni.duvod4.text")),
        ("option5", _("projekt.form.navrhzruseni.duvod5.text")),
        ("option6", _("projekt.form.navrhzruseni.duvod6.text")),
    ]

    reason = forms.ChoiceField(
        label=_("projekt.form.navrhzruseni.duvod.label"),
        choices=CHOICES,
        widget=forms.RadioSelect,
        help_text=_("projekt.form.navrhzruseni.duvod.tooltip"),
    )
    projekt_id = forms.CharField(
        label=_("projekt.form.navrhzruseni.projektId.label"),
        required=False,
        help_text=_("projekt.form.navrhZruseniProj.projektId.tooltip"),
    )
    reason_text = forms.CharField(
        label=_("projekt.form.navrhzruseni.vlastniduvod.label"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "cols": 80}),
        help_text=_("projekt.form.navrhZruseniProj.reasonText.tooltip"),
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
        cleaned_data = super().clean()
        if cleaned_data.get("reason") == "option1":
            if not cleaned_data.get("projekt_id"):
                raise forms.ValidationError(
                    _("projekt.form.navrhzruseni.validation.projektId.text")
                )
        elif cleaned_data.get("reason") == "option6":
            if not cleaned_data.get("reason_text"):
                raise forms.ValidationError(
                    _("projekt.form.navrhzruseni.validation.vlastniDuvod.text")
                )
        return self.cleaned_data


class PrihlaseniProjektForm(forms.ModelForm):
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
            "vedouci_projektu": _("Vedoucí projektu"),
            "organizace": _("Organizace"),
            "kulturni_pamatka": _("Památková ochrana"),
            "kulturni_pamatka_cislo": _("Rejstříkové číslo ÚSKP"),
            "kulturni_pamatka_popis": _("Název památky"),
            "uzivatelske_oznaceni": _("Uživatelské označení"),
        }
        help_texts = {
            "vedouci_projektu": _(
                "projekt.form.prihlaseniProj.vedouci_projektu.tooltip"
            ),
            "kulturni_pamatka": _(
                "projekt.form.prihlaseniProj.kulturni_pamatka.tooltip"
            ),
            "organizace": _("projekt.form.prihlaseniProj.organizace.tooltip"),
            "kulturni_pamatka_cislo": _(
                "projekt.form.prihlaseniProj.kulturni_pamatka_cislo.tooltip"
            ),
            "kulturni_pamatka_popis": _(
                "projekt.form.prihlaseniProj.kulturni_pamatka_popis.tooltip"
            ),
            "uzivatelske_oznaceni": _(
                "projekt.form.prihlaseniProj.uzivatelske_oznaceni.tooltip"
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
    datum_zahajeni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        help_text=_("projekt.form.zahajitVTerenu.datum_zahajeni.tooltip"),
    )
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    class Meta:
        model = Projekt
        fields = ("datum_zahajeni",)
        labels = {
            "datum_zahajeni": _("Datum zahájení terénních prací"),
        }
        help_texts = {
            "datum_zahajeni": _("projekt.form.zahajitVTerenu.datum_zahajeni.tooltip")
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
    datum_ukonceni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        help_text=_("projekt.form.ukoncitVTerenu.datum_ukonceni.tooltip"),
    )
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    class Meta:
        model = Projekt
        fields = ("datum_ukonceni",)
        labels = {
            "datum_ukonceni": _("Datum ukončení terénních prací"),
        }
        help_texts = {
            "datum_ukonceni": _("projekt.form.ukoncitVTerenu.datum_ukonceni.tooltip"),
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
        cleaned_data = super().clean()
        if {"datum_ukonceni"} <= cleaned_data.keys():
            if self.instance.datum_zahajeni > cleaned_data.get("datum_ukonceni"):
                raise forms.ValidationError(
                    "Datum ukončení nemůže být pred datem zahájení (%s)"
                    % self.instance.datum_zahajeni.strftime("%d. %m. %Y")
                )
        return self.cleaned_data


class ZruseniProjektForm(forms.Form):

    reason_text = forms.CharField(
        label=_("projekt.form.zruseni.duvod.label"),
        required=True,
        widget=forms.Textarea(attrs={"rows": 2, "cols": 80}),
        help_text=_("projekt.form.zruseni.duvod.tooltip"),
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
                    title="projekt.form.zruseni.duvodTooltip.text",
                ),
                css_class="row",
            ),
        )


class GenerovatNovePotvrzeniForm(forms.Form):
    odeslat_oznamovateli = forms.BooleanField(label=_("Odeslat oznamovateli"), required=False)

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
                        title="projekt.form.GenerovatNovePotvrzeniForm.odeslat_oznamovateliTooltip.text",
                    ),
                    css_class="row",
                ),
            ),
        )


TYP_VYZKUMU_CHOICES = [
    ("predstihovy", _("projekt.form.GenerovatExpertniListForm.predstihovy.typ_vyzkumu.text")),
    ("zachranny", _("projekt.form.GenerovatExpertniListForm.zachranny.typ_vyzkumu.text")),
    ("dohled", _("projekt.form.GenerovatExpertniListForm.dohled.typ_vyzkumu.text")),
]
VYSLEDEK_CHOICES = [
    ("pozitivni", _("projekt.form.GenerovatExpertniListForm.vysledek.pozitivni.text")),
    ("negativni", _("projekt.form.GenerovatExpertniListForm.vysledek..text")),
    ("jine", _("projekt.form.GenerovatExpertniListForm.vysledek.jine.text")),
]

class GenerovatExpertniListForm(forms.Form):
    cislo_jednaci = forms.CharField(label=_("projekt.form.GenerovatExpertniListForm.cislo_jednaci.label"),
                                    required=False,
                                    help_text=_("projekt.form.GenerovatExpertniListForm.cislo_jednaci.tooltip"), )
    typ_vyzkumu = forms.ChoiceField(
        label=_("projekt.form.GenerovatExpertniListForm.typ_vyzkumu.label"),
        choices=TYP_VYZKUMU_CHOICES,
        widget=forms.Select,
        help_text=_("projekt.form.GenerovatExpertniListForm.typ_vyzkumu.tooltip"),
    )
    vysledek = forms.ChoiceField(
        label=_("projekt.form.GenerovatExpertniListForm.vysledek.label"),
        choices=VYSLEDEK_CHOICES,
        widget=forms.Select,
        help_text=_("projekt.form.GenerovatExpertniListForm.vysledek.tooltip"),
    )
    poznamka_popis = forms.CharField(
        label=_("projekt.form.GenerovatExpertniListForm.poznamka_popis.label"),
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
    def __init__(self,dok=False, *args, **kwargs):
        super(PripojitProjektForm, self).__init__(*args, **kwargs)
        if dok:
            new_choices = list(
                Projekt.objects.filter(stav__gte=PROJEKT_STAV_ZAHAJENY_V_TERENU,stav__lte=PROJEKT_STAV_ARCHIVOVANY)
                .filter(typ_projektu__id=TYP_PROJEKTU_PRUZKUM_ID)
                .values_list("id", "ident_cely")
            )
            typ = "dok"
        else:
            new_choices = list(
                Projekt.objects.filter(stav__gte=PROJEKT_STAV_ZAHAJENY_V_TERENU,stav__lte=PROJEKT_STAV_ARCHIVOVANY)
                .exclude(typ_projektu__id=TYP_PROJEKTU_PRUZKUM_ID)
                .values_list("id", "ident_cely")
            )
            typ= "projekt"
        self.fields["projekt"] = forms.ChoiceField(
            label=_("arch_z.forms.projektPripojit.label"),
            choices=new_choices,
            widget=autocomplete.ListSelect2(
                url=reverse("projekt:projekt-autocomplete-bez-zrusenych", kwargs={"typ": typ})
            ),
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False