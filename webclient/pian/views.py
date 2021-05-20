import logging

from core.constants import KLADYZM10, KLADYZM50
from core.message_constants import (
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from pian.forms import PianCreateForm
from pian.models import Kladyzm, Pian

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def detail(request, ident_cely=None):
    pian = Pian.objects.get(ident_cely=ident_cely)
    if request.method == "POST":
        form = PianCreateForm(request.POST, instance=pian)
        if form.is_valid():
            logger.debug("Form is valid")
            pian = form.save()
            if form.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.warning("Form is not valid")
            logger.debug(form.errors)
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
    else:
        form = PianCreateForm(instance=pian)

    return render(request, "pian/detail.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    if request.method == "POST":
        form = PianCreateForm(request.POST)
        if form.is_valid():
            logger.debug("Form is valid")
            pian = form.save(commit=False)
            # Assign base map references
            zm10s = Kladyzm.objects.filter(kategorie=KLADYZM10).filter(
                the_geom__contains=pian.geom
            )
            zm50s = Kladyzm.objects.filter(kategorie=KLADYZM50).filter(
                the_geom__contains=pian.geom
            )
            if zm10s.count() == 1 and zm50s.count() == 1:
                pian.zm10 = zm10s[0]
                pian.zm50 = zm50s[0]
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
            else:
                logger.debug("")
                messages.add_message(
                    request, messages.SUCCESS, ZAZNAM_SE_NEPOVEDLO_VYTVORIT
                )
        else:
            logger.warning("Form is not valid")
            logger.debug(form.errors)
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
    else:
        form = PianCreateForm()

    return render(request, "pian/detail.html", {"form": form})


class PianAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Pian.objects.all()
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return qs
