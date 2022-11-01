import logging

from adb.forms import CreateADBForm, create_vyskovy_bod_form
from adb.models import Adb, VyskovyBod
from arch_z.models import ArcheologickyZaznam
from core.constants import DOKUMENTACNI_JEDNOTKA_RELATION_TYPE
from core.exceptions import MaximalIdentNumberError
from core.ident_cely import get_dj_ident
from core.message_constants import (
    MAXIMUM_DJ_DOSAZENO,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.utils import update_all_katastr_within_akce_or_lokalita
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from heslar.hesla import HESLAR_DJ_TYP, TYP_DJ_KATASTR
from heslar.models import Heslar
from komponenta.models import KomponentaVazby
from pian.models import Pian

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    pian_db = dj.pian
    form = CreateDJForm(request.POST, instance=dj, prefix=ident_cely)
    if form.is_valid():
        logger.debug("Dj.Form is valid:1")
        dj = form.save()
        if dj.pian is None and pian_db is not None:
            dj.pian = pian_db
            dj.save()
        if form.changed_data:
            logger.debug("changed data")
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        if dj.typ.heslo == "Celek akce":
            logger.debug("celek akce")
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & ~Q(ident_cely=dj.ident_cely)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = Heslar.objects.filter(
                    Q(nazev_heslare=HESLAR_DJ_TYP) & Q(heslo__iexact="část akce")
                ).first()
                dokumentacni_jednotka.save()
                update_all_katastr_within_akce_or_lokalita(dj.ident_cely)
        elif dj.typ.heslo == "Sonda":
            logger.debug("sonda")
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & ~Q(ident_cely=dj.ident_cely)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = Heslar.objects.filter(
                    Q(nazev_heslare=HESLAR_DJ_TYP) & Q(heslo__iexact="sonda")
                ).first()
                dokumentacni_jednotka.save()
                update_all_katastr_within_akce_or_lokalita(dj.ident_cely)
        elif dj.typ.heslo == "Lokalita":
            logger.debug("lokalita")
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & Q(ident_cely=dj.ident_cely)
            )
            # logger.debug(dokumentacni_jednotka_query)
            # logger.debug(dj.archeologicky_zaznam)
            # logger.debug(dj.ident_cely)
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = Heslar.objects.filter(
                    Q(nazev_heslare=HESLAR_DJ_TYP) & Q(heslo__iexact="lokalita")
                ).first()
                dokumentacni_jednotka.save()
                update_all_katastr_within_akce_or_lokalita(dj.ident_cely)
        elif dj.typ == Heslar.objects.get(id=TYP_DJ_KATASTR):
            logger.debug("katastralni uzemi")
            dj.pian = Pian.objects.get(id=dj.archeologicky_zaznam.hlavni_katastr.pian)
            dj.save()
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    if "adb_detail" in request.POST:
        logger.debug("adb_detail")
        ident_cely = request.POST.get("adb_detail")
        adb = get_object_or_404(Adb, ident_cely=ident_cely)
        form = CreateADBForm(
            request.POST,
            instance=adb,
            prefix=ident_cely,
        )
        if form.is_valid():
            logger.debug("Dj.Form is valid:")
            form.save()
            if form.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.warning("Form is not valid")
            logger.debug(form.errors)
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
            request.session["_old_adb_post"] = request.POST
            request.session["adb_ident_cely"] = ident_cely
            logger.debug(ident_cely)

    if "adb_zapsat_vyskove_body" in request.POST:
        logger.debug("adb_zapsat_vyskove_body")
        adb_ident_cely = request.POST.get("adb_zapsat_vyskove_body")
        adb = get_object_or_404(Adb, ident_cely=adb_ident_cely)
        vyskovy_bod_formset = inlineformset_factory(
            Adb,
            VyskovyBod,
            form=create_vyskovy_bod_form(pian=pian_db),
            extra=3,
        )
        formset = vyskovy_bod_formset(
            request.POST, instance=adb, prefix=adb.ident_cely + "_vb"
        )
        if formset.is_valid():
            logger.debug("Formset is valid")
            instances = formset.save()
            for vyskovy_bod in instances:
                if isinstance(vyskovy_bod, VyskovyBod):
                    vyskovy_bod.save()
                    # vyskovy_bod.set_ident()
        if formset.is_valid():
            logger.debug("Dj.Form is valid:3")
            if (
                formset.has_changed()
            ):  # TODO tady to hazi porad ze se zmenila kvuli specifikaci a druhu
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.warning("Form is not valid")
            logger.debug(formset.errors)
            messages.add_message(
                request,
                messages.ERROR,
                ZAZNAM_SE_NEPOVEDLO_EDITOVAT + "detail.vyskovy_bod.povinna_pole",
            )

    response = dj.archeologicky_zaznam.get_redirect(dj.ident_cely)
    response.set_cookie("show-form", f"detail_dj_form_{dj.ident_cely}", max_age=1000)
    response.set_cookie(
        "set-active",
        f"el_div_dokumentacni_jednotka_{dj.ident_cely.replace('-', '_')}",
        max_age=1000,
    )
    return response


@login_required
@require_http_methods(["POST"])
def zapsat(request, arch_z_ident_cely):
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    form = CreateDJForm(request.POST)
    if form.is_valid():
        logger.debug("Dj.Form is valid:4")
        vazba = KomponentaVazby(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
        vazba.save()  # TODO rewrite to signals

        dj = form.save(commit=False)
        try:
            ident_cely = get_dj_ident(az)
            dj.ident_cely = ident_cely
            redirect = az.get_redirect(dj.ident_cely)
        except MaximalIdentNumberError:
            messages.add_message(request, messages.ERROR, MAXIMUM_DJ_DOSAZENO)
            redirect = az.get_redirect()
        else:
            dj.komponenty = vazba
            dj.archeologicky_zaznam = az
            if dj.typ == Heslar.objects.get(id=TYP_DJ_KATASTR):
                dj.pian = Pian.objects.get(id=az.hlavni_katastr.pian)
            resp = dj.save()
            logger.debug(resp)
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        redirect = az.get_redirect()
    return redirect


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    if request.method == "POST":
        resp = dj.delete()
        update_all_katastr_within_akce_or_lokalita(dj.ident_cely)
        if resp:
            logger.debug("Byla smazána dokumentacni jednotka: " + str(resp))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            return JsonResponse({"redirect": dj.archeologicky_zaznam.get_reverse()})
        else:
            logger.warning("DJ nebyla smazana: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return JsonResponse(
                {"redirect": dj.archeologicky_zaznam.get_reverse()},
                status=403,
            )
    else:
        context = {
            "object": dj,
            "title": _("dj.modalForm.smazani.title.text"),
            "id_tag": "smazat-dj-form",
            "button": _("dj.modalForm.smazani.submit.button"),
        }
        return render(request, "core/transakce_modal.html", context)
