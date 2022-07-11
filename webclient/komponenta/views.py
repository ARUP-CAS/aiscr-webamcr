import logging

from core.exceptions import MaximalIdentNumberError
from core.ident_cely import get_komponenta_ident
from core.message_constants import (
    MAXIMUM_KOMPONENT_DOSAZENO,
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
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from heslar.hesla import (
    HESLAR_AREAL,
    HESLAR_AREAL_KAT,
    HESLAR_OBDOBI,
    HESLAR_OBDOBI_KAT,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PREDMET_SPECIFIKACE,
)
from heslar.models import Heslar
from heslar.views import heslar_12
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta
from nalez.forms import create_nalez_objekt_form, create_nalez_predmet_form
from nalez.models import NalezObjekt, NalezPredmet

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
        logger.debug("K.Form is valid:1")
        form.save()
        if form.changed_data:
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    if "nalez_edit_nalez" in request.POST:
        druh_objekt_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
        specifikace_objekt_choices = heslar_12(
            HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT
        )
        NalezObjektFormset = inlineformset_factory(
            Komponenta,
            NalezObjekt,
            form=create_nalez_objekt_form(
                druh_objekt_choices, specifikace_objekt_choices
            ),
            extra=1,
        )
        formset_objekt = NalezObjektFormset(
            request.POST, instance=komponenta, prefix=komponenta.ident_cely + "_o"
        )

        druh_predmet_choices = heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)
        specifikce_predmetu_choices = list(
            Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE).values_list(
                "id", "heslo"
            )
        )
        NalezPredmetFormset = inlineformset_factory(
            Komponenta,
            NalezPredmet,
            form=create_nalez_predmet_form(
                druh_predmet_choices, specifikce_predmetu_choices
            ),
            extra=1,
        )
        formset_predmet = NalezPredmetFormset(
            request.POST, instance=komponenta, prefix=komponenta.ident_cely + "_p"
        )
        if formset_objekt.is_valid() and formset_predmet.is_valid():
            logger.debug("K.Form is valid:2")
            formset_predmet.save()
            formset_objekt.save()
            if formset_objekt.has_changed() or formset_predmet.has_changed():
                logger.debug("Form data was changed")
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.warning("Form is not valid")
            logger.debug(formset_predmet.errors)
            logger.debug(formset_objekt.errors)
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
            request.session["_old_nalez_post"] = request.POST
            request.session["komp_ident_cely"] = ident_cely

    response = redirect(request.META.get("HTTP_REFERER"))
    response.set_cookie(
        "show-form", f"detail_komponenta_form_{ident_cely}", max_age=1000
    )
    response.set_cookie(
        "set-active", f"el_komponenta_{ident_cely.replace('-', '_')}", max_age=1000
    )
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
        logger.debug("K.Form is valid:3")
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
        response.set_cookie(
            "show-form", f"detail_komponenta_form_{komp_ident_cely}", max_age=1000
        )
        response.set_cookie(
            "set-active",
            f"el_komponenta_{komp_ident_cely.replace('-', '_')}",
            max_age=1000,
        )
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
            response = JsonResponse(
                {
                    "redirect": reverse(
                        "arch_z:detail", kwargs={"ident_cely": arch_z_ident_cely}
                    )
                }
            )
            response.set_cookie("show-form", f"detail_dj_form_{k.komponenta_vazby.dokumentacni_jednotka.ident_cely}",
                               max_age=1000)
            return response
        else:
            logger.warning("Komponenta nebyla smazana: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            response = JsonResponse(
                {
                    "redirect": reverse(
                        "arch_z:detail", kwargs={"ident_cely": arch_z_ident_cely}
                    )
                },
                status=403,
            )
            response.set_cookie("show-form", f"detail_komponenta_form_{ident_cely}", max_age=1000)
            return response
    else:
        context = {
            "object": k,
            "title": _("komponenta.modalForm.smazani.title.text"),
            "id_tag": "smazat-komponenta-form",
            "button": _("komponenta.modalForm.smazani.submit.button"),
        }
        return render(request, "core/transakce_modal.html", context)
