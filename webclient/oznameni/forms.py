import datetime
import logging
import os

from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Invisible
from core.validators import validate_phone_number
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from dal import autocomplete
from django import forms
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from oznameni.models import Oznamovatel
from projekt.models import Projekt
from psycopg2._range import DateRange

from core.utils import get_cadastre_from_point

logger = logging.getLogger(__name__)


class DateRangeField(forms.DateField):
    """
    Třída pro správnu práci s date range.
    """
    def to_python(self, value):
        values = value.split("-")
        if len(values) == 1:
            from_date = to_date = super(DateRangeField, self).to_python(values[0].strip())
        else:
            from_date = super(DateRangeField, self).to_python(values[0].strip())
            to_date = super(DateRangeField, self).to_python(values[1].strip())
        # add one day to the to_date since DateRangePicker has both bounds included 12/30/2020 - 12/30/2020 must be
        # stored as 12/30/2020 - 12/31/2020, since postgres does not include upper bound to the range
        if from_date is None or to_date is None:
            raise ValidationError(self.error_messages["invalid"], code="invalid")
        try:
            to_date += datetime.timedelta(days=1)
        except:
            raise ValidationError(self.error_messages["invalid"], code="invalid")
        return DateRange(lower=from_date, upper=to_date)


class DateRangeWidget(forms.TextInput):
    """
    Třída pro správne zobrazení date range.
    """
    def format_value(self, value):
        if value == "" or value is None:
            return None
        if isinstance(value, DateRange):
            if value.lower and value.upper:
                format_str="%-d.%-m.%Y"
                if os.name == 'nt':
                    format_str="%#d.%#m.%Y"
                return (
                    value.lower.strftime(format_str)
                    + " - "
                    + (value.upper - datetime.timedelta(days=1)).strftime(
                        format_str
                    )  # Now I must substract one day
                )

        return str(value)


class OznamovatelForm(forms.ModelForm):
    """
    Hlavní formulář pro vytvoření oznámení.
    """
    telefon = forms.CharField(
        validators=[validate_phone_number],
        help_text=_("oznameni.forms.oznamovatelForm.telefon.tooltip"),
        label=_("oznameni.forms.oznamovatelForm.telefon.label"),
        widget=forms.TextInput(),
    )
    email = forms.EmailField(
        help_text=_("oznameni.forms.oznamovatelForm.email.tooltip"),
        label=_("oznameni.forms.oznamovatelForm.email.label"),
    )

    class Meta:
        model = Oznamovatel
        fields = ("oznamovatel", "odpovedna_osoba", "telefon", "email", "adresa", "poznamka")
        widgets = {
            "oznamovatel": forms.TextInput(),
            "odpovedna_osoba": forms.TextInput(),
            "adresa": forms.TextInput(),
        }
        labels = {
            "oznamovatel": _("oznameni.forms.oznamovatelForm.oznamovatel.label"),
            "odpovedna_osoba": _("oznameni.forms.oznamovatelForm.odpovednaOsoba.label"),
            "telefon": _("oznameni.forms.oznamovatelForm.telefon.label"),
            "email": _("oznameni.forms.oznamovatelForm.email.label"),
            "adresa": _("oznameni.forms.oznamovatelForm.adresa.label"),
            "poznamka": _("oznameni.forms.oznamovatelForm.poznamka.label"),
        }
        help_texts = {
            "oznamovatel": _("oznameni.forms.oznamovatelForm.oznamovatel.tooltip"),
            "odpovedna_osoba": _(
                "oznameni.forms.oznamovatelForm.odpovednaOsoba.tooltip"
            ),
            "telefon": _("oznameni.forms.oznamovatelForm.telefon.tooltip"),
            "email": _("oznameni.forms.oznamovatelForm.email.tooltip"),
            "adresa": _("oznameni.forms.oznamovatelForm.adresa.tooltip"),
            "poznamka": _("oznameni.forms.oznamovatelForm.poznamka.tooltip")
        }

    def __init__(self, *args, **kwargs):
        uzamknout_formular = kwargs.pop("uzamknout_formular", False)
        required = kwargs.pop("required", True)
        required_next = kwargs.pop("required_next", False)
        add_oznamovatel = kwargs.pop("add_oznamovatel", False)
        super(OznamovatelForm, self).__init__(*args, **kwargs)
        self.fields["telefon"].widget.input_type="tel"
        if uzamknout_formular:
            self.fields["oznamovatel"].widget.attrs["readonly"] = True
            self.fields["odpovedna_osoba"].widget.attrs["readonly"] = True
            self.fields["adresa"].widget.attrs["readonly"] = True
            self.fields["telefon"].widget.attrs["readonly"] = True
            self.fields["email"].widget.attrs["readonly"] = True
            self.fields["poznamka"].widget.attrs["readonly"] = True
        if required is False:
            for field in self.fields:
                self.fields[field].required = False
        if add_oznamovatel:
            header = Div()
        else:
            header = Div(
                Div(
                    HTML(_("oznameni.forms.oznamovatelForm.header.oznamovatel")),
                    css_class="app-fx app-left",
                ),
                css_class="card-header",
            )

        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            Div(
                header,
                Div(
                    Div(
                        Div("oznamovatel", css_class="col-sm-6"),
                        Div("odpovedna_osoba", css_class="col-sm-6"),
                        Div("adresa", css_class="col-sm-6"),
                        Div("telefon", css_class="col-sm-3"),
                        Div("email", css_class="col-sm-3"),
                        Div("poznamka", css_class="col-sm-12"),
                        css_class="row",
                    ),
                    css_class="card-body oznamovatel-form-card",
                ),
                css_class="card app-card-form",
            )
        )
        self.helper.form_tag = False
        if required_next:
            for key in self.fields:
                if "class" in self.fields[key].widget.attrs.keys():
                    self.fields[key].widget.attrs["class"] = str(
                        self.fields[key].widget.attrs["class"]
                    ) + " required-next"
                else:
                    self.fields[key].widget.attrs["class"] = "required-next"


class ProjektOznameniForm(forms.ModelForm):
    """
    Hlavní formulář pro editaci a doplňení oznamovatele do projektu.
    """
    planovane_zahajeni = DateRangeField(
        required=True,
        label=_("oznameni.forms.projektOznameniForm.planovaneZahajeni.label"),
        widget=DateRangeWidget(attrs={"rows": 1, "cols": 40, "autocomplete": "off"}),
        help_text=_("oznameni.forms.projektOznameniForm.planovaneZahajeni.tooltip"),
    )
    coordinate_x2 = forms.CharField(widget=forms.HiddenInput())
    coordinate_x1 = forms.CharField(widget=forms.HiddenInput())
    katastralni_uzemi = forms.CharField(
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
        label=_("oznameni.forms.projektOznameniForm.katastralniUzemi.label"),
        help_text=_("oznameni.forms.projektOznameniForm.katastralniUzemi.tooltip"),
    )
    ident_cely = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Projekt
        fields = (
            "ident_cely",
            "planovane_zahajeni",
            "podnet",
            "lokalizace",
            "parcelni_cislo",
            "oznaceni_stavby",
            "katastry",
        )
        widgets = {
            "podnet": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "lokalizace": forms.TextInput(),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "oznaceni_stavby": forms.TextInput(),
            "katastry": autocomplete.ModelSelect2Multiple(
                url="heslar:katastr-autocomplete"
            ),
            "ident_cely": forms.HiddenInput(),
        }
        labels = {
            "podnet": _("oznameni.forms.projektOznameniForm.podnet.label"),
            "lokalizace": _("oznameni.forms.projektOznameniForm.lokalizace.label"),
            "parcelni_cislo": _("oznameni.forms.projektOznameniForm.parcelniCislo.label"),
            "oznaceni_stavby": _("oznameni.forms.projektOznameniForm.oznaceniStavby.label"),
            "katastry": _("oznameni.forms.projektOznameniForm.katastry.label"),
        }
        help_texts = {
            "podnet": _(
                "oznameni.forms.projektOznameniForm.podnet.tooltip"
            ),
            "lokalizace": _(
                "oznameni.forms.projektOznameniForm.lokalizace.tooltip"
            ),
            "parcelni_cislo": _("oznameni.forms.projektOznameniForm.parcelniCislo.tooltip"),
            "oznaceni_stavby": _(
                "oznameni.forms.projektOznameniForm.oznaceniStavby.tooltip"
            ),
            "katastry": _("oznameni.forms.projektOznameniForm.katastry.tooltip"),
        }

    def __init__(self, *args, **kwargs):
        change = kwargs.pop("change", False)
        super(ProjektOznameniForm, self).__init__(*args, **kwargs)
        self.fields["ident_cely"].required = False
        self.fields["katastry"].required = False
        self.fields["podnet"].required = True
        self.fields["lokalizace"].required = True
        self.fields["parcelni_cislo"].required = True
        if change:
            self.fields["katastralni_uzemi"].initial = get_cadastre_from_point(
                self.instance.geom
            ).__str__()
            self.fields["coordinate_x1"].initial = self.instance.geom[0]
            self.fields["coordinate_x2"].initial = self.instance.geom[1]
            self.fields["ident_cely"].initial = self.instance.ident_cely

        self.helper = FormHelper(self)
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("oznameni.forms.projektOznameniForm.header.charakteristikaZameru")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div("katastralni_uzemi", css_class="col-sm-12"),
                        Div("katastry", css_class="col-sm-12"),
                        css_class="row",
                    ),
                    "planovane_zahajeni",
                    "podnet",
                    "lokalizace",
                    "parcelni_cislo",
                    "oznaceni_stavby",
                    "coordinate_x1",
                    "coordinate_x2",
                    "ident_cely",
                    css_class="card-body",
                ),
                css_class="card app-card-form",
            )
        )


class FormWithCaptcha(forms.Form):
    """
    Hlavní formulář pro captchu.
    """
    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible, label="")
