from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import Osoba, User


class AuthUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ("email", "organizace", "jazyk")


class AuthUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "organizace", "jazyk")


class OsobaForm(forms.ModelForm):
    class Meta:
        model = Osoba
        fields = (
            "jmeno",
            "prijmeni",
            "rok_narozeni",
            "rok_umrti",
            "rodne_prijmeni",
        )
        widgets = {
            "jmeno": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "prijmeni": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "rodne_prijmeni": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }
        labels = {
            "jmeno": _("Jméno"),
            "prijmeni": _("Příjmení"),
            "rok_narozeni": _("Rok narození"),
            "rok_umrti": _("Rok úmrtí"),
            "rodne_prijmeni": _("Rodné příjmení"),
        }
        help_texts = {
            "jmeno": _("Lorem ipsum."),
            "prijmeni": _("Lorem ipsum."),
            "rok_narozeni": _("Lorem ipsum."),
            "rok_umrti": _("Lorem ipsum."),
            "rodne_prijmeni": _("Lorem ipsum."),
        }

    def __init__(self, *args, **kwargs):
        super(OsobaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_("Přidání jména")),
                    css_class="card-header",
                ),
                Div(
                    "jmeno",
                    "prijmeni",
                    "rok_narozeni",
                    "rok_umrti",
                    "rodne_prijmeni",
                    css_class="card-body",
                ),
                css_class="card",
            )
        )
        self.helper.form_tag = False
