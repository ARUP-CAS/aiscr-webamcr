import logging


from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.db.models import F, Value, CharField, IntegerField
from django.db.models import Q
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import UpdateView
from django_registration.backends.activation.views import RegistrationView
from services.mailer import Mailer
from django_registration.backends.activation.views import ActivationView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_xml.renderers import XMLRenderer

from core.decorators import odstavka_in_progress
from core.message_constants import (
    OSOBA_JIZ_EXISTUJE,
    OSOBA_USPESNE_PRIDANA,
    MAINTENANCE_AFTER_LOGOUT,
    AUTOLOGOUT_AFTER_LOGOUT,
)
from uzivatel.forms import AuthUserCreationForm, OsobaForm, AuthUserLoginForm, AuthReadOnlyUserChangeForm, \
    UpdatePasswordSettings, AuthUserChangeForm, NotificationsForm, UserPasswordResetForm
from uzivatel.models import Osoba, User
from .serializers import UserSerializer
from django.utils.encoding import force_str


logger = logging.getLogger(__name__)


class OsobaAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro získaní osob pro autocomplete.
    """
    def get_queryset(self):
        qs = Osoba.objects.all()
        if self.q:
            qs = qs.filter(vypis_cely__icontains=self.q)
        return qs


class UzivatelAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro získaní uživatelů pro autocomplete.
    """
    def get_queryset(self):
        qs = User.objects.all().order_by("last_name")
        if self.q and " " not in self.q:
            qs = qs.filter(
                Q(first_name__icontains=self.q)
                | Q(last_name__icontains=self.q)
                | Q(ident_cely__icontains=self.q)
                | Q(organizace__nazev_zkraceny__icontains=self.q)
            )
        elif self.q:
            qs = qs.annotate(
                grand_name=Concat(
                    F("last_name"),
                    Value(", "),
                    F("first_name"),
                    Value(" ("),
                    F("ident_cely"),
                    Value(", "),
                    F("organizace__nazev_zkraceny"),
                    Value(")"),
                    output_field=CharField(),
                )
            )
            new_qs = qs.filter(grand_name__istartswith=self.q).annotate(
                qs_order=Value(0, IntegerField())
            )
            new_qs2 = (
                qs.filter(grand_name__icontains=self.q)
                .exclude(grand_name__istartswith=self.q)
                .annotate(qs_order=Value(2, IntegerField()))
            )
            qs = new_qs.union(new_qs2).order_by("qs_order", "grand_name")
        return qs


class OsobaAutocompleteChoices(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro získaní osob choices pro autocomplete.
    """
    def get_queryset(self):
        qs = Osoba.objects.all()
        if self.q:
            qs = qs.filter(vypis_cely__icontains=self.q)
        qs.values_list("id", "vypis_cely"),
        return qs


@login_required
@require_http_methods(["POST", "GET"])
def create_osoba(request):
    """
    Funkce pohledu pro vytvoření osoby.
    """
    if request.method == "POST":
        form = OsobaForm(request.POST)
        if form.is_valid():
            try:
                osoba = form.save(commit=False)
                vypis = osoba.prijmeni + ","
                for j in osoba.jmeno.split():
                    if "-" in j:
                        vypis += " "
                        pom = []
                        for p in j.split("-"):
                            pom.append(p[0].upper() + ".")
                        vypis += "-".join(pom)
                    else:
                        vypis += " " + j.strip()[0].upper() + "."
                osoba.vypis_cely = osoba.prijmeni + ", " + osoba.jmeno
                osoba.vypis = vypis
                osoba.jmeno = " ".join(osoba.jmeno.split())
                osoba.save()
                messages.add_message(request, messages.SUCCESS, OSOBA_USPESNE_PRIDANA)
            except IntegrityError as ex:
                logger.debug(str(ex))
                messages.add_message(request, messages.WARNING, OSOBA_JIZ_EXISTUJE)
                return render(request, "uzivatel/create_osoba.html", {"form": form})

            # return JSON response to update dropdown and select and message
            django_messages = []
            for message in messages.get_messages(request):
                django_messages.append(
                    {
                        "level": message.level,
                        "message": message.message,
                        "extra_tags": message.tags,
                    }
                )
            return JsonResponse(
                {
                    "text": osoba.vypis_cely,
                    "value": osoba.pk,
                    "messages": django_messages,
                }
            )
        else:
            logger.debug("Form is not valid.")
            logger.debug(form.errors)
    else:
        form = OsobaForm()

    return render(request, "uzivatel/create_osoba.html", {"form": form})


class UserRegistrationView(RegistrationView):
    """
    Třída pohledu pro registraci uživatele.
    """
    form_class = AuthUserCreationForm
    success_url = reverse_lazy("django_registration_complete")


@method_decorator(odstavka_in_progress, name='dispatch')
class UserLoginView(LoginView):
    """
    Třída pohledu pro prihlášení uživatele.
    """
    authentication_form = AuthUserLoginForm


class UserLogoutView(LogoutView):
    """
    Třída pohledu pro odhlášení uživatele, kvůli zobrazení info o logoutu
    """
    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("autologout") == "true":
            messages.add_message(
                self.request, messages.SUCCESS, AUTOLOGOUT_AFTER_LOGOUT
            )
        if request.GET.get("maintenance_logout") == "true":
            messages.add_message(
                self.request, messages.SUCCESS, MAINTENANCE_AFTER_LOGOUT
            )
        return super().dispatch(request, *args, **kwargs)


class UserAccountUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Třída pohledu pro editaci uživatele.
    """
    model = User
    form_class = AuthUserChangeForm
    template_name = "uzivatel/update_user.html"

    def get_object(self, queryset=None):
        user_pk = self.request.user.pk
        return User.objects.get(pk=user_pk)

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class(instance=self.request.user)
        context["form_read_only"] = AuthReadOnlyUserChangeForm(instance=self.request.user, prefix="ro_")
        context["form_password"] = UpdatePasswordSettings(instance=self.request.user, prefix="pass")
        context["sign_in_history"] = self.get_object().history.all()[:5]
        context["form_notifications"] = NotificationsForm(instance=self.request.user)
        return context

    def _change_password(self, request, request_data):
        form = UpdatePasswordSettings(request_data, instance=self.request.user, prefix="pass")
        if form.is_valid():
            self.request.user.set_password(str(request_data["pass-password1"][0]))
            self.request.user.save()
            messages.add_message(request, messages.SUCCESS,
                                 _("uzivatel.UserAccountUpdateView._change_password.success"))
            return None
        else:
            messages.add_message(request, messages.ERROR,
                                 _("uzivatel.UserAccountUpdateView._change_password.fail"))
            return self.invalid_form_context(form, "form_password")

    def invalid_form_context(self, form, form_tag="form"):
        # Attribute "object" needs to exist.
        # This is because Django's get_context_data() function uses the object to pass it into the context.
        self.object = None
        context = self.get_context_data()
        # Update context with need form instances which contain form validation errors.
        context[form_tag] = form
        return context

    def post(self, request, *args, **kwargs):
        request_data = dict(request.POST)
        logger.debug("uzivatel.views.UserAccountUpdateView.post.start", request_data=request_data)
        form = self.form_class(data=request.POST, instance=self.request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save(update_fields=("telefon",))
            messages.add_message(request, messages.SUCCESS,
                                 _("uzivatel.UserAccountUpdateView.post.success"))
        else:
            messages.add_message(request, messages.ERROR,
                                 _("uzivatel.UserAccountUpdateView._change_password.fail"))
            context = self.invalid_form_context(form, "form")
            return render(request, self.template_name, context)
        if tuple(request_data.get("pass-password1", [""])) != ("",) \
                or tuple(request_data.get("pass-password2", [""])) != ("",):
            result = self._change_password(request, request_data)
            if result is not None:
                return render(request, self.template_name, result)
            else:
                return redirect("/accounts/login")
        context = self.get_context_data()
        return render(request, self.template_name, context)


@login_required
def update_notifications(request):
    """
    Funkce pohledu pro editaci notifikací.
    """
    form = NotificationsForm(request.POST)
    if form.is_valid():
        notifications = form.cleaned_data.get('notification_types')
        user: User = request.user
        user.notification_types.set(notifications)
        messages.add_message(request, messages.SUCCESS,
                             _("uzivatel.update_notifications.post.success"))
        return redirect("/upravit-uzivatele/")


class UserActivationView(ActivationView):
    """
    Třída pohledu pro aktivaci uživatele.
    """
    def activate(self, *args, **kwargs):
        username = self.validate_key(kwargs.get("activation_key"))
        user = self.get_user(username)
        user.save()
        return user

class UserPasswordResetView(PasswordResetView):
    """
    Třída pohledu pro resetování hesla.
    """
    form_class = UserPasswordResetForm
    
class TokenAuthenticationBearer(TokenAuthentication):
    """
    Override třídy pro nastavení názvu tokenu na Bearer.
    """
    keyword = "Bearer"
    
class MyXMLRenderer(XMLRenderer):
    """
    Override třídy pro nastavení správnych tagů.
    """
    root_tag_name = 'amcr:uzivatel'

    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement(self.item_tag_name, {})
                self._to_xml(xml, item)
                xml.endElement(self.item_tag_name)

        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict) and "idRef" in value:
                    xml.startElement(key, {"id":value.pop("idRef")})
                    self._to_xml(xml, value["value"])
                else:
                    xml.startElement(key, {})
                    self._to_xml(xml, value)
                xml.endElement(key)

        elif data is None:
            # Don't output any value
            pass

        else:
            xml.characters(force_str(data))

class GetUserInfo(APIView):
    """
    Třída podlehu pro získaní základních info o uživately.
    """
    authentication_classes = [TokenAuthenticationBearer]
    permission_classes = [IsAuthenticated]
    renderer_classes = [MyXMLRenderer,]
    http_method_names = ["get",]
    
    def get(self, request, format=None):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
