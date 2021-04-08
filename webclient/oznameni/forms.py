import datetime
import logging

from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Invisible
from core.validators import validate_phone_number
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from dal import autocomplete
from django import forms
from django.utils.translation import gettext as _
from oznameni.models import Oznamovatel
from projekt.models import Projekt
from psycopg2._range import DateRange

logger = logging.getLogger(__name__)


class DateRangeField(forms.DateField):
    def to_python(self, value):
        values = value.split(" - ")
        from_date = super(DateRangeField, self).to_python(values[0])
        to_date = super(DateRangeField, self).to_python(values[1])
        # add one day to the to_date since DateRangePicker has both bounds included 12/30/2020 - 12/30/2020 must be
        # stored as 12/30/2020 - 12/31/2020, since postgres does not include upper bound to the range
        to_date += datetime.timedelta(days=1)
        return from_date, to_date


class DateRangeWidget(forms.TextInput):
    def format_value(self, value):
        """
        Return a value as it should appear when rendered in a template.
        """
        if value == "" or value is None:
            return None
        if isinstance(value, DateRange):
            return (
                value.lower.strftime("%d.%m.%Y")
                + " - "
                + value.upper.strftime("%d.%m.%Y")
            )
        else:
            return str(value)


class OznamovatelForm(forms.ModelForm):
    telefon = forms.CharField(validators=[validate_phone_number])
    email = forms.EmailField()

    class Meta:
        model = Oznamovatel
        fields = ("oznamovatel", "odpovedna_osoba", "telefon", "email", "adresa")
        widgets = {
            "oznamovatel": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "odpovedna_osoba": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "adresa": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }
        labels = {
            "oznamovatel": _("Oznamovatel"),
            "odpovedna_osoba": _("Zástupce oznamovatele"),
            "telefon": _("Telefon"),
            "email": _("Email"),
            "adresa": _("Adresa oznamovatele"),
        }
        help_texts = {
            "oznamovatel": _("Jméno / název osoby realizující stavební či jiný záměr."),
            "odpovedna_osoba": _(
                "Jméno fyzické osoby, která zastupuje oznamovatele při jednání a podání oznámení."
            ),
        }

    def __init__(self, *args, **kwargs):
        super(OznamovatelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("Oznamovatel")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div("oznamovatel", css_class="col-sm-6"),
                        Div("odpovedna_osoba", css_class="col-sm-6"),
                        Div("adresa", css_class="col-sm-6"),
                        Div("telefon", css_class="col-sm-3"),
                        Div("email", css_class="col-sm-3"),
                       css_class="row", 
                    ),                 
                    css_class="card-body",
                ),
                css_class="card app-card-form",
            )    
        )
        self.helper.form_tag = False


class ProjektOznameniForm(forms.ModelForm):
    planovane_zahajeni = DateRangeField(
        required=True,
        label=_("Plánované zahájení prací"),
        widget=forms.TextInput(attrs={"rows": 1, "cols": 40}),
        help_text=_("Termín plánovaného zahájení realizace záměru."),
    )
    latitude = forms.CharField(widget=forms.HiddenInput())
    longitude = forms.CharField(widget=forms.HiddenInput())
    katastralni_uzemi = forms.CharField(
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
        label=_("Katastrální území"),
        help_text=_("Katastální území zadané bodem."),
    )

    class Meta:
        model = Projekt
        fields = (
            "planovane_zahajeni",
            "podnet",
            "lokalizace",
            "parcelni_cislo",
            "oznaceni_stavby",
            "katastry",
        )
        widgets = {
            "podnet": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "lokalizace": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "oznaceni_stavby": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "katastry": autocomplete.ModelSelect2Multiple(
                url="heslar:katastr-autocomplete"
            ),
        }
        labels = {
            "podnet": _("Podnět"),
            "lokalizace": _("Lokalizace"),
            "parcelni_cislo": _("Parcelní číslo"),
            "oznaceni_stavby": _("Označení stavby"),
            "katastry": _("Další katastry"),
        }
        help_texts = {
            "podnet": _(
                "Charakteristika stavebního nebo jiného záměru (např. rodinný dům, inženýrské sítě, výstavba "
                "komunikace, terénní úpravy, těžba suroviny apod.). "
            ),
            "lokalizace": _(
                "Bližší specifikace umístění zamýšlené stavby či jiného záměru (např. ulice a číslo popisné, "
                "název polní trati, místní název  apod.). "
            ),
            "parcelni_cislo": _("Čísla parcel dotčených záměrem."),
            "oznaceni_stavby": _("Lorem ipsum"),
            "katastry": _("Vyberte případné další katastry dotčené záměrem."),
        }

    def __init__(self, *args, **kwargs):
        super(ProjektOznameniForm, self).__init__(*args, **kwargs)
        self.fields["katastry"].required = False
        self.helper = FormHelper(self)
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(_("Charakteristika záměru")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div("katastralni_uzemi", css_class="col-sm-6"),
                        Div("katastry", css_class="col-sm-6"),
                        css_class="row",
                    ),
                    "planovane_zahajeni",
                    "podnet",
                    "lokalizace",
                    "parcelni_cislo",
                    "oznaceni_stavby",
                    "latitude",
                    "longitude",
                    css_class="card-body",
                ),
                css_class="card app-card-form",
            )
        )


class FormWithCaptcha(forms.Form):
    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible)
