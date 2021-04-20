from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _
from dokument.models import Dokument, DokumentExtraData


class CreateDokumentExtraDataForm(forms.ModelForm):
    class Meta:
        model = DokumentExtraData
        fields = (
            "datum_vzniku",
            "zachovalost",
            "nahrada",
            "pocet_variant_originalu",
            "odkaz",
            "format",
            "meritko",
            "vyska",
            "sirka",
            "cislo_objektu",
            "zeme",
            "region",
            "udalost",
            "udalost_typ",
            "rok_od",
            "rok_do",
            "duveryhodnost",
        )

        labels = {
            "datum_vzniku": _("Datum vzniku"),
            "zachovalost": _("Zachovalost"),
            "nahrada": _("Náhrada"),
            "pocet_variant_originalu": _("Počet variant originálu"),
            "odkaz": _("Odkaz"),
            "format": _("Formát plánu/foto"),
            "meritko": _("Měřítko plánu"),
            "vyska": _("Výška plánu"),
            "sirka": _("Šířka plánu"),
            "cislo_objektu": _("Objekt/kontext"),
            "zeme": _("Země"),
            "region": _("Region"),
            "udalost": _("Událost"),
            "udalost_typ": _("Typ události"),
            "rok_od": _("Rok od"),
            "rok_do": _("Rok do"),
            "duveryhodnost": _("Důvěryhodnost"),
        }

        def __init__(self, *args, **kwargs):
            super(CreateDokumentExtraDataForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper(self)
            self.helper.form_tag = False


class CreateDokumentForm(forms.ModelForm):
    class Meta:
        model = Dokument
        fields = (
            "typ_dokumentu",
            "organizace",
            "rok_vzniku",
            "pristupnost",
            "material_originalu",
            "popis",
            "poznamka",
            "ulozeni_originalu",
            "oznaceni_originalu",
            "datum_zverejneni",
            "licence",
            "jazyky",
            "posudky",
            "osoby",
        )
        widgets = {
            "typ_dokumentu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "material_originalu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        }
        labels = {
            "organizace": _("Organizace"),
            "rok_vzniku": _("Rok vzniku"),
            "material_originalu": _("Materiál originálu"),
            "typ_dokumentu": _("Typ dokumentu"),
            "popis": _("Popis"),
            "poznamka": _("Poznámka"),
            "ulozeni_originalu": _("Uložení originálu"),
            "oznaceni_originalu": _("Označení originálu"),
            "pristupnost": _("Přístupnost"),
            "datum_zverejneni": _("Datum zveřejnění"),
        }

    def __init__(self, *args, **kwargs):
        super(CreateDokumentForm, self).__init__(*args, **kwargs)
        self.fields["jazyky"].required = False
        self.fields["posudky"].required = False
        self.fields["osoby"].required = False
        self.helper = FormHelper(self)
        self.helper.form_tag = False
