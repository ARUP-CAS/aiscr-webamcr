import logging
from cacheops import invalidate_model

from arch_z.models import ArcheologickyZaznam, Akce
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
from core.repository_connector import FedoraTransaction
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
from historie.models import Historie
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta, KomponentaAktivita
from nalez.forms import create_nalez_objekt_form, create_nalez_predmet_form
from nalez.models import NalezObjekt, NalezPredmet
from core.constants import DOKUMENTACNI_JEDNOTKA_RELATION_TYPE
from dokument.models import DokumentCast, Dokument

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, typ_vazby, ident_cely):
    """
    Funkce pohledu pro zapsání editace komponenty.
    """
    komponenta = get_object_or_404(Komponenta, ident_cely=ident_cely)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    komponenta: Komponenta
    form = CreateKomponentaForm(
        obdobi_choices,
        areal_choices,
        request.POST,
        instance=komponenta,
        prefix=ident_cely,
    )
    fedora_transcation = FedoraTransaction()
    komponenta.active_transaction = fedora_transcation
    if form.is_valid():
        logger.debug("komponenta.views.detail.form_valid", extra={"ident_cely": ident_cely})
        komponenta = form.save(commit=False)
        komponenta.active_transaction = fedora_transcation
        komponenta.save()
        form.save_m2m()
        invalidate_model(Akce)
        invalidate_model(ArcheologickyZaznam)
        invalidate_model(Dokument)
        invalidate_model(Historie)
        if form.changed_data:
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
    else:
        logger.debug("komponenta.views.detail.not_valid", extra={"errors": form.errors, "ident_cely": ident_cely})
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
            logger.debug("komponenta.views.detail.form_valid_2")
            formset_predmet.save()
            formset_objekt.save()
            if formset_objekt.has_changed() or formset_predmet.has_changed():
                logger.debug("Form data was changed")
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("komponenta.views.detail.form_not_valid_2",
                         extra={"formset_predmet_errors": formset_predmet.errors,
                                "formset_objekt_errors": formset_objekt.errors})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
            request.session["_old_nalez_post"] = request.POST
            request.session["komp_ident_cely"] = ident_cely

    if komponenta.komponenta_vazby.typ_vazby == DOKUMENTACNI_JEDNOTKA_RELATION_TYPE:
        if (
            komponenta.komponenta_vazby.dokumentacni_jednotka.archeologicky_zaznam.typ_zaznamu
            == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
        ):
            url = reverse(
                "arch_z:update-komponenta",
                args=[
                    komponenta.komponenta_vazby.dokumentacni_jednotka.archeologicky_zaznam.ident_cely,
                    komponenta.komponenta_vazby.dokumentacni_jednotka.ident_cely,
                    komponenta.ident_cely,
                ],
            )
        else:
            url = reverse(
                "lokalita:update-komponenta",
                args=[
                    komponenta.komponenta_vazby.dokumentacni_jednotka.archeologicky_zaznam.ident_cely,
                    komponenta.komponenta_vazby.dokumentacni_jednotka.ident_cely,
                    komponenta.ident_cely,
                ],
            )
    else:
        url = reverse(
            "dokument:detail-komponenta",
            args=[
                komponenta.komponenta_vazby.casti_dokumentu.dokument.ident_cely,
                komponenta.ident_cely,
            ],
        )
    response = redirect(url)
    response.set_cookie(
        "show-form", f"detail_komponenta_form_{ident_cely}", max_age=1000
    )
    response.set_cookie(
        "set-active", f"el_komponenta_{ident_cely.replace('-', '_')}", max_age=1000
    )
    komponenta.close_active_transaction_when_finished = True
    komponenta.save()
    return response


@login_required
@require_http_methods(["POST"])
def zapsat(request, typ_vazby, dj_ident_cely):
    """
    Funkce pohledu pro zapsání vytvořeni komponenty.
    """
    dj = None
    cast = None
    if typ_vazby == "dok":
        cast = get_object_or_404(DokumentCast, ident_cely=dj_ident_cely)
    else:
        dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    form = CreateKomponentaForm(obdobi_choices, areal_choices, request.POST)
    komp_ident_cely = None
    if form.is_valid():
        logger.debug("komponenta.views.zapsat.form_valid")
        fedora_transcation = FedoraTransaction()
        komponenta = form.save(commit=False)
        komponenta.active_transaction = fedora_transcation
        try:
            if dj:
                komponenta.ident_cely = get_komponenta_ident(dj.archeologicky_zaznam)
            else:
                komponenta.ident_cely = get_komponenta_ident(cast.dokument)
            komp_ident_cely = komponenta.ident_cely
        except MaximalIdentNumberError:
            messages.add_message(request, messages.ERROR, MAXIMUM_KOMPONENT_DOSAZENO)
        else:
            if dj:
                komponenta.komponenta_vazby = dj.komponenty
            else:
                komponenta.komponenta_vazby = cast.komponenty
            komponenta.close_active_transaction_when_finished = True
            komponenta.save()
            form.save_m2m()  # this must be called to store komponenta_aktivity

            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
        if dj:
            if (
                dj.archeologicky_zaznam.typ_zaznamu
                == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            ):
                url = reverse(
                    "arch_z:update-komponenta",
                    args=[
                        dj.archeologicky_zaznam.ident_cely,
                        dj.ident_cely,
                        komponenta.ident_cely,
                    ],
                )
            else:
                url = reverse(
                    "lokalita:update-komponenta",
                    args=[
                        dj.archeologicky_zaznam.ident_cely,
                        dj.ident_cely,
                        komponenta.ident_cely,
                    ],
                )
        else:
            url = reverse(
                "dokument:detail-komponenta",
                args=[cast.dokument.ident_cely, komponenta.ident_cely],
            )
    else:
        logger.debug("komponenta.views.zapsat.form_not_valid", extra={"formset_errors": form.errors})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)
        if dj:
            url = reverse(
                "arch_z:create-komponenta",
                args=[dj.archeologicky_zaznam.ident_cely, dj.ident_cely],
            )
        else:
            url = reverse(
                "dokument:create-komponenta",
                args=[cast.dokument.ident_cely, cast.ident_cely],
            )
    response = redirect(url)
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
def smazat(request, typ_vazby, ident_cely):
    """
    Funkce pohledu pro smazání komponenty pomoci modalu.
    """
    komponenta = get_object_or_404(Komponenta, ident_cely=ident_cely)
    dj = None
    cast = None
    if komponenta.komponenta_vazby.typ_vazby == DOKUMENTACNI_JEDNOTKA_RELATION_TYPE:
        dj = komponenta.komponenta_vazby.dokumentacni_jednotka
    else:
        cast = komponenta.komponenta_vazby.casti_dokumentu
    if request.method == "POST":
        fedora_transaction = FedoraTransaction()
        komponenta.active_transaction = fedora_transaction
        komponenta.close_active_transaction_when_finished = True
        resp = komponenta.delete()

        if resp:
            logger.debug("komponenta.views.smazat.resp", extra={"resp": resp})
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            if dj:
                response = JsonResponse({"redirect": dj.get_absolute_url()})
                response.set_cookie(
                    "show-form",
                    f"detail_dj_form_{dj.ident_cely}",
                    max_age=1000,
                )
            else:
                response = JsonResponse(
                    {
                        "redirect": reverse(
                            "dokument:detail-cast",
                            args=[
                                cast.dokument.ident_cely,
                                cast.ident_cely,
                            ],
                        )
                    }
                )
            return response
        else:
            logger.warning("komponenta.views.smazat.not_deleted", extra={"ident_cely": ident_cely})
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            if dj:
                response = JsonResponse(
                    {"redirect": dj.get_absolute_url()},
                    status=403,
                )
                response.set_cookie(
                    "show-form", f"detail_komponenta_form_{ident_cely}", max_age=1000
                )
            else:
                response = JsonResponse(
                    {
                        "redirect": reverse(
                            "dokument:detail-komponenta",
                            args=[
                                cast.dokument.ident_cely,
                                komponenta.ident_cely,
                            ],
                        )
                    }
                )
            return response
    else:
        context = {
            "object": komponenta,
            "title": _("komponenta.views..smazat.title.text"),
            "id_tag": "smazat-komponenta-form",
            "button": _("komponenta.views.smazat.submitButton.text"),
        }
        return render(request, "core/transakce_modal.html", context)
