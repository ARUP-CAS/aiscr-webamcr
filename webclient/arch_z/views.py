import logging

from arch_z.forms import CreateAkceForm, CreateArchZForm
from arch_z.models import ArcheologickyZaznam, DokumentacniJednotka
from core.constants import AZ_STAV_ZAPSANY
from core.ident_cely import get_project_event_ident
from core.message_constants import AKCE_USPESNE_ZAPSANA
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from dokument.models import Dokument
from heslar.hesla import SPECIFIKACE_DATA_PRESNE
from heslar.models import Heslar
from projekt.models import Projekt

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    zaznam = (
        ArcheologickyZaznam.objects.select_related("hlavni_katastr")
        .select_related("akce__vedlejsi_typ")
        .select_related("akce__hlavni_typ")
        .select_related("pristupnost")
        .get(ident_cely=ident_cely)
    )
    # TODO continue here
    dokumenty = (
        Dokument.objects.filter(
            dokumentcast__archeologicky_zaznam__ident_cely=ident_cely
        )
        .select_related("soubory")
        .prefetch_related("soubory__soubor_set")
    )
    jednotky = (
        DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely=ident_cely)
        .select_related("komponenty")
        .prefetch_related("komponenty__komponenta_set")
    )

    context["zaznam"] = zaznam
    context["dokumenty"] = dokumenty
    context["dokumentacni_jednotky"] = jednotky

    return render(request, "arch_z/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def zapsat(request, projekt_ident_cely):
    context = {}
    projekt = Projekt.objects.get(ident_cely=projekt_ident_cely)
    if request.method == "POST":
        form_az = CreateArchZForm(request.POST)
        form_akce = CreateAkceForm(request.POST)

        if form_az.is_valid() and form_akce.is_valid():
            logger.debug("Form is valid")
            az = form_az.save(commit=False)
            az.stav = AZ_STAV_ZAPSANY
            az.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            az.ident_cely = get_project_event_ident(projekt)
            az.save()
            # TODO continue here
            akce = form_akce.save(commit=False)
            akce.specifikace_data = Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
            akce.archeologicky_zaznam = az
            akce.projekt = projekt
            akce.save()

            messages.add_message(request, messages.SUCCESS, AKCE_USPESNE_ZAPSANA)

        else:
            logger.warning("Form is not valid")
            logger.debug(form_az.errors)
            logger.debug(form_akce.errors)

        return redirect("/arch_z/detail/" + az.ident_cely)
    else:
        form_az = CreateArchZForm()
        form_akce = CreateAkceForm()
        context["formAZ"] = form_az
        context["formAkce"] = form_akce

    return render(request, "arch_z/create.html", context)
