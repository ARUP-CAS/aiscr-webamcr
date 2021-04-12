import logging

from arch_z.models import ArcheologickyZaznam
from core.constants import DOKUMENTACNI_JEDNOTKA_RELATION_TYPE
from core.ident_cely import get_dj_ident
from core.message_constants import (
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPECNE_VYTVOREN,
    ZAZNAM_USPESNE_EDITOVAN,
)
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from komponenta.models import KomponentaVazby

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, ident_cely):
    dj = DokumentacniJednotka.objects.get(ident_cely=ident_cely)
    form = CreateDJForm(request.POST, instance=dj)
    if form.is_valid():
        logger.debug("Form is valid")
        dj = form.save()
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    return redirect("/arch_z/detail/" + dj.archeologicky_zaznam.ident_cely)


@login_required
@require_http_methods(["POST"])
def zapsat(request, arch_z_ident_cely):
    az = ArcheologickyZaznam.objects.get(ident_cely=arch_z_ident_cely)
    form = CreateDJForm(request.POST)
    if form.is_valid():
        logger.debug("Form is valid")
        vazba = KomponentaVazby(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
        vazba.save()  # TODO rewrite to signals

        dj = form.save(commit=False)
        dj.ident_cely = get_dj_ident(az)
        dj.komponenty = vazba
        dj.archeologicky_zaznam = az
        resp = dj.save()
        logger.debug(resp)

        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPECNE_VYTVOREN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)

    return redirect("/arch_z/detail/" + az.ident_cely)
