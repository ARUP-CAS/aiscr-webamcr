import datetime
import re
from django.forms import ValidationError
import structlog
from arch_z.models import Akce, AkceVedouci, ArcheologickyZaznam
from core.forms import TwoLevelSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from dal import autocomplete
from django import forms
from django.utils.translation import gettext as _
from django.utils import formats
from heslar.hesla import HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT, SPECIFIKACE_DATA_PRESNE
from heslar.models import Heslar
from heslar.views import heslar_12
from projekt.models import Projekt

from . import validators

logger_s = structlog.get_logger(__name__)


class AkceVedouciFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = "inline_formset_vedouci.html"
        self.form_tag = False


def create_akce_vedouci_objekt_form(readonly=True):
    class CreateAkceVedouciObjektForm(forms.ModelForm):
        def clean(self):
            cleaned_data = super().clean()
            if (
                cleaned_data.get("vedouci", None) is None
                and cleaned_data.get("organizace", None) is not None
            ) or (
                cleaned_data.get("vedouci", None) is not None
                and cleaned_data.get("organizace", None) is None
            ):
                raise forms.ValidationError(
                    _("create_akce_vedouci_objekt_form.clean.error")
                )

        class Meta:
            model = AkceVedouci
            fields = ["vedouci", "organizace"]

            labels = {
                "vedouci": _("Vedoucí"),
                "organizace": _("Organizace"),
            }
            if readonly:
                widgets = {
                    "vedouci": forms.TextInput(attrs={"readonly": "readonly"}),
                    "organizace": forms.TextInput(attrs={"readonly": "readonly"}),
                }
            else:
                widgets = {
                    "vedouci": forms.Select(
                        attrs={
                            "class": "selectpicker",
                            "data-multiple-separator": "; ",
                            "data-live-search": "true",
                        }
                    ),
                    "organizace": forms.Select(
                        attrs={
                            "class": "selectpicker",
                            "data-multiple-separator": "; ",
                            "data-live-search": "true",
                        }
                    ),
                }

            help_texts = {
                "vedouci": _("arch_z.form.vedouci.tooltip"),
                "organizace": _("arch_z.form.organizace.tooltip"),
            }

        def __init__(self, *args, **kwargs):
            super(CreateAkceVedouciObjektForm, self).__init__(*args, **kwargs)
            self.readonly = readonly
            logger_s.debug(
                "CreateAkceVedouciObjektForm.init",
                readonly=readonly,
                initial=self.initial,
            )
            self.fields["vedouci"].required = False

    return CreateAkceVedouciObjektForm


class CreateArchZForm(forms.ModelForm):
    class Meta:
        model = ArcheologickyZaznam
        fields = (
            "hlavni_katastr",
            "pristupnost",
            "uzivatelske_oznaceni",
            "katastry",
        )

        labels = {
            "hlavni_katastr": _("Hlavní katastr"),
            "pristupnost": _("Přístupnost"),
            "uzivatelske_oznaceni": _("Uživatelské označení"),
            "katastry": _("Další katastry"),
        }
        widgets = {
            "hlavni_katastr": autocomplete.ModelSelect2(
                url="heslar:katastr-autocomplete"
            ),
            "katastry": autocomplete.ModelSelect2Multiple(
                url="heslar:katastr-autocomplete"
            ),
            "uzivatelske_oznaceni": forms.TextInput(),
            "pristupnost": forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
        }
        help_texts = {
            "hlavni_katastr": _("arch_z.form.hlavni_katastr.tooltip"),
            "pristupnost": _("arch_z.form.pristupnost.tooltip"),
            "uzivatelske_oznaceni": _("arch_z.form.uzivatelske_oznaceni.tooltip"),
            "katastry": _("arch_z.form.katastry.tooltip"),
        }

    def __init__(
        self,
        *args,
        required=[],
        required_next=None,
        readonly=False,
        **kwargs,
    ):
        projekt = kwargs.pop("projekt", None)
        projekt: Projekt
        super(CreateArchZForm, self).__init__(*args, **kwargs)
        if projekt:
            self.fields["hlavni_katastr"].initial = projekt.hlavni_katastr
            self.fields["uzivatelske_oznaceni"].initial = projekt.uzivatelske_oznaceni
            self.fields["katastry"].initial = projekt.katastry.all()
        else:
            try:
                self.fields["hlavni_katastr"].initial = self.instance.hlavni_katastr
                self.fields["katastry"].initial = self.instance.katastry.all()
            except Exception as e:
                logger_s.debug(e)
                pass
        try:
            self.fields["hlavni_katastr_show"] = forms.CharField(
                label=_("Hlavní katastr"),
                help_text=_("arch_z.form.hlavni_katastr.tooltip"),
                required=False,
                disabled=True,
            )
            self.fields["katastry_show"] = forms.CharField(
                label=_("Další katastry"),
                help_text=_("arch_z.form.katastry.tooltip"),
                required=False,
                disabled=True,
            )
            self.fields["hlavni_katastr_show"].initial = self.fields[
                "hlavni_katastr"
            ].initial
            self.fields["hlavni_katastr_show"].widget.attrs["id"] = "main_cadastre_id"
            self.fields["katastry_show"].widget.attrs["id"] = "other_cadastre_id"
            if self.fields["katastry"].initial is not None:
                value = [str(i) for i in self.fields["katastry"].initial.all()]
                display = ", ".join(value)
                self.fields["katastry_show"].initial = display
                self.fields["katastry_show"].disabled = True
                self.fields["hlavni_katastr_show"].disabled = True
            else:
                pass
        except Exception as e:
            logger_s.debug(e)

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
            if self.fields[key].disabled == True:
                if isinstance(self.fields[key].widget, forms.widgets.Select):
                    self.fields[key].widget.template_name = "core/select_to_text.html"
                self.fields[key].help_text = ""
            if required or required_next:
                self.fields[key].required = True if key in required else False
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(
                        self.fields[key].widget.attrs["class"]
                    ) + (" required-next" if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"] = (
                        "required-next" if key in required_next else ""
                    )


class CustomDateInput(forms.DateField):
    year_only_month = None
    year_only_day = None

    @classmethod
    def year_only(cls, value):
        return re.fullmatch(r"\d{4}", value)

    def get_date_based_on_year(self, year):
        return datetime.date(year, self.year_only_month, self.year_only_day)

    def to_python(self, value):
        if value:
            if isinstance(value, str) and CustomDateInput.year_only(value):
                return self.get_date_based_on_year(int(value))
            logger_s.info("arch_z.forms.CustomDateInput.to_python",
                          format=formats.get_format_lazy('DATE_INPUT_FORMATS'))
            return super().to_python(value)  # return self.strptime(value, "%d.%m.%Y")
        return super().to_python(value)


class StartDateInput(CustomDateInput):
    year_only_month = 1
    year_only_day = 1


class EndDateInput(CustomDateInput):
    year_only_month = 12
    year_only_day = 31


class CreateAkceForm(forms.ModelForm):
    datum_zahajeni = StartDateInput(
        help_text=_("arch_z.form.datum_zahajeni.tooltip"),
    )
    datum_ukonceni = EndDateInput(
        help_text=_("arch_z.form.datum_ukonceni.tooltip"),
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("datum_ukonceni") is not None
            and cleaned_data.get("datum_zahajeni") is None
        ):
            raise forms.ValidationError(
                _("Je-li vyplněno datum ukončení, musí být vyplněno i datum zahájení")
            )
        elif (
            cleaned_data.get("datum_ukonceni") is not None
            and cleaned_data.get("datum_zahajeni") is not None
        ):
            if cleaned_data.get("datum_zahajeni") > cleaned_data.get("datum_ukonceni"):
                raise forms.ValidationError(
                    _("Datum zahájení nemůže být po datu ukončení")
                )
        return self.cleaned_data

    class Meta:
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
            "hlavni_vedouci": _("Hlavní vedoucí"),
            "datum_zahajeni": _("Datum zahájení"),
            "datum_ukonceni": _("Datum ukončení"),
            "lokalizace_okolnosti": _("Lokalizace/okolnosti"),
            "ulozeni_nalezu": _("Uložení nálezů"),
            "souhrn_upresneni": _("Poznámka"),
            "je_nz": _("Odeslat ZAA jako NZ"),
            "specifikace_data": _("Specifikace data"),
            "ulozeni_dokumentace": _("Uložení dokumentace"),
            "odlozena_nz": _("arch_z.form.odlozenaNZ.label"),
        }

        widgets = {
            "hlavni_vedouci": forms.Select(
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                }
            ),
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
                choices=[("False", _("Ne")), ("True", _("Ano"))],
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
                choices=[("False", _("Ne")), ("True", _("Ano"))],
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
        }

        help_texts = {
            "hlavni_vedouci": _("arch_z.form.hlavni_vedouci.tooltip"),
            "organizace": _("arch_z.form.organizace.tooltip"),
            "lokalizace_okolnosti": _("arch_z.form.lokalizace_okolnosti.tooltip"),
            "ulozeni_nalezu": _("arch_z.form.ulozeni_nalezu.tooltip"),
            "souhrn_upresneni": _("arch_z.form.souhrn_upresneni.tooltip"),
            "je_nz": _("arch_z.form.je_nz.tooltip"),
            "specifikace_data": _("arch_z.form.specifikace_data.tooltip"),
            "ulozeni_dokumentace": _("arch_z.form.ulozeni_dokumentace.tooltip"),
            "odlozena_nz": _("arch_z.form.odlozenaNZ.tooltip"),
        }

    def __init__(self, *args, required=None, required_next=None, **kwargs):
        uzamknout_specifikace = kwargs.pop("uzamknout_specifikace", False)
        projekt = kwargs.pop("projekt", None)
        projekt: Projekt
        super(CreateAkceForm, self).__init__(*args, **kwargs)
        self.fields["specifikace_data"].choices = list(
            self.fields["specifikace_data"].choices
        )[1:]
        choices = heslar_12(HESLAR_AKCE_TYP, HESLAR_AKCE_TYP_KAT)
        self.fields["hlavni_typ"] = TwoLevelSelectField(
            label=_("Hlavní typ"),
            widget=forms.Select(
                choices=choices,
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
            help_text=_("arch_z.form.hlavni_typ.tooltip"),
        )
        self.fields["vedlejsi_typ"] = TwoLevelSelectField(
            label=_("Vedlejší typ"),
            widget=forms.Select(
                choices=choices,
                attrs={
                    "class": "selectpicker",
                    "data-multiple-separator": "; ",
                    "data-live-search": "true",
                },
            ),
            help_text=_("arch_z.form.vedlejsi_typ.tooltip"),
        )
        if projekt:
            self.fields["hlavni_vedouci"].initial = projekt.vedouci_projektu
            self.fields["organizace"].initial = projekt.organizace
            self.fields["datum_zahajeni"].initial = projekt.datum_zahajeni
            self.fields["datum_ukonceni"].initial = projekt.datum_ukonceni
            self.fields[
                "lokalizace_okolnosti"
            ].initial = f"{projekt.lokalizace}. Parc.č.: {projekt.parcelni_cislo}"
        self.helper = FormHelper(self)
        if uzamknout_specifikace:
            self.fields["specifikace_data"].disabled = True
            self.fields["specifikace_data"].initial = Heslar.objects.filter(
                heslo="přesně"
            ).first()

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div("hlavni_vedouci", css_class="col-sm-10"),
                        Div(
                            HTML(
                                '<a href="{% url "heslar:create_osoba" %}" target="_blank"><input type="button" value="+" class="btn btn-secondary" /></a>'
                            ),
                            css_class="col-sm-2",
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
                    self.fields[key].widget.attrs["class"] = str(
                        self.fields[key].widget.attrs["class"]
                    ) + (" required-next" if key in required_next else "")
                else:
                    self.fields[key].widget.attrs["class"] = (
                        "required-next" if key in required_next else ""
                    )
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""
                if self.fields[key].disabled == True:
                    self.fields[key].widget.template_name = "core/select_to_text.html"
            if self.fields[key].disabled is True:
                self.fields[key].help_text = ""

    def clean_odlozena_nz(self):
        je_nz = self.cleaned_data["je_nz"]
        odlozena_nz = self.cleaned_data["odlozena_nz"]
        if odlozena_nz and je_nz:
            raise ValidationError(_("arch_z.form.odlozenaNz.error"))
        return odlozena_nz

    def clean_datum_zahajeni(self):
        if (
            self.cleaned_data["specifikace_data"]
            == Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
            and self.cleaned_data["datum_zahajeni"] is not None
        ):
            validators.datum_max_1_mesic_v_budoucnosti(
                self.cleaned_data["datum_zahajeni"]
            )
        return self.cleaned_data["datum_zahajeni"]

    def clean_datum_ukonceni(self):
        if (
            self.cleaned_data["specifikace_data"]
            == Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
            and self.cleaned_data["datum_ukonceni"] is not None
        ):
            validators.datum_max_1_mesic_v_budoucnosti(
                self.cleaned_data["datum_ukonceni"]
            )
        return self.cleaned_data["datum_ukonceni"]
