from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, HTML
from dal import autocomplete
from django import forms
from django.utils.translation import gettext as _

from arch_z.models import Akce, ArcheologickyZaznam
from core.forms import TwoLevelSelectField
from heslar.hesla import HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT
from heslar.models import Heslar
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
        help_texts = {
            "hlavni_katastr": _("arch_z.form.hlavni_katastr.tooltip"),
            "pristupnost": _("arch_z.form.pristupnost.tooltip"),
            "uzivatelske_oznaceni": _("arch_z.form.uzivatelske_oznaceni.tooltip"),
            "katastry": _("arch_z.form.katastry.tooltip"),
        }

    def __init__(self, *args, **kwargs):
        projekt = kwargs.pop("projekt", None)
        projekt: Projekt
        super(CreateArchZForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
        self.fields["hlavni_katastr"].required = False
        self.fields["katastry"].widget.attrs["readonly"] = True
        self.fields["katastry"].widget.attrs["style"] = "pointer-events: none;"
        self.fields["hlavni_katastr"].widget.attrs["readonly"] = True
        self.fields["hlavni_katastr"].widget.attrs["style"] = "pointer-events: none;"
        if projekt:
            self.fields["hlavni_katastr"].initial = projekt.hlavni_katastr
            self.fields["uzivatelske_oznaceni"].initial = projekt.uzivatelske_oznaceni
            self.fields["katastry"].initial = projekt.katastry.all()

        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            Div(
                Div(
                    "hlavni_katastr",
                    css_class="col-sm-4",
                    style="pointer-events: none;",
                ),
                Div("pristupnost", css_class="col-sm-4"),
                Div("katastry", css_class="col-sm-4", style="pointer-events: none;"),
                Div("uzivatelske_oznaceni", css_class="col-sm-12"),
                css_class="row",
            ),
        )

        self.helper.form_tag = False
        for key in self.fields.keys():
            if self.fields[key].disabled == True:
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"
                self.fields[key].help_text = ""


class CreateAkceForm(forms.ModelForm):
    datum_zahajeni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        help_text=_("arch_z.form.datum_zahajeni.tooltip"),
    )
    datum_ukonceni = forms.DateField(
        validators=[validators.datum_max_1_mesic_v_budoucnosti],
        help_text=_("arch_z.form.datum_ukonceni.tooltip"),
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

        help_texts = {
            "hlavni_vedouci": _("arch_z.form.hlavni_vedouci.tooltip"),
            "organizace": _("arch_z.form.organizace.tooltip"),
            "lokalizace_okolnosti": _("arch_z.form.lokalizace_okolnosti.tooltip"),
            "ulozeni_nalezu": _("arch_z.form.ulozeni_nalezu.tooltip"),
            "souhrn_upresneni": _("arch_z.form.souhrn_upresneni.tooltip"),
            "je_nz": _("arch_z.form.je_nz.tooltip"),
            "specifikace_data": _("arch_z.form.specifikace_data.tooltip"),
            "ulozeni_dokumentace": _("arch_z.form.ulozeni_dokumentace.tooltip"),
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
            help_text=_("arch_z.form.hlavni_typ.tooltip"),
        )
        self.fields["vedlejsi_typ"] = TwoLevelSelectField(
            label=_("Vedlejší typ"),
            widget=forms.Select(
                choices=choices,
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
            required=False,
            help_text=_("arch_z.form.vedlejsi_typ.tooltip"),
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
            self.fields["specifikace_data"].widget.attrs["readonly"] = True
            self.fields["specifikace_data"].widget.attrs[
                "style"
            ] = "pointer-events: none;"
            self.fields["specifikace_data"].initial = Heslar.objects.filter(
                heslo="přesně"
            ).first()

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
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled == True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
<<<<<<< HEAD
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
=======
>>>>>>> 13d65913134be67ebc7b8650f28e76f9de02b51b
