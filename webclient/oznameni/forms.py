from core.validators import validate_phone_number
from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Reset, Submit
from django import forms
from django.utils.translation import gettext as _
from oznameni.models import Oznamovatel
from projekt.models import Projekt


class OznamovatelForm(forms.ModelForm):
    telefon = forms.CharField(validators=[validate_phone_number])
    email = forms.EmailField()

    class Meta:
        model = Oznamovatel
        fields = ("oznamovatel", "odpovedna_osoba", "telefon", "email", "adresa")
        widgets = {
            "oznamovatel": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "odpovedna_osoba": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "adresa": forms.Textarea(attrs={"rows": 2, "cols": 40}),
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
    class Meta:
        model = Projekt
        fields = ("planovane_zahajeni", "podnet", "lokalizace", "parcelni_cislo")
        widgets = {
            "podnet": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "lokalizace": forms.Textarea(attrs={"rows": 2, "cols": 40}),
            "parcelni_cislo": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }
        labels = {
            "planovane_zahajeni": _("Plánované zahájení prací"),
            "podnet": _("Podnět"),
            "lokalizace": _("Lokalizace"),
            "parcelni_cislo": _("Parcelní číslo"),
        }
        help_texts = {
            "planovane_zahajeni": _("Termín plánovaného zahájení realizace záměru."),
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

        self.helper.layout.append(Submit("save", _("Odeslat formulář")))
        self.helper.layout.append(Reset("reset", _("Smazat formulář")))
