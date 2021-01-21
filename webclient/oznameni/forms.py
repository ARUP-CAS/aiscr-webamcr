import datetime
import logging

from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from core.validators import validate_phone_number
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from django import forms
from django.utils.translation import gettext as _
from oznameni.models import Oznamovatel
from projekt.models import Projekt

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
                    HTML(_("Oznamovatel")),
                    css_class="card-header",
                ),
                Div(
                    "oznamovatel",
                    "odpovedna_osoba",
                    "adresa",
                    Div(
                        Div("telefon", css_class="col-sm-6"),
                        Div("email", css_class="col-sm-6"),
                        css_class="row",
                    ),
                    css_class="card-body",
                ),
                css_class="card",
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

    class Meta:
        model = Projekt
        fields = (
            "planovane_zahajeni",
            "podnet",
            "lokalizace",
            "parcelni_cislo",
            "oznaceni_stavby",
        )
        widgets = {
            "podnet": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "lokalizace": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "oznaceni_stavby": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }
        labels = {
            "podnet": _("Podnět"),
            "lokalizace": _("Lokalizace"),
            "parcelni_cislo": _("Parcelní číslo"),
            "oznaceni_stavby": _("Označení stavby"),
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
        }

    def __init__(self, *args, **kwargs):
        super(ProjektOznameniForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Charakteristika záměru")),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        HTML('  <label for="id_ku" class="">Katastální území</label>'),
                        Div(
                            HTML('<textarea name="ku" cols="40" rows="1" class="textarea form-control" id="katastr_name" readonly /></textarea>'),
                            HTML('<small id="hint_id_ku" class="form-text text-muted">Katastální území zadanné bodem </small>'),
                        ),
                    css_class="form-group"
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
                css_class="card",
            )
        )


class UploadFileForm(forms.Form):
    soubor = forms.FileField(
        required=False, widget=forms.ClearableFileInput(attrs={"multiple": True})
    )

    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Projektová a jiná dokumentace")),
                    css_class="card-header",
                ),
                Div(
                    "soubor",
                    css_class="card-body",
                ),
                css_class="card",
            )
        )


class FormWithCaptcha(forms.Form):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
