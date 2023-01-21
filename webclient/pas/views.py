import logging

import simplejson as json
import structlog
from core.constants import (
    ARCHIVACE_SN,
    ODESLANI_SN,
    POTVRZENI_SN,
    ROLE_ADMIN_ID,
    ROLE_ARCHIVAR_ID,
    SN_ARCHIVOVANY,
    SN_ODESLANY,
    SN_POTVRZENY,
    SN_ZAPSANY,
    SPOLUPRACE_NEAKTIVNI,
    SPOLUPRACE_ZADOST,
    UZIVATEL_SPOLUPRACE_RELATION_TYPE,
    ZAPSANI_SN,
)
from core.exceptions import MaximalIdentNumberError
from core.forms import CheckStavNotChangedForm, VratitForm
from core.ident_cely import get_sn_ident
from core.message_constants import (
    FORM_NOT_VALID,
    MAXIMUM_IDENT_DOSAZEN,
    PRISTUP_ZAKAZAN,
    SAMOSTATNY_NALEZ_ARCHIVOVAN,
    SAMOSTATNY_NALEZ_NELZE_ODESLAT,
    SAMOSTATNY_NALEZ_ODESLAN,
    SAMOSTATNY_NALEZ_POTVRZEN,
    SAMOSTATNY_NALEZ_VRACEN,
    SPOLUPRACE_BYLA_AKTIVOVANA,
    SPOLUPRACE_BYLA_DEAKTIVOVANA,
    SPOLUPRACI_NELZE_AKTIVOVAT,
    SPOLUPRACI_NELZE_DEAKTIVOVAT,
    ZADOST_O_SPOLUPRACI_VYTVORENA,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.utils import get_cadastre_from_point, get_cadastre_from_point_with_geometry
from core.views import SearchListView, check_stav_changed
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from dokument.forms import CoordinatesDokumentForm
from heslar.hesla import PRISTUPNOST_ARCHEOLOG_ID
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from pas.filters import SamostatnyNalezFilter, UzivatelSpolupraceFilter
from pas.forms import CreateSamostatnyNalezForm, CreateZadostForm, PotvrditNalezForm
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pas.tables import SamostatnyNalezTable, UzivatelSpolupraceTable
from uzivatel.models import Organizace, User
from services.mailer import Mailer

logger = logging.getLogger(__name__)
logger_s = structlog.get_logger(__name__)


def get_detail_context(sn, request):
    context = {"sn": sn}
    context["form"] = CreateSamostatnyNalezForm(
        instance=sn, readonly=True, user=request.user
    )
    context["ulozeni_form"] = PotvrditNalezForm(instance=sn, readonly=True)
    context["history_dates"] = get_history_dates(sn.historie)
    context["show"] = get_detail_template_shows(sn)
    logger.debug(context)
    if sn.soubory:
        context["soubory"] = sn.soubory.soubory.all()
    else:
        context["soubory"] = None
    return context


@login_required
@require_http_methods(["GET"])
def index(request):
    return render(request, "pas/index.html")


@login_required
@require_http_methods(["GET", "POST"])
def create(request, ident_cely=None):
    required_fields = get_required_fields()
    required_fields_next = get_required_fields(next=1)
    if request.method == "POST":
        form = CreateSamostatnyNalezForm(
            request.POST,
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
        )
        form_coor = CoordinatesDokumentForm(
            request.POST,
        )
        if form.is_valid():
            geom = None
            geom_sjtsk = None
            try:
                wgs84_dx = float(form_coor.data.get("coordinate_wgs84_x"))
                wgs84_dy = float(form_coor.data.get("coordinate_wgs84_y"))
                if wgs84_dx > 0 and wgs84_dy > 0:
                    geom = Point(wgs84_dy, wgs84_dx)
                sjtsk_dx = float(form_coor.data.get("coordinate_sjtsk_x"))
                sjtsk_dy = float(form_coor.data.get("coordinate_sjtsk_y"))
                if sjtsk_dx > 0 and sjtsk_dy > 0:
                    geom_sjtsk = Point(sjtsk_dy, sjtsk_dx)
            except Exception:
                logger.error("PAS.Chybny format souradnic:1")
            # latitude = form.cleaned_data["latitude"]
            # longitude = form.cleaned_data["longitude"]
            sn = form.save(commit=False)
            try:
                sn.ident_cely = get_sn_ident(sn.projekt)
            except MaximalIdentNumberError:
                messages.add_message(request, messages.ERROR, MAXIMUM_IDENT_DOSAZEN)
            else:
                sn.stav = SN_ZAPSANY
                sn.pristupnost = Heslar.objects.get(id=PRISTUPNOST_ARCHEOLOG_ID)
                sn.predano_organizace = sn.projekt.organizace
                sn.geom_system = form_coor.data.get("coordinate_system")
                if geom is not None:
                    sn.katastr = get_cadastre_from_point(geom)
                    sn.geom = geom
                if geom_sjtsk is not None:
                    sn.geom_sjtsk = geom_sjtsk
                form.save()
                sn.set_zapsany(request.user)
                form.save_m2m()
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
                return redirect("pas:detail", ident_cely=sn.ident_cely)

        else:
            logger.debug(form.errors)
            messages.add_message(request, messages.ERROR, FORM_NOT_VALID)
    else:
        form = CreateSamostatnyNalezForm(
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
            project_ident=ident_cely,
        )
        form_coor = CoordinatesDokumentForm()
    return render(
        request,
        "pas/create.html",
        {
            "global_map_can_edit": True,
            "formCoor": form_coor,
            "form": form,
            "title": _("Nový samostatný nález"),
            "header": _("Nový samostatný nález"),
            "button": _("Vytvořit samostatný nález"),
        },
    )


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {"warnings": request.session.pop("temp_data", None)}
    sn = get_object_or_404(
        SamostatnyNalez.objects.select_related(
            "soubory",
            "okolnosti",
            "obdobi",
            "druh_nalezu",
            "specifikace",
            "predano_organizace",
            "historie",
        ),
        ident_cely=ident_cely,
    )
    context.update(get_detail_context(sn=sn, request=request))
    if sn.geom:
        geom = "0 0"
        if sn.geom:
            geom = str(sn.geom).split("(")[1].replace(", ", ",").replace(")", "")
        geom_sjtsk = "0 0"
        if sn.geom_sjtsk:
            geom_sjtsk = (
                str(sn.geom_sjtsk).split("(")[1].replace(", ", ",").replace(")", "")
            )
        logger.debug("++++++++++++++++++")
        logger.debug(sn.geom_system)
        system = (
            "WGS-84"
            if sn.geom_system == "wgs84"
            else ("S-JTSK*" if sn.geom_system == "sjtsk*" else "S-JTSK")
        )
        logger.debug(system)
        context["formCoor"] = CoordinatesDokumentForm(
            initial={
                "detector_coordinates_x": geom.split(" ")[1]
                if (system == "WGS-84")
                else geom_sjtsk.split(" ")[1],
                "detector_coordinates_y": geom.split(" ")[0]
                if (system == "WGS-84")
                else geom_sjtsk.split(" ")[0],
                "coordinate_wgs84_x": geom.split(" ")[1],
                "coordinate_wgs84_y": geom.split(" ")[0],
                "coordinate_sjtsk_x": geom_sjtsk.split(" ")[1],
                "coordinate_sjtsk_y": geom_sjtsk.split(" ")[0],
                "coordinate_system": system,
            }
        )  # Zmen musis poslat data do formulare
        context["global_map_can_edit"] = False
    else:
        context["formCoor"] = CoordinatesDokumentForm()
    return render(request, "pas/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav == SN_ARCHIVOVANY:
        raise PermissionDenied()
    kwargs = {"projekt_disabled": "disabled"}
    required_fields = get_required_fields(sn)
    required_fields_next = get_required_fields(sn, 1)
    if request.method == "POST":
        request_post = request.POST.copy()
        request_post["projekt"] = sn.projekt
        form = CreateSamostatnyNalezForm(
            request_post,
            instance=sn,
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
            **kwargs,
        )
        form_coor = CoordinatesDokumentForm(request.POST)
        geom = None
        geom_sjtsk = None
        try:
            wgs84_dx = float(form_coor.data.get("coordinate_wgs84_x"))
            wgs84_dy = float(form_coor.data.get("coordinate_wgs84_y"))
            if wgs84_dx > 0 and wgs84_dy > 0:
                geom = Point(wgs84_dy, wgs84_dx)
            sjtsk_dx = float(form_coor.data.get("coordinate_sjtsk_x"))
            sjtsk_dy = float(form_coor.data.get("coordinate_sjtsk_y"))
            if sjtsk_dx > 0 and sjtsk_dy > 0:
                geom_sjtsk = Point(sjtsk_dy, sjtsk_dx)
        except Exception as e:
            logger.error("PAS.Chybny format souradnic:2 " + e)
        if form.is_valid():
            logger.debug("PAS Form is valid:1")
            sn.geom_system = form_coor.data.get("coordinate_system")
            if geom is not None:
                sn.katastr = get_cadastre_from_point(geom)
                sn.geom = geom
            if geom_sjtsk is not None:
                sn.geom_sjtsk = geom_sjtsk
            form.save()
            if form.changed_data:
                logger.debug(form.changed_data)
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("pas:detail", ident_cely=ident_cely)
        else:
            logger.debug("The form is not valid!")
            logger.debug(form.errors)

    else:
        form = CreateSamostatnyNalezForm(
            instance=sn,
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
            **kwargs,
        )
        if sn.geom:
            geom = "0 0"
            if sn.geom:
                geom = str(sn.geom).split("(")[1].replace(", ", ",").replace(")", "")
            geom_sjtsk = "0 0"
            if sn.geom_sjtsk:
                geom_sjtsk = (
                    str(sn.geom_sjtsk).split("(")[1].replace(", ", ",").replace(")", "")
                )
            system = (
                "WGS-84"
                if sn.geom_system == "wgs84"
                else ("S-JTSK*" if sn.geom_system == "sjtsk*" else "S-JTSK")
            )
            gx = geom.split(" ")[1] if system == "WGS-84" else geom_sjtsk.split(" ")[1]
            gy = geom.split(" ")[0] if system == "WGS-84" else geom_sjtsk.split(" ")[0]
            form_coor = CoordinatesDokumentForm(
                initial={
                    "detector_coordinates_x": gx,
                    "detector_coordinates_y": gy,
                    "coordinate_wgs84_x": geom.split(" ")[1],
                    "coordinate_wgs84_y": geom.split(" ")[0],
                    "coordinate_sjtsk_x": geom_sjtsk.split(" ")[1],
                    "coordinate_sjtsk_y": geom_sjtsk.split(" ")[0],
                    "coordinate_system": system,
                }
            )  # Zmen musis poslat data do formulare
        else:
            form_coor = CoordinatesDokumentForm()
    return render(
        request,
        "pas/edit.html",
        {
            "global_map_can_edit": True,
            "formCoor": form_coor,
            "form": form,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit_ulozeni(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    predano_required = True if sn.stav == SN_POTVRZENY else False
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = PotvrditNalezForm(
            request.POST, instance=sn, predano_required=predano_required
        )
        if form.is_valid():
            logger.debug("PAS Form is valid:2")
            formObj = form.save(commit=False)
            formObj.predano_organizace = get_object_or_404(
                Organizace, id=sn.projekt.organizace_id
            )
            formObj.save()
            if form.changed_data:
                logger.debug(form.changed_data)
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return JsonResponse(
                {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
            )
        else:
            logger.debug("The form is not valid!")
            logger.debug(form.errors)
    else:
        form = PotvrditNalezForm(
            instance=sn,
            predano_required=predano_required,
            initial={"old_stav": sn.stav},
            predano_hidden=True,
        )
    context = {
        "object": sn,
        "form": form,
        "title": _("pas.modalForm.editUlozeni.title.text"),
        "id_tag": "edit-ulozeni-pas-form",
        "button": _("pas.modalForm.editUlozeni.submit.button"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if not SN_ARCHIVOVANY >= sn.stav > SN_ZAPSANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            Mailer.send_en03_en04(project=sn, reason=duvod)
            sn.set_vracen(request.user, sn.stav - 1, duvod)
            sn.save()
            messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_VRACEN)
            return JsonResponse(
                {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
            )
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitForm(initial={"old_stav": sn.stav})
    context = {
        "object": sn,
        "form": form,
        "title": _("pas.modalForm.vraceni.title.text"),
        "id_tag": "vratit-pas-form",
        "button": _("pas.modalForm.vraceni.submit.button"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def odeslat(request, ident_cely):
    sn = get_object_or_404(
        SamostatnyNalez.objects.select_related(
            "soubory",
            "okolnosti",
            "obdobi",
            "druh_nalezu",
            "specifikace",
            "predano_organizace",
            "historie",
        ),
        ident_cely=ident_cely,
    )
    if sn.stav != SN_ZAPSANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        sn.set_odeslany(request.user)
        messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_ODESLAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
        )

    warnings = sn.check_pred_odeslanim()
    logger.debug(warnings)
    if warnings:
        request.session["temp_data"] = warnings
        messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NELZE_ODESLAT)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    form_check = CheckStavNotChangedForm(initial={"old_stav": sn.stav})
    context = {
        "object": sn,
        "title": _("pas.modalForm.odeslat.title.text"),
        "id_tag": "odeslat-pas-form",
        "button": _("pas.modalForm.odeslat.submit.button"),
        "form_check": form_check,
    }

    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def potvrdit(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav != SN_ODESLANY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        form = PotvrditNalezForm(request.POST, instance=sn, predano_required=True)
        if form.is_valid():
            formObj = form.save(commit=False)
            formObj.set_potvrzeny(request.user)
            formObj.predano_organizace = get_object_or_404(
                Organizace, id=sn.projekt.organizace_id
            )
            formObj.save()
            messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_POTVRZEN)
            return JsonResponse(
                {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
            )
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = PotvrditNalezForm(
            instance=sn, initial={"old_stav": sn.stav}, predano_hidden=True
        )
    context = {
        "object": sn,
        "form": form,
        "title": _("pas.modalForm.potvrdit.title.text"),
        "id_tag": "potvrdit-pas-form",
        "button": _("pas.modalForm.potvrdit.submit.button"),
    }
    return render(request, "core/transakce_modal.html", context)


def archivovat(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav != SN_POTVRZENY:
        messages.add_message(request, messages.ERROR, PRISTUP_ZAKAZAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, sn):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        sn.set_archivovany(request.user)
        messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_ARCHIVOVAN)
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})}
        )
    else:
        # TODO nejake kontroly? warnings = sn.check_pred_archivaci()
        form_check = CheckStavNotChangedForm(initial={"old_stav": sn.stav})
        context = {
            "object": sn,
            "title": _("pas.modalForm.archivovat.title.text"),
            "id_tag": "archivovat-pas-form",
            "button": _("pas.modalForm.archivovat.submit.button"),
            "form_check": form_check,
        }
    return render(request, "core/transakce_modal.html", context)


class SamostatnyNalezListView(SearchListView):
    table_class = SamostatnyNalezTable
    model = SamostatnyNalez
    template_name = "pas/samostatny_nalez_list.html"
    filterset_class = SamostatnyNalezFilter
    export_name = "export_samostatny-nalez_"
    page_title = _("pas.vyber.pageTitle")
    app = "samostatny_nalez"
    toolbar = "toolbar_pas.html"
    search_sum = _("pas.vyber.pocetVyhledanych")
    pick_text = _("pas.vyber.pickText")
    hasOnlyVybrat_header = _("pas.vyber.header.hasOnlyVybrat")
    hasOnlyVlastnik_header = _("pas.vyber.header.hasOnlyVlastnik")
    hasOnlyArchive_header = _("pas.vyber.header.hasOnlyArchive")
    hasOnlyPotvrdit_header = _("pas.vyber.header.hasOnlyPotvrdit")
    default_header = _("pas.vyber.header.default")
    toolbar_name = _("pas.template.toolbar.title")

    def get_queryset(self):
        # Only allow to view 3D models
        qs = super().get_queryset()
        qs = qs.select_related(
            "obdobi", "specifikace", "nalezce", "druh_nalezu", "predano_organizace"
        )
        return qs


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    nalez = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if check_stav_changed(request, nalez):
        return JsonResponse(
            {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
            status=403,
        )
    if request.method == "POST":
        historie = nalez.historie
        soubory = nalez.soubory
        resp1 = nalez.delete()
        resp2 = historie.delete()
        resp3 = soubory.delete()

        if resp1:
            logger.debug("Nalez byl smazan: " + str(resp1 + resp2 + resp3))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            return JsonResponse({"redirect": reverse("core:home")})
        else:
            logger.warning("Nalez nebyl smazan: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return JsonResponse(
                {"redirect": reverse("pas:detail", kwargs={"ident_cely": ident_cely})},
                status=403,
            )
    else:
        form_check = CheckStavNotChangedForm(initial={"old_stav": nalez.stav})
        context = {
            "object": nalez,
            "title": _("pas.modalForm.smazani.title.text"),
            "id_tag": "smazat-pas-form",
            "button": _("pas.modalForm.smazani.submit.button"),
            "form_check": form_check,
        }
        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def zadost(request):
    if request.method == "POST":
        logger_s.debug("zadost.start")
        form = CreateZadostForm(request.POST)
        if form.is_valid():
            logger_s.debug("zadost.form_valid")
            uzivatel_email = form.cleaned_data["email_uzivatele"]
            uzivatel_text = form.cleaned_data["text"]
            uzivatel = get_object_or_404(User, email=uzivatel_email)
            exists = UzivatelSpoluprace.objects.filter(
                vedouci=uzivatel, spolupracovnik=request.user
            ).exists()

            if uzivatel == request.user:
                messages.add_message(
                    request, messages.ERROR, _("Nelze vytvořit spolupráci sám se sebou")
                )
                logger_s.debug(
                    "zadost.post.error",
                    error=_("Nelze vytvořit spolupráci sám se sebou"),
                )
            elif exists:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "Spolupráce s uživatelem s emailem "
                        + uzivatel_email
                        + " již existuje."
                    ),
                )
                logger_s.debug(
                    "zadost.post.error",
                    error=_("Spoluprace jiz existuje"),
                    email=uzivatel_email,
                )
            else:
                hv = HistorieVazby(typ_vazby=UZIVATEL_SPOLUPRACE_RELATION_TYPE)
                hv.save()
                s = UzivatelSpoluprace(
                    vedouci=uzivatel,
                    spolupracovnik=request.user,
                    stav=SPOLUPRACE_NEAKTIVNI,
                    historie=hv,
                )
                s.save()
                hist = Historie(
                    typ_zmeny=SPOLUPRACE_ZADOST,
                    uzivatel=request.user,
                    vazba=hv,
                    poznamka=uzivatel_text,
                )
                hist.save()
                messages.add_message(
                    request, messages.SUCCESS, ZADOST_O_SPOLUPRACI_VYTVORENA
                )
                logger_s.debug(
                    "zadost.post.success",
                    hv_id=hv.pk,
                    s_id=s.pk,
                    hist_id=hist.pk,
                    message=ZADOST_O_SPOLUPRACI_VYTVORENA,
                )
                Mailer.send_en05(
                    email_to=uzivatel_email, reason=uzivatel_text, user=request.user, spoluprace_id=s.pk
                )
                return redirect("pas:spoluprace_list")
        else:
            print("Form is no valid")
            logger.debug(form.errors)
    else:
        logger_s.debug("zadost.form_invalid")
        form = CreateZadostForm()

    return render(
        request,
        "pas/zadost.html",
        {"title": _("Žádost o spolupráci"), "header": _("Nová žádost"), "form": form},
    )


class UzivatelSpolupraceListView(SearchListView):
    table_class = UzivatelSpolupraceTable
    model = UzivatelSpoluprace
    template_name = "pas/uzivatel_spoluprace_list.html"
    filterset_class = UzivatelSpolupraceFilter
    export_name = "export_spoluprace_"
    page_title = _("spoluprace.vyber.pageTitle")
    app = "spoluprace"
    toolbar = "toolbar_spoluprace.html"
    search_sum = _("spoluprace.vyber.pocetVyhledanych")
    pick_text = _("spoluprace.vyber.pickText")
    toolbar_name = _("spoluprace.template.toolbar.title")

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("vedouci", "spolupracovnik")
        return qs.order_by("id")

    def get_table_kwargs(self):
        if self.request.user.hlavni_role.id not in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID):
            return {"exclude": ("smazani",)}
        return {}


@login_required
@require_http_methods(["GET", "POST"])
def aktivace(request, pk):
    spoluprace = get_object_or_404(UzivatelSpoluprace, id=pk)
    if request.method == "POST":
        spoluprace.set_aktivni(request.user)
        messages.add_message(request, messages.SUCCESS, SPOLUPRACE_BYLA_AKTIVOVANA)
        Mailer.send_en06(cooperation=spoluprace)
        return JsonResponse({"redirect": reverse("pas:spoluprace_list")})
    else:
        warnings = spoluprace.check_pred_aktivaci()
        logger.debug(warnings)
        if warnings:
            messages.add_message(
                request, messages.ERROR, f"{SPOLUPRACI_NELZE_AKTIVOVAT} {warnings[0]}"
            )
            return JsonResponse(
                {"redirect": reverse("pas:spoluprace_list")}, status=403
            )
    context = {
        "object": spoluprace,
        "title": (
            _("Aktivace spolupráce mezi ")
            + spoluprace.vedouci.email
            + " a "
            + spoluprace.spolupracovnik.email
        ),
        "id_tag": "aktivace-spoluprace-form",
        "button": _("pas.spoluprace.modalForm.aktivace.submit.button"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def deaktivace(request, pk):
    spoluprace = get_object_or_404(UzivatelSpoluprace, id=pk)
    if request.method == "POST":
        spoluprace.set_neaktivni(request.user)
        messages.add_message(request, messages.SUCCESS, SPOLUPRACE_BYLA_DEAKTIVOVANA)
        return JsonResponse({"redirect": reverse("pas:spoluprace_list")})
    else:
        warnings = spoluprace.check_pred_deaktivaci()
        logger.debug(warnings)
        if warnings:
            messages.add_message(
                request, messages.ERROR, f"{SPOLUPRACI_NELZE_DEAKTIVOVAT} {warnings[0]}"
            )
            return JsonResponse(
                {"redirect": reverse("pas:spoluprace_list")}, status=403
            )
    context = {
        "object": spoluprace,
        "title": (
            _("Deaktivace spolupráce mezi ")
            + spoluprace.vedouci.email
            + " a "
            + spoluprace.spolupracovnik.email
        ),
        "id_tag": "deaktivace-spoluprace-form",
        "button": _("pas.spoluprace.modalForm.deaktivace.submit.button"),
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def smazat_spolupraci(request, pk):
    spoluprace = get_object_or_404(UzivatelSpoluprace, id=pk)
    if request.method == "POST":
        historie = spoluprace.historie
        resp1 = spoluprace.delete()
        resp2 = historie.delete()

        if resp1:
            logger.debug("Spoluprace byla smazana: " + str(resp1 + resp2))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
            return JsonResponse({"redirect": reverse("pas:spoluprace_list")})
        else:
            logger.warning("Spoluprace nebyla smazana: " + str(pk))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return JsonResponse(
                {"redirect": reverse("pas:spoluprace_list")}, status=403
            )

    else:
        context = {
            "object": spoluprace,
            "title": (
                _("pas.spoluprace.modalForm.smazani.title.text")
                + spoluprace.vedouci.email
                + _(" a ")
                + spoluprace.spolupracovnik.email
            ),
            "id_tag": "smazani-spoluprace-form",
            "button": _("pas.spoluprace.modalForm.smazani.submit.button"),
        }
    return render(request, "core/transakce_modal.html", context)


def get_history_dates(historie_vazby):
    historie = {
        "datum_zapsani": historie_vazby.get_last_transaction_date(ZAPSANI_SN),
        "datum_odeslani": historie_vazby.get_last_transaction_date(ODESLANI_SN),
        "datum_potvrzeni": historie_vazby.get_last_transaction_date(POTVRZENI_SN),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_SN),
    }
    return historie


def get_detail_template_shows(sn):
    show_vratit = sn.stav > SN_ZAPSANY
    show_odeslat = sn.stav == SN_ZAPSANY
    show_potvrdit = sn.stav == SN_ODESLANY
    show_archivovat = sn.stav == SN_POTVRZENY
    show_edit = sn.stav not in [
        SN_ARCHIVOVANY,
    ]
    show_arch_links = sn.stav == SN_ARCHIVOVANY
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "potvrdit_link": show_potvrdit,
        "archivovat_link": show_archivovat,
        "editovat": show_edit,
        "arch_links": show_arch_links,
    }
    return show


@require_http_methods(["POST"])
def post_point_position_2_katastre(request):
    body = json.loads(request.body.decode("utf-8"))
    logger.debug(body)
    katastr_name = get_cadastre_from_point(Point(body["cX"], body["cY"]))
    if katastr_name is not None:
        return JsonResponse(
            {
                "katastr_name": katastr_name.nazev_stary,
            },
            status=200,
        )
    else:
        return JsonResponse({"katastr_name": ""}, status=200)


@require_http_methods(["POST"])
def post_point_position_2_katastre_with_geom(request):
    body = json.loads(request.body.decode("utf-8"))
    [katastr_name, katastr_db, katastr_geom] = get_cadastre_from_point_with_geometry(
        Point(body["cX"], body["cY"])
    )
    if katastr_name is not None:
        return JsonResponse(
            {
                "katastr_name": katastr_name,
                "katastr_db": katastr_db,
                "katastr_geom": katastr_geom,
            },
            status=200,
        )
    else:
        return JsonResponse({"katastr_name": ""}, status=200)


def get_required_fields(zaznam=None, next=0):
    required_fields = []
    if zaznam:
        stav = zaznam.stav
    else:
        stav = 1
    if stav >= SN_ZAPSANY - next:
        required_fields = [
            "projekt",
        ]
    if stav > SN_ZAPSANY - next:
        required_fields += [
            "lokalizace",
            "datum_nalezu",
            "okolnosti",
            "hloubka",
            "katastr",
            "nalezce",
            "specifikace",
            "obdobi",
            "druh_nalezu",
            "detector_system_coordinates",
            "detector_coordinates_x",
            "detector_coordinates_y",
        ]
    return required_fields
