import datetime
import logging
from smtplib import SMTPException

from core.constants import ZMENA_HESLA_UZIVATEL, ZMENA_UDAJU_UZIVATEL
from core.decorators import odstavka_in_progress
from core.message_constants import (
    AUTOLOGOUT_AFTER_LOGOUT,
    MAINTENANCE_AFTER_LOGOUT,
    OSOBA_JIZ_EXISTUJE,
    OSOBA_USPESNE_PRIDANA,
    ZADOST_SMAZANI_UZIVATELE_SUCCESS,
)
from core.models import Permissions as p
from core.models import check_permissions
from core.repository_connector import FedoraTransaction
from core.views import PermissionFilterMixin
from dal import autocomplete
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.forms.renderers import BaseRenderer
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import UpdateView
from django_registration.backends.activation.views import ActivationView, RegistrationView
from fedora_management.decorators import handle_fedora_error
from historie.models import Historie
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from services.mailer import Mailer
from uzivatel.forms import (
    AuthActivationForm,
    AuthReadOnlyUserChangeForm,
    AuthUserChangeForm,
    AuthUserCreationFormWithRecaptcha,
    AuthUserLoginForm,
    NotificationsForm,
    OsobaForm,
    UpdatePasswordSettings,
    UserPasswordResetForm,
)
from uzivatel.models import NotificationsLog, Osoba, User, UserNotificationType, UzivatelPrihlaseniLog

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


class UzivatelAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView, PermissionFilterMixin):
    """
    Třída pohledu pro získaní uživatelů pro autocomplete.
    """

    def get_result_label(self, result):
        return result.display_name(viewer=self.request.user)

    def get_queryset(self):
        qs = User.objects.select_related("organizace")

        if self.q:
            terms = self.q.strip().split()

            q_obj = Q()
            for term in terms:
                q_obj &= (
                    Q(first_name__icontains=term)
                    | Q(last_name__icontains=term)
                    | Q(ident_cely__icontains=term)
                    | Q(organizace__nazev_zkraceny__icontains=term)
                    | Q(organizace__nazev_zkraceny_en__icontains=term)
                )

            qs = qs.filter(q_obj)

        qs = qs.order_by("last_name", "first_name")

        return self.check_filter_permission(qs)

    def add_accessibility_lookup(self, permission, qs):
        return qs

    def add_ownership_lookup(self, ownership, qs=None):
        return Q()


class UzivatelAutocompletePublic(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro získaní uživatelů pro autocomplete - verze pouze s ident_cely uživatele, beze jména.
    """

    def get_result_label(self, result):
        return result.display_name()

    def get_queryset(self):
        qs = User.objects.all().select_related("organizace").order_by("ident_cely")
        if self.q:
            qs = qs.filter(Q(ident_cely__icontains=self.q) | Q(organizace__nazev_zkraceny__icontains=self.q))
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
                        for part in j.split("-"):
                            pom.append(part[0].upper() + ".")
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

            # Vrátí JSON odpověď pro aktualizaci rozbalovací nabídky, výběru a zprávy.
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
        form = OsobaForm(create=True)

    return render(request, "uzivatel/create_osoba.html", {"form": form})


@method_decorator(odstavka_in_progress, name="dispatch")
class UserRegistrationView(RegistrationView):
    """
    Třída pohledu pro registraci uživatele.
    """

    form_class = AuthUserCreationFormWithRecaptcha
    success_url = reverse_lazy("django_registration_complete")

    def send_activation_email(self, user):
        try:
            super().send_activation_email(user)
            notification_type = UserNotificationType.objects.get(ident_cely="E-U-01")
            Mailer._log_notification(notification_type, user, user.email, "OK", None)
            logger.debug("uzivatel.views.UserRegistrationView.send_activation_email.sent", extra={"pk": user})
        except SMTPException as err:
            messages.add_message(
                self.request, messages.ERROR, _("uzivatel.views.UserRegistrationView.send_activation_email.error")
            )
            logger.error(
                "uzivatel.views.UserRegistrationView.send_activation_email.error", extra={"pk": user, "error": err}
            )


@method_decorator(odstavka_in_progress, name="dispatch")
class UserLoginView(LoginView):
    """
    Třída pohledu pro prihlášení uživatele.
    """

    authentication_form = AuthUserLoginForm


class UserLogoutView(LogoutView):
    """
    Třída pohledu pro odhlášení uživatele, kvůli zobrazení info o logoutu
    """

    def post(self, request, *args, **kwargs):
        if request.POST.get("logout_type") == "autologout":
            logger.debug("message added")
            messages.add_message(self.request, messages.SUCCESS, AUTOLOGOUT_AFTER_LOGOUT)
        if request.POST.get("logout_type") == "maintenance":
            messages.add_message(self.request, messages.SUCCESS, MAINTENANCE_AFTER_LOGOUT)
        return super().post(request, *args, **kwargs)


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
        context["sign_in_history"] = UzivatelPrihlaseniLog.objects.filter(user=self.request.user).order_by(
            "-prihlaseni_datum_cas"
        )[:5]
        context["form_notifications"] = NotificationsForm(instance=self.request.user)
        context["show_edit_notifikace"] = check_permissions(
            p.actionChoices.notifikace_projekty, self.request.user, self.request.user.ident_cely
        )
        return context

    def _change_password(self, request, request_data):
        form = UpdatePasswordSettings(request_data, instance=self.request.user, prefix="pass")
        if form.is_valid():
            Historie(
                typ_zmeny=ZMENA_HESLA_UZIVATEL,
                uzivatel=request.user,
                vazba=self.request.user.history_vazba,
            ).save()
            self.request.user.set_password(str(request_data["pass-password1"][0]))
            self.request.user.save()
            messages.add_message(
                request, messages.SUCCESS, _("uzivatel.views.UserAccountUpdateView.change_password.success")
            )
            return None
        else:
            messages.add_message(
                request, messages.ERROR, _("uzivatel.views.UserAccountUpdateView.change_password.fail")
            )
            return self.invalid_form_context(form, "form_password")

    def invalid_form_context(self, form, form_tag="form"):
        # Atribut "object" musí existovat.
        # Důvod: Django `get_context_data()` používá objekt pro jeho předání do contextu.
        self.object = None
        context = self.get_context_data()
        # Doplní context o potřebné instance formulářů obsahující validační chyby.
        context[form_tag] = form
        return context

    @method_decorator(handle_fedora_error)
    def post(self, request, *args, **kwargs):
        request_data = dict(request.POST)
        logger.debug("uzivatel.views.UserAccountUpdateView.post.start")
        form = self.form_class(data=request.POST, instance=self.request.user)
        has_changed = (
            request.POST.get("telefon") != self.request.user.telefon
            or request.POST.get("orcid") != self.request.user.orcid
        )
        if form.is_valid() and has_changed:
            obj = form.save(commit=False)
            obj: User
            obj.active_transaction = FedoraTransaction(obj, request.user)
            obj.active_transaction.redirect_on_error = True
            obj.active_transaction.redirect_url = reverse_lazy("uzivatel:update-uzivatel")
            obj.save(update_fields=("telefon",))
            poznamka = ", ".join([f"{fieldname}: {form.cleaned_data[fieldname]}" for fieldname in form.changed_data])
            if len(poznamka) > 0:
                Historie(
                    typ_zmeny=ZMENA_UDAJU_UZIVATEL,
                    uzivatel=request.user,
                    poznamka=poznamka,
                    vazba=obj.history_vazba,
                ).save()
            messages.add_message(request, messages.SUCCESS, _("uzivatel.views.UserAccountUpdateView.post.success"))
            obj.close_active_transaction_when_finished = True
            obj.save()
        elif not form.is_valid():
            messages.add_message(
                request, messages.ERROR, _("uzivatel.views.UserAccountUpdateView.post.change_password.fail")
            )
            context = self.invalid_form_context(form, "form")
            return render(request, self.template_name, context)
        if tuple(request_data.get("pass-password1", [""])) != ("",) or tuple(
            request_data.get("pass-password2", [""])
        ) != ("",):
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
    from services.mailer import NOTIFICATION_GROUPS

    form = NotificationsForm(request.POST)
    if form.is_valid():
        notifications = form.cleaned_data.get("notification_types")
        user: User = request.user
        user.active_transaction = FedoraTransaction(user, request.user)
        notification_group_idents = {x.ident_cely: x for x in notifications.all()}
        for group_ident in NOTIFICATION_GROUPS.keys():
            if group_ident in notification_group_idents:
                user.notification_types.add(notification_group_idents[group_ident])
            else:
                type_obj = UserNotificationType.objects.get(ident_cely=group_ident)
                user.notification_types.remove(type_obj)
        messages.add_message(request, messages.SUCCESS, _("uzivatel.views.update_notifications.post.success"))
        user.close_active_transaction_when_finished = True
        user.save()
        return redirect("/uzivatel/edit/")


@method_decorator(odstavka_in_progress, name="dispatch")
class UserActivationView(ActivationView):
    """
    Třída pohledu pro aktivaci uživatele.
    """

    form_class = AuthActivationForm

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)

    def activate(self, form):
        username = form.cleaned_data["activation_key"]
        user = self.get_user(username)
        # Uživatel musí být aktivován ručně administrátorem systému.
        user.is_active = False
        user.save()
        for notification in UserNotificationType.objects.filter(
            Q(ident_cely__icontains="S-E-") | Q(ident_cely="zpravodaj")
        ):
            user.notification_types.add(notification)
        cutoff_time = timezone.now() - datetime.timedelta(minutes=10)
        if not NotificationsLog.objects.filter(
            notification_type=UserNotificationType.objects.get(ident_cely="E-U-02"),
            status="OK",
            user=user,
            created_at__gt=cutoff_time,
        ).exists():
            Mailer.send_eu02(user=user)
        if not NotificationsLog.objects.filter(
            notification_type=UserNotificationType.objects.get(ident_cely="E-U-04"),
            status="OK",
            user=user,
            created_at__gt=cutoff_time,
        ).exists():
            Mailer.send_eu04(user=user)
        return user


@method_decorator(odstavka_in_progress, name="dispatch")
class UserPasswordResetView(PasswordResetView):
    """
    Třída pohledu pro resetování hesla.
    """

    form_class = UserPasswordResetForm

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)


@method_decorator(odstavka_in_progress, name="dispatch")
class TokenAuthenticationBearer(TokenAuthentication):
    """
    Override třídy pro nastavení názvu tokenu na Bearer.
    """

    keyword = "Bearer"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related("user").get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("uzivatel.views.tokenAuthenticationBearer.invalidToken"))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_("uzivatel.views.tokenAuthenticationBearer.userInactiveOrDeleted."))

        if not token.created + datetime.timedelta(hours=settings.TOKEN_EXPIRATION_HOURS) > timezone.now():
            raise exceptions.AuthenticationFailed(_("uzivatel.views.tokenAuthenticationBearer.userTokenTooOld."))

        return (token.user, token)


class MyXMLRenderer(BaseRenderer):
    """
    Override třídy pro nastavení správnych tagů.
    """

    media_type = "application/xml"
    format = "xml"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders `data` into serialized XML.
        """
        return data


@method_decorator(odstavka_in_progress, name="get")
class GetUserInfo(APIView):
    """
    Třída podlehu pro získaní základních info o uživately.
    """

    authentication_classes = [TokenAuthenticationBearer]
    permission_classes = [IsAuthenticated]
    renderer_classes = [
        MyXMLRenderer,
    ]
    http_method_names = [
        "get",
    ]

    def get(self, request, format=None):
        user = request.user
        return Response(user.metadata)

    def handle_exception(self, exc):
        self.is_exception = True
        return super().handle_exception(exc)

    def perform_content_negotiation(self, request, force=False):
        try:
            self.is_exception
            return JSONRenderer(), JSONRenderer.media_type
        except Exception:
            return super().perform_content_negotiation(request, force)

    def finalize_response(self, request, response, *args, **kwargs):
        try:
            self.is_exception
            neg = self.perform_content_negotiation(request, force=True)
            request.accepted_renderer, request.accepted_media_type = neg
        finally:
            return super().finalize_response(request, response, *args, **kwargs)


@method_decorator(odstavka_in_progress, name="post")
class ObtainAuthTokenWithUpdate(ObtainAuthToken):
    """
    Třída pohledu pro získaní tokenu pro API.
    """

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        if not token.created + datetime.timedelta(hours=settings.TOKEN_EXPIRATION_HOURS) > timezone.now():
            try:
                with transaction.atomic():
                    Token.objects.filter(user=user).delete()
                    token = Token.objects.create(user=user)
            except IntegrityError:
                # Pokud mezitím druhý request token vytvořil,
                # jen si ho načteme.
                token = Token.objects.get(user=user)
        return Response({"token": token.key})


class UserDeleteRequest(LoginRequiredMixin, UpdateView):
    """
    Třída pohledu pro požádání o smazání účtu
    """

    def post(self, request, *args, **kwargs):
        user: User = request.user
        Mailer.send_eu07(user, request)
        messages.add_message(request, messages.SUCCESS, ZADOST_SMAZANI_UZIVATELE_SUCCESS)
        return JsonResponse({"redirect": reverse("uzivatel:update-uzivatel")})

    def get(self, request, *args, **kwargs):
        context = {
            "title": _("uzivatel.views.UserDeleteRequest.title.text"),
            "id_tag": "user-delete-request-dialog",
            "button": _("uzivatel.views.UserDeleteRequest.submitButton.text"),
        }
        return render(request, "core/transakce_modal.html", context)
