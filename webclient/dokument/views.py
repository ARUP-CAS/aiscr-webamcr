from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from dokument.models import Dokument


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    dokument = Dokument.objects.select_related(
        "soubory",
        "organizace",
        "material_originalu",
        "typ_dokumentu",
        "rada",
        "pristupnost",
    ).get(ident_cely=ident_cely)

    context["dokument"] = dokument
    if dokument.soubory:
        context["soubory"] = dokument.soubory.soubor_set.all()
    else:
        context["soubory"] = None
    return render(request, "dokument/detail.html", context)
