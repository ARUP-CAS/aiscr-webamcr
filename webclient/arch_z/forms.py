from arch_z.models import Akce, ArcheologickyZaznam
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _
from heslar.models import RuianKatastr
from heslar.views import heslar_typ_akce_12


class CreateArchZForm(forms.ModelForm):

    dalsi_katastry = forms.MultipleChoiceField()

    class Meta:
        model = ArcheologickyZaznam
        fields = (
            "hlavni_katastr",
            "pristupnost",
            "uzivatelske_oznaceni",
        )

        labels = {
            "hlavni_katastr": _("Hlavní katastr"),
            "pristupnost": _("Přístupnost"),
            "uzivatelske_oznaceni": _("Uživatelské označení"),
        }

    def __init__(self, *args, **kwargs):
        super(CreateArchZForm, self).__init__(*args, **kwargs)
        self.fields["dalsi_katastry"] = forms.MultipleChoiceField(
            label=_("Další katastry"),
            required=False,
            choices=RuianKatastr.objects.all().values_list("id", "nazev"),
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class CreateAkceForm(forms.ModelForm):
    hlavni_typ = forms.CharField()
    vedlejsi_typ = forms.CharField()

    class Meta:
        model = Akce
        fields = (
            "hlavni_vedouci",
            "datum_zahajeni_v",
            "datum_ukonceni_v",
            "lokalizace_okolnosti",
        )

        labels = {
            "hlavni_vedouci": _("Hlavní vedoucí"),
            "datum_zahajeni_v": _("Datum zahájení"),
            "datum_ukonceni_v": _("Datum ukončení"),
            "lokalizace_okolnosti": _("Lokalizace okolností"),
        }

    def __init__(self, *args, **kwargs):
        super(CreateAkceForm, self).__init__(*args, **kwargs)
        choices = heslar_typ_akce_12()
        self.fields["hlavni_typ"] = forms.CharField(
            label=_("Hlavní typ"), widget=forms.Select(choices=choices), required=True
        )
        self.fields["vedlejsi_typ"] = forms.CharField(
            label=_("Vedlejší typ"),
            widget=forms.Select(choices=choices),
            required=False,
        )
        self.fields["lokalizace_okolnosti"].required = True
        self.fields["datum_zahajeni_v"].required = True
        self.helper = FormHelper(self)
        self.helper.form_tag = False
