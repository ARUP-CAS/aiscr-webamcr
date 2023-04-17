import logging

from core.message_constants import (
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
)
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from heslar.hesla import (
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
from komponenta.models import Komponenta
from nalez.forms import create_nalez_objekt_form, create_nalez_predmet_form
from nalez.models import NalezObjekt, NalezPredmet

logger = logging.getLogger('python-logstash-logger')


@login_required
@require_http_methods(["GET", "POST"])
def smazat_nalez(request, typ, ident_cely):
    if typ == "objekt":
        zaznam = get_object_or_404(NalezObjekt, id=ident_cely)
        context = {
            "object": zaznam,
            "title": _("nalez.modalForm.smazaniObjektu.title.text"),
            "id_tag": "smazat-objekt-form",
            "button": _("nalez.modalForm.smazaniObjektu.submit.button"),
        }
    if typ == "predmet":
        zaznam = get_object_or_404(NalezPredmet, id=ident_cely)
        context = {
            "object": zaznam,
            "title": _("nalez.modalForm.smazaniPredmetu.title.text"),
            "id_tag": "smazat-objekt-form",
            "button": _("nalez.modalForm.smazaniPredmetu.submit.button"),
        }
    if request.method == "POST":
        resp = zaznam.delete()
        next_url = request.POST.get("next")
        if next_url:
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
                response = next_url
            else:
                logger.warning("Redirect to URL " + str(next_url) + " is not safe!!")
                response = reverse("core:home")
        else:
            response = reverse("core:home")
        if resp:
            logger.debug("Objekt dokumentu byl smazan: " + str(resp))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            response = JsonResponse({"redirect": response})
        else:
            logger.warning("Dokument nebyl smazan: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            response = JsonResponse({"redirect": response}, status=403)
        response.set_cookie("show-form", f"detail_komponenta_form_{zaznam.komponenta.ident_cely}", max_age=1000)
        return response
    else:
        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["POST"])
def edit_nalez(request, komp_ident_cely):
    komponenta = get_object_or_404(Komponenta, ident_cely=komp_ident_cely)
    druh_objekt_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
    specifikace_objekt_choices = heslar_12(
        HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT
    )
    NalezObjektFormset = inlineformset_factory(
        Komponenta,
        NalezObjekt,
        form=create_nalez_objekt_form(druh_objekt_choices, specifikace_objekt_choices),
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
        logger.debug("Nalez Form is valid")
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
        request.session["komp_ident_cely"] = komp_ident_cely

    response = redirect(request.META.get("HTTP_REFERER"))
    response.set_cookie(
        "show-form", f"detail_komponenta_form_{komp_ident_cely}", max_age=1000
    )
    response.set_cookie(
        "set-active", f"el_komponenta_{komp_ident_cely.replace('-', '_')}", max_age=1000
    )
    return response
