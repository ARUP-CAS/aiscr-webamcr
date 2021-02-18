import logging

from arch_z.models import ArcheologickyZaznam, DokumentacniJednotka
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from dokument.models import Dokument

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
