from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Field
from crispy_forms.bootstrap import AppendedText
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from django.contrib.auth.password_validation import validate_password
from django.forms import PasswordInput
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationForm
from django.core.exceptions import ValidationError

from core.widgets import ForeignKeyReadOnlyTextInput
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
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
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


class AuthUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("telefon",)
        help_texts = {
            "telefon": _("uzivatel.form.userChange.telefon.tooltip"),
        }

        widgets = {
            "telefon": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("telefon", css_class="col-sm-3"),
                css_class="row",
            )
        )


class AuthReadOnlyUserChangeForm(forms.ModelForm):
    hlavni_role = forms.CharField(widget=ForeignKeyReadOnlyTextInput())

    class Meta:
        model = User
        fields = (
            "first_name", "last_name", "email", "ident_cely", "date_joined", "organizace", "groups")
        help_texts = {
            "first_name": _("uzivatel.form.userChange.first_name.tooltip"),
            "last_name": _("uzivatel.form.userChange.last_name.tooltip"),
            "email": _("uzivatel.form.userChange.email.tooltip"),
            "ident_cely": _("uzivatel.form.userChange.ident_cely.tooltip"),
            "date_joined": _("uzivatel.form.userChange.date_joined.tooltip"),
            "organizace": _("uzivatel.form.userChange.organizace.tooltip"),
            "hlavni_role": _("uzivatel.form.userChange.hlavni_role.tooltip"),
            "groups": _("uzivatel.form.userChange.hlavni_role.tooltip"),
        }

        widgets = {
            "first_name": forms.TextInput(attrs={"readonly": True}),
            "last_name": forms.TextInput(attrs={"readonly": True}),
            "email": forms.TextInput(attrs={"readonly": True}),
            "ident_cely": forms.TextInput(attrs={"readonly": True}),
            "date_joined": forms.TextInput(attrs={"readonly": True}),
            "organizace": ForeignKeyReadOnlyTextInput(),
            "groups": ForeignKeyReadOnlyTextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organizace"].widget.value = self.instance.organizace
        self.fields["hlavni_role"].widget.value = self.instance.hlavni_role
        self.fields["groups"].widget.value = ", ".join([str(group.name) for group in self.instance.groups.all()])
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("first_name", css_class="col-sm-3"),
                Div("last_name", css_class="col-sm-3"),
                Div("email", css_class="col-sm-3"),
                Div("ident_cely", css_class="col-sm-3"),
                Div("date_joined", css_class="col-sm-3"),
                Div("organizace", css_class="col-sm-3"),
                Div("hlavni_role", css_class="col-sm-3"),
                Div("groups", css_class="col-sm-3"),
                css_class="row"
            )
        )


class NotificationsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('notification_types',)


class UpdatePasswordSettings(forms.ModelForm):
    password1 = forms.CharField(required=False, widget=PasswordInput())
    password2 = forms.CharField(required=False, widget=PasswordInput())

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 == "" and password2 != "":
            raise ValidationError({"password1": [_("Toto pole musí být vyplněno!")]})
        elif password2 != "" and password2 == "":
            raise ValidationError({"password2": [_("Toto pole musí být vyplněno!")]})
        if password1 != password2:
            raise ValidationError(_("Hesla se neshodují"))
        validate_password(password1)

    class Meta:
        model = User
        fields = ["password1", "password2"]
        help_texts = {
            "password1": _("uzivatel.form.UpdatePasswordSettings.password1.tooltip"),
            "password2": _("uzivatel.form.UpdatePasswordSettings.password2.tooltip"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("password1", css_class="col-sm-3"),
                Div("password2", css_class="col-sm-3"),
                css_class="row",
            )
        )


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
            "jmeno": forms.TextInput(),
            "prijmeni": forms.TextInput(),
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
