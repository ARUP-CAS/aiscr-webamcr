from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout, Submit
from dal import autocomplete
from django import forms
from django.forms import HiddenInput
from django.utils.translation import gettext as _
from oznameni.forms import DateRangeField, DateRangeWidget
from projekt.models import Projekt


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
            "hlavni_katastr": autocomplete.ModelSelect2(
                url="heslar:katastr-autocomplete"
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

    def __init__(self, *args, **kwargs):
        super(CreateProjektForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
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
        self.helper.form_tag = False


class EditProjektForm(forms.ModelForm):
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
            #"termin_odevzdani",
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
            "datum_zahajeni": forms.DateInput(attrs={"data-provide": "datepicker"}),
            "datum_ukonceni": forms.DateInput(attrs={"data-provide": "datepicker"}),
            "hlavni_katastr": autocomplete.ModelSelect2(
                url="heslar:katastr-autocomplete"
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
            #"termin_odevzdani": _("Termín odevzdání"),
        }

    def __init__(self, *args, **kwargs):
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
                            HTML(_("<span class=\"app-divider-label\">Přihlášení projektu</span>")),
                            HTML(_("<hr class=\"mt-0\" />")),
                            css_class="col-sm-12"
                        ),
                        Div(
                            Div("vedouci_projektu", css_class="flex-fill"),
                            HTML(_("<a href=\"/uzivatel/osoba/create\" class=\"btn app-btn-in-form\"><span class=\"material-icons\">add</span></a>")),
                            #"vedouci_projektu", 
                            css_class="col-sm-4 d-flex align-items-end"
                        ),
                        Div("organizace", css_class="col-sm-4"),
                        Div("uzivatelske_oznaceni", css_class="col-sm-4"),
                        Div("kulturni_pamatka", css_class="col-sm-3"),
                        Div("kulturni_pamatka_cislo", css_class="col-sm-3"),
                        Div("kulturni_pamatka_popis", css_class="col-sm-6"),
                        Div("latitude", css_class="hidden"),
                        Div("longitude", css_class="hidden"),
                        Div(
                            HTML(_("<span class=\"app-divider-label\">Terenní část</span>")),
                            HTML(_("<hr class=\"mt-0\" />")),
                            css_class="col-sm-12"
                        ),
                        Div("datum_zahajeni", css_class="col-sm-4"),
                        Div("datum_ukonceni", css_class="col-sm-4"),
                        #Div("termin_odevzdani", css_class="col-sm-4"),          
                        css_class="row",
                    ),
                    css_class="card-body",
                ),
                css_class="card app-card-form",
            )
        )
        self.helper.form_tag = False


class NavrhnoutZruseniProjektForm(forms.Form):
    reason = forms.CharField(label=_("Důvod návrhu zrušení"), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Návrh zrušení projektu")),
                    css_class="card-header",
                ),
                Div(
                    "reason",
                    css_class="card-body",
                ),
                Div(
                    FormActions(
                        Submit("save", "Navrhnout zrušení"),
                        HTML(
                            '<button type="button" class="btn" onclick="window.history.back();">Zpět</button>'
                        ),
                    ),
                ),
                css_class="card",
            )
        )


class PrihlaseniProjektForm(forms.ModelForm):
    class Meta:
        model = Projekt
        fields = (
            "vedouci_projektu",
            "kulturni_pamatka",
            "kulturni_pamatka_cislo",
            "kulturni_pamatka_popis",
            "uzivatelske_oznaceni",
        )
        widgets = {
            "kulturni_pamatka_popis": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "kulturni_pamatka_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "vedouci_projektu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "kulturni_pamatka": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        }
        labels = {
            "vedouci_projektu": _("Vedoucí projektu"),
            "kulturni_pamatka": _("Kulturní památka"),
            "kulturni_pamatka_cislo": _("Popis"),
            "kulturni_pamatka_popis": _("Číslo"),
            "uzivatelske_oznaceni": _("Uživatelské označení"),
        }
        help_texts = {
            "vedouci_projektu": _("Lorem ipsum."),
            "kulturni_pamatka": _("Lorem ipsum."),
            "kulturni_pamatka_cislo": _("Lorem ipsum."),
            "kulturni_pamatka_popis": _("Lorem ipsum."),
            "uzivatelske_oznaceni": _("Lorem ipsum."),
        }

    def __init__(self, *args, **kwargs):
        super(PrihlaseniProjektForm, self).__init__(*args, **kwargs)
        self.fields["vedouci_projektu"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Přihlášení projektu")),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        "vedouci_projektu",
                        "uzivatelske_oznaceni",
                        "kulturni_pamatka",
                        "kulturni_pamatka_cislo",
                        "kulturni_pamatka_popis",
                        css_class="card-body",
                    )
                ),
                css_class="card",
            )
        )
        self.helper.form_tag = False


class ZahajitVTerenuForm(forms.ModelForm):
    class Meta:
        model = Projekt
        fields = ("datum_zahajeni",)
        labels = {
            "datum_zahajeni": _("Datum zahájení prací"),
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
                    HTML(_("Zahájení výzkumu projektu")),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        "datum_zahajeni",
                        css_class="card-body",
                    )
                ),
                Div(
                    FormActions(
                        Submit("save", "Zahájit v terénu"),
                        HTML(
                            '<button type="button" class="btn" onclick="window.history.back();">Zpět</button>'
                        ),
                    )
                ),
                css_class="card",
            )
        )


class UkoncitVTerenuForm(forms.ModelForm):
    class Meta:
        model = Projekt
        fields = ("datum_ukonceni",)
        labels = {
            "datum_ukonceni": _("Datum ukončení prací"),
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
                    HTML(_("Ukončení výzkumu projektu")),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        "datum_ukonceni",
                        css_class="card-body",
                    ),
                    Div(
                        FormActions(
                            Submit("save", "Ukončit v terénu"),
                            HTML(
                                '<button type="button" class="btn" onclick="window.history.back();">Zpět</button>'
                            ),
                        )
                    ),
                ),
                css_class="card",
            )
        )
