import logging

import simplejson as json
from adb.forms import CreateADBForm, VyskovyBodFormSetHelper, create_vyskovy_bod_form
from adb.models import Adb, VyskovyBod
from arch_z.forms import (
    AkceVedouciFormSetHelper,
    CreateAkceForm,
    CreateArchZForm,
    create_akce_vedouci_objekt_form
)
from arch_z.models import Akce, AkceVedouci, ArcheologickyZaznam
from core.constants import (
    ARCHIVACE_AZ,
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    ODESLANI_AZ,
    PIAN_NEPOTVRZEN,
    PIAN_POTVRZEN,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAPSANY,
    ZAPSANI_AZ,
)
from core.exceptions import MaximalEventCount
from core.forms import VratitForm, CheckStavNotChangedForm
from core.ident_cely import get_cast_dokumentu_ident, get_project_event_ident
from core.message_constants import (
    AKCE_USPESNE_ARCHIVOVANA,
    AKCE_USPESNE_ODESLANA,
    AKCE_USPESNE_VRACENA,
    AKCE_USPESNE_ZAPSANA,
    AKCI_NELZE_ARCHIVOVAT,
    AKCI_NELZE_ODESLAT,
    MAXIMUM_AKCII_DOSAZENO,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    PRISTUP_ZAKAZAN,
)
from core.utils import get_all_pians_with_dj, get_centre_from_akce
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from dokument.views import odpojit, pripojit
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.translation import gettext as _
from django.utils.html import format_html, mark_safe
from django.views.decorators.http import require_http_methods
from dokument.models import Dokument, DokumentCast
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
    SPECIFIKACE_DATA_PRESNE,
    TYP_DJ_SONDA_ID,
    TYP_PROJEKTU_PRUZKUM_ID,
)
from heslar.models import Heslar
from heslar.views import heslar_12
from komponenta.forms import CreateKomponentaForm
from komponenta.models import Komponenta
from nalez.forms import (
    NalezFormSetHelper,
    create_nalez_objekt_form,
    create_nalez_predmet_form,
)
from nalez.models import NalezObjekt, NalezPredmet
from pian.forms import PianCreateForm
from projekt.models import Projekt
from core.views import check_stav_changed

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {
        "warnings": request.session.pop("temp_data", None),
        "arch_projekt_link": request.session.pop("arch_projekt_link", None),
    }
    old_nalez_post = request.session.pop("_old_nalez_post", None)
    komp_ident_cely = request.session.pop("komp_ident_cely", None)
    old_adb_post = request.session.pop("_old_adb_post", None)
    adb_ident_cely = request.session.pop("adb_ident_cely", None)
    zaznam = get_object_or_404(
        ArcheologickyZaznam.objects.select_related("hlavni_katastr")
        .select_related("akce__vedlejsi_typ")
        .select_related("akce__hlavni_typ")
        .select_related("pristupnost"),
        ident_cely=ident_cely,
    )
    show = get_detail_template_shows(zaznam)
    obdobi_choices = heslar_12(HESLAR_OBDOBI, HESLAR_OBDOBI_KAT)
    areal_choices = heslar_12(HESLAR_AREAL, HESLAR_AREAL_KAT)
    druh_objekt_choices = heslar_12(HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_DRUH_KAT)
    druh_predmet_choices = heslar_12(HESLAR_PREDMET_DRUH, HESLAR_PREDMET_DRUH_KAT)
    specifikace_objekt_choices = heslar_12(
        HESLAR_OBJEKT_SPECIFIKACE, HESLAR_OBJEKT_SPECIFIKACE_KAT
    )
    specifikce_predmetu_choices = list(
        Heslar.objects.filter(nazev_heslare=HESLAR_PREDMET_SPECIFIKACE).values_list(
            "id", "heslo"
        )
    )
    dokumenty = (
        Dokument.objects.filter(casti__archeologicky_zaznam__ident_cely=ident_cely)
        .select_related("soubory")
        .prefetch_related("soubory__soubory")
    ).order_by("ident_cely")
    jednotky = (
        DokumentacniJednotka.objects.filter(archeologicky_zaznam__ident_cely=ident_cely)
        .select_related("komponenty", "typ", "pian")
        .prefetch_related(
            "komponenty__komponenty",
            "komponenty__komponenty__aktivity",
            "komponenty__komponenty__obdobi",
            "komponenty__komponenty__areal",
            "komponenty__komponenty__objekty",
            "komponenty__komponenty__predmety",
            "adb",
        )
    )

    dj_form_create = CreateDJForm(jednotky=jednotky)
    pian_form_create = PianCreateForm()
    komponenta_form_create = CreateKomponentaForm(obdobi_choices, areal_choices)
    adb_form_create = CreateADBForm()
    dj_forms_detail = []
    komponenta_forms_detail = []
    pian_forms_detail = []
    NalezObjektFormset = inlineformset_factory(
        Komponenta,
        NalezObjekt,
        form=create_nalez_objekt_form(
            druh_objekt_choices,
            specifikace_objekt_choices,
            not_readonly=show["editovat"],
        ),
        extra=1 if show["editovat"] else 0,
        can_delete=False,
    )
    NalezPredmetFormset = inlineformset_factory(
        Komponenta,
        NalezPredmet,
        form=create_nalez_predmet_form(
            druh_predmet_choices,
            specifikce_predmetu_choices,
            not_readonly=show["editovat"],
        ),
        extra=1 if show["editovat"] else 0,
        can_delete=False,
    )
    ostatni_vedouci_objekt_formset = inlineformset_factory(
        Akce,
        AkceVedouci,
        form=create_akce_vedouci_objekt_form(
            readonly=True
        ),
        extra=0,
        can_delete=False,
    )
    ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
        None,
        instance=zaznam.akce,
        prefix="",
    )
    for jednotka in jednotky:
        jednotka: DokumentacniJednotka
        vyskovy_bod_formset = inlineformset_factory(
            Adb,
            VyskovyBod,
            form=create_vyskovy_bod_form(pian=jednotka.pian),
            extra=1,
        )
        has_adb = jednotka.has_adb()
        show_adb_add = (
            jednotka.pian
            and jednotka.typ.id == TYP_DJ_SONDA_ID
            and not has_adb
            and show["editovat"]
        )
        show_add_komponenta = not jednotka.negativni_jednotka and show["editovat"]
        show_add_pian = False if jednotka.pian else True
        show_approve_pian = (
            True
            if jednotka.pian
            and jednotka.pian.stav == PIAN_NEPOTVRZEN
            and show["editovat"]
            else False
        )
        dj_form_detail = {
            "ident_cely": jednotka.ident_cely,
            "pian_ident_cely": jednotka.pian.ident_cely if jednotka.pian else "",
            "form": CreateDJForm(
                instance=jednotka,
                jednotky=jednotky,
                prefix=jednotka.ident_cely,
                not_readonly=show["editovat"],
                pian_potvrzen=True if jednotka.pian and jednotka.pian.stav==PIAN_POTVRZEN else False
            ),
            "show_add_adb": show_adb_add,
            "show_add_komponenta": show_add_komponenta,
            "show_add_pian": (show_add_pian and show["editovat"]),
            "show_remove_pian": (not show_add_pian and show["editovat"]),
            "show_uprav_pian": jednotka.pian
            and jednotka.pian.stav == PIAN_NEPOTVRZEN
            and show["editovat"],
            "show_approve_pian": show_approve_pian,
            "show_pripojit_pian": True if jednotka.pian and jednotka.pian.stav==PIAN_POTVRZEN else False
        }
        if has_adb:
            logger.debug(jednotka.ident_cely)
            dj_form_detail["adb_form"] = (
                CreateADBForm(
                    old_adb_post, instance=jednotka.adb, prefix=jednotka.adb.ident_cely
                )
                if jednotka.adb.ident_cely == adb_ident_cely
                else CreateADBForm(
                    instance=jednotka.adb, prefix=jednotka.adb.ident_cely
                )
            )
            dj_form_detail["adb_ident_cely"] = jednotka.adb.ident_cely
            dj_form_detail["vyskovy_bod_formset"] = vyskovy_bod_formset(
                instance=jednotka.adb, prefix=jednotka.adb.ident_cely + "_vb"
            )
            dj_form_detail["vyskovy_bod_formset_helper"] = VyskovyBodFormSetHelper()
            dj_form_detail["show_remove_adb"] = True if show["editovat"] else False
        dj_forms_detail.append(dj_form_detail)
        if jednotka.pian:
            pian_forms_detail.append(
                {
                    "ident_cely": jednotka.pian.ident_cely,
                    "center_point": "",
                    "form": PianCreateForm(
                        instance=jednotka.pian, prefix=jednotka.pian.ident_cely
                    ),
                }
            )
        for komponenta in jednotka.komponenty.komponenty.all():
            komponenta_forms_detail.append(
                {
                    "ident_cely": komponenta.ident_cely,
                    "form": CreateKomponentaForm(
                        obdobi_choices,
                        areal_choices,
                        instance=komponenta,
                        prefix=komponenta.ident_cely,
                        readonly=not show["editovat"],
                    ),
                    "form_nalezy_objekty": NalezObjektFormset(
                        old_nalez_post,
                        instance=komponenta,
                        prefix=komponenta.ident_cely + "_o",
                    )
                    if komponenta.ident_cely == komp_ident_cely
                    else NalezObjektFormset(
                        instance=komponenta, prefix=komponenta.ident_cely + "_o"
                    ),
                    "form_nalezy_predmety": NalezPredmetFormset(
                        old_nalez_post,
                        instance=komponenta,
                        prefix=komponenta.ident_cely + "_p",
                    )
                    if komponenta.ident_cely == komp_ident_cely
                    else NalezPredmetFormset(
                        instance=komponenta, prefix=komponenta.ident_cely + "_p"
                    ),
                    "helper": NalezFormSetHelper(),
                }
            )

    context["dj_form_create"] = dj_form_create
    context["pian_form_create"] = pian_form_create
    context["ostatni_vedouci_objekt_formset"] = ostatni_vedouci_objekt_formset
    context["ostatni_vedouci_objekt_formset_helper"] = AkceVedouciFormSetHelper()
    context["ostatni_vedouci_objekt_formset_readonly"] = True
    context["dj_forms_detail"] = dj_forms_detail
    context["adb_form_create"] = adb_form_create
    context["komponenta_form_create"] = komponenta_form_create
    context["komponenta_forms_detail"] = komponenta_forms_detail
    context["pian_forms_detail"] = pian_forms_detail

    context["history_dates"] = get_history_dates(zaznam.historie)
    context["zaznam"] = zaznam
    context["dokumenty"] = dokumenty
    context["dokumentacni_jednotky"] = jednotky
    context["show"] = show

    return render(request, "arch_z/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    zaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if zaznam.stav == AZ_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    required_fields = get_required_fields(zaznam)
    required_fields_next = get_required_fields(zaznam,1)
    if request.method == "POST":
        form_az = CreateArchZForm(
            request.POST,
            instance=zaznam
            )
        form_akce = CreateAkceForm(
            request.POST,
            instance=zaznam.akce,
            required=required_fields,
            required_next=required_fields_next
            )

        ostatni_vedouci_objekt_formset = inlineformset_factory(
            Akce,
            AkceVedouci,
            form=create_akce_vedouci_objekt_form(
            ),
            extra=1,
            can_delete=True,
        )
        ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
            request.POST,
            instance=zaznam.akce,
            prefix="_osv",
        )

        if form_az.is_valid() and form_akce.is_valid() and ostatni_vedouci_objekt_formset.is_valid():
            logger.debug("Form is valid")
            form_az.save()
            form_akce.save()
            ostatni_vedouci_objekt_formset.save()
            if form_az.changed_data or form_akce.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("arch_z:detail", ident_cely=ident_cely)
        else:
            logger.warning("Form is not valid")
            logger.debug(form_az.errors)
            logger.debug(form_akce.errors)
    else:
        form_az = CreateArchZForm(instance=zaznam)
        form_akce = CreateAkceForm(
            instance=zaznam.akce,
            required=required_fields,
            required_next=required_fields_next
            )
        ostatni_vedouci_objekt_formset = inlineformset_factory(
            Akce,
            AkceVedouci,
            form=create_akce_vedouci_objekt_form(
                readonly=False
            ),
            extra=1,
            can_delete=False,
        )
        ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
            None,
            instance=zaznam.akce,
            prefix="_osv",
        )

    return render(
        request,
        "arch_z/create.html",
        {
            "formAZ": form_az,
            "formAkce": form_akce,
            "ostatni_vedouci_objekt_formset": ostatni_vedouci_objekt_formset,
            "ostatni_vedouci_objekt_formset_helper": AkceVedouciFormSetHelper(),
            "ostatni_vedouci_objekt_formset_readonly": False,
            "title": _("Editace archeologického záznamu"),
            "header": _("Archeologický záznam"),
            "button": _("Uložit změny"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    logger.debug("arch_z.views.odeslat start")
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ZAPSANY:
        logger.debug("arch_z.views.odeslat permission denied")
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect":reverse("projekt:detail", kwargs={'ident_cely':ident_cely})},status=403)
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, az):
        logger.debug("arch_z.views.odeslat redirec to arch_z:detail")
        return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})},status=403)
    if request.method == "POST":
        az.set_odeslany(request.user)
        az.save()
        messages.add_message(request, messages.SUCCESS, AKCE_USPESNE_ODESLANA)
        logger.debug("arch_z.views.odeslat akce uspesne odeslana " + AKCE_USPESNE_ODESLANA)
        return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})})
    else:
        warnings = az.akce.check_pred_odeslanim()
        logger.debug("arch_z.views.odeslat warnings " + ident_cely + " " + str(warnings))
        
        if warnings:
            request.session['temp_data'] = warnings
            messages.add_message(request, messages.ERROR, AKCI_NELZE_ODESLAT)
            logger.debug("arch_z.views.odeslat akci nelze odeslat " + AKCI_NELZE_ODESLAT)
            return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})},status=403)
    form_check = CheckStavNotChangedForm(initial={"old_stav":az.stav})
    context = {
        "object": az,
        "title": _("arch_z.modalForm.odeslatArchz.title.text"),
        "id_tag": "odeslat-akci-form",
        "button": _("arch_z.modalForm.odeslatArchz.submit.button"),
        "form_check": form_check
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ODESLANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})},status=403)
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, az):
        return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})},status=403)
    if request.method == "POST":
        # TODO BR-A-5
        az.set_archivovany(request.user)
        az.save()
        all_akce = Akce.objects.filter(projekt=az.akce.projekt).exclude(archeologicky_zaznam__stav=AZ_STAV_ARCHIVOVANY)  
        if not all_akce and az.akce.projekt.stav == PROJEKT_STAV_UZAVRENY:
            request.session['arch_projekt_link'] = True
        messages.add_message(request, messages.SUCCESS, AKCE_USPESNE_ARCHIVOVANA)
        return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})})
    else:
        warnings = az.akce.check_pred_archivaci()
        logger.debug(warnings)
        if warnings:
            request.session['temp_data'] = warnings
            messages.add_message(request, messages.ERROR, AKCI_NELZE_ARCHIVOVAT)
            return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})},status=403)
    form_check = CheckStavNotChangedForm(initial={"old_stav":az.stav})
    context = {
        "object": az,
        "title": _("arch_z.modalForm.archivovatArchz.title.text"),
        "id_tag": "archivovat-akci-form",
        "button": _("arch_z.modalForm.archivovatArchz.submit.button"),
        "form_check": form_check,
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ODESLANY and az.stav != AZ_STAV_ARCHIVOVANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})},status=403)
    if check_stav_changed(request, az):
        return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})},status=403)
    if request.method == "POST":
        form = VratitForm(request.POST)
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
            return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})})
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitForm(initial={"old_stav":az.stav})
    context = {
        "object": az,
        "form": form,
        "title": _("arch_z.modalForm.vratitArchz.title.text"),
        "id_tag": "vratit-akci-form",
        "button": _("arch_z.modalForm.vratitArchz.submit.button"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def zapsat(request, projekt_ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=projekt_ident_cely)

    # Projektove akce lze pridavat pouze pokud je projekt jiz prihlasen
    if not PROJEKT_STAV_ZAPSANY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY:
        logger.debug(
            "arch_z.views.zapsat: "
            f"Status of project {projekt_ident_cely} is {projekt.stav} and action cannot be added."
        )
        raise PermissionDenied(
            "Nelze pridat akci k projektu ve stavu " + str(projekt.stav)
        )
    # Projektove akce nelze vytvorit pro projekt typu pruzkum
    if projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID:
        logger.debug(
            "arch_z.views.zapsat: "
            f"Type of project {projekt_ident_cely} is {projekt.typ_projektu} and action cannot be added."
        )
        raise PermissionDenied(
            f"Nelze pridat akci k projektu typu {projekt.typ_projektu}"
        )
    required_fields = get_required_fields()
    required_fields_next = get_required_fields(next=1)
    if request.method == "POST":
        form_az = CreateArchZForm(request.POST)
        form_akce = CreateAkceForm(
            request.POST,
            required=required_fields,
            required_next=required_fields_next
            )
        ostatni_vedouci_objekt_formset = inlineformset_factory(
            Akce,
            AkceVedouci,
            form=create_akce_vedouci_objekt_form(
                readonly=False
            ),
            extra=1,
            can_delete=False,
        )
        ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
            request.POST,
            instance=None,
            prefix="_osv",
        )
        if form_az.is_valid() and form_akce.is_valid() and ostatni_vedouci_objekt_formset.is_valid():
            logger.debug("Form is valid")
            az = form_az.save(commit=False)
            az.stav = AZ_STAV_ZAPSANY
            az.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            try:
                az.ident_cely = get_project_event_ident(projekt)
            except MaximalEventCount:
                messages.add_message(request, messages.ERROR, MAXIMUM_AKCII_DOSAZENO)
            else:
                az.save()
                form_az.save_m2m()  # This must be called to save many to many (katastry) since we are doing commit = False
                az.set_zapsany(request.user)
                akce = form_akce.save(commit=False)
                akce.specifikace_data = Heslar.objects.get(id=SPECIFIKACE_DATA_PRESNE)
                akce.archeologicky_zaznam = az
                akce.projekt = projekt
                akce.save()

                ostatni_vedouci_objekt_formset = inlineformset_factory(
                    Akce,
                    AkceVedouci,
                    form=create_akce_vedouci_objekt_form(
                        readonly=False
                    ),
                    extra=1,
                    can_delete=False,
                )
                ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
                    request.POST,
                    instance=akce,
                    prefix="_osv",
                )
                if ostatni_vedouci_objekt_formset.is_valid():
                    ostatni_vedouci_objekt_formset.save()
                else:
                    logger.warning("arch_z.views.zapsat: " "Form is not valid")
                    logger.debug(ostatni_vedouci_objekt_formset.errors)

                messages.add_message(request, messages.SUCCESS, AKCE_USPESNE_ZAPSANA)
                logger.debug(f"arch_z.views.zapsat: {AKCE_USPESNE_ZAPSANA}, ID akce: {akce.pk}, "
                             f"projekt: {projekt_ident_cely}")
                return redirect("arch_z:detail", az.ident_cely)

        else:
            logger.warning("arch_z.views.zapsat: " "Form is not valid")
            logger.debug(form_az.errors)
            logger.debug(form_akce.errors)

    else:
        ostatni_vedouci_objekt_formset = inlineformset_factory(
            Akce,
            AkceVedouci,
            form=create_akce_vedouci_objekt_form(
                readonly=False
            ),
            extra=1,
            can_delete=False,
        )
        ostatni_vedouci_objekt_formset = ostatni_vedouci_objekt_formset(
            None,
            instance=None,
            prefix="_osv",
        )
        form_az = CreateArchZForm(projekt=projekt)
        form_akce = CreateAkceForm(
            uzamknout_specifikace=True,
            projekt=projekt,
            required=required_fields,
            required_next=required_fields_next
            )

    return render(
        request,
        "arch_z/create.html",
        {
            "formAZ": form_az,
            "formAkce": form_akce,
            "ostatni_vedouci_objekt_formset": ostatni_vedouci_objekt_formset,
            "ostatni_vedouci_objekt_formset_helper": AkceVedouciFormSetHelper(),
            "title": _("Nová projektová akce"),
            "header": _("Nová projektová akce"),
            "button": _("Vytvoř akci"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    akce = get_object_or_404(Akce, archeologicky_zaznam__ident_cely=ident_cely)
    if check_stav_changed(request, akce.archeologicky_zaznam):
        return JsonResponse({"redirect":reverse("arch_z:detail", kwargs={'ident_cely':ident_cely})},status=403)
    projekt = akce.projekt
    if request.method == "POST":
        az = akce.archeologicky_zaznam
        # Parent records
        historie_vazby = az.historie
        komponenty_jednotek_vazby = []
        for dj in az.dokumentacni_jednotky_akce.all():
            if dj.komponenty:
                komponenty_jednotek_vazby.append(dj.komponenty)
        az.delete()
        historie_vazby.delete()
        for komponenta_vazba in komponenty_jednotek_vazby:
            komponenta_vazba.delete()

        logger.debug("Byla smazána akce: " + str(ident_cely))
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)

        if projekt:
            return JsonResponse({"redirect":reverse("projekt:detail", kwargs={'ident_cely':projekt.ident_cely})})
        else:
            return JsonResponse({"redirect":reverse("index")})
    else:
        form_check = CheckStavNotChangedForm(initial={"old_stav":akce.archeologicky_zaznam.stav})
        context = {
        "object": akce,
        "title": _("arch_z.modalForm.smazani.title.text"),
        "id_tag": "smazat-akci-form",
        "button": _("arch_z.modalForm.smazani.submit.button"),
        "form_check": form_check,
        }
        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def pripojit_dokument(
    request, arch_z_ident_cely, proj_ident_cely=None
):  
    return pripojit(request, arch_z_ident_cely, proj_ident_cely, ArcheologickyZaznam)


@login_required
@require_http_methods(["GET", "POST"])
def odpojit_dokument(request, ident_cely, arch_z_ident_cely):
    return odpojit (request, ident_cely, arch_z_ident_cely, "arch_z")


def get_history_dates(historie_vazby):
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_AZ),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_AZ),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_AZ),
    }
    return historie


@login_required
@require_http_methods(["POST"])
def post_ajax_get_pians(request):
    body = json.loads(request.body.decode("utf-8"))
    pians = get_all_pians_with_dj(body["dj_ident_cely"], body["lat"], body["lng"])
    back = []
    for pian in pians:
        # logger.debug('%s %s %s',projekt.ident_cely,projekt.lat,projekt.lng)
        back.append(
            {
                "id": pian.id,
                "ident_cely": pian.ident_cely,
                "geom": pian.geometry.replace(", ", ","),
                "dj": pian.dj,
            }
        )
    if len(pians) > 0:
        return JsonResponse({"points": back}, status=200)
    else:
        return JsonResponse({"points": []}, status=200)


@require_http_methods(["POST"])
def post_akce2kat(request):
    body = json.loads(request.body.decode("utf-8"))
    logger.debug(body)
    katastr_name = body["cadastre"]
    pian_ident_cely = body["pian"]

    if len(katastr_name) > 0:
        [poi, geom] = get_centre_from_akce(katastr_name, pian_ident_cely)
        if len(str(poi)) > 0:
            return JsonResponse(
                {
                    "lat": str(poi.lat),
                    "lng": str(poi.lng),
                    "zoom": str(poi.zoom),
                    "geom": str(geom).split(";")[1].replace(", ", ",")
                    if geom
                    else None,
                },
                status=200,
            )
    return JsonResponse({"lat": "", "lng": "", "zoom": "", "geom": ""}, status=200)

def get_history_dates(historie_vazby):
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_AZ),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_AZ),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_AZ),
    }
    return historie


def get_detail_template_shows(archeologicky_zaznam):
    show_vratit = archeologicky_zaznam.stav > AZ_STAV_ZAPSANY
    show_odeslat = archeologicky_zaznam.stav == AZ_STAV_ZAPSANY
    show_archivovat = archeologicky_zaznam.stav == AZ_STAV_ODESLANY
    show_edit = archeologicky_zaznam.stav not in [
        AZ_STAV_ARCHIVOVANY,
    ]
    show_arch_links = archeologicky_zaznam.stav == AZ_STAV_ARCHIVOVANY
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "archivovat_link": show_archivovat,
        "editovat": show_edit,
        "arch_links": show_arch_links,
    }
    return show

def get_required_fields(zaznam=None,next=0):
    required_fields = []
    if zaznam:
        stav = zaznam.stav
    else:
        stav=1
    if stav >= AZ_STAV_ZAPSANY-next:
        required_fields = [
            
        ]
    if stav > AZ_STAV_ZAPSANY-next:
        required_fields += [
            "hlavni_vedouci",
            "organizace",
            "datum_ukonceni",
            "lokalizace_okolnosti",
            "hlavni_typ",
            "datum_zahajeni",
        ]
    return required_fields


@login_required
@require_http_methods(["GET"])
def smazat_akce_vedoucí(request, akce_vedouci_id):
    zaznam = AkceVedouci.objects.get(id=akce_vedouci_id)
    resp = zaznam.delete()
    next_url = request.GET.get("next")
    if next_url:
        if is_safe_url(next_url, allowed_hosts=settings.ALLOWED_HOSTS):
            response = next_url
        else:
            logger.warning("Redirect to URL " + str(next_url) + " is not safe!!")
            response = reverse("core:home")
    messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
    response = redirect(next_url)
    return response
