from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Div, Layout, Submit
from dal import autocomplete
from django import forms
from django.forms import HiddenInput
from django.utils.translation import gettext as _
from oznameni.forms import DateRangeField, DateRangeWidget
from projekt.models import Projekt


class EditProjektForm(forms.ModelForm):
    latitude = forms.FloatField(required=True, widget=HiddenInput())
    longitude = forms.FloatField(required=True, widget=HiddenInput())
    planovane_zahajeni = DateRangeField(
        required=True,
        label=_("Plánované zahájení prací"),
        widget=DateRangeWidget(attrs={"rows": 1, "cols": 40}),
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
            "organizace",
            "kulturni_pamatka",
            "kulturni_pamatka_cislo",
            "kulturni_pamatka_popis",
            "datum_zahajeni",
            "datum_ukonceni",
            "latitude",
            "longitude",
            "katastry",
        )
        widgets = {
            "podnet": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "lokalizace": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "oznaceni_stavby": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "kulturni_pamatka_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "kulturni_pamatka_popis": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "datum_zahajeni": forms.DateInput(attrs={"data-provide": "datepicker"}),
            "datum_ukonceni": forms.DateInput(attrs={"data-provide": "datepicker"}),
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
            "podnet": _("Podnět"),
            "lokalizace": _("Lokalizace"),
            "parcelni_cislo": _("Parcelní číslo"),
            "oznaceni_stavby": _("Označení stavby"),
            "organizace": _("Organizace"),
            "kulturni_pamatka": _("Památková ochrana"),
            "kulturni_pamatka_cislo": _("Rejstříkové číslo USKP"),
            "kulturni_pamatka_popis": _("Název památky"),
            "datum_zahajeni": _("Datum zahájení výzkumu"),
            "datum_ukonceni": _("Datum ukončení výzkumu"),
        }

    def __init__(self, *args, **kwargs):
        super(EditProjektForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Editace projektu")),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div(
                            Div(
                                Div("typ_projektu", css_class="col-sm-3"),
                                Div("hlavni_katastr", css_class="col-sm-3"),
                                Div("katastry", css_class="col-sm-3"),
                                Div("planovane_zahajeni", css_class="col-sm-3"),
                                css_class="row",
                            ),
                            Div(
                                Div("podnet", css_class="col-sm-3"),
                                Div("lokalizace", css_class="col-sm-3"),
                                Div("parcelni_cislo", css_class="col-sm-3"),
                                Div("oznaceni_stavby", css_class="col-sm-3"),
                                css_class="row",
                            ),
                            Div(
                                # Div("latitude", css_class="col-sm-6,"),
                                # Div("longitude", css_class="col-sm-6"),
                                Div("latitude", css_class="hidden"),
                                Div("longitude", css_class="hidden"),
                                css_class="row",
                            ),
                            Div(
                                Div("datum_zahajeni", css_class="col-sm-3"),
                                Div("datum_ukonceni", css_class="col-sm-3"),
                                Div("organizace", css_class="col-sm-3"),
                                Div("kulturni_pamatka", css_class="col-sm-3"),
                                css_class="row",
                            ),
                            Div(
                                Div("kulturni_pamatka_cislo", css_class="col-sm-3"),
                                Div("kulturni_pamatka_popis", css_class="col-sm-3"),
                                css_class="row",
                            ),
                            Div(
                                FormActions(
                                    Submit("save", "Upravit"),
                                )
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
                css_class="card",
            )
        )


class VratitProjektForm(forms.Form):
    reason = forms.CharField(label=_("Důvod vrácení"), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Vrácení projektu")),
                    css_class="card-header",
                ),
                Div(
                    "reason",
                    css_class="card-body",
                ),
                Div(
                    FormActions(
                        Submit("save", "Vrátit"),
                        Button("cancel", "Zrušit"),
                    )
                ),
                css_class="card",
            )
        )


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
                        Button("cancel", "Zrušit"),
                    )
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
                        )
                    ),
                ),
                css_class="card",
            )
        )
