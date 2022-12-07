import logging

from adb.forms import CreateADBForm, create_vyskovy_bod_form
from adb.models import Adb, VyskovyBod
from core.exceptions import DJNemaPianError, MaximalIdentNumberError
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
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def zapsat(request, dj_ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    dj: DokumentacniJednotka
    form = CreateADBForm(request.POST)
    if form.is_valid():
        logger.debug("Adb. Form is valid:2")
        adb = form.save(commit=False)
        if not dj.pian:
            raise DJNemaPianError(dj)
        try:
            adb.ident_cely, sm5 = get_adb_ident(dj.pian)
        except MaximalIdentNumberError as e:
            messages.add_message(request, messages.ERROR, e.message)
        else:
            adb.dokumentacni_jednotka = dj
            adb.sm5 = sm5
            adb.save()
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
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
@require_http_methods(["POST"])
def zapsat_vyskove_body(request, adb_ident_cely):
    adb = get_object_or_404(Adb, ident_cely=adb_ident_cely)
    vyskovy_bod_formset = inlineformset_factory(
        Adb,
        VyskovyBod,
        form=create_vyskovy_bod_form(),
        extra=3,
    )
    formset = vyskovy_bod_formset(
        request.POST, instance=adb, prefix=adb.ident_cely + "_vb"
    )
    if formset.is_valid():
        logger.debug("Formset is valid")
        instances = formset.save()
        for vyskovy_bod in instances:
            vyskovy_bod: VyskovyBod
            vyskovy_bod.save()
            # vyskovy_bod.set_ident()
    if formset.is_valid():
        logger.debug("Adb Form is valid3")
        if (
            formset.has_changed()
        ):  # TODO tady to hazi porad ze se zmenila kvuli specifikaci a druhu
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
    else:
        logger.warning("Form is not valid")
        logger.debug(formset.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    adb = get_object_or_404(Adb, ident_cely=ident_cely)
    if request.method == "POST":
        arch_z_ident_cely = adb.dokumentacni_jednotka.archeologicky_zaznam.ident_cely
        dj: DokumentacniJednotka = adb.dokumentacni_jednotka
        dj_ident_cely = dj.ident_cely
        resp = adb.delete()

        if resp:
            logger.debug("Byla smazána adb: " + str(resp))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            response = JsonResponse(
                {
                    "redirect": dj.get_absolute_url()
                }
            )
        else:
            logger.warning("Adb nebyla smazana: " + str(ident_cely))
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
            "title": _("adb.modalForm.smazani.title.text"),
            "id_tag": "smazat-adb-form",
            "button": _("adb.modalForm.smazani.submit.button"),
        }
        response = render(request, "core/transakce_modal.html", context)
        response.set_cookie("show-form", f"detail_dj_form_{adb.dokumentacni_jednotka.ident_cely}", max_age=1000)
        return response


@login_required
@require_http_methods(["GET", "POST"])
def smazat_vb(request, ident_cely):
    zaznam = get_object_or_404(VyskovyBod, id=ident_cely)
    context = {
        "object": zaznam,
        "title": _("vb.modalForm.smazaniVB.title.text"),
        "id_tag": "smazat-vb-form",
        "button": _("vb.modalForm.smazaniVB.submit.button"),
    }
    if request.method == "POST":
        resp = zaznam.delete()
        next_url = request.POST.get("next")
        if next_url:
            if is_safe_url(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
                response = next_url
            else:
                logger.warning("Redirect to URL " + str(next_url) + " is not safe!!")
                response = redirect(request.META.get("HTTP_REFERER"))
        else:
            response = redirect(request.META.get("HTTP_REFERER"))
        if resp:
            logger.debug("Objekt dokumentu byl smazan: " + str(resp))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            response = JsonResponse({"redirect": response})
        else:
            logger.warning("Dokument nebyl smazan: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            response = JsonResponse({"redirect": response}, status=403)
        response.set_cookie("show-form", f"detail_dj_form_{zaznam.adb.dokumentacni_jednotka.ident_cely}", max_age=1000)
        return response
    else:
        return render(request, "core/transakce_modal.html", context)
