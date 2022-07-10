from adb.models import Adb, VyskovyBod
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from crispy_forms.bootstrap import AppendedText
from cron.convertToSJTSK import convertToJTSK
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
            "cislo_popisne": _("Číslo popisné"),
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
            "uzivatelske_oznaceni_sondy": forms.TextInput(),
            "trat": forms.TextInput(),
            "cislo_popisne": forms.TextInput(),
            "parcelni_cislo": forms.TextInput(),
            "stratigraficke_jednotky": forms.TextInput(),
            "poznamka": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "autor_popisu": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "autor_revize": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        }

        help_texts = {
            "typ_sondy": _("adb.form.typSondy.tooltip"),
            "uzivatelske_oznaceni_sondy": _(
                "adb.form.uzivatelske_oznaceni_sondy.tooltip"
            ),
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

    def __init__(self, *args, readonly=False, **kwargs):
        super(CreateADBForm, self).__init__(*args, **kwargs)
        self.fields["uzivatelske_oznaceni_sondy"].required = False
        self.fields["autor_revize"].required = False
        self.fields["rok_revize"].required = False
        self.helper = FormHelper(self)
        if readonly:
            self.helper.layout = Layout(
            Div(
                Div("typ_sondy", css_class="col-sm-2"),
                Div("podnet", css_class="col-sm-2"),
                Div("uzivatelske_oznaceni_sondy", css_class="col-sm-2"),
                Div("trat", css_class="col-sm-2"),
                Div("cislo_popisne", css_class="col-sm-2"),
                Div("parcelni_cislo", css_class="col-sm-2"),
                Div("stratigraficke_jednotky", css_class="col-sm-2"),
                Div(css_class="col-sm-2"),
                Div("autor_popisu", css_class="col-sm-2"),
                Div("rok_popisu", css_class="col-sm-2"),
                Div("autor_revize", css_class="col-sm-2"),
                Div("rok_revize", css_class="col-sm-2"),
                Div("poznamka", css_class="col-sm-12"),
                css_class="row",
            ),
        )
        else:
            self.helper.layout = Layout(
                Div(
                    Div("typ_sondy", css_class="col-sm-2"),
                    Div("podnet", css_class="col-sm-2"),
                    Div("uzivatelske_oznaceni_sondy", css_class="col-sm-2"),
                    Div("trat", css_class="col-sm-2"),
                    Div("cislo_popisne", css_class="col-sm-2"),
                    Div("parcelni_cislo", css_class="col-sm-2"),
                    Div("stratigraficke_jednotky", css_class="col-sm-2"),
                    Div(css_class="col-sm-2"),
                    Div(
                                AppendedText("autor_popisu", '<button id="create-autor-popisu" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'),
                                css_class="col-sm-2 input-osoba",
                            ),
                    # Div("autor_popisu", css_class="col-sm-2"),
                    Div("rok_popisu", css_class="col-sm-2"),
                    Div(
                                AppendedText("autor_revize", '<button id="create-autor-revize" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'),
                                css_class="col-sm-2 input-osoba",
                            ),
                    #Div("autor_revize", css_class="col-sm-2"),
                    Div("rok_revize", css_class="col-sm-2"),
                    Div("poznamka", css_class="col-sm-12"),
                    css_class="row",
                ),
            )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
            if self.fields[key].disabled == True:
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"
                self.fields[key].help_text = ""


class VyskovyBodFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "inline_formset.html"
        self.form_tag = False
        self.form_id = "vb"


def create_vyskovy_bod_form(pian=None, niveleta=None,not_readonly=True):
    class CreateVyskovyBodForm(forms.ModelForm):
        northing = forms.FloatField(
            label=_("adb.form.vyskovyBod.northing.label"),
            help_text=_("adb.form.vyskovyBod.northing.tooltip"),
        )
        easting = forms.FloatField(
            label=_("adb.form.vyskovyBod.easting.label"),
            help_text=_("adb.form.vyskovyBod.easting.tooltip"),
        )
        niveleta = forms.FloatField(
            label=_("adb.form.vyskovyBod.niveleta.label"),
            help_text=_("adb.form.vyskovyBod.niveleta.tooltip"),
        )

        class Meta:
            model = VyskovyBod

            fields = ("ident_cely", "typ", "northing", "easting", "niveleta")

            labels = {
                 "ident_cely": _("adb.form.vyskovyBod.ident_cely.label"),
                "typ": _("adb.form.vyskovyBod.typ.label"),
                "niveleta": _("adb.form.vyskovyBod.niveleta.label"),
                "northing": _("adb.form.vyskovyBod.northing.label"),
                "easting": _("adb.form.vyskovyBod.easting.label"),
            }
            
            widgets = {
                "ident_cely": forms.Textarea(attrs={"rows": 1, "cols": 20}),
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
            self.fields["ident_cely"].required = False
            # self.fields["northing"].label = "X"
            # self.fields["easting"].label = "Y"
            if pian:
                [x, y] = convertToJTSK(pian.geom.centroid.y, pian.geom.centroid.x)
                self.fields["northing"].initial = round(x, 2)
                self.fields["easting"].initial = round(y, 2)
            if niveleta:
                self.fields["niveleta"].initial = niveleta

            for key in self.fields.keys():
                self.fields[key].disabled = not not_readonly
                if self.fields[key].disabled == True:
                    if isinstance(self.fields[key].widget, forms.widgets.Select):
                        self.fields[
                            key
                        ].widget.template_name = "core/select_to_text.html"
                    self.fields[key].help_text = ""
            self.fields["ident_cely"].disabled = True

    return CreateVyskovyBodForm
