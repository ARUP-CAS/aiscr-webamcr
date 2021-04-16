from adb.models import Adb
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.utils.translation import gettext as _


class CreateADBForm(forms.ModelForm):
    class Meta:
        model = Adb
        fields = (
            "typ_sondy",
            "uzivatelske_oznaceni_sondy",
            "trat",
            "cislo_popisne",
            "parcelni_cislo",
            "podnet",
            "stratigraficke_jednotky",
            "autor_popisu",
            "rok_popisu",
            "autor_revize",
            "rok_revize",
            "poznamka",
        )

        labels = {
            "typ_sondy": _("Typ sondy"),
            "uzivatelske_oznaceni_sondy": _("Uživatelské označení"),
            "trat": _("Ulice (trať)"),
            "cislo_popisne": _("Popisné číslo"),
            "parcelni_cislo": _("Číslo parcely"),
            "podnet": _("Podnět"),
            "stratigraficke_jednotky": _("Počet SJ"),
            "autor_popisu": _("Autor popisu"),
            "rok_popisu": _("Rok popisu"),
            "autor_revize": _("Autor revize"),
            "rok_revize": _("Rok revize"),
            "poznamka": _("Poznámka"),
        }

        widgets = {}

    def __init__(self, *args, **kwargs):
        super(CreateADBForm, self).__init__(*args, **kwargs)
        self.fields["uzivatelske_oznaceni_sondy"].required = False
        self.fields["autor_revize"].required = False
        self.fields["rok_revize"].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("typ_sondy", css_class="col"),
                Div("uzivatelske_oznaceni_sondy", css_class="col"),
                Div("trat", css_class="col"),
                Div("cislo_popisne", css_class="col"),
                Div("parcelni_cislo", css_class="col"),
                Div("podnet", css_class="col"),
                Div("stratigraficke_jednotky", css_class="col"),
                Div("autor_popisu", css_class="col"),
                Div("rok_popisu", css_class="col"),
                Div("autor_revize", css_class="col"),
                Div("rok_revize", css_class="col"),
                Div("poznamka", css_class="col"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
