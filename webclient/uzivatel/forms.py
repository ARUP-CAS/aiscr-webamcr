from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout,Field
from crispy_forms.bootstrap import AppendedText
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationForm
from django.core.exceptions import ValidationError

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
            "telefon": _("Telefon"),
        }

        widgets = {
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-live-search": "true"}
            ),
            "telefon": forms.TextInput,
        }
        help_texts = {
            "first_name": _("uzivatel.form.userCreation.first_name.tooltip"),
            "last_name": _("uzivatel.form.userCreation.last_name.tooltip"),
            "email": _("uzivatel.form.userCreation.email.tooltip"),
            "organizace": _("uzivatel.form.userCreation.organizace.tooltip"),
            "password1": _("uzivatel.form.userCreation.password1.tooltip"),
            "telefon": _("uzivatel.form.userCreation.telefon.tooltip"),
        }

    def __init__(self, *args, **kwargs):
        super(AuthUserCreationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("first_name"),
            Field("last_name"),
            Field("email"),
            Field("telefon"),
            Field("organizace"),
            AppendedText('password1', '<i class="bi bi-eye-slash" id="togglePassword1"></i>'),
            AppendedText('password2', '<i class="bi bi-eye-slash" id="togglePassword2"></i>'),
            )
        for key in self.fields.keys():
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""


class AuthUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "organizace", "jazyk", "ident_cely", "telefon")
        help_texts = {
            "email": _("uzivatel.form.userChange.email.tooltip"),
            "jazyk": _("uzivatel.form.userChange.jazyk.tooltip"),
            "organizace": _("uzivatel.form.userChange.organizace.tooltip"),
            "ident_cely": _("uzivatel.form.userChange.ident_cely.tooltip"),
            "telefon": _("uzivatel.form.userChange.telefon.tooltip"),
        }


class AuthUserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(AuthUserLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("username"),
            AppendedText('password', '<i class="bi bi-eye-slash" id="togglePassword"></i>'),
            )
        

    def get_invalid_login_error(self):
        return ValidationError(
            _("Nesprávne zadaný email nebo heslo."),
            code="invalid_login",
        )


class OsobaForm(forms.ModelForm):
    class Meta:
        model = Osoba
        fields = (
            "jmeno",
            "prijmeni",
            # "rok_narozeni",
            # "rok_umrti",
            # "rodne_prijmeni",
        )
        widgets = {
            "jmeno": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "prijmeni": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            # "rodne_prijmeni": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }
        labels = {
            "jmeno": _("uzivatel.form.osoba.jmeno.label"),
            "prijmeni": _("uzivatel.form.osoba.prijmeni.label"),
            # "rok_narozeni": _("Rok narození"),
            # "rok_umrti": _("Rok úmrtí"),
            # "rodne_prijmeni": _("Rodné příjmení"),
        }
        help_texts = {
            "jmeno": _("uzivatel.form.osoba.jmeno.tooltip"),
            "prijmeni": _("uzivatel.form.osoba.prijmeni.tooltip"),
            # "rok_narozeni": _("Lorem ipsum."),
            # "rok_umrti": _("Lorem ipsum."),
            # "rodne_prijmeni": _("Lorem ipsum."),
        }

    def __init__(self, *args, **kwargs):
        super(OsobaForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("jmeno", css_class="col-sm-6"),
                Div("prijmeni", css_class="col-sm-6"),
                # Div("rok_narozeni", css_class="col-sm-6"),
                # Div("rok_umrti", css_class="col-sm-6"),
                # Div("rodne_prijmeni", css_class="col-sm-12"),
                css_class="row",
            )
        )
        self.helper.form_tag = False
