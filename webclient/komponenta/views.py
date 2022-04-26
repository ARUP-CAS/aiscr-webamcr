import logging

from django.http import JsonResponse
from django.urls import reverse
from core.exceptions import MaximalIdentNumberError

from core.ident_cely import get_komponenta_ident
from core.message_constants import (
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
    MAXIMUM_KOMPONENT_DOSAZENO,
)
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext as _
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
    komponenta = get_object_or_404(Komponenta, ident_cely=ident_cely)
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
        if form.changed_data:
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    response = redirect(request.META.get("HTTP_REFERER"))
    response.set_cookie("show-form", f"detail_komponenta_form_{ident_cely}", max_age=1000)
    return response


@login_required
@require_http_methods(["POST"])
def zapsat(request, dj_ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    form = CreateKomponentaForm(obdobi_choices, areal_choices, request.POST)
    komp_ident_cely = None
    if form.is_valid():
        logger.debug("Form is valid")
        komponenta = form.save(commit=False)
        try:
            komponenta.ident_cely = get_komponenta_ident(dj.archeologicky_zaznam)
            komp_ident_cely = komponenta.ident_cely
        except MaximalIdentNumberError:
            messages.add_message(request, messages.ERROR, MAXIMUM_KOMPONENT_DOSAZENO)
        else:
            komponenta.komponenta_vazby = dj.komponenty
            komponenta.save()
            form.save_m2m()  # this must be called to store komponenta_aktivity

            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
    else:
        logger.warning("Form CreateKomponentaForm is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)

    response = redirect(request.META.get("HTTP_REFERER"))
    if komp_ident_cely:
        response.set_cookie("show-form", f"detail_komponenta_form_{komp_ident_cely}", max_age=1000)
    return response


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    k = get_object_or_404(Komponenta, ident_cely=ident_cely)
    if request.method == "POST":
        arch_z_ident_cely = (
            k.komponenta_vazby.dokumentacni_jednotka.archeologicky_zaznam.ident_cely
        )
        resp = k.delete()

        if resp:
            logger.debug("Byla smazána komponenta: " + str(resp))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':arch_z_ident_cely})})
        else:
            logger.warning("Komponenta nebyla smazana: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':arch_z_ident_cely})},status=403)
    else:
        context = {
        "object": k,
        "title": _("komponenta.modalForm.smazani.title.text"),
        "id_tag": "smazat-komponenta-form",
        "button": _("komponenta.modalForm.smazani.submit.button"),
        
        }
        return render(request, "core/transakce_modal.html", context)
