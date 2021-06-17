from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationForm

from .models import Osoba, User


class AuthUserCreationForm(RegistrationForm):
    class Meta(RegistrationForm):
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "telefon",
            "organizace",
            "password1",
            "password2",
        )

        labels = {
            "first_name": _("Jméno"),
            "last_name": _("Přijmení"),
            "email": _("Email"),
            "organizace": _("Organizace"),
            "password1": _("Heslo"),
            "telefon": _("Telefon")
        }

        widgets = {
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "telefon": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }

    def __init__(self, *args, **kwargs):
        super(AuthUserCreationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False


class AuthUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "organizace", "jazyk", "ident_cely", "telefon")


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
                    Div(
                        HTML(_("Přidání osoby")),
                        css_class="app-fx app-left",
                    ),
                    css_class="card-header",
                ),
                Div(
                    Div(
                        Div("jmeno", css_class="col-sm-6"),
                        Div("prijmeni", css_class="col-sm-6"),
                        Div("rok_narozeni", css_class="col-sm-6"),
                        Div("rok_umrti", css_class="col-sm-6"),
                        Div("rodne_prijmeni", css_class="col-sm-12"),
                        css_class="row",
                    ),
                    css_class="card-body",
                ),
                css_class="card app-card-form",
            )
        )
        self.helper.form_tag = False
