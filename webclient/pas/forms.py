from core.constants import ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID
from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.contrib.auth.models import Group
from django.contrib.gis.forms import ValidationError
from django.forms import HiddenInput
from django.utils.translation import gettext as _
from django.forms import ModelChoiceField
from heslar.hesla import (
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    TYP_PROJEKTU_PRUZKUM_ID,
)
from heslar.views import heslar_12
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from uzivatel.models import User


def validate_uzivatel_email(email):
    user = User.objects.filter(email=email)
    if not user.exists():
        raise ValidationError(
            _("Uživatel s emailem ") + email + _(" neexistuje."),
        )
    if user[0].hlavni_role not in Group.objects.filter(
        id__in=(ROLE_ARCHEOLOG_ID, ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    ):
        raise ValidationError(
            _("Uživatel s emailem ") + email + _(" nemá vhodnou roli pro spolupráci."),
        )


class ProjectModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s (%s)" % (obj.ident_cely, obj.vedouci_projektu)


class PotvrditNalezForm(forms.ModelForm):
    class Meta:
        model = SamostatnyNalez
        fields = ("predano_organizace", "evidencni_cislo", "predano", "pristupnost")
        widgets = {
            "evidencni_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "predano_organizace": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        }
        labels = {
            "evidencni_cislo": _("Evidenční číslo"),
            "predano_organizace": _("Předáno organizaci"),
            "predano": _("Nález předán"),
            "pristupnost": _("Přístupnost"),
        }
        help_texts = {
            "evidencni_cislo": _("Lorem ipsum."),
            "predano_organizace": _("Lorem ipsum."),
            "predano": _("Lorem ipsum."),
            "pristupnost": _("Lorem ipsum."),
        }

    def __init__(self, *args, readonly=False, **kwargs):
        super(PotvrditNalezForm, self).__init__(*args, **kwargs)
        self.fields["evidencni_cislo"].required = True
        self.fields["predano_organizace"].required = True
        self.fields["predano"].required = True
        self.fields["pristupnost"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("predano_organizace", css_class="col-sm-6"),
                Div("evidencni_cislo", css_class="col-sm-6"),
                Div("predano", css_class="col-sm-6"),
                Div("pristupnost", css_class="col-sm-6"),
                css_class="row",
            ),
        )
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
        self.helper.form_tag = False
        self.fields["predano_organizace"].disabled = True
        for key in self.fields.keys():
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled == True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"


class CreateSamostatnyNalezForm(forms.ModelForm):
    latitude = forms.FloatField(required=False, widget=HiddenInput())
    longitude = forms.FloatField(required=False, widget=HiddenInput())

    class Meta:
        model = SamostatnyNalez
        fields = (
            "projekt",
            "nalezce",
            "datum_nalezu",
            "lokalizace",
            "okolnosti",
            "hloubka",
            "obdobi",
            "druh_nalezu",
            "pocet",
            "presna_datace",
            "specifikace",  # material
            "poznamka",
        )
        widgets = {
            "nalezce": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "okolnosti": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "specifikace": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        }
        labels = {
            "nalezce": _("Nálezce"),
            "datum_nalezu": _("Datum nálezu"),
            "lokalizace": _("Lokalizace"),
            "okolnosti": _("Nálezové okolnosti"),
            "hloubka": _("Hloubka (cm)"),
            "obdobi": _("Období"),
            "druh_nalezu": _("Nález"),
            "pocet": _("Počet"),
            "presna_datace": _("Přesná datace"),
            "specifikace": _("Materiál"),
            "poznamka": _("Poznámka / bližší popis"),
        }

    def __init__(self, *args, readonly=False, user=None, **kwargs):
        projekt_disabed = kwargs.pop("projekt_disabled", False)
        fields_required = kwargs.pop("fields_required", False)
        super(CreateSamostatnyNalezForm, self).__init__(*args, **kwargs)
        self.fields["lokalizace"].widget.attrs["rows"] = 1
        self.fields["pocet"].widget.attrs["rows"] = 1
        self.fields["presna_datace"].widget.attrs["rows"] = 1
        self.fields["poznamka"].widget.attrs["rows"] = 1
        self.fields["projekt"] = ProjectModelChoiceField(
            queryset=Projekt.objects.filter(typ_projektu=TYP_PROJEKTU_PRUZKUM_ID)
            .filter(organizace__in=user.moje_spolupracujici_organizace())
            .filter(stav__in=user.moje_stavy_pruzkumnych_projektu()),
            widget=forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
        )
        self.fields["druh_nalezu"] = TwoLevelSelectField(
            label=_("Druh nálezu"),
            widget=forms.Select(
                choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT),
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.fields["obdobi"] = TwoLevelSelectField(
            label=_("Období"),
            widget=forms.Select(
                choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT),
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
        )
        self.fields["druh_nalezu"].required = False
        self.fields["obdobi"].required = False
        if fields_required:
            self.fields["druh_nalezu"].required = True
            self.fields["lokalizace"].required = True
            self.fields["datum_nalezu"].required = True
            self.fields["okolnosti"].required = True
            self.fields["specifikace"].required = True
            self.fields["obdobi"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("projekt", css_class="col-sm-4"),
                Div("nalezce", css_class="col-sm-4"),
                Div("datum_nalezu", css_class="col-sm-4"),
                Div("lokalizace", css_class="col-sm-12"),
                Div("okolnosti", css_class="col-sm-6"),
                Div("hloubka", css_class="col-sm-6"),
                Div("latitude", css_class="hidden"),
                Div("longitude", css_class="hidden"),
                Div("obdobi", css_class="col-sm-4"),
                Div("druh_nalezu", css_class="col-sm-4"),
                Div("pocet", css_class="col-sm-4"),
                Div("presna_datace", css_class="col-sm-4"),
                Div("specifikace", css_class="col-sm-4"),
                Div("poznamka", css_class="col-sm-4"),
                css_class="row",
            ),
        )
        self.helper.form_tag = False
        for key in self.fields.keys():
            self.fields[key].disabled = readonly
        if projekt_disabed:
            self.fields["projekt"].disabled = projekt_disabed
        for key in self.fields.keys():
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled == True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"


class CreateZadostForm(forms.Form):
    email_uzivatele = forms.EmailField(
        label=_("Uživatel"),
        widget=forms.EmailInput(
            attrs={"placeholder": _("Zadejte email uživatele pro spolupráci")}
        ),
        required=True,
        validators=[validate_uzivatel_email],
    )

    def __init__(self, *args, **kwargs):
        super(CreateZadostForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
