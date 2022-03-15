import logging

from django.http import JsonResponse

from core.message_constants import (
    FORM_NOT_VALID,
    OSOBA_JIZ_EXISTUJE,
    OSOBA_USPESNE_PRIDANA,
)
from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django_registration.backends.activation.views import RegistrationView
from django.contrib.auth.views import LoginView, LogoutView
from uzivatel.forms import AuthUserCreationForm, OsobaForm, AuthUserLoginForm
from uzivatel.models import Osoba
from core.message_constants import AUTOLOGOUT_AFTER_LOGOUT

logger = logging.getLogger(__name__)


class OsobaAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Osoba.objects.all()
        if self.q:
            qs = qs.filter(vypis_cely__icontains=self.q)
        return qs


@login_required
@require_http_methods(["POST", "GET"])
def create_osoba(request):

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
                django_messages.append({ 
                    "level": message.level,
                    "message": message.message,
                    "extra_tags": message.tags,
                })
            return JsonResponse({"text": osoba.vypis_cely, "value":osoba.pk, "messages":django_messages})
        else:
            logger.debug("Form is not valid.")
            logger.debug(form.errors)
    else:
        form = OsobaForm()

    return render(request, "uzivatel/create_osoba.html", {"form": form})


class UserRegistrationView(RegistrationView):
    form_class = AuthUserCreationForm
    success_url = reverse_lazy("django_registration_complete")


class UserLoginView(LoginView):
    authentication_form = AuthUserLoginForm


# overriding logout view for adding message after auto logout
class UserLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("autologout") == "true":
            messages.add_message(
                self.request, messages.SUCCESS, AUTOLOGOUT_AFTER_LOGOUT
            )
            logger.debug("something")
        return super().dispatch(request, *args, **kwargs)
