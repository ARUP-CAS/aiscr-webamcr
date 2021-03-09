from arch_z.models import Akce, ArcheologickyZaznam
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Div, Layout, Submit
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
        self.fields["hlavni_katastr"].required = True
        self.helper = FormHelper(self)
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
        )

        labels = {
            "hlavni_vedouci": _("Hlavní vedoucí"),
            "datum_zahajeni": _("Datum zahájení"),
            "datum_ukonceni": _("Datum ukončení"),
            "lokalizace_okolnosti": _("Lokalizace okolností"),
            "ulozeni_nalezu": _("Uložení nálezu"),
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
        self.fields["datum_zahajeni"].required = True
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class VratitAkciForm(forms.Form):
    reason = forms.CharField(label=_("Důvod vrácení"), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Vrácení akce")),
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
