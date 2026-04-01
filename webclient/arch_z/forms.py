import datetime
import logging
import re

from arch_z.models import Akce, AkceVedouci, ArcheologickyZaznam
from core.forms import BaseFilterForm, OptimisticLockingMixin, TwoLevelSelectField
from core.validators import validate_date_min_1600
from core.widgets import AutocompleteModelSelect2, AutocompleteModelSelect2Multiple
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from django import forms
from django.forms import ValidationError
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from heslar.hesla import HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT
from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID, SPECIFIKACE_DATA_PRESNE, TYP_DJ_KATASTR
from heslar.models import Heslar
from heslar.views import heslar_12
from projekt.models import Projekt

from . import validators

logger = logging.getLogger(__name__)


class AkceVedouciFormSetHelper(FormHelper):
    """Form helper pro správné vykreslení formuláře vedoucích."""

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.template = "inline_formset_vedouci.html"
        self.form_tag = False


def create_akce_vedouci_objekt_form(readonly=True):
    """
    Funkce která vrací formulář VB pro formset.

    :param readonly: Pokud ``True``, pole formuláře jsou pouze pro čtení.
    :return: Vnitřní ``ModelForm`` pro evidenci vedoucího akce.
    """

    class CreateAkceVedouciObjektForm(OptimisticLockingMixin, forms.ModelForm):
        """Implementuje komponentu ``CreateAkceVedouciObjektForm`` v rámci aplikace."""

        def clean(self):
            """Ověří, že vedoucí a organizace jsou buď oba vyplněni, nebo oba prázdní.

            :raises forms.ValidationError: Vyvolá se při splnění podmínky ``cleaned_data.get('vedouci', None) is None and cleaned_data.get('organizace', None) is not None or (cleaned_data.get('vedouci', None) is not ``.
            """
            cleaned_data = super().clean()
            if (cleaned_data.get("vedouci", None) is None and cleaned_data.get("organizace", None) is not None) or (
                cleaned_data.get("vedouci", None) is not None and cleaned_data.get("organizace", None) is None
            ):
                raise forms.ValidationError(_("arch_z.forms.CreateAkceVedouciObjektForm.clean.error"))

        class Meta:
            """Implementuje komponentu ``Meta`` v rámci aplikace."""

            model = AkceVedouci
            fields = ["vedouci", "organizace"]

            labels = {
                "vedouci": _("arch_z.forms.CreateAkceVedouciObjektForm.vedouci.label"),
                "organizace": _("arch_z.forms.CreateAkceVedouciObjektForm.organizace.label"),
            }
            if readonly:
                widgets = {
                    "vedouci": forms.TextInput(attrs={"readonly": "readonly"}),
                    "organizace": forms.TextInput(attrs={"readonly": "readonly"}),
                }
            else:
                widgets = {
                    "vedouci": AutocompleteModelSelect2(url="heslar:osoba-autocomplete"),
                    "organizace": forms.Select(
                        attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
                    ),
                }

            help_texts = {
                "vedouci": _("arch_z.forms.CreateAkceVedouciObjektForm.vedouci.tooltip"),
                "organizace": _("arch_z.forms.CreateAkceVedouciObjektForm.organizace.tooltip"),
            }

        def __init__(self, *args, **kwargs):
            """
            Inicializuje instanci třídy.

            :param args: Parametr ``args`` se předává do volání ``__init__()``.
            :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
            """
            super(CreateAkceVedouciObjektForm, self).__init__(*args, **kwargs)
            self.readonly = readonly
            logger.debug("CreateAkceVedouciObjektForm.init", extra={"option": readonly, "initial": self.initial})
            if readonly:
                self.fields["organizace"].required = False
                self.fields["vedouci"].required = False

    return CreateAkceVedouciObjektForm


class CreateArchZForm(OptimisticLockingMixin, forms.ModelForm):
    """Hlavní formulář pro vytvoření, editaci a zobrazení Archeologického záznamu."""

    optimistic_lock_field_name = "optimistic_lock_data_az"

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = ArcheologickyZaznam
        fields = (
            "hlavni_katastr",
            "pristupnost",
            "uzivatelske_oznaceni",
            "katastry",
        )

        labels = {
            "hlavni_katastr": _("arch_z.forms.CreateArchZForm.hlavni_katastr.label"),
            "pristupnost": _("arch_z.forms.CreateArchZForm.pristupnost.label"),
            "uzivatelske_oznaceni": _("arch_z.forms.CreateArchZForm.uzivatelske_oznaceni.label"),
            "katastry": _("arch_z.forms.CreateArchZForm.katastry.label"),
        }
        widgets = {
            "hlavni_katastr": AutocompleteModelSelect2(url="heslar:katastr-autocomplete"),
            "katastry": AutocompleteModelSelect2Multiple(url="heslar:katastr-autocomplete"),
            "uzivatelske_oznaceni": forms.TextInput(),
            "pristupnost": forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-live-search": "true",
                },
            ),
        }
        help_texts = {
            "hlavni_katastr": _("arch_z.forms.CreateArchZForm.hlavni_katastr.tooltip"),
            "pristupnost": _("arch_z.forms.CreateArchZForm.pristupnost.tooltip"),
            "uzivatelske_oznaceni": _("arch_z.forms.CreateArchZForm.uzivatelske_oznaceni.tooltip"),
            "katastry": _("arch_z.forms.CreateArchZForm.katastry.tooltip"),
        }

    def __init__(
        self,
        *args,
        required=[],
        required_next=None,
        readonly=False,
        **kwargs,
    ):
        """Prepis init metody pro vyplnení init hodnot, nastanvení readonly.

        :param required: Parametr ``required`` ovlivňuje větvení podmínek.
        :param required_next: Parametr ``required_next`` ovlivňuje větvení podmínek.
        :param readonly: Parametr ``readonly`` ovlivňuje větvení podmínek.
        :param args: Parametr ``args`` předává se do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` předává se do volání ``__init__()``, pracuje se s atributy ``pop``.
        """
        projekt = kwargs.pop("projekt", None)
        projekt: Projekt
        super(CreateArchZForm, self).__init__(*args, **kwargs)
        self.fields["pristupnost"].initial = [PRISTUPNOST_ANONYM_ID]
        self.fields["pristupnost"].empty_label = None
        if projekt:
            self.fields["hlavni_katastr"].initial = projekt.hlavni_katastr
            self.fields["uzivatelske_oznaceni"].initial = projekt.uzivatelske_oznaceni
            self.fields["katastry"].initial = projekt.katastry.all()
        else:
            try:
                self.fields["hlavni_katastr"].initial = self.instance.hlavni_katastr
                self.fields["katastry"].initial = self.instance.katastry.all()
            except Exception as e:
                logger.debug(e)
                pass
        try:
            self.fields["hlavni_katastr_show"] = forms.CharField(
                label=_("arch_z.forms.CreateArchZForm.hlavni_katastr.label"),
                help_text=_("arch_z.forms.CreateArchZForm.hlavni_katastr.tooltip"),
                required=False,
                disabled=True,
            )
            self.fields["katastry_show"] = forms.CharField(
                label=_("arch_z.forms.CreateArchZForm.katastry.label"),
                help_text=_("arch_z.forms.CreateArchZForm.katastry.tooltip"),
                required=False,
                disabled=True,
            )
            self.fields["hlavni_katastr_show"].initial = self.fields["hlavni_katastr"].initial
            self.fields["hlavni_katastr_show"].widget.attrs["id"] = "main_cadastre_id"
            self.fields["katastry_show"].widget.attrs["id"] = "other_cadastre_id"
            if self.fields["katastry"].initial is not None:
                value = [str(i) for i in self.fields["katastry"].initial.all()]
                display = "; ".join(value)
                self.fields["katastry_show"].initial = display
                self.fields["katastry_show"].disabled = True
                self.fields["hlavni_katastr_show"].disabled = True
            else:
                pass
            if (
                self.instance.dokumentacni_jednotky_akce.count() == 1
                and self.instance.dokumentacni_jednotky_akce.first().typ.id == TYP_DJ_KATASTR
                and readonly is False
            ):
                self.fields.pop("katastry_show")
            else:
                self.fields.pop("katastry")
        except Exception as e:
            logger.debug(e)

        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            Div(
                Div(
                    "hlavni_katastr",
                    css_class="col-sm-4",
                ),
                Div("pristupnost", css_class="col-sm-4"),
                Div("katastry", css_class="col-sm-4"),
                Div("uzivatelske_oznaceni", css_class="col-sm-12"),
                css_class="row",
            ),
        )

        self.helper.form_tag = False
        for key in self.fields.keys():
            if readonly:
                self.fields[key].disabled = readonly
            if self.fields[key].disabled is True:
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"
                self.fields[key].help_text = ""
            if required or required_next:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(self.fields[key].widget.attrs["class"]) + (
                        " required-next" if key in required_next else ""
                    )
                else:
                    self.fields[key].widget.attrs["class"] = "required-next" if key in required_next else ""


class CustomDateInput(forms.DateField):
    """Custom class pro zadávaní počátečního a konečního datumu v roce zadaním jen roku."""

    year_only_month = None
    year_only_day = None

    @classmethod
    def year_only(cls, value):
        """
        Ověří, zda zadaná hodnota odpovídá formátu čtyřciferného roku.

        :param value: Parametr ``value`` předává se do volání ``fullmatch()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``fullmatch()``.
        """
        return re.fullmatch(r"\d{4}", value)

    def get_date_based_on_year(self, year):
        """
        Vrací date based on year.

        :param year: Časový údaj ``year`` použitý při filtrování nebo výpočtu.

            :return: Vrací výsledek volání ``date()``.
        """
        return datetime.date(year, self.year_only_month, self.year_only_day)

    def to_python(self, value):
        """
        Prepis kvůli jinému objektu CustomDateInput.

        :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``year_only()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get_date_based_on_year()``, výsledek volání ``to_python()``.
        """
        if value:
            if isinstance(value, str) and CustomDateInput.year_only(value):
                return self.get_date_based_on_year(int(value))
            logger.info(
                "arch_z.forms.CustomDateInput.to_python",
                extra={"format": formats.get_format_lazy("DATE_INPUT_FORMATS")},
            )

            return super().to_python(value)  # Alternativou je vlastní `strptime` formátu `%d.%m.%Y`.
        return super().to_python(value)


class StartDateInput(CustomDateInput):
    """Class pro input prvního dne v roce."""

    year_only_month = 1
    year_only_day = 1


class EndDateInput(CustomDateInput):
    """Class pro input posledního dne v roce."""

    year_only_month = 12
    year_only_day = 31


class CreateAkceForm(OptimisticLockingMixin, forms.ModelForm):
    """Hlavní formulář pro vytvoření, editaci a zobrazení akce."""

    optimistic_lock_field_name = "optimistic_lock_data_akce"

    datum_zahajeni = StartDateInput(
        help_text=_("arch_z.forms.CreateAkceForm.datum_zahajeni.tooltip"),
        label=_("arch_z.forms.CreateAkceForm.datum_zahajeni.label"),
        validators=[
            validate_date_min_1600,
        ],
    )
    datum_ukonceni = EndDateInput(
        help_text=_("arch_z.forms.CreateAkceForm.datum_ukonceni.tooltip"),
        label=_("arch_z.forms.CreateAkceForm.datum_ukonceni.label"),
        validators=[
            validate_date_min_1600,
        ],
        required=False,
    )

    def clean(self):
        """Přepis clean metody s custom oveřením datumu ukončení a zahájení.

        :return: Vrací atribut objektu.
        :raises forms.ValidationError: Vyvolá se při splnění podmínky ``cleaned_data.get('datum_ukonceni') is not None and cleaned_data.get('datum_zahajeni') is None``; nebo při splnění podmínky ``cleaned_data.get('datum_zahajeni') > cleaned_data.get('datum_ukonceni')``.
        """
        cleaned_data = super().clean()
        if cleaned_data.get("datum_ukonceni") is not None and cleaned_data.get("datum_zahajeni") is None:
            raise forms.ValidationError(_("arch_z.forms.CreateAkceForm.validation.datum_zahajeni.error"))
        elif cleaned_data.get("datum_ukonceni") is not None and cleaned_data.get("datum_zahajeni") is not None:
            if cleaned_data.get("datum_zahajeni") > cleaned_data.get("datum_ukonceni"):
                raise forms.ValidationError(_("arch_z.forms.CreateAkceForm.validation.datum_ukonceni.error"))
        return self.cleaned_data

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = Akce
        fields = (
            "hlavni_vedouci",
            "organizace",
            "specifikace_data",
            "datum_zahajeni",
            "datum_ukonceni",
            "lokalizace_okolnosti",
            "ulozeni_nalezu",
            "souhrn_upresneni",
            "je_nz",
            "hlavni_typ",
            "vedlejsi_typ",
            "ulozeni_dokumentace",
            "odlozena_nz",
        )

        labels = {
            "hlavni_vedouci": _("arch_z.forms.CreateAkceForm.hlavni_vedouci.label"),
            "organizace": _("arch_z.forms.CreateAkceForm.organizace.label"),
            "datum_zahajeni": _("arch_z.forms.CreateAkceForm.datum_zahajeni.label"),
            "datum_ukonceni": _("arch_z.forms.CreateAkceForm.datum_ukonceni.label"),
            "lokalizace_okolnosti": _("arch_z.forms.CreateAkceForm.lokalizace_okolnosti.label"),
            "ulozeni_nalezu": _("arch_z.forms.CreateAkceForm.ulozeni_nalezu.label"),
            "souhrn_upresneni": _("arch_z.forms.CreateAkceForm.souhrn_upresneni.label"),
            "je_nz": _("arch_z.forms.CreateAkceForm.je_nz.label"),
            "specifikace_data": _("arch_z.forms.CreateAkceForm.specifikace_data.label"),
            "ulozeni_dokumentace": _("arch_z.forms.CreateAkceForm.ulozeni_dokumentace.label"),
            "odlozena_nz": _("arch_z.forms.CreateAkceForm.odlozena_nz.label"),
            "hlavni_typ": _("arch_z.forms.CreateAkceForm.hlavni_typ.label"),
            "vedlejsi_typ": _("arch_z.forms.CreateAkceForm.vedlejsi_typ.label"),
        }

        widgets = {
            "hlavni_vedouci": AutocompleteModelSelect2(url="heslar:osoba-autocomplete"),
            "organizace": forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
            "lokalizace_okolnosti": forms.TextInput(),
            "ulozeni_nalezu": forms.TextInput(),
            "souhrn_upresneni": forms.Textarea(attrs={"rows": 4, "cols": 40}),
            "ulozeni_dokumentace": forms.TextInput(),
            "je_nz": forms.Select(
                choices=[
                    ("False", _("arch_z.forms.CreateAkceForm.je_nz.choice.ne.label")),
                    ("True", _("arch_z.forms.CreateAkceForm.je_nz.choice.ano.label")),
                ],
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
            "specifikace_data": forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
            "odlozena_nz": forms.Select(
                choices=[
                    ("False", _("arch_z.forms.CreateAkceForm.odlozena_nz.choice.ne.label")),
                    ("True", _("arch_z.forms.CreateAkceForm.odlozena_nz.choice.ano.label")),
                ],
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
        }

        help_texts = {
            "hlavni_vedouci": _("arch_z.forms.CreateAkceForm.hlavni_vedouci.tooltip"),
            "organizace": _("arch_z.forms.CreateAkceForm.organizace.tooltip"),
            "lokalizace_okolnosti": _("arch_z.forms.CreateAkceForm.lokalizace_okolnosti.tooltip"),
            "ulozeni_nalezu": _("arch_z.forms.CreateAkceForm.ulozeni_nalezu.tooltip"),
            "souhrn_upresneni": _("arch_z.forms.CreateAkceForm.souhrn_upresneni.tooltip"),
            "je_nz": _("arch_z.forms.CreateAkceForm.je_nz.tooltip"),
            "specifikace_data": _("arch_z.forms.CreateAkceForm.specifikace_data.tooltip"),
            "ulozeni_dokumentace": _("arch_z.forms.CreateAkceForm.ulozeni_dokumentace.tooltip"),
            "odlozena_nz": _("arch_z.forms.CreateAkceForm.odlozena_nz.tooltip"),
        }

    def __init__(self, *args, required=None, required_next=None, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param required: Parametr ``required`` ovlivňuje větvení podmínek.
        :param required_next: Parametr ``required_next`` ovlivňuje větvení podmínek.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.
        """
        uzamknout_specifikace = kwargs.pop("uzamknout_specifikace", False)
        projekt = kwargs.pop("projekt", None)
        projekt: Projekt
        super(CreateAkceForm, self).__init__(*args, **kwargs)
        self.fields["specifikace_data"].choices = list(self.fields["specifikace_data"].choices)[1:]
        """
        Prepis init metody pro vyplnení init hodnot, nastanvení readonly.
        """
        choices = heslar_12(HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT)
        self.fields["hlavni_typ"] = TwoLevelSelectField(
            label=_("arch_z.forms.CreateAkceForm.hlavni_typ.label"),
            widget=forms.Select(
                choices=choices,
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
            help_text=_("arch_z.forms.CreateAkceForm.hlavni_typ.tooltip"),
        )
        self.fields["vedlejsi_typ"] = TwoLevelSelectField(
            label=_("arch_z.forms.CreateAkceForm.vedlejsi_typ.label"),
            widget=forms.Select(
                choices=choices,
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
            help_text=_("arch_z.forms.CreateAkceForm.vedlejsi_typ.tooltip"),
        )
        if projekt:
            self.fields["hlavni_vedouci"].initial = projekt.vedouci_projektu
            self.fields["organizace"].initial = projekt.organizace
            self.fields["datum_zahajeni"].initial = projekt.datum_zahajeni
            self.fields["datum_ukonceni"].initial = projekt.datum_ukonceni
            self.fields["lokalizace_okolnosti"].initial = (
                f"{projekt.lokalizace}. Parcelní číslo: {projekt.parcelni_cislo}"
            )
        self.helper = FormHelper(self)
        if uzamknout_specifikace:
            self.fields["specifikace_data"].disabled = True
            self.fields["specifikace_data"].initial = Heslar.objects.filter(heslo="přesně").first()

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div("hlavni_vedouci", css_class="col-sm-10"),
                        Div(
                            HTML(
                                '<a href="{% url "heslar:create_osoba" %}" target="_blank"><input type="button" value="+" class="btn btn-secondary" /></a>'
                            ),
                            css_class="col-sm-2 input-osoba select2-input form-group",
                            style="display: flex; align-items: center;",
                        ),
                        css_class="row",
                    ),
                    css_class="col-sm-4",
                ),
                Div("organizace", css_class="col-sm-4"),
                Div("datum_zahajeni", css_class="col-sm-4"),
                Div("datum_ukonceni", css_class="col-sm-4"),
                Div("lokalizace_okolnosti", css_class="col-sm-4"),
                Div("ulozeni_nalezu", css_class="col-sm-4"),
                Div("souhrn_upresneni", css_class="col-sm-4"),
                Div("hlavni_typ", css_class="col-sm-4"),
                Div("vedlejsi_typ", css_class="col-sm-4"),
                Div("je_nz", css_class="col-sm-4"),
                Div("specifikace_data", css_class="col-sm-4"),
                Div("ulozeni_dokumentace", css_class="col-sm-4"),
                css_class="row",
            ),
        )

        self.helper.form_tag = False
        for key in self.fields.keys():
            if required or required_next:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(self.fields[key].widget.attrs["class"]) + (
                        " required-next" if key in required_next else ""
                    )
                else:
                    self.fields[key].widget.attrs["class"] = "required-next" if key in required_next else ""
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled is True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""

    def clean_odlozena_nz(self):
        """Custom clean metoda pro ověření že je_nz a odlozena_nz nejsou oba True.

        :return: Vrací proměnná ``odlozena_nz``.
        :raises ValidationError: Vyvolá se při splnění podmínky ``odlozena_nz and je_nz``.
        """
        je_nz = self.cleaned_data["je_nz"]
        odlozena_nz = self.cleaned_data["odlozena_nz"]
        if odlozena_nz and je_nz:
            raise ValidationError(_("arch_z.forms.CreateAkceForm.clean.odlozenaNz.error"))
        return odlozena_nz

    def clean_datum_zahajeni(self):
        """
        Custom clean metoda pro ověření:

        ak je specifikace_data=přesně tak datum_zahájení nesmí být prázdne

        datum zahájení není dále něž mesíc v budoucnu

            :return: Vrací vybranou hodnotu z kolekce.
        """
        if (
            self.cleaned_data["specifikace_data"] == Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
            and self.cleaned_data["datum_zahajeni"] is not None
        ):
            validators.datum_max_1_mesic_v_budoucnosti(self.cleaned_data["datum_zahajeni"])
        return self.cleaned_data["datum_zahajeni"]

    def clean_datum_ukonceni(self):
        """
        Custom clean metoda pro ověření:

        ak je specifikace_data=přesně tak datum_ukončení nesmí být prázdne

        datum ukončení není dále něž mesíc v budoucnu

            :return: Vrací vybranou hodnotu z kolekce.
        """
        if (
            self.cleaned_data["specifikace_data"] == Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
            and self.cleaned_data["datum_ukonceni"] is not None
        ):
            validators.datum_max_1_mesic_v_budoucnosti(self.cleaned_data["datum_ukonceni"])
        return self.cleaned_data["datum_ukonceni"]


class ArchzFilterForm(BaseFilterForm):
    """Implementuje komponentu ``ArchzFilterForm`` v rámci aplikace."""

    list_to_check = ["historie_datum_zmeny_od", "datum_ukonceni", "datum_zahajeni"]
