import logging

from adb.forms import CreateADBForm
from adb.models import Adb
from core.exceptions import DJNemaPianError
from core.ident_cely import get_adb_ident
from core.message_constants import (
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, ident_cely):
    adb = Adb.objects.get(ident_cely=ident_cely)
    form = CreateADBForm(
        request.POST,
        instance=adb,
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

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
@require_http_methods(["POST"])
def zapsat(request, dj_ident_cely):
    dj = DokumentacniJednotka.objects.get(ident_cely=dj_ident_cely)
    form = CreateADBForm(request.POST)
    if form.is_valid():
        logger.debug("Form is valid")
        adb = form.save(commit=False)
        if not dj.pian:
            raise DJNemaPianError(dj)
        adb.ident_cely, sm5 = get_adb_ident(dj.pian)
        adb.dokumentacni_jednotka = dj
        adb.sm5 = sm5
        adb.save()

        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    adb = Adb.objects.get(ident_cely=ident_cely)
    if request.method == "POST":
        arch_z_ident_cely = adb.dokumentacni_jednotka.archeologicky_zaznam.ident_cely
        resp = adb.delete()

        if resp:
            logger.debug("Byla smazána adb: " + str(resp))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        else:
            logger.warning("Adb nebyla smazana: " + str(ident_cely))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_SE_NEPOVEDLO_SMAZAT)

        return redirect("arch_z:detail", ident_cely=arch_z_ident_cely)
    else:
        return render(request, "core/smazat.html", {"objekt": adb})
