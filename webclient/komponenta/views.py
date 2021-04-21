import logging

from core.ident_cely import get_komponenta_ident
from core.message_constants import (
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPECNE_VYTVOREN,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
)
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from heslar.hesla import (
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
)
from heslar.views import heslar_12
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, ident_cely):
    komponenta = Komponenta.objects.get(ident_cely=ident_cely)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    form = CreateKomponentaForm(
        obdobi_choices,
        areal_choices,
        request.POST,
        instance=komponenta,
        prefix=ident_cely,
    )
    if form.is_valid():
        logger.debug("Form is valid")
        form.save()
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
@require_http_methods(["POST"])
def zapsat(request, dj_ident_cely):
    dj = DokumentacniJednotka.objects.get(ident_cely=dj_ident_cely)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    form = CreateKomponentaForm(obdobi_choices, areal_choices, request.POST)
    if form.is_valid():
        logger.debug("Form is valid")
        komponenta = form.save(commit=False)
        komponenta.ident_cely = get_komponenta_ident(dj.archeologicky_zaznam)
        komponenta.komponenta_vazby = dj.komponenty
        komponenta.save()
        form.save_m2m()  # this must be called to store komponenta_aktivity

        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPECNE_VYTVOREN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    k = Komponenta.objects.get(ident_cely=ident_cely)
    if request.method == "POST":
        arch_z_ident_cely = (
            k.komponenta_vazby.dokumentacni_jednotka.archeologicky_zaznam.ident_cely
        )
        resp = k.delete()

        if resp:
            logger.debug("Byla smazána komponenta: " + str(resp))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        else:
            logger.warning("Komponenta nebyla smazana: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)

        return redirect("arch_z:detail", ident_cely=arch_z_ident_cely)
    else:
        return render(request, "core/smazat.html", {"objekt": k})
