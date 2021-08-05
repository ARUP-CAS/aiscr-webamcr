import logging

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
from uzivatel.forms import AuthUserCreationForm, OsobaForm
from uzivatel.models import Osoba

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
        next_url = request.POST.get("next", "/")
        if not next_url:
            next_url = "/"
        if form.is_valid():
            try:
                osoba = form.save(commit=False)
                vypis = osoba.prijmeni + ","
                for j in osoba.jmeno.split():
                    vypis += " " + j.strip()[0].upper() + "."
                osoba.vypis_cely = osoba.prijmeni + ", " + osoba.jmeno
                osoba.vypis = vypis
                osoba.jmeno = " ".join(osoba.jmeno.split())
                osoba.save()
                # Add message to the user
                messages.add_message(request, messages.SUCCESS, OSOBA_USPESNE_PRIDANA)
            except IntegrityError as ex:
                logger.debug(str(ex))
                messages.add_message(request, messages.WARNING, OSOBA_JIZ_EXISTUJE)

            # redirect to the page you came from
            return redirect(next_url)
        else:
            logger.debug("Form is not valid.")
            logger.debug(form.errors)
            messages.add_message(request, messages.WARNING, FORM_NOT_VALID)
    else:
        form = OsobaForm()

    return render(request, "uzivatel/create_osoba.html", {"form": form})


class UserRegistrationView(RegistrationView):
    form_class = AuthUserCreationForm
    success_url = reverse_lazy("django_registration_complete")
