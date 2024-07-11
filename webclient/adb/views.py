import logging

from adb.forms import CreateADBForm
from adb.models import Adb, VyskovyBod
from core.exceptions import DJNemaPianError, MaximalIdentNumberError
from core.ident_cely import get_adb_ident
from core.message_constants import (
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN, ZAZNAM_NELZE_SMAZAT_FEDORA,
)
from core.repository_connector import FedoraTransaction, FedoraRepositoryConnector
from dj.models import DokumentacniJednotka
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods


logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def zapsat(request, dj_ident_cely):
    """
    Pohled pro vytvoření novího ADB.
    Pred uložením do DB se vytvoří relace na DB, nový ident celý je vygenerovaný a sm5 je přidané.
    Po úspešném uložení je uživatel presměrován na pohled detailu DJ.
    """
    logger.debug("adb.views.zapsat.start", extra={"dj_ident_cely": dj_ident_cely})
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    dj: DokumentacniJednotka
    form = CreateADBForm(request.POST)
    if form.is_valid():
        logger.debug("adb.views.zapsat.is_valid")
        adb = form.save(commit=False)
        if not dj.pian:
            raise DJNemaPianError(dj)
        try:
            adb.ident_cely, sm5 = get_adb_ident(dj.pian)
        except MaximalIdentNumberError as e:
            messages.add_message(request, messages.ERROR, e.message)
        else:
            if FedoraRepositoryConnector.check_container_deleted_or_not_exists(adb.ident_cely, "adb"):
                fedora_transaction = FedoraTransaction()
                adb.active_transaction = fedora_transaction
                adb.close_active_transaction_when_finished = True
                adb.dokumentacni_jednotka = dj
                adb.sm5 = sm5
                adb.save()
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
            else:
                logger.debug("adb.views.zapsat.check_container_deleted_or_not_exists.incorrect",
                             extra={"ident_cely": adb.ident_cely})
                messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
    else:
        logger.debug("adb.views.zapsat.not_valid", extra={"errors": form.errors})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)

    response = redirect(dj.get_absolute_url())
    response.set_cookie("show-form", f"detail_dj_form_{dj.ident_cely}", max_age=1000)
    response.set_cookie(
        "set-active",
        f"el_div_dokumentacni_jednotka_{dj.ident_cely.replace('-', '_')}",
        max_age=1000,
    )
    return response


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    """
    Pohled pro smazání ADB.
    Po úspešném smazání je uživatel presměrován na pohled detailu DJ.
    """
    adb = get_object_or_404(Adb, ident_cely=ident_cely)
    if request.method == "POST":
        dj: DokumentacniJednotka = adb.dokumentacni_jednotka
        dj_ident_cely = dj.ident_cely
        fedora_transaction = FedoraTransaction()
        adb.active_transaction = fedora_transaction
        adb.close_active_transaction_when_finished = True
        for vb in adb.vyskove_body.all():
            vb.active_transaction = fedora_transaction
            vb.delete()
        resp = adb.delete()

        if resp:
            logger.debug("adb.views.smazat.resp", extra={"resp": str(resp)})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            response = JsonResponse(
                {
                    "redirect": dj.get_absolute_url()
                }
            )
        else:
            logger.warning("adb.views.smazat.error", extra={"ident_cely": str(ident_cely)})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            response = JsonResponse(
                {
                    "redirect": dj.get_absolute_url()
                },
                status=403,
            )
        response.set_cookie("show-form", f"detail_dj_form_{dj_ident_cely}", max_age=1000)
        return response
    else:
        context = {
            "object": adb,
            "title": _("adb.views.smazat.modalForm.title"),
            "id_tag": "smazat-adb-form",
            "button": _("adb.views.smazat.modalForm.submit.button"),
        }
        response = render(request, "core/transakce_modal.html", context)
        response.set_cookie("show-form", f"detail_dj_form_{adb.dokumentacni_jednotka.ident_cely}", max_age=1000)
        return response


@login_required
@require_http_methods(["GET", "POST"])
def smazat_vb(request, ident_cely):
    """
    Pohled pro smazání VB.
    Po úspešném smazání je uživatel presměrován na next_url z requestu.
    """
    zaznam = get_object_or_404(VyskovyBod, ident_cely=ident_cely)
    zaznam: VyskovyBod
    context = {
        "object": zaznam,
        "title": _("adb.views.smazat_vb.modalForm.title"),
        "id_tag": "smazat-vb-form",
        "button": _("adb.views.smazat_vb.modalForm.submit.button"),
    }
    if request.method == "POST":
        fedora_transaction = FedoraTransaction()
        zaznam.active_transaction = fedora_transaction
        zaznam.close_active_transaction_when_finished = True
        resp = zaznam.delete()
        next_url = request.POST.get("next")
        if url_has_allowed_host_and_scheme(request.META.get("HTTP_REFERER"), allowed_hosts=settings.ALLOWED_HOSTS):
            safe_redirect = request.META.get("HTTP_REFERER")
        else:
            safe_redirect = "/"
        if next_url:
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
                response = next_url
            else:
                logger.warning("adb.views.smazat.smazat_vb.not_safe", extra={"next_url": str(next_url)})
                response = redirect(safe_redirect)
        else:
            response = redirect(safe_redirect)
        if resp:
            logger.debug("adb.views.smazat.smazat_vb.deleted", extra={"resp": str(resp)})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            response = JsonResponse({"redirect": response})
        else:
            logger.warning("adb.views.smazat.smazat_vb.deleted", extra={"ident_cely": str(ident_cely)})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            response = JsonResponse({"redirect": response}, status=403)
        response.set_cookie("show-form", f"detail_dj_form_{zaznam.adb.dokumentacni_jednotka.ident_cely}", max_age=1000)
        return response
    else:
        return render(request, "core/transakce_modal.html", context)
