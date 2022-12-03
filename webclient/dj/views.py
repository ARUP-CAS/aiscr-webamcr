import logging
import structlog

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
from core.utils import (
    update_all_katastr_within_akce_or_lokalita,
    update_main_katastr_within_ku,
)
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
logger_s = structlog.get_logger(__name__)

@login_required
@require_http_methods(["POST"])
def detail(request, ident_cely):
    logger_s.debug("dj.views.detail.start")
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=ident_cely)
    pian_db = dj.pian
    form = CreateDJForm(request.POST, instance=dj, prefix=ident_cely)
    if form.is_valid():
        logger_s.debug("dj.views.detail.form_is_valid")
        dj = form.save()
        if dj.pian is None and pian_db is not None:
            dj.pian = pian_db
            dj.save()
        if form.changed_data:
            logger.debug("changed data")
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        if dj.typ.heslo == "Celek akce":
            logger_s.debug("dj.views.detail.celek_akce")
            typ = Heslar.objects.filter(Q(nazev_heslare=HESLAR_DJ_TYP) & Q(heslo__iexact="část akce")).first()
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & ~Q(ident_cely=dj.ident_cely) & ~Q(typ=typ)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = typ
                dokumentacni_jednotka.save()
            update_all_katastr_within_akce_or_lokalita(dj.ident_cely)
        elif dj.typ.heslo == "Sonda":
            logger_s.debug("dj.views.detail.sonda")
            typ = Heslar.objects.filter(Q(nazev_heslare=HESLAR_DJ_TYP) & Q(heslo__iexact="sonda")).first()
            dokumentacni_jednotka_query = DokumentacniJednotka.objects.filter(
                Q(archeologicky_zaznam=dj.archeologicky_zaznam)
                & ~Q(ident_cely=dj.ident_cely) & ~Q(typ=typ)
            )
            for dokumentacni_jednotka in dokumentacni_jednotka_query:
                dokumentacni_jednotka.typ = typ
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
            new_ku = form.cleaned_data["ku_change"]
            dj.pian = Pian.objects.get(id=dj.archeologicky_zaznam.hlavni_katastr.pian)
            dj.save()
            if len(new_ku) > 3:
                update_main_katastr_within_ku(dj.ident_cely, new_ku)

    else:
        logger_s.warning("dj.views.detail.form_is_not_valid", erros=form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    if "adb_detail" in request.POST:
        logger_s.debug("dj.views.detail.adb_detail")
        ident_cely = request.POST.get("adb_detail")
        adb = get_object_or_404(Adb, ident_cely=ident_cely)
        form = CreateADBForm(
            request.POST,
            instance=adb,
            prefix=ident_cely,
        )
        if form.is_valid():
            logger_s.debug("dj.views.detail.adb_detail.form_is_valid")
            form.save()
            if form.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger_s.debug("dj.views.detail.adb_detail.form_is_not_valid")
            logger.debug(form.errors)
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
            request.session["_old_adb_post"] = request.POST
            request.session["adb_ident_cely"] = ident_cely
            logger.debug(ident_cely)

    if "adb_zapsat_vyskove_body" in request.POST:
        logger_s.debug("dj.views.detail.adb_zapsat_vyskove_body")
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
            logger_s.debug("dj.views.detail.adb_zapsat_vyskove_body.form_set_is_valid")
            instances = formset.save()
            for vyskovy_bod in instances:
                if isinstance(vyskovy_bod, VyskovyBod):
                    vyskovy_bod.save()
                    # vyskovy_bod.set_ident()
        if formset.is_valid():
            logger_s.debug("dj.views.detail.adb_zapsat_vyskove_body.form_set_is_valid")
            if (
                formset.has_changed()
            ):  # TODO tady to hazi porad ze se zmenila kvuli specifikaci a druhu
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger_s.debug("dj.views.detail.adb_zapsat_vyskove_body.form_set_is_not_valid", errors=formset.errors)
            messages.add_message(
                request,
                messages.ERROR,
                ZAZNAM_SE_NEPOVEDLO_EDITOVAT + "detail.vyskovy_bod.povinna_pole",
            )

    response = dj.archeologicky_zaznam.get_redirect(dj.ident_cely)
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
            return JsonResponse({"redirect": dj.archeologicky_zaznam.get_absolute_url()})
        else:
            logger.warning("DJ nebyla smazana: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return JsonResponse(
                {"redirect": dj.archeologicky_zaznam.get_absolute_url()},
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
