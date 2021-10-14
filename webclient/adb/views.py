import logging

from adb.forms import CreateADBForm, create_vyskovy_bod_form, VyskovyBodFormSetHelper
from adb.models import Adb
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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from adb.models import Adb, VyskovyBod

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, ident_cely):
    adb = get_object_or_404(Adb, ident_cely=ident_cely)
    form = CreateADBForm(request.POST, instance=adb, prefix=ident_cely,)
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
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    form = CreateADBForm(request.POST)
    if form.is_valid():
        logger.debug("Form is valid")
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

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
@require_http_methods(["POST"])
def zapsat_vyskove_body(request, adb_ident_cely):
    adb = get_object_or_404(Adb, ident_cely=adb_ident_cely)
    vyskovy_bod_formset = inlineformset_factory(
        Adb, VyskovyBod, form=create_vyskovy_bod_form(), extra=3,
    )
    formset = vyskovy_bod_formset(
        request.POST, instance=adb, prefix=adb.ident_cely + "_vb"
    )
    if formset.is_valid():
        logger.debug("Formset is valid")
        instances = formset.save()
        for vyskovy_bod in instances:
            vyskovy_bod: VyskovyBod
            vyskovy_bod.geom = Point(x=vyskovy_bod.northing, y=vyskovy_bod.easting)
            vyskovy_bod.save()
            # vyskovy_bod.set_ident()
    if formset.is_valid():
        logger.debug("Form is valid")
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
