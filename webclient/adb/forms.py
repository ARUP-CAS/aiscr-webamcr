from adb.models import Adb, VyskovyBod
from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.utils.translation import gettext as _
from django.contrib.gis.forms import PointField
from django.contrib.gis.geos import Point


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

        help_texts = {
            "typ_sondy": _("adb.form.typSondy.tooltip"),
            "uzivatelske_oznaceni_sondy": _("adb.form.uzivatelske_oznaceni_sondy.tooltip"),
            "trat": _("adb.form.trat.tooltip"),
            "cislo_popisne": _("adb.form.cislo_popisne.tooltip"),
            "parcelni_cislo": _("adb.form.parcelni_cislo.tooltip"),
            "podnet": _("adb.form.podnet.tooltip"),
            "stratigraficke_jednotky": _("adb.form.stratigraficke_jednotky.tooltip"),
            "autor_popisu": _("adb.form.autor_popisu.tooltip"),
            "rok_popisu": _("adb.form.rok_popisu.tooltip"),
            "autor_revize": _("adb.form.autor_revize.tooltip"),
            "rok_revize": _("adb.form.rok_revize.tooltip"),
            "poznamka": _("adb.form.poznamka.tooltip"),
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
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""


class VyskovyBodFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "bootstrap4/table_inline_formset.html"
        self.form_tag = False


def create_vyskovy_bod_form(pian=None):
    class CreateVyskovyBodForm(forms.ModelForm):
        northing = forms.FloatField(help_text=_("adb.form.vyskovyBod.northing.tooltip"),)
        easting = forms.FloatField(help_text=_("adb.form.vyskovyBod.easting.tooltip"),)
        def save(self, commit=True):
            form_data = self.cleaned_data
            self.instance.geom = Point(form_data['northing'], form_data['easting'])
            return super(CreateVyskovyBodForm, self).save(commit)
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
            help_texts = {
            "ident_cely": _("adb.form.vyskovyBod.ident_cely.tooltip"),
            "typ": _("adb.form.vyskovyBod.typ.tooltip"),
            "niveleta": _("adb.form.vyskovyBod.niveleta.tooltip"),
            "northing": _("adb.form.vyskovyBod.northing.tooltip"),
            "easting": _("adb.form.vyskovyBod.easting.tooltip"),
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
            else:
                if self.instance.geom:
                    self.fields["northing"].initial = self.instance.geom.centroid.x
                    self.fields["easting"].initial = self.instance.geom.centroid.y

            for key in self.fields.keys():
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    self.fields[key].help_text = ""

    return CreateVyskovyBodForm
