import logging

from core.constants import ROLE_ADMIN_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID
from core.forms import BaseFilterForm, TwoLevelSelectField
from crispy_forms.bootstrap import AppendedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout
from dal import autocomplete
from django import forms
from django.contrib.auth.models import Group
from django.contrib.gis.forms import ValidationError
from django.forms import ModelChoiceField
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from heslar.hesla import HESLAR_OBDOBI, HESLAR_OBDOBI_KAT, HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT
from heslar.hesla_dynamicka import TYP_PROJEKTU_PRUZKUM_ID
from heslar.views import heslar_12
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from uzivatel.models import User

logger = logging.getLogger(__name__)


def validate_uzivatel_email(email):
    """
    Funkce pro validaci zadaného emailu uživatele.
    """
    user = User.objects.filter(email=email)
    if not user.exists():
        raise ValidationError(
            _("pas.forms.te_uzivatel_email.error.noUser.part1")
            + email
            + _("pas.forms.te_uzivatel_email.error.noUser.part2"),
        )
    if user[0].hlavni_role not in Group.objects.filter(id__in=(ROLE_ARCHEOLOG_ID, ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)):
        logger.debug(
            "validate_uzivatel_email.ValidationError",
            extra={"email": email, "hlavni_role": user[0].hlavni_role},
        )
        raise ValidationError(
            _("pas.forms.te_uzivatel_email.error.wrongGroup.part1")
            + email
            + _("pas.forms.te_uzivatel_email.error.wrongGroup.part2"),
        )


class ProjectModelChoiceField(ModelChoiceField):
    """
    Třída pro správne zobrazení label.
    """

    def label_from_instance(self, obj):
        return "%s (%s)" % (obj.ident_cely, obj.vedouci_projektu)


class PotvrditNalezForm(forms.ModelForm):
    """
    Hlavní formulář pro potvrzení nálezu lokality.
    """

    predano = forms.BooleanField(
        required=False,
        widget=forms.Select(
            attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"},
            choices=(
                (True, _("pas.forms.potvrditNalezForm.prenado.choice.ano")),
                (False, _("pas.forms.potvrditNalezForm.prenado.choice.ne")),
            ),
        ),
        label=_("pas.forms.potvrditNalezForm.prenado.label"),
        help_text=_("pas.forms.potvrditNalezForm.prenado.tooltip"),
        error_messages={
            "required": _("pas.forms.potvrditNalezForm.prenado.errorMessage"),
        },
    )
    old_stav = forms.CharField(required=True, widget=forms.HiddenInput())

    class Meta:
        model = SamostatnyNalez
        fields = ("predano_organizace", "evidencni_cislo", "predano", "pristupnost")
        widgets = {
            "evidencni_cislo": forms.TextInput(),
            "predano_organizace": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "pristupnost": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
        }
        labels = {
            "evidencni_cislo": _("pas.forms.potvrditNalezForm.evidencniCislo.label"),
            "predano_organizace": _("pas.forms.potvrditNalezForm.predanoOrganizaci.label"),
            "pristupnost": _("pas.forms.potvrditNalezForm.pristupnost.label"),
        }
        help_texts = {
            "evidencni_cislo": _("pas.forms.potvrditNalezForm.evidencniCislo.tooltip"),
            "predano_organizace": _("pas.forms.potvrditNalezForm.predanoOrganizace.tooltip"),
            "pristupnost": _("pas.forms.potvrditNalezForm.pristupnost.tooltip"),
        }

    def __init__(self, *args, readonly=False, predano_required=False, predano_hidden=False, **kwargs):
        super(PotvrditNalezForm, self).__init__(*args, **kwargs)
        self.fields["evidencni_cislo"].required = True
        self.fields["predano_organizace"].required = False
        self.fields["predano"].required = predano_required
        self.fields["pristupnost"].required = True
        self.helper = FormHelper(self)
        if not predano_hidden:
            self.helper.layout = Layout(
                Div(
                    Div("predano_organizace", css_class="col-sm-3"),
                    Div("evidencni_cislo", css_class="col-sm-3"),
                    Div("predano", css_class="col-sm-3"),
                    Div("pristupnost", css_class="col-sm-3"),
                    Div("old_stav"),
                    css_class="row",
                ),
            )
        else:
            self.helper.layout = Layout(
                Div(
                    Div("evidencni_cislo", css_class="col-sm-3"),
                    Div("predano", css_class="col-sm-3"),
                    Div("pristupnost", css_class="col-sm-3"),
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
                self.fields[key].required = False


class CreateSamostatnyNalezForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení samostatnýho nálezu.
    """

    katastr = forms.CharField(
        max_length=50,
        label=_("pas.forms.createSamostatnyNalezForm.katastr.label"),
        error_messages={"required": _("pas.forms.createSamostatnyNalezForm.katastr.errorMessage")},
        help_text=_("pas.forms.createSamostatnyNalezForm.katastr.tooltip"),
        required=True,
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
            "nalezce": autocomplete.ModelSelect2(url="heslar:osoba-autocomplete"),
            "okolnosti": forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                    "data-container": ".content-with-table-responsive-container",
                }
            ),
            "specifikace": forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                    "data-container": ".content-with-table-responsive-container",
                }
            ),
            "presna_datace": forms.TextInput(),
            "pocet": forms.TextInput(),
            "poznamka": forms.TextInput(),
        }
        labels = {
            "projekt": _("pas.forms.createSamostatnyNalezForm.projekt.label"),
            "nalezce": _("pas.forms.createSamostatnyNalezForm.nalezce.label"),
            "datum_nalezu": _("pas.forms.createSamostatnyNalezForm.datumNalezu.label"),
            "lokalizace": _("pas.forms.createSamostatnyNalezForm.lokalizace.label"),
            "okolnosti": _("pas.forms.createSamostatnyNalezForm.okolnosti.label"),
            "hloubka": _("pas.forms.createSamostatnyNalezForm.hloubka.label"),
            "obdobi": _("pas.forms.createSamostatnyNalezForm.obdobi.label"),
            "druh_nalezu": _("pas.forms.createSamostatnyNalezForm.druhNalezu.label"),
            "pocet": _("pas.forms.createSamostatnyNalezForm.pocet.label"),
            "presna_datace": _("pas.forms.createSamostatnyNalezForm.presnaDatace.label"),
            "specifikace": _("pas.forms.createSamostatnyNalezForm.specifikace.label"),
            "poznamka": _("pas.forms.createSamostatnyNalezForm.poznamka.label"),
        }
        help_texts = {
            "nalezce": _("pas.forms.createSamostatnyNalezForm.nalezce.tooltip"),
            "datum_nalezu": _("pas.forms.createSamostatnyNalezForm.datumNalezu.tooltip"),
            "lokalizace": _("pas.forms.createSamostatnyNalezForm.lokalizace.tooltip"),
            "okolnosti": _("pas.forms.createSamostatnyNalezForm.okolnosti.tooltip"),
            "hloubka": _("pas.forms.createSamostatnyNalezForm.hloubka.tooltip"),
            "obdobi": _("pas.forms.createSamostatnyNalezForm.obdobi.tooltip"),
            "druh_nalezu": _("pas.forms.createSamostatnyNalezForm.druhNalezu.tooltip"),
            "pocet": _("pas.forms.createSamostatnyNalezForm.pocet.tooltip"),
            "presna_datace": _("pas.forms.createSamostatnyNalezForm.presnaDatace.tooltip"),
            "specifikace": _("pas.forms.createSamostatnyNalezForm.specifikace.tooltip"),
            "poznamka": _("pas.forms.createSamostatnyNalezForm.poznamka.tooltip"),
        }

    def __init__(
        self, *args, readonly=False, user=None, required=None, required_next=None, project_ident=None, **kwargs
    ):
        projekt_disabed = kwargs.pop("projekt_disabled", False)
        super(CreateSamostatnyNalezForm, self).__init__(*args, **kwargs)
        self.fields["lokalizace"].widget.attrs["rows"] = 2
        self.fields["pocet"].widget.attrs["rows"] = 1
        self.fields["presna_datace"].widget.attrs["rows"] = 1
        self.fields["poznamka"].widget.attrs["rows"] = 1
        self.fields["projekt"] = ProjectModelChoiceField(
            queryset=Projekt.objects.filter(typ_projektu=TYP_PROJEKTU_PRUZKUM_ID)
            .filter(organizace__in=user.moje_spolupracujici_organizace())
            .filter(stav__in=user.moje_stavy_pruzkumnych_projektu()),
            widget=forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            help_text=_("pas.forms.createSamostatnyNalezForm.projekt.tooltip"),
            label=_("pas.forms.createSamostatnyNalezForm.projekt.label"),
            initial=Projekt.objects.filter(ident_cely=project_ident)[0] if project_ident else None,
        )
        self.fields["katastr"].widget.attrs["readonly"] = True
        self.fields["druh_nalezu"] = TwoLevelSelectField(
            label=_("pas.forms.createSamostatnyNalezForm.druhNalezu.label"),
            widget=forms.Select(
                choices=heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT),
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"},
            ),
            help_text=_("pas.forms.createSamostatnyNalezForm.druhNalezu.tooltip"),
        )
        self.fields["obdobi"] = TwoLevelSelectField(
            label=_("pas.forms.createSamostatnyNalezForm.obdobi.label"),
            widget=forms.Select(
                choices=heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT),
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"},
            ),
            help_text=_("pas.forms.createSamostatnyNalezForm.obdobi.tooltip"),
        )
        self.fields["druh_nalezu"].required = False
        self.fields["obdobi"].required = False
        if readonly:
            nalezce_div = Div(
                "nalezce",
                css_class="col-sm-4",
            )
        else:
            nalezce_div = Div(
                AppendedText(
                    "nalezce",
                    mark_safe(
                        '<button id="create-nalezce-osoba" class="btn btn-sm app-btn-in-form" type="button" name="button"><span class="material-icons">add</span></button>'
                    ),
                ),
                css_class="col-sm-4 input-osoba select2-input",
            )
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("projekt", css_class="col-sm-4"),
                nalezce_div,
                Div("datum_nalezu", css_class="col-sm-4"),
                Div("lokalizace", css_class="col-sm-8"),
                Div("katastr", css_class="col-sm-4"),
                Div("okolnosti", css_class="col-sm-6"),
                Div("hloubka", css_class="col-sm-6"),
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
                    if key == "nalezce":
                        self.fields[key].widget = forms.widgets.Select()
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""
                self.fields[key].required = False
            if required:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(self.fields[key].widget.attrs["class"]) + (
                        " required-next" if key in required_next else ""
                    )
                else:
                    self.fields[key].widget.attrs["class"] = "required-next" if key in required_next else ""
        if projekt_disabed:
            self.fields["projekt"].disabled = projekt_disabed
        if self.instance is not None:
            self.fields["katastr"].initial = self.instance.katastr


class CreateZadostForm(forms.Form):
    """
    Hlavní formulář pro vytvoření, editaci a zobrazení žádosti o spoluprácu.
    """

    email_uzivatele = forms.EmailField(
        label=_("pas.forms.createZadostForm.emailUzivatele.label"),
        widget=forms.EmailInput(attrs={"placeholder": _("pas.forms.createZadostForm.emailUzivatele.placeholder")}),
        required=True,
        validators=[validate_uzivatel_email],
        help_text=_("pas.forms.createZadostForm.emailUzivatele.tooltip"),
    )
    text = forms.CharField(
        widget=forms.Textarea,
        required=True,
        help_text=_("pas.forms.createZadostForm.text.tooltip"),
        label=_("pas.forms.createZadostForm.text.label"),
    )

    def __init__(self, *args, **kwargs):
        super(CreateZadostForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class PasFilterForm(BaseFilterForm):
    list_to_check = ["historie_datum_zmeny_od", "datum_nalezu"]
