from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout, Submit
from dal import autocomplete
from django import forms
from django.forms import HiddenInput
from django.utils.translation import gettext as _
from oznameni.forms import DateRangeField, DateRangeWidget
from projekt.models import Projekt
from arch_z import validators


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
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "podnet": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "lokalizace": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "oznaceni_stavby": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "hlavni_katastr": forms.Textarea(
                attrs={"rows": 1, "cols": 20, "readonly": "readonly"}
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

    def __init__(self, *args, **kwargs):
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
        ].widget.template_name = "core/select_to_textarea.html"
        self.helper.form_tag = False
        for key in self.fields.keys():
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
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "podnet": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "lokalizace": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "oznaceni_stavby": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "kulturni_pamatka_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "kulturni_pamatka_popis": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "uzivatelske_oznaceni": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "hlavni_katastr": forms.Textarea(
                attrs={
                    "rows": 1,
                    "cols": 20,
                    "readonly": "readonly",
                },
            ),
            "katastry": autocomplete.ModelSelect2Multiple(
                url="heslar:katastr-autocomplete"
            ),
            "vedouci_projektu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "termin_odevzdani_nz": forms.DateInput(
                attrs={"data-provide": "datepicker", "autocomplete": "off"}
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

    def __init__(self, *args, required, **kwargs):
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
                            Div("vedouci_projektu", css_class="flex-fill"),
                            HTML(
                                _(
                                    '<a href="/uzivatel/osoba/create" class="btn app-btn-in-form" rel="tooltip" data-placement="top" title="Přidání osoby"><span class="material-icons">add</span></a>'
                                )
                            ),
                            css_class="col-sm-4 d-flex align-items-end",
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
                        Div("datum_zahajeni", css_class="col-sm-4"),
                        Div("datum_ukonceni", css_class="col-sm-4"),
                        Div("termin_odevzdani_nz", css_class="col-sm-4"),
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
        ].widget.template_name = "core/select_to_textarea.html"
        for key in self.fields.keys():
            if required:
                self.fields[key].required = True if key in required else False
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
        label=_("projekt.form.navrhzruseni.projektId.label"), required=False
    )
    reason_text = forms.CharField(
        label=_("projekt.form.navrhzruseni.vlastniduvod.label"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "cols": 80}),
    )
    enable_submit = True

    def __init__(self, *args, **kwargs):
        if "enable_form_submit" in kwargs:
            enable_form_submit = kwargs.pop("enable_form_submit")
        else:
            enable_form_submit = True
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("Návrh zrušení projektu")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
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
                ),
                css_class="card app-card-form",
            ),
            Div(
                FormActions(
                    Submit(
                        "save", "Navrhnout zrušení", disabled=not enable_form_submit
                    ),
                    HTML(
                        '<button type="button" class="btn btn-secondary ml-1" onclick="window.history.back();">Zpět</button>'
                    ),
                ),
                css_class="mt-3",
            ),
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
            "kulturni_pamatka_popis": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "kulturni_pamatka_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "uzivatelske_oznaceni": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "vedouci_projektu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "kulturni_pamatka": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
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
        super(PrihlaseniProjektForm, self).__init__(*args, **kwargs)
        self.fields["vedouci_projektu"].required = True
        self.fields["kulturni_pamatka"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("Přihlášení projektu")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div(
                            Div(
                                Div("vedouci_projektu", css_class="flex-fill"),
                                HTML(
                                    _(
                                        '<a href="{% url \'uzivatel:create_osoba\' %}?next={{ request.path|urlencode }}" class="btn app-btn-in-form" rel="tooltip" data-placement="top" title="Přidání osoby"><span class="material-icons">add</span></a>'
                                    )
                                ),
                                css_class="col-sm-4 d-flex align-items-center",
                            ),
                            Div("organizace", css_class="col-sm-4"),
                            Div("uzivatelske_oznaceni", css_class="col-sm-4"),
                            Div("kulturni_pamatka", css_class="col-sm-2"),
                            Div("kulturni_pamatka_cislo", css_class="col-sm-2"),
                            Div("kulturni_pamatka_popis", css_class="col-sm-8"),
                            Div("old_stav"),
                            css_class="row",
                        ),
                        css_class="card-body",
                    )
                ),
                css_class="card app-card-form",
            )
        )
        self.helper.form_tag = False

        for key in self.fields.keys():
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""


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
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("Zahájení výzkumu ")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div(
                            Div("datum_zahajeni", css_class="col-sm-3"),
                            Div("old_stav"),
                            css_class="row",
                        ),
                        css_class="card-body",
                    )
                ),
                css_class="card app-card-form",
            ),
            Div(
                FormActions(
                    Submit("save", "Zahájit v terénu"),
                    HTML(
                        '<button type="button" class="btn btn-secondary ml-1" onclick="window.history.back();">Zpět</button>'
                    ),
                ),
                css_class="mt-3",
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
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("Ukončení výzkumu")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div(
                            Div("datum_ukonceni", css_class="col-sm-3"),
                            Div("old_stav"),
                            css_class="row",
                        ),
                        css_class="card-body",
                    ),
                ),
                css_class="card app-card-form",
            ),
            Div(
                FormActions(
                    Submit("save", "Ukončit v terénu"),
                    HTML(
                        '<button type="button" class="btn btn-secondary ml-1" onclick="window.history.back();">Zpět</button>'
                    ),
                ),
                css_class="mt-3",
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
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        "reason_text",
                        css_class="col-sm-12",
                        title="projekt.form.zruseni.duvodTooltip.text",
                    ),
                    css_class="row",
                ),
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
