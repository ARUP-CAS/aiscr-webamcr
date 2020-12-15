import logging

from core.validators import validate_phone_number
from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
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
            Accordion(
                AccordionGroup(
                    _("Oznamovatel"),
                    "oznamovatel",
                    "odpovedna_osoba",
                    "adresa",
                    Div(
                        Div("telefon", css_class="col-sm-6"),
                        Div("email", css_class="col-sm-6"),
                        css_class="row",
                    ),
                )
            ),
        )
        self.helper.form_tag = False


class ProjektOznameniForm(forms.ModelForm):

    planovane_zahajeni = DateRangeField(
        label=_("Plánované zahájení prací"),
        widget=forms.TextInput(attrs={"rows": 1, "cols": 40}),
        help_text=_("Termín plánovaného zahájení realizace záměru."),
    )

    class Meta:
        model = Projekt
        fields = ("planovane_zahajeni", "podnet", "lokalizace", "parcelni_cislo")
        widgets = {
            "podnet": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "lokalizace": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }
        labels = {
            "podnet": _("Podnět"),
            "lokalizace": _("Lokalizace"),
            "parcelni_cislo": _("Parcelní číslo"),
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
        }

    def __init__(self, *args, **kwargs):
        super(ProjektOznameniForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Accordion(
                AccordionGroup(
                    _("Charakteristika záměru"),
                    "planovane_zahajeni",
                    "podnet",
                    "lokalizace",
                    "parcelni_cislo",
                )
            ),
        )


class UploadFileForm(forms.Form):
    soubory = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        help_text="Vyberte jeden nebo více souborů.",
        required=False,
    )
    souhlas = forms.BooleanField(
        label=_("Souhlasím s podmínkami o zpracování osobních údajů")
    )

    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Accordion(
                AccordionGroup(
                    _("Projektová a jiná dokumentace"),
                    "soubory",
                )
            ),
            Field("souhlas"),
        )

        self.helper.layout.append(Submit("save", _("Odeslat formulář")))
