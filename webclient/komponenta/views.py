import logging

from core.message_constants import ZAZNAM_USPECNE_VYTVOREN
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from heslar.models import Heslar
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    komponenta = Komponenta.objects.select_related("obdobi", "areal").get(
        ident_cely=ident_cely
    )

    context["komponenta"] = komponenta
    nalezy = {
        "objekty": komponenta.objekty.all(),
        "predmety": komponenta.predmety.all(),
    }
    context["nalezy"] = nalezy
    context["dj_ident"] = ident_cely

    return render(request, "komponenta/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def zapsat(request, dj_ident_cely):
    dj = DokumentacniJednotka.objects.get(ident_cely=dj_ident_cely)
    if request.method == "POST":
        form = CreateKomponentaForm(request.POST)

        if form.is_valid():
            logger.debug("Form is valid")
            komponenta = form.save(commit=False)
            komponenta.ident_cely = "IDENTAAA-K01"  # TODO

            # Multi-level selectpickers return text not instances
            areal = form.cleaned_data["areal"]
            obdobi = form.cleaned_data["obdobi"]
            if areal:
                komponenta.areal = Heslar.objects.get(pk=int(areal))
            if obdobi:
                komponenta.obdobi = Heslar.objects.get(pk=int(obdobi))

            komponenta.komponenta_vazby = dj.komponenty
            komponenta.save()

            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPECNE_VYTVOREN)
            return redirect("/dj/detail/" + dj.ident_cely)

        else:
            logger.warning("Form is not valid")
            logger.debug(form.errors)
    else:
        form = CreateKomponentaForm()

    return render(request, "komponenta/create.html", {"form": form})
