from adb.models import Adb, VyskovyBod
from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.utils.translation import gettext as _
from django.contrib.gis.forms import PointField


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
        widgets = {
            "uzivatelske_oznaceni_sondy": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "trat": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "cislo_popisne": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "stratigraficke_jednotky": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "poznamka": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }

        # widgets = {
        #     "autor_popisu": autocomplete.ModelSelect2(
        #         url="uzivatel:osoba-autocomplete"
        #     ),
        #     "autor_revize": autocomplete.ModelSelect2(
        #         url="uzivatel:osoba-autocomplete"
        #     ),
        # }

    def __init__(self, *args, **kwargs):
        super(CreateADBForm, self).__init__(*args, **kwargs)
        self.fields["uzivatelske_oznaceni_sondy"].required = False
        self.fields["autor_revize"].required = False
        self.fields["rok_revize"].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("typ_sondy", css_class="col-sm-3"),
                Div("uzivatelske_oznaceni_sondy", css_class="col-sm-3"),
                Div("trat", css_class="col-sm-3"),
                Div("cislo_popisne", css_class="col-sm-3"),
                Div("parcelni_cislo", css_class="col-sm-3"),
                Div("podnet", css_class="col-sm-3"),
                Div("stratigraficke_jednotky", css_class="col-sm-3"),
                Div("autor_popisu", css_class="col-sm-3"),
                Div("rok_popisu", css_class="col-sm-3"),
                Div("autor_revize", css_class="col-sm-3"),
                Div("rok_revize", css_class="col-sm-3"),
                Div("poznamka", css_class="col-sm-3"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""


class VyskovyBodFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "bootstrap4/table_inline_formset.html"
        self.form_tag = False


def create_vyskovy_bod_form(pian=None):
    class CreateVyskovyBodForm(forms.ModelForm):
        northing = forms.FloatField()
        easting = forms.FloatField()
        class Meta:
            model = VyskovyBod

            fields = ("ident_cely", "typ", "niveleta", "northing", "easting")

            # labels = {
            #     "pocet": _("Počet"),
            #     "poznamka": _("Poznámka"),
            # }
            #
            widgets = {
                "ident_cely": forms.Textarea(attrs={"rows": 1, "10": 40}),
            }

        def __init__(self, *args, **kwargs):
            super(CreateVyskovyBodForm, self).__init__(*args, **kwargs)
            self.fields["ident_cely"].disabled = True
            self.fields["ident_cely"].required = False
            self.fields["northing"].label = "X"
            self.fields["easting"].label = "Y"
            if pian:
                self.fields["northing"].initial = pian.geom.centroid.x
                self.fields["easting"].initial = pian.geom.centroid.y

            for key in self.fields.keys():
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].empty_label = ""

    return CreateVyskovyBodForm
