import structlog

from core.constants import ROLE_ADMIN_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID
from core.forms import CheckStavNotChangedForm, TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from django import forms
from django.contrib.auth.models import Group
from django.contrib.gis.forms import ValidationError
from django.forms import ModelChoiceField
from django.utils.translation import gettext as _
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

logger_s = structlog.get_logger(__name__)


def validate_uzivatel_email(email):
    user = User.objects.filter(email=email)
    if not user.exists():
        raise ValidationError(
            _("Uživatel s emailem ") + email + _(" neexistuje."),
        )
    if user[0].hlavni_role not in Group.objects.filter(
        id__in=(ROLE_ARCHEOLOG_ID, ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)
    ):
        logger_s.debug("validate_uzivatel_email.ValidationError", email=email, hlavni_role_id=user[0].hlavni_role.pk)
        raise ValidationError(
            _("Uživatel s emailem ") + email + _(" nemá vhodnou roli pro spolupráci."),
        )


class ProjectModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s (%s)" % (obj.ident_cely, obj.vedouci_projektu)


class PotvrditNalezForm(forms.ModelForm):
    predano = forms.BooleanField(
        required=False,
        widget=forms.Select(
            attrs={"class": "select"},
            choices=(
                (True, "Ano"),
                (False, "Ne"),
            ),
        ),
        label=_("Nález předán"),
        help_text=_("pas.form.potvrditNalez.predano.tooltip"),
        error_messages={
            "required": _("Nález musí být předán. Vyplňte Ano"),
        },
    )
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

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
            "pristupnost": _("Přístupnost"),
        }
        help_texts = {
            "evidencni_cislo": _("pas.form.potvrditNalez.evidencni_cislo.tooltip"),
            "predano_organizace": _("pas.form.potvrditNalez.predano_organizace.tooltip"),
            "pristupnost": _("pas.form.potvrditNalez.pristupnost.tooltip"),
        }

    def __init__(self, *args, readonly=False, predano_required=False, **kwargs):
        super(PotvrditNalezForm, self).__init__(*args, **kwargs)
        self.fields["evidencni_cislo"].required = True
        self.fields["predano_organizace"].required = True
        self.fields["predano"].required = predano_required
        self.fields["pristupnost"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("predano_organizace", css_class="col-sm-6"),
                Div("evidencni_cislo", css_class="col-sm-6"),
                Div("predano", css_class="col-sm-6"),
                Div("pristupnost", css_class="col-sm-6"),
                Div("old_stav"),
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
                if self.fields[key].disabled is True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""


class CreateSamostatnyNalezForm(forms.ModelForm):
    # latitude = forms.FloatField(required=False, widget=HiddenInput())
    # longitude = forms.FloatField(required=False, widget=HiddenInput())
    katastr = forms.CharField(
        max_length=50,
        label=_("Katastrální území"),
        error_messages={"required": "Je třeba vybrat bod na mapě."},
        help_text=_("pas.form.createSamostatnyNalez.katastr.tooltip"),
        required=True
    )

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
        help_texts = {
            "nalezce": _("pas.form.createSamostatnyNalez.nalezce.tooltip"),
            "datum_nalezu": _("pas.form.createSamostatnyNalez.datum_nalezu.tooltip"),
            "lokalizace": _("pas.form.createSamostatnyNalez.lokalizace.tooltip"),
            "okolnosti": _("pas.form.createSamostatnyNalez.okolnosti.tooltip"),
            "hloubka": _("pas.form.createSamostatnyNalez.hloubka.tooltip"),
            "obdobi": _("pas.form.createSamostatnyNalez.obdobi.tooltip"),
            "druh_nalezu": _("pas.form.createSamostatnyNalez.druh_nalezu.tooltip"),
            "pocet": _("pas.form.createSamostatnyNalez.pocet.tooltip"),
            "presna_datace": _("pas.form.createSamostatnyNalez.presna_datace.tooltip"),
            "specifikace": _("pas.form.createSamostatnyNalez.specifikace.tooltip"),
            "poznamka": _("pas.form.createSamostatnyNalez.poznamka.tooltip"),
        }

    def __init__(self, *args, readonly=False, user=None, required=None,required_next=None, **kwargs):
        projekt_disabed = kwargs.pop("projekt_disabled", False)
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
            help_text=_("pas.form.createSamostatnyNalez.projekt.tooltip"),
        )
        self.fields["katastr"].widget.attrs["readonly"] = True
        self.fields["druh_nalezu"] = TwoLevelSelectField(
            label=_("Druh nálezu"),
            widget=forms.Select(
                choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT),
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
            help_text=_("pas.form.createSamostatnyNalez.drih_nalezu.tooltip"),
        )
        self.fields["obdobi"] = TwoLevelSelectField(
            label=_("Období"),
            widget=forms.Select(
                choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT),
                attrs={"class": "selectpicker", "data-live-search": "true"},
            ),
            help_text=_("pas.form.createSamostatnyNalez.obdobi.tooltip"),
        )
        self.fields["druh_nalezu"].required = False
        self.fields["obdobi"].required = False
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("projekt", css_class="col-sm-4"),
                Div("nalezce", css_class="col-sm-4"),
                Div("datum_nalezu", css_class="col-sm-4"),
                Div("lokalizace", css_class="col-sm-8"),
                Div("katastr", css_class="col-sm-4"),
                Div("okolnosti", css_class="col-sm-6"),
                Div("hloubka", css_class="col-sm-6"),
                #                Div("latitude", css_class="hidden"),
                #                Div("longitude", css_class="hidden"),
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
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
                self.fields[key].required = False
            if required:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"]= str(self.fields[key].widget.attrs["class"]) + (' required-next' if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"]= 'required-next' if key in required_next else ""
        if projekt_disabed:
            self.fields["projekt"].disabled = projekt_disabed
        if self.instance is not None:
            self.fields["katastr"].initial = self.instance.katastr
            

class CreateZadostForm(forms.Form):
    email_uzivatele = forms.EmailField(
        label=_("Uživatel"),
        widget=forms.EmailInput(
            attrs={"placeholder": _("Zadejte email uživatele pro spolupráci")}
        ),
        required=True,
        validators=[validate_uzivatel_email],
        help_text=_("pas.form.createZadost.email_uzivatele.tooltip"),
    )
    text = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(CreateZadostForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
