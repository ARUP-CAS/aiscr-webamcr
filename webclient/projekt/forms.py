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
                    Div(HTML(_("Detail projektu")), css_class="app-fx app-left",),
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
                        Div(Div(id="projectMap"), css_class="col-sm-3",),
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


class EditProjektForm(forms.ModelForm):
    latitude = forms.FloatField(required=False, widget=HiddenInput())
    longitude = forms.FloatField(required=False, widget=HiddenInput())
    planovane_zahajeni = DateRangeField(
        required=True,
        label=_("Plánované zahájení prací"),
        widget=DateRangeWidget(attrs={"rows": 1, "cols": 40, "autocomplete": "off"}),
    )
    datum_zahajeni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        widget=forms.DateInput(
            attrs={"data-provide": "datepicker", "autocomplete": "off"}
        ),
    )
    datum_ukonceni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        widget=forms.DateInput(
            attrs={"data-provide": "datepicker", "autocomplete": "off"}
        ),
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
                attrs={"rows": 1, "cols": 20, "readonly": "readonly",},
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

    def __init__(self, *args, required, **kwargs):
        super(EditProjektForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(HTML(_("Editace projektu")), css_class="app-fx app-left",),
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
                        Div(Div(id="projectMap"), css_class="col-sm-3",),
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
    reason = forms.CharField(label=_("Důvod návrhu zrušení"), required=True)
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
                        HTML(_("Návrh zrušení projektu")), css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div("reason", css_class="card-body",),
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


class PrihlaseniProjektForm(forms.ModelForm):
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
            "vedouci_projektu": _("Lorem ipsum."),
            "kulturni_pamatka": _("Lorem ipsum."),
            "organizace": _("Lorem ipsum."),
            "kulturni_pamatka_cislo": _("Lorem ipsum."),
            "kulturni_pamatka_popis": _("Lorem ipsum."),
            "uzivatelske_oznaceni": _("Lorem ipsum."),
        }

    def __init__(self, *args, **kwargs):
        super(PrihlaseniProjektForm, self).__init__(*args, **kwargs)
        self.fields["vedouci_projektu"].required = True
        self.fields["kulturni_pamatka"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(HTML(_("Přihlášení projektu")), css_class="app-fx app-left",),
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


class ZahajitVTerenuForm(forms.ModelForm):
    datum_zahajeni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti]
    )

    class Meta:
        model = Projekt
        fields = ("datum_zahajeni",)
        labels = {
            "datum_zahajeni": _("Datum zahájení terénních prací"),
        }
        help_texts = {
            "datum_zahajeni": _("Lorem ipsum."),
        }

    def __init__(self, *args, **kwargs):
        super(ZahajitVTerenuForm, self).__init__(*args, **kwargs)
        self.fields["datum_zahajeni"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(HTML(_("Zahájení výzkumu ")), css_class="app-fx app-left",),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div(
                            Div("datum_zahajeni", css_class="col-sm-3"),
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
        validators=[validators.datum_max_1_mesic_v_budoucnosti]
    )

    class Meta:
        model = Projekt
        fields = ("datum_ukonceni",)
        labels = {
            "datum_ukonceni": _("Datum ukončení terénních prací"),
        }
        help_texts = {
            "datum_ukonceni": _("Lorem ipsum."),
        }

    def __init__(self, *args, **kwargs):
        super(UkoncitVTerenuForm, self).__init__(*args, **kwargs)
        self.fields["datum_ukonceni"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(HTML(_("Ukončení výzkumu")), css_class="app-fx app-left",),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div(
                            Div("datum_ukonceni", css_class="col-sm-3"),
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
