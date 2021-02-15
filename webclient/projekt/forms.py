from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Div, Layout, Submit
from django import forms
from django.utils.translation import gettext as _
from projekt.models import Projekt


class VratitProjektForm(forms.Form):
    reason = forms.CharField(label=_("Důvod vrácení"), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Vrácení projektu")),
                    css_class="card-header",
                ),
                Div(
                    "reason",
                    css_class="card-body",
                ),
                Div(
                    FormActions(
                        Submit("save", "Vrátit"),
                        Button("cancel", "Zrušit"),
                    )
                ),
                css_class="card",
            )
        )


class PrihlaseniProjektForm(forms.ModelForm):
    class Meta:
        model = Projekt
        fields = (
            "vedouci_projektu",
            "kulturni_pamatka",
            "kulturni_pamatka_cislo",
            "kulturni_pamatka_popis",
        )
        widgets = {
            "kulturni_pamatka_popis": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "kulturni_pamatka_cislo": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }
        labels = {
            "vedouci_projektu": _("Vedoucí projektu"),
            "kulturni_pamatka": _("Kulturní památka"),
            "kulturni_pamatka_cislo": _("Popis"),
            "kulturni_pamatka_popis": _("Číslo"),
        }
        help_texts = {
            "vedouci_projektu": _("Lorem ipsum."),
            "kulturni_pamatka": _("Lorem ipsum."),
            "kulturni_pamatka_cislo": _("Lorem ipsum."),
            "kulturni_pamatka_popis": _("Lorem ipsum."),
        }

    def __init__(self, *args, **kwargs):
        super(PrihlaseniProjektForm, self).__init__(*args, **kwargs)
        self.fields["vedouci_projektu"].required = True
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Přihlášení projektu")),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        "vedouci_projektu",
                        "kulturni_pamatka",
                        "kulturni_pamatka_cislo",
                        "kulturni_pamatka_popis",
                        css_class="card-body",
                    )
                ),
                css_class="card",
            )
        )
        self.helper.form_tag = False
