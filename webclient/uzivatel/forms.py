import logging

from core.validators import validate_phone_number
from core.widgets import AutocompleteListSelect2, ForeignKeyReadOnlyTextInput
from crispy_forms.bootstrap import AppendedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, UserChangeForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.forms import PasswordInput
from django.template import loader
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Invisible
from django_registration.backends.activation.forms import ActivationForm
from django_registration.forms import RegistrationForm
from pid.fields import OrcidAutocompleteField
from pid.forms import FormWithOrcid, FormWithWikidata
from services.mailer import Mailer

from .models import Osoba, User, UserNotificationType

logger = logging.getLogger(__name__)


class AuthUserCreationForm(RegistrationForm, FormWithOrcid):
    """Formulář pro vytvoření uživatele."""

    class Meta(RegistrationForm):
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "telefon",
            "organizace",
            "orcid",
            "password1",
            "password2",
        )

        labels = {
            "first_name": _("uzivatel.forms.userCreation.first_name.label"),
            "last_name": _("uzivatel.forms.userCreation.last_name.label"),
            "email": _("uzivatel.forms.userCreation.email.label"),
            "organizace": _("uzivatel.forms.userCreation.organizace.label"),
            "password1": _("uzivatel.forms.userCreation.password1.label"),
            "telefon": _("uzivatel.forms.userCreation.telefon.label"),
        }

        widgets = {
            "organizace": forms.Select(
                attrs={"class": "selectpicker", "data-multiple-separator": "; ", "data-live-search": "true"}
            ),
            "telefon": forms.TextInput,
        }
        help_texts = {
            "first_name": _("uzivatel.forms.userCreation.first_name.tooltip"),
            "last_name": _("uzivatel.forms.userCreation.last_name.tooltip"),
            "email": _("uzivatel.forms.userCreation.email.tooltip"),
            "organizace": _("uzivatel.forms.userCreation.organizace.tooltip"),
            "password1": _("uzivatel.forms.userCreation.password1.tooltip"),
            "telefon": _("uzivatel.forms.userCreation.telefon.tooltip"),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, ``OrcidAutocompleteField()``, pracuje se s atributy ``get``.
        """
        super(AuthUserCreationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.fields["telefon"].validators = [validate_phone_number]
        self.fields["telefon"].widget.input_type = "tel"
        self.fields["orcid"] = OrcidAutocompleteField(
            widget=AutocompleteListSelect2(url="pid:orcid-autocomplete"),
            label=_("uzivatel.forms.AuthUserChangeForm.orcid.label"),
            help_text=_("uzivatel.forms.AuthUserChangeForm.orcid.tooltip"),
            initial_value=kwargs.get("data").get("orcid") if kwargs.get("data") else None,
            required=False,
        )
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("first_name"),
            Field("last_name"),
            Field("email"),
            Field("telefon"),
            Field("organizace"),
            Field("orcid"),
            AppendedText(
                "password1",
                mark_safe('<i class="bi bi-eye-slash" id="togglePassword1"></i>'),
                input_size="input-group-sm",
            ),
            AppendedText(
                "password2",
                mark_safe('<i class="bi bi-eye-slash" id="togglePassword2"></i>'),
                input_size="input-group-sm",
            ),
        )
        for key in self.fields.keys():
            if isinstance(self.fields[key].widget, forms.widgets.Select):
                self.fields[key].empty_label = ""


class AuthUserCreationFormWithRecaptcha(AuthUserCreationForm):
    """Implementuje komponentu ``AuthUserCreationFormWithRecaptcha`` v rámci aplikace."""

    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible)

    class Meta(AuthUserCreationForm):
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "telefon",
            "organizace",
            "password1",
            "password2",
            "orcid",
            "captcha",
        )

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(AuthUserCreationFormWithRecaptcha, self).__init__(*args, **kwargs)
        if settings.SKIP_RECAPTCHA:
            self.fields.pop("captcha")


class AuthUserChangeForm(forms.ModelForm, FormWithOrcid):
    """Formulář pro editaci uživatele."""

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = User
        fields = ("telefon", "orcid")
        labels = {
            "telefon": _("uzivatel.forms.AuthUserChangeForm.telefon.label"),
        }
        help_texts = {
            "telefon": _("uzivatel.forms.AuthUserChangeForm.telefon.tooltip"),
        }

        widgets = {
            "telefon": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``, ``OrcidAutocompleteField()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("telefon", css_class="col-sm-3"),
                Div("orcid", css_class="col-sm-3"),
                css_class="row",
            )
        )
        self.fields["orcid"] = OrcidAutocompleteField(
            widget=AutocompleteListSelect2(url="pid:orcid-autocomplete"),
            label=_("uzivatel.forms.AuthUserChangeForm.orcid.label"),
            help_text=_("uzivatel.forms.AuthUserChangeForm.orcid.tooltip"),
            instance=self.instance,
            initial_value=args[0].get("orcid") if args else None,
            required=False,
        )


class AuthReadOnlyUserChangeForm(forms.ModelForm):
    """Formulář pro zobrazení detailu uživatele."""

    hlavni_role = forms.CharField(
        widget=ForeignKeyReadOnlyTextInput(),
        label=_("uzivatel.forms.userChange.hlavni_role.label"),
        help_text=_("uzivatel.forms.userChange.hlavni_role.tooltip"),
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = User
        fields = ("first_name", "last_name", "email", "ident_cely", "date_joined", "organizace", "groups")
        labels = {
            "first_name": _("uzivatel.forms.userChange.first_name.label"),
            "last_name": _("uzivatel.forms.userChange.last_name.label"),
            "email": _("uzivatel.forms.userChange.email.label"),
            "ident_cely": _("uzivatel.forms.userChange.ident_cely.label"),
            "date_joined": _("uzivatel.forms.userChange.date_joined.label"),
            "organizace": _("uzivatel.forms.userChange.organizace.label"),
            "groups": _("uzivatel.forms.userChange.groups.label"),
        }
        help_texts = {
            "first_name": _("uzivatel.forms.userChange.first_name.tooltip"),
            "last_name": _("uzivatel.forms.userChange.last_name.tooltip"),
            "email": _("uzivatel.forms.userChange.email.tooltip"),
            "ident_cely": _("uzivatel.forms.userChange.ident_cely.tooltip"),
            "date_joined": _("uzivatel.forms.userChange.date_joined.tooltip"),
            "organizace": _("uzivatel.forms.userChange.organizace.tooltip"),
            "groups": _("uzivatel.forms.userChange.groups.tooltip"),
        }

        widgets = {
            "first_name": forms.TextInput(attrs={"readonly": True}),
            "last_name": forms.TextInput(attrs={"readonly": True}),
            "email": forms.TextInput(attrs={"readonly": True}),
            "ident_cely": forms.TextInput(attrs={"readonly": True}),
            "date_joined": ForeignKeyReadOnlyTextInput(),
            "organizace": ForeignKeyReadOnlyTextInput(),
            "groups": ForeignKeyReadOnlyTextInput(),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.fields["organizace"].widget.value = self.instance.organizace
        self.fields["hlavni_role"].widget.value = self.instance.hlavni_role
        self.fields["date_joined"].widget.value = self.instance.date_joined.replace(microsecond=0).replace(tzinfo=None)
        self.fields["groups"].widget.value = ", ".join([str(group.name) for group in self.instance.groups.all()])
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("first_name", css_class="col-sm-6 col-lg-3"),
                Div("last_name", css_class="col-sm-6 col-lg-3"),
                Div("email", css_class="col-sm-6 col-lg-3"),
                Div("ident_cely", css_class="col-sm-6 col-lg-3"),
                Div("date_joined", css_class="col-sm-6 col-lg-3"),
                Div("organizace", css_class="col-sm-6 col-lg-3"),
                Div("hlavni_role", css_class="col-sm-6 col-lg-3"),
                Div("groups", css_class="col-sm-6 col-lg-3"),
                css_class="row",
            )
        )


class AuthUserChangeAdminForm(UserChangeForm, FormWithOrcid):
    """Implementuje komponentu ``AuthUserChangeAdminForm`` v rámci aplikace."""

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``, ``OrcidAutocompleteField()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.fields["orcid"] = OrcidAutocompleteField(
            widget=AutocompleteListSelect2(url="pid:orcid-autocomplete"),
            label=_("uzivatel.forms.AuthUserChangeAdminForm.orcid.label"),
            instance=self.instance,
            initial_value=args[0].get("orcid") if args else None,
        )


class NotificationsForm(forms.ModelForm):
    """Formulář pro správu typu notifikací."""

    notification_types = forms.ModelMultipleChoiceField(
        queryset=UserNotificationType.objects.filter(
            Q(ident_cely__icontains="S-E-A")
            | Q(ident_cely__icontains="S-E-N")
            | Q(ident_cely__icontains="S-E-K")
            | Q(ident_cely__icontains="zpravodaj")
        ),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("uzivatel.forms.notifications_form.notification_types.notification_types_label"),
        help_text=_("uzivatel.forms.notifications_form.notification_types.notification_types.tooltip"),
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = User
        fields = ("notification_types",)


class UpdatePasswordSettings(forms.ModelForm):
    """Formulář pro změnu hesla."""

    old_password = forms.CharField(
        required=False,
        widget=PasswordInput(),
        label=_("uzivatel.forms.userChange.old_password.label"),
        help_text=_("uzivatel.forms.UpdatePasswordSettings.old_password.tooltip"),
    )
    password1 = forms.CharField(
        required=False,
        widget=PasswordInput(),
        label=_("uzivatel.forms.userChange.password1.label"),
        help_text=_("uzivatel.forms.UpdatePasswordSettings.password1.tooltip"),
    )
    password2 = forms.CharField(
        required=False,
        widget=PasswordInput(),
        label=_("uzivatel.forms.userChange.password2.label"),
        help_text=_("uzivatel.forms.UpdatePasswordSettings.password2.tooltip"),
    )

    def clean(self):
        """
        Provádí operaci clean.

        :raises ValidationError: Vyvolá se při splnění podmínky ``not old_password and (password1 or password2)``; nebo při splnění podmínky ``old_password and (not (password1 or password2))``.
        """
        cleaned_data = super().clean()
        old_password = cleaned_data.get("old_password")[2:-2]
        password1 = cleaned_data.get("password1")[2:-2]
        password2 = cleaned_data.get("password2")[2:-2]

        if not old_password and (password1 or password2):
            raise ValidationError(_("uzivatel.forms.UpdatePasswordSettings.old_password.error"))
        if old_password and not (password1 or password2):
            raise ValidationError(_("uzivatel.forms.UpdatePasswordSettings.now_new.error"))
        if not password1 and password2:
            raise ValidationError(_("uzivatel.forms.UpdatePasswordSettings.password1.error"))
        elif not password2 and password1:
            raise ValidationError(_("uzivatel.forms.UpdatePasswordSettings.password2.error"))
        if password1 != password2:
            raise ValidationError(_("uzivatel.forms.UpdatePasswordSettings.passwordsDifferent.error"))
        if not self.instance.check_password(old_password):
            raise ValidationError(_("uzivatel.forms.UpdatePasswordSettings.old_password.error"))
        validate_password(password1)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = User
        fields = ("password1", "password2")

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div("old_password", css_class="col-sm-3"),
                Div("password1", css_class="col-sm-3"),
                Div("password2", css_class="col-sm-3"),
                css_class="row",
            )
        )


class AuthUserLoginForm(AuthenticationForm):
    """Formulář pro prihlášení uživatele."""

    error_messages = {
        "invalid_login": _("uzivatel.forms.login.error"),
        "inactive": _("core.authenticators.user_can_authenticate"),
    }

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(AuthUserLoginForm, self).__init__(*args, **kwargs)
        self.fields["username"].help_text = _("uzivatel.forms.login.username.tooltip")
        self.fields["password"].help_text = _("uzivatel.forms.login.password.tooltip")
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("username"),
            AppendedText(
                "password",
                mark_safe('<i class="bi bi-eye-slash" id="togglePassword"> </i>'),
                input_size="input-group-sm",
            ),
        )


class UserPasswordResetForm(PasswordResetForm):
    """Implementuje komponentu ``UserPasswordResetForm`` v rámci aplikace."""

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(UserPasswordResetForm, self).__init__(*args, **kwargs)
        self.fields["email"].label = _("uzivatel.forms.passwordReset.email.label")
        self.fields["email"].help_text = _("uzivatel.forms.passwordReset.email.tooltip")
        self.helper = FormHelper(self)
        self.helper.form_tag = False

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.

        :param subject_template_name: Parametr ``subject_template_name`` se předává do volání ``render_to_string()``.
        :param email_template_name: Parametr ``email_template_name`` se předává do volání ``render_to_string()``.
        :param context: Parametr ``context`` se předává do volání ``render_to_string()``, ``_log_notification()``.
        :param from_email: Uživatel nebo osoba ``from_email``, v jejímž kontextu se operace provádí.
        :param to_email: Uživatel nebo osoba ``to_email``, v jejímž kontextu se operace provádí.
        :param html_email_template_name: Parametr ``html_email_template_name`` se předává do volání ``render_to_string()``, ovlivňuje větvení podmínek.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Předmět e-mailu *nesmí* obsahovat znaky nového řádku.
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")
        try:
            email_message.send()
            status = "OK"
            exception = None
        except Exception as e:
            logger.warning(
                "uzivatel.forms.send_mail.warning",
                extra={"email": from_email, "to": to_email, "subject": subject, "exception": e},
            )
            status = "NOK"
            exception = e
        notification_type = UserNotificationType.objects.get(ident_cely="E-U-05")
        Mailer._log_notification(
            notification_type=notification_type,
            receiver_object=context["user"],
            receiver_address=to_email,
            status=status,
            exception=exception,
        )


class OsobaForm(forms.ModelForm, FormWithOrcid, FormWithWikidata):
    """Formulář pro vytvoření osoby."""

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        model = Osoba
        fields = (
            "jmeno",
            "prijmeni",
            # "orcid",
            # "wikidata"
            # "rok_narozeni",
            # "rok_umrti",
            # "rodne_prijmeni",
        )
        widgets = {
            "jmeno": forms.TextInput(),
            "prijmeni": forms.TextInput(),
            # "orcid": forms.TextInput(),
            # "wikidata": forms.TextInput(),
            # "rodne_prijmeni": forms.Textarea(attrs={"rows": 1, "cols": 40}),
        }
        labels = {
            "jmeno": _("uzivatel.forms.osoba.jmeno.label"),
            "prijmeni": _("uzivatel.forms.osoba.prijmeni.label"),
            "orcid": _("uzivatel.forms.osoba.orcid.label"),
            "wikidata": _("uzivatel.forms.osoba.wikidata.label"),
            # "rok_narozeni": _("uzivatel.forms.osoba.rok_narozeni.label"),
            # "rok_umrti": _("uzivatel.forms.osoba.rok_umrti.label"),
            # "rodne_prijmeni": _("uzivatel.forms.osoba.rodne_prijmeni.label"),
        }
        help_texts = {
            "jmeno": _("uzivatel.forms.osoba.jmeno.tooltip"),
            "prijmeni": _("uzivatel.forms.osoba.prijmeni.tooltip"),
            "orcid": _("uzivatel.forms.osoba.orcid.tooltip"),
            "wikidata": _("uzivatel.forms.osoba.wikidata.tooltip"),
            # "rok_narozeni": _("uzivatel.forms.osoba.rok_narozeni.tooltip"),
            # "rok_umrti": _("uzivatel.forms.osoba.rok_umrti.tooltip"),
            # "rodne_prijmeni": _("uzivatel.forms.osoba.rodne_prijmeni.tooltip"),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.
        """
        kwargs.pop("create", False)
        super(OsobaForm, self).__init__(*args, **kwargs)
        # Pokud jde o vytvoření:
        # self.fields["orcid"] = OrcidAutocompleteField(
        #     widget=AutocompleteListSelect2(url="pid:orcid-autocomplete"),
        #     label=_("uzivatel.forms.AuthUserChangeForm.orcid.label"),
        #     help_text=_("uzivatel.forms.AuthUserChangeForm.orcid.tooltip"),
        #     required=False,
        # )
        # self.fields["wikidata"] = WikiDataAutocompleteField(
        #     widget=AutocompleteListSelect2(url="pid:wikidata-autocomplete"),
        #     label=_("heslar.forms.OsobaAdminForm.wikidata.label"),
        #     instance=self.instance,
        #     required=False,
        # )
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div("jmeno", css_class="col-sm-6"),
                Div("prijmeni", css_class="col-sm-6"),
                # Div("orcid", css_class="col-sm-6"),
                # Div("wikidata", css_class="col-sm-6"),
                # Div("rok_narozeni", css_class="col-sm-6"),
                # Div("rok_umrti", css_class="col-sm-6"),
                # Div("rodne_prijmeni", css_class="col-sm-12"),
                css_class="row",
            )
        )
        self.helper.form_tag = False


class AuthActivationForm(ActivationForm):
    """Implementuje komponentu ``AuthActivationForm`` v rámci aplikace."""

    activation_key = forms.CharField(label=_("templates.djangoRegistration.activationKey.label"))


class TestEmailForm(forms.Form):
    """
    Formulář pro odeslání testovacího mailu v administraci.
    """

    email = forms.EmailField(label=_("uzivatel.forms.TestEmailForm.email_address"), required=True)
