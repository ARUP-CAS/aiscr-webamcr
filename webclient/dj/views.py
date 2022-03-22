import logging

from django.db.models import Q

from core.exceptions import MaximalIdentNumberError

from arch_z.models import ArcheologickyZaznam
from core.constants import DOKUMENTACNI_JEDNOTKA_RELATION_TYPE
from core.ident_cely import get_dj_ident
from core.message_constants import (
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
    MAXIMUM_DJ_DOSAZENO,
)
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from komponenta.models import KomponentaVazby
from heslar.hesla import HESLAR_DJ_TYP
from heslar.models import Heslar

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    form = CreateDJForm(request.POST, instance=dj, prefix=ident_cely)
    if form.is_valid():
        logger.debug("Form is valid")
        dj = form.save()
        if form.changed_data:
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        if dj.typ.heslo == "Celek akce":
            dokumentacni_jednotka_query = \
                DokumentacniJednotka.objects.filter(Q(archeologicky_zaznam=dj.archeologicky_zaznam) &
                                                    ~Q(ident_cely=dj.ident_cely))
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = Heslar.objects.filter(Q(nazev_heslare=HESLAR_DJ_TYP)
                                                                  & Q(heslo__iexact="část akce")).first()
                dokumentacni_jednotka.save()
        elif dj.typ.heslo == "Sonda":
            dokumentacni_jednotka_query = \
                DokumentacniJednotka.objects.filter(Q(archeologicky_zaznam=dj.archeologicky_zaznam) &
                                                    ~Q(ident_cely=dj.ident_cely))
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = Heslar.objects.filter(Q(nazev_heslare=HESLAR_DJ_TYP)
                                                                  & Q(heslo__iexact="sonda")).first()
                dokumentacni_jednotka.save()
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    return redirect("arch_z:detail", dj.archeologicky_zaznam.ident_cely)


@login_required
@require_http_methods(["POST"])
def zapsat(request, arch_z_ident_cely):
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    form = CreateDJForm(request.POST)
    if form.is_valid():
        logger.debug("Form is valid")
        vazba = KomponentaVazby(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
        vazba.save()  # TODO rewrite to signals

        dj = form.save(commit=False)
        try:
            dj.ident_cely = get_dj_ident(az)
        except MaximalIdentNumberError:
            messages.add_message(request, messages.ERROR, MAXIMUM_DJ_DOSAZENO)
        else:
            dj.komponenty = vazba
            dj.archeologicky_zaznam = az
            resp = dj.save()
            logger.debug(resp)

            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)

    response = redirect("arch_z:detail", az.ident_cely)
    response.set_cookie("show-form", f"detail_dj_form_{dj.ident_cely}", max_age=1000)
    return response


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    arch_z_ident_cely = dj.archeologicky_zaznam.ident_cely
    if request.method == "POST":
        resp = dj.delete()
        if resp:
            logger.debug("Byla smazána dokumentacni jednotka: " + str(resp))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        else:
            logger.warning("DJ nebyla smazana: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)

        return redirect("arch_z:detail", ident_cely=arch_z_ident_cely)
    else:
        return render(request, "core/smazat.html", {"objekt": dj})
