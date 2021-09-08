import logging

import simplejson as json
from adb.forms import CreateADBForm, create_vyskovy_bod_form, VyskovyBodFormSetHelper
from adb.models import Adb, VyskovyBod
from arch_z.forms import (
    CreateAkceForm,
    CreateArchZForm,
    PripojitDokumentForm,
    PripojitProjDocForm,
)
from arch_z.models import Akce, ArcheologickyZaznam
from core.constants import (
    ARCHIVACE_AZ,
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    ODESLANI_AZ,
    PIAN_NEPOTVRZEN,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAPSANY,
    ZAPSANI_AZ,
)
from core.forms import VratitForm
from core.exceptions import MaximalEventCount
from core.ident_cely import get_cast_dokumentu_ident, get_project_event_ident
from core.message_constants import (
    AKCE_USPESNE_ARCHIVOVANA,
    AKCE_USPESNE_ODESLANA,
    AKCE_USPESNE_VRACENA,
    AKCE_USPESNE_ZAPSANA,
    AKCI_NELZE_ARCHIVOVAT,
    AKCI_NELZE_ODESLAT,
    DOKUMENT_JIZ_BYL_PRIPOJEN,
    DOKUMENT_USPESNE_ODPOJEN,
    DOKUMENT_USPESNE_PRIPOJEN,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    MAXIMUM_AKCII_DOSAZENO,
)
from core.utils import get_all_pians_with_dj, get_centre_from_akce
from dj.forms import CreateDJForm
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
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

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
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
        can_delete=show["editovat"],
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
        can_delete=show["editovat"],
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
                prefix=jednotka.ident_cely,
                not_readonly=show["editovat"],
            ),
            "show_add_adb": show_adb_add,
            "show_add_komponenta": show_add_komponenta,
            "show_add_pian": (show_add_pian and show["editovat"]),
            "show_remove_pian": (not show_add_pian and show["editovat"]),
            "show_uprav_pian": jednotka.pian
            and jednotka.pian.stav == PIAN_NEPOTVRZEN
            and show["editovat"],
            "show_approve_pian": show_approve_pian,
        }
        if has_adb:
            dj_form_detail["adb_form"] = CreateADBForm(
                instance=jednotka.adb, prefix=jednotka.adb.ident_cely
            )
            dj_form_detail["adb_ident_cely"] = jednotka.adb.ident_cely
            dj_form_detail["vyskovy_bod_formset"] = \
                vyskovy_bod_formset(instance=jednotka.adb, prefix=jednotka.adb.ident_cely + "_vb")
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
                        instance=komponenta, prefix=komponenta.ident_cely + "_o"
                    ),
                    "form_nalezy_predmety": NalezPredmetFormset(
                        instance=komponenta, prefix=komponenta.ident_cely + "_p"
                    ),
                    "helper": NalezFormSetHelper(),
                }
            )

    context["dj_form_create"] = dj_form_create
    context["pian_form_create"] = pian_form_create
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
    if request.method == "POST":
        form_az = CreateArchZForm(request.POST, instance=zaznam)
        form_akce = CreateAkceForm(request.POST, instance=zaznam.akce)

        if form_az.is_valid() and form_akce.is_valid():
            logger.debug("Form is valid")
            form_az.save()
            form_akce.save()
            if form_az.changed_data or form_akce.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("arch_z:detail", ident_cely=ident_cely)
        else:
            logger.warning("Form is not valid")
            logger.debug(form_az.errors)
            logger.debug(form_akce.errors)
    else:
        form_az = CreateArchZForm(instance=zaznam)
        form_akce = CreateAkceForm(instance=zaznam.akce)

    return render(
        request,
        "arch_z/create.html",
        {
            "formAZ": form_az,
            "formAkce": form_akce,
            "title": _("Editace archeologického záznamu"),
            "header": _("Archeologický záznam"),
            "button": _("Uložit změny"),
        },
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
    context["title"] = _("Odeslání akce")
    context["header"] = _("Odeslání akce")
    context["button"] = _("Odeslat akci")
    return render(request, "core/transakce.html", context)


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
    context["title"] = _("Archivace akce")
    context["header"] = _("Archivace akce")
    context["button"] = _("Archivovat akci")
    return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    if az.stav != AZ_STAV_ODESLANY and az.stav != AZ_STAV_ARCHIVOVANY:
        raise PermissionDenied()
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
            return redirect("/arch_z/detail/" + ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitForm()
    return render(request, "core/vratit.html", {"form": form, "objekt": az})


@login_required
@require_http_methods(["GET", "POST"])
def zapsat(request, projekt_ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=projekt_ident_cely)

    # Projektove akce lze pridavat pouze pokud je projekt jiz prihlasen
    if not PROJEKT_STAV_ZAPSANY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY:
        raise PermissionDenied(
            "Nelze pridat akci k projektu ve stavu " + str(projekt.stav)
        )

    if request.method == "POST":
        form_az = CreateArchZForm(request.POST)
        form_akce = CreateAkceForm(request.POST)

        if form_az.is_valid() and form_akce.is_valid():
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

                messages.add_message(request, messages.SUCCESS, AKCE_USPESNE_ZAPSANA)
                return redirect("/arch_z/detail/" + az.ident_cely)

        else:
            logger.warning("Form is not valid")
            logger.debug(form_az.errors)
            logger.debug(form_akce.errors)

    else:
        form_az = CreateArchZForm(projekt=projekt)
        form_akce = CreateAkceForm(uzamknout_specifikace=True, projekt=projekt)

    return render(
        request,
        "arch_z/create.html",
        {
            "formAZ": form_az,
            "formAkce": form_akce,
            "title": _("Nová projektová akce"),
            "header": _("Nová projektová akce"),
            "button": _("Vytvoř akci"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    akce = get_object_or_404(Akce, archeologicky_zaznam__ident_cely=ident_cely)
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
            return redirect("/projekt/detail/" + projekt.ident_cely)
        else:
            return redirect("/")
    else:
        return render(request, "core/smazat.html", {"objekt": akce})


@login_required
@require_http_methods(["GET", "POST"])
def pripojit_dokument(request, arch_z_ident_cely, proj_ident_cely=None):
    az = get_object_or_404(ArcheologickyZaznam, ident_cely=arch_z_ident_cely)
    if request.method == "POST":
        dokument_ids = request.POST.getlist("dokument")
        casti_zaznamu = DokumentCast.objects.filter(
            archeologicky_zaznam__ident_cely=arch_z_ident_cely
        )
        for dokument_id in dokument_ids:
            dokument = get_object_or_404(Dokument, id=dokument_id)
            relace = casti_zaznamu.filter(dokument__id=dokument_id)
            if not relace.exists():
                dc_ident = get_cast_dokumentu_ident(dokument)
                DokumentCast(
                    archeologicky_zaznam=az, dokument=dokument, ident_cely=dc_ident
                ).save()
                logger.debug(
                    "K akci "
                    + str(arch_z_ident_cely)
                    + " byl pripojen dokument "
                    + str(dokument.ident_cely)
                )
                messages.add_message(
                    request, messages.SUCCESS, DOKUMENT_USPESNE_PRIPOJEN
                )
            else:
                messages.add_message(
                    request, messages.WARNING, DOKUMENT_JIZ_BYL_PRIPOJEN
                )
        return redirect("arch_z:detail", ident_cely=arch_z_ident_cely)
    else:
        if proj_ident_cely:
            # Pridavam projektove dokumenty
            projektove_dokumenty = set()
            dokumenty_akce = set(
                Dokument.objects.filter(
                    casti__archeologicky_zaznam__ident_cely=arch_z_ident_cely
                )
            )
            projekt = get_object_or_404(Projekt, ident_cely=proj_ident_cely)
            for akce in projekt.akce_set.all().exclude(
                archeologicky_zaznam__ident_cely=arch_z_ident_cely
            ):
                for cast in akce.archeologicky_zaznam.casti_dokumentu.all():
                    if cast.dokument not in dokumenty_akce:
                        projektove_dokumenty.add(
                            (cast.dokument.id, cast.dokument.ident_cely)
                        )
            form = PripojitProjDocForm(projekt_docs=list(projektove_dokumenty))
        else:
            # Pridavam vsechny dokumenty
            form = PripojitDokumentForm()
    return render(
        request, "arch_z/pripojit_dokument.html", {"form": form, "object": az}
    )


@login_required
@require_http_methods(["GET", "POST"])
def odpojit_dokument(request, ident_cely, arch_z_ident_cely):
    relace_dokumentu = DokumentCast.objects.filter(dokument__ident_cely=ident_cely)
    remove_orphan = False
    if len(relace_dokumentu) == 0:
        raise Http404("Nelze najít zadne relace dokumentu " + str(ident_cely))
    if len(relace_dokumentu) == 1:
        orphan_dokument = relace_dokumentu[0].dokument
        if "X-" in orphan_dokument.ident_cely:
            remove_orphan = True
    if request.method == "POST":
        dokument_cast = relace_dokumentu.filter(
            archeologicky_zaznam__ident_cely=arch_z_ident_cely
        )
        if len(dokument_cast) == 0:
            raise Http404("Nelze najít relaci mezi zaznamem a dokumentem")
        resp = dokument_cast[0].delete()
        logger.debug("Byla smazana cast dokumentu " + str(resp))
        if remove_orphan:
            orphan_dokument.delete()
            logger.debug("Docasny soubor bez relaci odstranen.")
        messages.add_message(request, messages.SUCCESS, DOKUMENT_USPESNE_ODPOJEN)
        return redirect("arch_z:detail", ident_cely=arch_z_ident_cely)
    else:
        warnings = []
        if remove_orphan:
            warnings.append(
                "Nearchivovaný dokument "
                + str(orphan_dokument)
                + " nemá žádnou jinou relaci a odpojením bude automaticky smazán."
            )
        return render(
            request,
            "arch_z/transakce_dokument.html",
            {
                "object": relace_dokumentu[0],
                "warnings": warnings,
                "title": _("Odpojení dokumentu"),
                "header": _("Odpojení dokumentu"),
                "button": _("Odpojit dokument"),
            },
        )


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
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "archivovat_link": show_archivovat,
        "editovat": show_edit,
    }
    return show


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

    [poi, geom] = get_centre_from_akce(katastr_name, pian_ident_cely)
    if len(str(poi)) > 0:
        return JsonResponse(
            {
                "lat": str(poi.lat),
                "lng": str(poi.lng),
                "zoom": str(poi.zoom),
                "geom": str(geom).split(";")[1].replace(", ", ",") if geom else None,
            },
            status=200,
        )
    else:
        return JsonResponse({"lat": "", "lng": "", "zoom": "", "geom": ""}, status=200)
