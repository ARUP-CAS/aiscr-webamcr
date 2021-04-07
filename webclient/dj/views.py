import logging

from arch_z.models import ArcheologickyZaznam
from core.constants import DOKUMENTACNI_JEDNOTKA_RELATION_TYPE
from core.message_constants import ZAZNAM_USPECNE_VYTVOREN
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from komponenta.models import KomponentaVazby

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    dj = DokumentacniJednotka.objects.select_related("typ").get(ident_cely=ident_cely)

    context["dj"] = dj
    context["komponenty"] = dj.komponenty.komponenty.all()

    return render(request, "dj/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def zapsat(request, arch_z_ident_cely):
    az = ArcheologickyZaznam.objects.get(ident_cely=arch_z_ident_cely)
    if request.method == "POST":
        form = CreateDJForm(request.POST)

        if form.is_valid():
            logger.debug("Form is valid")
            vazba = KomponentaVazby(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
            vazba.save()  # TODO rewrite to signals

            dj = form.save(commit=False)
            dj.ident_cely = "IDENT AAA"  # TODO
            dj.komponenty = vazba
            dj.archeologicky_zaznam = az
            dj.save()

            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPECNE_VYTVOREN)
            return redirect("/arch_z/detail/" + az.ident_cely)

        else:
            logger.warning("Form is not valid")
            logger.debug(form.errors)
    else:
        form = CreateDJForm()

    return render(request, "dj/create.html", {"form": form})
