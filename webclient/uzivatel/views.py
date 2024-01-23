import logging
from io import StringIO

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
from django.forms.renderers import BaseRenderer
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import UpdateView
from django_registration.backends.activation.views import RegistrationView
from django_registration.backends.activation.views import ActivationView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import exceptions
from django.conf import settings
import datetime
from django.utils import timezone
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from core.constants import ZMENA_UDAJU_UZIVATEL, ZMENA_HESLA_UZIVATEL
from core.decorators import odstavka_in_progress
from core.message_constants import (
    OSOBA_JIZ_EXISTUJE,
    OSOBA_USPESNE_PRIDANA,
    MAINTENANCE_AFTER_LOGOUT,
    AUTOLOGOUT_AFTER_LOGOUT,
)
from historie.models import Historie
from uzivatel.forms import AuthUserCreationForm, OsobaForm, AuthUserLoginForm, AuthReadOnlyUserChangeForm, \
    UpdatePasswordSettings, AuthUserChangeForm, NotificationsForm, UserPasswordResetForm
from uzivatel.models import Osoba, User, UserNotificationType
from core.views import PermissionFilterMixin
from core.models import Permissions as p, check_permissions

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
        return f"{result.last_name}, {result.first_name} ({result.ident_cely}, {result.organizace.nazev_zkraceny})"
    
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
        return self.check_filter_permission(qs)
    
    def add_accessibility_lookup(self,permission, qs):
        return qs
    
    def add_ownership_lookup(self, ownership, qs=None):
        return Q()

class UzivatelAutocompletePublic(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_result_label(self, result):
        return f"{result.ident_cely} ({result.organizace.nazev_zkraceny})"
    def get_queryset(self):
        qs = User.objects.all().order_by("ident_cely")
        if self.q:
            qs = qs.filter(Q(ident_cely__icontains=self.q)
                           | Q(organizace__nazev_zkraceny__icontains=self.q))
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
        context["show_edit_notifikace"] = check_permissions(p.actionChoices.notifikace_projekty, self.request.user, self.request.user.ident_cely)
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
            messages.add_message(request, messages.SUCCESS,
                                 _("uzivatel.views.UserAccountUpdateView.change_password.success"))
            return None
        else:
            messages.add_message(request, messages.ERROR,
                                 _("uzivatel.views.UserAccountUpdateView.change_password.fail"))
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
        logger.debug("uzivatel.views.UserAccountUpdateView.post.start", extra={"request_data": request_data})
        form = self.form_class(data=request.POST, instance=self.request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save(update_fields=("telefon",))
            poznamka = ", ".join([f"{fieldname}: {form.cleaned_data[fieldname]}" for fieldname in form.changed_data])
            if len(poznamka) > 0:
                Historie(
                    typ_zmeny=ZMENA_UDAJU_UZIVATEL,
                    uzivatel=request.user,
                    poznamka=poznamka,
                    vazba=obj.history_vazba,
                ).save()
            messages.add_message(request, messages.SUCCESS,
                                 _("uzivatel.views.UserAccountUpdateView.post.success"))
        else:
            messages.add_message(request, messages.ERROR,
                                 _("uzivatel.views.UserAccountUpdateView.post.change_password.fail"))
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
    from services.mailer import NOTIFICATION_GROUPS
    form = NotificationsForm(request.POST)
    if form.is_valid():
        notifications = form.cleaned_data.get('notification_types')
        user: User = request.user
        notification_group_idents = [x.ident_cely for x in notifications.all()]
        for group_ident, current_group_notification_idents in NOTIFICATION_GROUPS.items():
            group_obj = UserNotificationType.objects.get(ident_cely=group_ident)
            if group_ident in notification_group_idents:
                user.notification_types.add(group_obj)
            else:
                user.notification_types.remove(group_obj)
            for current_inner_ident in current_group_notification_idents:
                type_obj = UserNotificationType.objects.get(ident_cely=current_inner_ident)
                if group_ident in notification_group_idents:
                    user.notification_types.add(type_obj)
                else:
                    user.notification_types.remove(type_obj)
        messages.add_message(request, messages.SUCCESS,
                             _("uzivatel.views.update_notifications.post.success"))
        user.save_metadata()
        return redirect("/uzivatel/edit/")


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

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('uzivatel.views.tokenAuthenticationBearer.invalidToken'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('uzivatel.views.tokenAuthenticationBearer.userInactiveOrDeleted.'))

        if not token.created + datetime.timedelta(hours=settings.TOKEN_EXPIRATION_HOURS) > timezone.now():
            raise exceptions.AuthenticationFailed(_('uzivatel.views.tokenAuthenticationBearer.userTokenTooOld.'))

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


class GetUserInfo(APIView):
    """
    Třída podlehu pro získaní základních info o uživately.
    """
    authentication_classes = [TokenAuthenticationBearer]
    permission_classes = [IsAuthenticated]
    renderer_classes = [MyXMLRenderer, ]
    http_method_names = ["get", ]
    
    def get(self, request, format=None):
        user = request.user
        return Response(user.metadata)

class ObtainAuthTokenWithUpdate(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        if not token.created + datetime.timedelta(hours=settings.TOKEN_EXPIRATION_HOURS) > timezone.now():
            token.delete()
            token.save()
        return Response({'token': token.key})
