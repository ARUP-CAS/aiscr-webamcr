import logging

from core.message_constants import ZAZNAM_USPESNE_EDITOVAN
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from dokument.forms import EditDokumentForm
from dokument.models import Dokument

logger = logging.getLogger(__name__)


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
        context["soubory"] = dokument.soubory.soubory.all()
    else:
        context["soubory"] = None
    return render(request, "dokument/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):

    dokument = Dokument.objects.get(ident_cely=ident_cely)
    if request.method == "POST":
        form = EditDokumentForm(request.POST, instance=dokument)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
        return render(
            request, "dokument/edit.html", {"form": form, "dokument": dokument}
        )
    else:
        form = EditDokumentForm(instance=dokument)

    return render(request, "dokument/edit.html", {"form": form, "dokument": dokument})
