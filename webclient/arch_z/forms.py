from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, HTML
from dal import autocomplete
from django import forms
from django.utils.translation import gettext as _

from arch_z.models import Akce, ArcheologickyZaznam
from core.constants import (
    D_STAV_ARCHIVOVANY,
    D_STAV_ODESLANY,
)
from core.forms import TwoLevelSelectField
from dokument.models import Dokument
from heslar.hesla import HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT
from heslar.views import heslar_12
from projekt.models import Projekt
from . import validators


class CreateArchZForm(forms.ModelForm):
    class Meta:
        model = ArcheologickyZaznam
        fields = (
            "hlavni_katastr",
            "pristupnost",
            "uzivatelske_oznaceni",
            "katastry",
        )

        labels = {
            "hlavni_katastr": _("Hlavní katastr"),
            "pristupnost": _("Přístupnost"),
            "uzivatelske_oznaceni": _("Uživatelské označení"),
            "katastry": _("Další katastry"),
        }
        widgets = {
            "hlavni_katastr": autocomplete.ModelSelect2(
                url="heslar:katastr-autocomplete"
            ),
            "katastry": autocomplete.ModelSelect2Multiple(
                url="heslar:katastr-autocomplete"
            ),
            "uzivatelske_oznaceni": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }

    def __init__(self, *args, **kwargs):
        projekt = kwargs.pop("projekt", None)
        projekt: Projekt
        super(CreateArchZForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
        self.fields["hlavni_katastr"].required = False
        self.fields["katastry"].disabled = True
        self.fields["hlavni_katastr"].disabled = True
        if projekt:
            self.fields["hlavni_katastr"].initial = projekt.hlavni_katastr
            self.fields["uzivatelske_oznaceni"].initial = projekt.uzivatelske_oznaceni

        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            Div(
                Div("hlavni_katastr", css_class="col-sm-4"),
                Div("pristupnost", css_class="col-sm-4"),
                Div("katastry", css_class="col-sm-4"),
                Div("uzivatelske_oznaceni", css_class="col-sm-12"),
                css_class="row",
            ),
        )

        self.helper.form_tag = False
        for key in self.fields.keys():
            if self.fields[key].disabled == True:
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"


class CreateAkceForm(forms.ModelForm):
    datum_zahajeni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti]
    )
    datum_ukonceni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti]
    )

    def clean(self):
        cleaned_data = super().clean()
        if {"datum_zahajeni", "datum_ukonceni"} <= cleaned_data.keys():
            if cleaned_data.get("datum_zahajeni") > cleaned_data.get("datum_ukonceni"):
                raise forms.ValidationError(
                    "Datum zahájení nemůže být po datu ukončení"
                )
        return self.cleaned_data

    class Meta:
        model = Akce
        fields = (
            "hlavni_vedouci",
            "organizace",
            "datum_zahajeni",
            "datum_ukonceni",
            "lokalizace_okolnosti",
            "ulozeni_nalezu",
            "souhrn_upresneni",
            "je_nz",
            "hlavni_typ",
            "vedlejsi_typ",
            "specifikace_data",
            "ulozeni_dokumentace",
        )

        labels = {
            "hlavni_vedouci": _("Hlavní vedoucí"),
            "datum_zahajeni": _("Datum zahájení"),
            "datum_ukonceni": _("Datum ukončení"),
            "lokalizace_okolnosti": _("Lokalizace okolností"),
            "ulozeni_nalezu": _("Uložení nálezu"),
            "souhrn_upresneni": _("Poznámka"),
            "je_nz": _("Odeslat ZAA jako NZ"),
            "specifikace_data": _("Specifikace data"),
            "ulozeni_dokumentace": _("Uložení dokumentace"),
        }

        widgets = {
            "hlavni_vedouci": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "lokalizace_okolnosti": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "ulozeni_nalezu": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "souhrn_upresneni": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "ulozeni_dokumentace": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }

    def __init__(self, *args, **kwargs):
        if "uzamknout_specifikace" in kwargs:
            uzamknout_specifikace = kwargs.pop("uzamknout_specifikace")
        else:
            uzamknout_specifikace = False
        projekt = kwargs.pop("projekt", None)
        projekt: Projekt
        super(CreateAkceForm, self).__init__(*args, **kwargs)
        choices = heslar_12(HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT)
        self.fields["hlavni_typ"] = TwoLevelSelectField(
            label=_("Hlavní typ"),
            widget=forms.Select(
                choices=choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
            required=True,
        )
        self.fields["vedlejsi_typ"] = TwoLevelSelectField(
            label=_("Vedlejší typ"),
            widget=forms.Select(
                choices=choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
            required=False,
        )
        self.fields["lokalizace_okolnosti"].required = True
        if projekt:
            self.fields["hlavni_vedouci"].initial = projekt.vedouci_projektu
            self.fields["organizace"].initial = projekt.organizace
            self.fields["datum_zahajeni"].initial = projekt.datum_zahajeni
            self.fields["datum_ukonceni"].initial = projekt.datum_ukonceni
            self.fields[
                "lokalizace_okolnosti"
            ].initial = f"{projekt.lokalizace}. Parc.č.: {projekt.parcelni_cislo}"
        self.fields["datum_zahajeni"].required = True
        self.helper = FormHelper(self)
        if uzamknout_specifikace:
            self.fields["specifikace_data"].disabled = True

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div("hlavni_vedouci", css_class="col-sm-10"),
                        Div(
                            HTML(
                                '<a href="{% url "uzivatel:create_osoba" %}" target="_blank"><input type="button" value="+" class="btn btn-secondary" /></a>'
                            ),
                            css_class="col-sm-2",
                            style="display: flex; align-items: center;",
                        ),
                        css_class="row",
                    ),
                    css_class="col-sm-4",
                ),
                Div("organizace", css_class="col-sm-4"),
                Div("datum_zahajeni", css_class="col-sm-4"),
                Div("datum_ukonceni", css_class="col-sm-4"),
                Div("lokalizace_okolnosti", css_class="col-sm-4"),
                Div("ulozeni_nalezu", css_class="col-sm-4"),
                Div("souhrn_upresneni", css_class="col-sm-4"),
                Div("hlavni_typ", css_class="col-sm-4"),
                Div("vedlejsi_typ", css_class="col-sm-4"),
                Div("je_nz", css_class="col-sm-4 d-flex align-items-end"),
                Div("specifikace_data", css_class="col-sm-4"),
                Div("ulozeni_dokumentace", css_class="col-sm-4"),
                css_class="row",
            ),
        )

        self.helper.form_tag = False
        for key in self.fields.keys():
            if self.fields[key].disabled == True:
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"


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
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class PripojitProjDocForm(forms.Form):
    def __init__(self, *args, projekt_docs, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["dokument"] = forms.MultipleChoiceField(
            label=_("Projektové dokumenty k připojení"),
            required=True,
            choices=projekt_docs + [("", "")],
            widget=forms.SelectMultiple(
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False
