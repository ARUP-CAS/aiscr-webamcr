import logging
from typing import Union

from core.constants import DOKUMENT_CAST_RELATION_TYPE
from core.message_constants import ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_SE_NEPOVEDLO_SMAZAT, ZAZNAM_USPESNE_SMAZAN
from core.repository_connector import FedoraTransaction
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
from dokument.models import Dokument
from heslar.hesla import (
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_DRUH_KAT,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_OBJEKT_SPECIFIKACE_KAT,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_DRUH_KAT,
    HESLAR_PREDMET_SPECIFIKACE,
)
from heslar.views import heslar_12, heslar_list
from komponenta.models import Komponenta
from nalez.forms import create_nalez_objekt_form, create_nalez_predmet_form
from nalez.models import NalezObjekt, NalezPredmet

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def smazat_nalez(request, typ_vazby, typ, ident_cely):
    """
    Funkce pohledu pro smazání nálezu předmětu nebo objektu pomocí modalu.
    """
    if typ == "objekt":
        zaznam = get_object_or_404(NalezObjekt, id=ident_cely)
        context = {
            "object": zaznam,
            "title": _("nalez.views.smazatNalez.objekt.title.text"),
            "id_tag": "smazat-objekt-form",
            "button": _("nalez.views.smazatNalez.objekt.submitButton"),
        }
    elif typ == "predmet":
        zaznam = get_object_or_404(NalezPredmet, id=ident_cely)
        context = {
            "object": zaznam,
            "title": _("nalez.views.smazatNalez.predmet.title.text"),
            "id_tag": "smazat-objekt-form",
            "button": _("nalez.views.smazatNalez.predmet.submitButton"),
        }
    else:
        return
    if request.method == "POST" and zaznam:
        zaznam: Union[NalezObjekt, NalezPredmet]
        zaznam.active_transaction = FedoraTransaction(transaction_user=request.user)
        zaznam.close_active_transaction_when_finished = True
        resp = zaznam.delete()
        next_url = request.POST.get("next")
        if next_url:
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
                response = next_url
            else:
                logger.warning("nalez.views.smazat_nalez.redirect_not_safe", extra={"next_url": next_url})
                response = reverse("core:home")
        else:
            response = reverse("core:home")
        if resp:
            logger.debug("nalez.views.smazat_nalez.deleted", extra={"resp": resp})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            response = JsonResponse({"redirect": response})
        else:
            logger.debug("nalez.views.smazat_nalez.not_deleted", extra={"ident_cely": ident_cely})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            response = JsonResponse({"redirect": response}, status=403)
        response.set_cookie("show-form", f"detail_komponenta_form_{zaznam.komponenta.ident_cely}", max_age=1000)
        return response
    else:
        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["POST"])
def edit_nalez(request, typ_vazby, komp_ident_cely):
    """
    Funkce pohledu pro zapsání editace nálezu předmětu a objektu.
    """
    komponenta: Komponenta = get_object_or_404(Komponenta, ident_cely=komp_ident_cely)
    druh_objekt_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
    specifikace_objekt_choices = heslar_12(HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT)
    NalezObjektFormset = inlineformset_factory(
        Komponenta,
        NalezObjekt,
        form=create_nalez_objekt_form(druh_objekt_choices, specifikace_objekt_choices),
        extra=3,
    )
    formset_objekt = NalezObjektFormset(request.POST, instance=komponenta, prefix=komponenta.ident_cely + "_o")

    druh_predmet_choices = heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)
    specifikce_predmetu_choices = heslar_list(HESLAR_PREDMET_SPECIFIKACE)
    NalezPredmetFormset = inlineformset_factory(
        Komponenta,
        NalezPredmet,
        form=create_nalez_predmet_form(druh_predmet_choices, specifikce_predmetu_choices),
        extra=3,
    )
    formset_predmet = NalezPredmetFormset(request.POST, instance=komponenta, prefix=komponenta.ident_cely + "_p")
    if formset_objekt.is_valid() and formset_predmet.is_valid():
        logger.debug("nalez.views.edit_nalez.form_valid", extra={"typ_vazby": komponenta.komponenta_vazby.typ_vazby})
        formset_predmet.save()
        formset_objekt.save()
        if formset_objekt.has_changed() or formset_predmet.has_changed():
            if komponenta.komponenta_vazby.typ_vazby == DOKUMENT_CAST_RELATION_TYPE:
                navazany_objekt: Dokument = komponenta.komponenta_vazby.casti_dokumentu
                navazany_objekt.active_transaction = FedoraTransaction()
                logger.debug(
                    "nalez.views.edit_nalez.form_valid.save_metadata_dokument",
                    extra={
                        "ident_cely": navazany_objekt.ident_cely,
                        "fedora_transaction": navazany_objekt.active_transaction.uid,
                    },
                )
                navazany_objekt.create_transaction(request.user)
                logger.debug(
                    "nalez.views.edit_nalez.form_valid.save_metadata_dokument",
                    extra={
                        "ident_cely": navazany_objekt.ident_cely,
                        "fedora_transaction": navazany_objekt.active_transaction.uid,
                    },
                )
                navazany_objekt.close_active_transaction_when_finished = True
                navazany_objekt.save()
            logger.debug("Form data was changed")
    else:
        logger.debug(
            "nalez.views.edit_nalez.form_not_valid",
            extra={"formset_predmet_errors": formset_predmet.errors, "formset_objekt_errors": formset_objekt.errors},
        )
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
        request.session["_old_nalez_post"] = request.POST
        request.session["komp_ident_cely"] = komp_ident_cely
    safe_redirect = request.META.get("HTTP_REFERER")
    if url_has_allowed_host_and_scheme(safe_redirect, allowed_hosts=settings.ALLOWED_HOSTS):
        response = redirect(safe_redirect)
    else:
        response = redirect(reverse("core:home"))
    response.set_cookie("show-form", f"detail_komponenta_form_{komp_ident_cely}", max_age=1000)
    response.set_cookie("set-active", f"el_komponenta_{komp_ident_cely.replace('-', '_')}", max_age=1000)
    return response
