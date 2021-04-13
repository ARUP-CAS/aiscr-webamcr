import logging

from arch_z.forms import CreateAkceForm, CreateArchZForm, VratitAkciForm
from arch_z.models import Akce, ArcheologickyZaznam
from core.constants import (
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_UZAVRENY,
)
from core.ident_cely import get_project_event_ident
from core.message_constants import (
    AKCE_USPESNE_ARCHIVOVANA,
    AKCE_USPESNE_ODESLANA,
    AKCE_USPESNE_VRACENA,
    AKCE_USPESNE_ZAPSANA,
    AKCI_NELZE_ARCHIVOVAT,
    AKCI_NELZE_ODESLAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
)
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from dokument.models import Dokument
from heslar.hesla import SPECIFIKACE_DATA_PRESNE
from heslar.models import Heslar
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta
from nalez.forms import CreateNalezObjektForm, NalezFormSetHelper
from nalez.models import NalezObjekt
from projekt.models import Projekt

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    zaznam = (
        ArcheologickyZaznam.objects.select_related("hlavni_katastr")
        .select_related("akce__vedlejsi_typ")
        .select_related("akce__hlavni_typ")
        .select_related("pristupnost")
        .get(ident_cely=ident_cely)
    )
    # TODO continue here
    dokumenty = (
        Dokument.objects.filter(
            dokumentcast__archeologicky_zaznam__ident_cely=ident_cely
        )
        .select_related("soubory")
        .prefetch_related("soubory__soubory")
    )
    jednotky = (
        DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely=ident_cely)
        .select_related("komponenty")
        .prefetch_related("komponenty__komponenty")
    )

    dj_form_create = CreateDJForm()
    komponenta_form_create = CreateKomponentaForm()
    dj_forms_detail = []
    komponenta_forms_detail = []
    NalezObjektFormset = inlineformset_factory(
        Komponenta, NalezObjekt, form=CreateNalezObjektForm, extra=1
    )
    for jednotka in jednotky:
        dj_forms_detail.append(
            {"ident_cely": jednotka.ident_cely, "form": CreateDJForm(instance=jednotka)}
        )
        for komponenta in jednotka.komponenty.komponenty.all():
            komponenta_forms_detail.append(
                {
                    "ident_cely": komponenta.ident_cely,
                    "form": CreateKomponentaForm(instance=komponenta),
                    "form_nalezy": NalezObjektFormset(instance=komponenta),
                    "helper": NalezFormSetHelper(),
                }
            )

    context["dj_form_create"] = dj_form_create
    context["dj_forms_detail"] = dj_forms_detail
    context["komponenta_form_create"] = komponenta_form_create
    context["komponenta_forms_detail"] = komponenta_forms_detail

    context["zaznam"] = zaznam
    context["dokumenty"] = dokumenty
    context["dokumentacni_jednotky"] = jednotky
    context["show"] = get_detail_template_shows(zaznam)

    return render(request, "arch_z/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    zaznam = ArcheologickyZaznam.objects.get(ident_cely=ident_cely)
    if request.method == "POST":
        form_az = CreateArchZForm(request.POST, instance=zaznam)
        form_akce = CreateAkceForm(request.POST, instance=zaznam.akce)

        if form_az.is_valid() and form_akce.is_valid():
            logger.debug("Form is valid")
            form_az.save()
            form_akce.save()
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.warning("Form is not valid")
            logger.debug(form_az.errors)
            logger.debug(form_akce.errors)
    else:
        form_az = CreateArchZForm(instance=zaznam)
        form_akce = CreateAkceForm(instance=zaznam.akce)

    return render(
        request, "arch_z/edit.html", {"formAZ": form_az, "formAkce": form_akce}
    )


@login_required
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ZAPSANY:
        raise PermissionDenied()
    if request.method == "POST":
        az.set_odeslany(request.user)
        az.save()
        messages.add_message(request, messages.SUCCESS, AKCE_USPESNE_ODESLANA)
        return redirect("/arch_z/detail/" + ident_cely)
    else:
        warnings = az.akce.check_pred_odeslanim()
        logger.debug(warnings)
        context = {"object": az}
        if warnings:
            context["warnings"] = warnings
            messages.add_message(request, messages.ERROR, AKCI_NELZE_ODESLAT)
        else:
            pass
    return render(request, "arch_z/odeslat.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ODESLANY:
        raise PermissionDenied()
    if request.method == "POST":
        # TODO BR-A-5
        az.set_archivovany(request.user)
        az.save()
        messages.add_message(request, messages.SUCCESS, AKCE_USPESNE_ARCHIVOVANA)
        return redirect("/arch_z/detail/" + ident_cely)
    else:
        warnings = az.akce.check_pred_archivaci()
        logger.debug(warnings)
        context = {"object": az}
        if warnings:
            context["warnings"] = warnings
            messages.add_message(request, messages.ERROR, AKCI_NELZE_ARCHIVOVAT)
        else:
            pass
    return render(request, "arch_z/archivovat.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ODESLANY and az.stav != AZ_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    if request.method == "POST":
        form = VratitAkciForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            projekt = az.akce.projekt
            # BR-A-3
            if az.stav == AZ_STAV_ODESLANY and projekt is not None:
                #  Return also project from the states P6 or P5 to P4
                projekt_stav = projekt.stav
                if projekt_stav == PROJEKT_STAV_UZAVRENY:
                    logger.debug(
                        "Automaticky vracím projekt do stavu " + str(projekt_stav - 1)
                    )
                    projekt.set_vracen(
                        request.user, projekt_stav - 1, "Automatické vrácení projektu"
                    )
                    projekt.save()
                if projekt_stav == PROJEKT_STAV_ARCHIVOVANY:
                    logger.debug(
                        "Automaticky vracím projekt do stavu " + str(projekt_stav - 2)
                    )
                    projekt.set_vracen(
                        request.user, projekt_stav - 1, "Automatické vrácení projektu"
                    )
                    projekt.save()
                    projekt.set_vracen(
                        request.user, projekt_stav - 2, "Automatické vrácení projektu"
                    )
                    projekt.save()
            az.set_vraceny(request.user, az.stav - 1, duvod)
            az.save()
            messages.add_message(request, messages.SUCCESS, AKCE_USPESNE_VRACENA)
            return redirect("/arch_z/detail/" + ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitAkciForm()
    return render(request, "arch_z/vratit.html", {"form": form, "zaznam": az})


@login_required
@require_http_methods(["GET", "POST"])
def zapsat(request, projekt_ident_cely):
    projekt = Projekt.objects.get(ident_cely=projekt_ident_cely)
    if request.method == "POST":
        form_az = CreateArchZForm(request.POST)
        form_akce = CreateAkceForm(request.POST)

        if form_az.is_valid() and form_akce.is_valid():
            logger.debug("Form is valid")
            az = form_az.save(commit=False)
            az.stav = AZ_STAV_ZAPSANY
            az.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            az.ident_cely = get_project_event_ident(projekt)
            az.save()
            form_az.save_m2m()  # This must be called to save many to many (katastry) since we are doing commit = False
            az.set_zapsany(request.user)
            akce = form_akce.save(commit=False)
            akce.specifikace_data = Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
            akce.archeologicky_zaznam = az
            akce.projekt = projekt
            akce.save()

            messages.add_message(request, messages.SUCCESS, AKCE_USPESNE_ZAPSANA)
            return redirect("/arch_z/detail/" + az.ident_cely)

        else:
            logger.warning("Form is not valid")
            logger.debug(form_az.errors)
            logger.debug(form_akce.errors)

    else:
        form_az = CreateArchZForm()
        form_akce = CreateAkceForm()

    return render(
        request, "arch_z/create.html", {"formAZ": form_az, "formAkce": form_akce}
    )


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    akce = Akce.objects.get(archeologicky_zaznam__ident_cely=ident_cely)
    projekt = akce.projekt
    if request.method == "POST":
        az = akce.archeologicky_zaznam
        # Parent records
        historie_vazby = az.historie
        komponenty_jednotek_vazby = []
        for dj in az.dokumentacnijednotka_set.all():
            if dj.komponenty:
                komponenty_jednotek_vazby.append(dj.komponenty)
        az.delete()

        historie_vazby.delete()
        historie_vazby.delete()
        for komponenta_vazba in komponenty_jednotek_vazby:
            komponenta_vazba.delete()

        logger.debug("Byla smazána akce: " + str(ident_cely))
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)

        if projekt:
            return redirect("/projekt/detail/" + projekt.ident_cely)
        else:
            return redirect("/")
    else:
        return render(request, "arch_z/smazat.html", {"akce": akce})


@login_required
@require_http_methods(["GET", "POST"])
def pripojit_dokument(request, ident_cely):
    # TODO add implementation
    return None


def get_detail_template_shows(archeologicky_zaznam):
    show_vratit = archeologicky_zaznam.stav > AZ_STAV_ZAPSANY
    show_odeslat = archeologicky_zaznam.stav == AZ_STAV_ZAPSANY
    show_archivovat = archeologicky_zaznam.stav == AZ_STAV_ODESLANY
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "archivovat_link": show_archivovat,
    }
    return show
