from arch_z.models import Akce, ArcheologickyZaznam
from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from dal import autocomplete
from django import forms
from django.utils.translation import gettext as _
from dokument.models import Dokument
from heslar.hesla import HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT
from heslar.views import heslar_12


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
        super(CreateArchZForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
        self.fields["hlavni_katastr"].required = True
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


class CreateAkceForm(forms.ModelForm):
    class Meta:
        model = Akce
        fields = (
            "hlavni_vedouci",
            "datum_zahajeni",
            "datum_ukonceni",
            "lokalizace_okolnosti",
            "ulozeni_nalezu",
            "souhrn_upresneni",
            "je_nz",
            "hlavni_typ",
            "vedlejsi_typ",
        )

        labels = {
            "hlavni_vedouci": _("Hlavní vedoucí"),
            "datum_zahajeni": _("Datum zahájení"),
            "datum_ukonceni": _("Datum ukončení"),
            "lokalizace_okolnosti": _("Lokalizace okolností"),
            "ulozeni_nalezu": _("Uložení nálezu"),
            "souhrn_upresneni": _("Poznámka"),
            "je_nz": _("Odeslat ZAA jako NZ"),
        }

        widgets = {
            "hlavni_vedouci": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "lokalizace_okolnosti": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "ulozeni_nalezu": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "souhrn_upresneni": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }

    def __init__(self, *args, **kwargs):
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
        self.fields["datum_zahajeni"].required = True
        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            Div(
                Div("hlavni_vedouci", css_class="col-sm-4"),
                Div("datum_zahajeni", css_class="col-sm-4"),
                Div("datum_ukonceni", css_class="col-sm-4"),
                Div("lokalizace_okolnosti", css_class="col-sm-4"),
                Div("ulozeni_nalezu", css_class="col-sm-4"),
                Div("souhrn_upresneni", css_class="col-sm-4"),
                Div("hlavni_typ", css_class="col-sm-4"),
                Div("vedlejsi_typ", css_class="col-sm-4"),
                Div("je_nz", css_class="col-sm-4 d-flex align-items-end"),
                css_class="row",
            ),
        )

        self.helper.form_tag = False


class PripojitDokumentForm(forms.Form):

    dokument = forms.MultipleChoiceField(
        label=_("Vyberte dokument k připojení"),
        choices=list(Dokument.objects.all().values_list("id", "ident_cely")),
        widget=autocomplete.Select2Multiple(url="dokument:dokument-autocomplete"),
    )

    def __init__(self, projekt=None, *args, **kwargs):
        super(PripojitDokumentForm, self).__init__(projekt, *args, **kwargs)
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
