import logging
import structlog

import simplejson as json
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
from core.utils import get_cadastre_from_point
from core.views import check_stav_changed
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from dokument.forms import CoordinatesDokumentForm
from heslar.hesla import PRISTUPNOST_ARCHEOLOG_ID
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from pas.filters import SamostatnyNalezFilter, UzivatelSpolupraceFilter
from pas.forms import CreateSamostatnyNalezForm, CreateZadostForm, PotvrditNalezForm
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pas.tables import SamostatnyNalezTable, UzivatelSpolupraceTable
from uzivatel.models import User

logger = logging.getLogger(__name__)
logger_s = structlog.get_logger(__name__)


def get_detail_context(sn, request):
    context = {"sn" : sn}
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
def create(request):
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
            try:
                dx = float(form_coor.data.get("detector_coordinates_x"))
                dy = float(form_coor.data.get("detector_coordinates_y"))
                if dx > 0 and dy > 0:
                    geom = Point(dy, dx)
            except Exception:
                logger.error("Chybny format souradnic")
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
                if geom:
                    # if latitude and longitude:
                    #    sn.geom = Point(longitude, latitude)
                    sn.geom = geom
                    sn.katastr = get_cadastre_from_point(sn.geom)
                sn.save()
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
            )
        form_coor = CoordinatesDokumentForm(
        )
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
    context = { "warnings": request.session.pop("temp_data", None) }
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
        geom = str(sn.geom).split("(")[1].replace(", ", ",").replace(")", "")
        context["formCoor"] = CoordinatesDokumentForm(
            initial={
                "detector_system_coordinates": "WGS-84",
                "detector_coordinates_x": geom.split(" ")[1],
                "detector_coordinates_y": geom.split(" ")[0],
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
    required_fields_next = get_required_fields(sn,1)
    if request.method == "POST":
        request_post = request.POST.copy()
        request_post["projekt"] = sn.projekt
        form = CreateSamostatnyNalezForm(
            request_post,
            instance=sn,
            user=request.user,
            required=required_fields,
            required_next=required_fields_next,
            **kwargs
        )
        form_coor = CoordinatesDokumentForm(request.POST)
        geom = None
        try:
            dx = float(form_coor.data.get("detector_coordinates_x"))
            dy = float(form_coor.data.get("detector_coordinates_y"))
            if dx > 0 and dy > 0:
                geom = Point(dy, dx)
        except Exception:
            logger.error("Chybny format souradnic")
        if form.is_valid():
            logger.debug("Form is valid")
            if geom is not None:
                sn.katastr = get_cadastre_from_point(geom)
                sn.geom = geom
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
            **kwargs
            )
        if sn.geom:
            geom = str(sn.geom).split("(")[1].replace(", ", ",").replace(")", "")
            form_coor = CoordinatesDokumentForm(
                initial={
                    "detector_system_coordinates": "WGS-84",
                    "detector_coordinates_x": geom.split(" ")[1],
                    "detector_coordinates_y": geom.split(" ")[0],
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
            "global_map_can_edit": True,
            "formCoor": form_coor,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit_ulozeni(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    predano_required = True if sn.stav == SN_POTVRZENY else False
    if request.method == "POST":
        form = PotvrditNalezForm(
            request.POST, instance=sn, predano_required=predano_required
        )
        if form.is_valid():
            logger.debug("Form is valid")
            form.save()
            if form.changed_data:
                logger.debug(form.changed_data)
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("pas:detail", ident_cely=ident_cely)
        else:
            logger.debug("The form is not valid!")
            logger.debug(form.errors)
    else:
        form = PotvrditNalezForm(instance=sn, predano_required=predano_required)
    return render(
        request,
        "pas/edit.html",
        {"form": form},
    )


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if not SN_ARCHIVOVANY >= sn.stav > SN_ZAPSANY:
        raise PermissionDenied()
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, sn):
        return redirect("pas:detail", ident_cely)
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            sn.set_vracen(request.user, sn.stav - 1, duvod)
            sn.save()
            messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_VRACEN)
            return redirect("pas:detail", ident_cely=ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitForm(initial={"old_stav":sn.stav})
    return render(request, "core/vratit.html", {"form": form, "objekt": sn})


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
        raise PermissionDenied()
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, sn):
        return redirect("pas:detail", ident_cely)
    if request.method == "POST":
        sn.set_odeslany(request.user)
        messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_ODESLAN)
        return redirect("pas:detail", ident_cely=ident_cely)

    warnings = sn.check_pred_odeslanim()
    logger.debug(warnings)
    if warnings:
        request.session['temp_data'] = warnings
        messages.add_message(request, messages.ERROR, SAMOSTATNY_NALEZ_NELZE_ODESLAT)
        return redirect("pas:detail", ident_cely)
    form_check = CheckStavNotChangedForm(initial={"old_stav":sn.stav})
    context = {
        "object": sn,
        "title": _("Odeslání nálezu"),
        "header": _("Odeslání nálezu"),
        "button": _("Odeslat nález"),
        "form_check": form_check,
    }

    return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def potvrdit(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav != SN_ODESLANY:
        raise PermissionDenied()
    if check_stav_changed(request, sn):
        return redirect("pas:detail", ident_cely)
    if request.method == "POST":
        form = PotvrditNalezForm(request.POST, instance=sn, predano_required=True)
        if form.is_valid():
            sn = form.save(commit=False)
            sn.set_potvrzeny(request.user)
            messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_POTVRZEN)
            return redirect("pas:detail", ident_cely=ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = PotvrditNalezForm(instance=sn, initial={"old_stav":sn.stav})
    return render(request, "pas/potvrdit.html", {"form": form, "sn": sn})


def archivovat(request, ident_cely):
    sn = get_object_or_404(SamostatnyNalez, ident_cely=ident_cely)
    if sn.stav != SN_POTVRZENY:
        raise PermissionDenied()
    # Momentalne zbytecne, kdyz tak to padne hore
    if check_stav_changed(request, sn):
        return redirect("pas:detail", ident_cely)
    if request.method == "POST":
        sn.set_archivovany(request.user)
        messages.add_message(request, messages.SUCCESS, SAMOSTATNY_NALEZ_ARCHIVOVAN)
        return redirect("pas:detail", ident_cely=ident_cely)
    else:
        # TODO nejake kontroly? warnings = sn.check_pred_archivaci()
        form_check = CheckStavNotChangedForm(initial={"old_stav":sn.stav})
        context = {
            "title": _("Archivace nálezu"),
            "header": _("Archivace nálezu ") + sn.ident_cely,
            "button": _("Archivovat nález"),
            "form_check": form_check,
        }
    return render(request, "core/transakce.html", context)


class SamostatnyNalezListView(
    ExportMixin, LoginRequiredMixin, SingleTableMixin, FilterView
):
    table_class = SamostatnyNalezTable
    model = SamostatnyNalez
    template_name = "pas/samostatny_nalez_list.html"
    filterset_class = SamostatnyNalezFilter
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_formats"] = ["csv", "json", "xlsx"]
        return context

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
        return redirect("pas:detail", ident_cely)
    if request.method == "POST":
        historie = nalez.historie
        soubory = nalez.soubory
        resp1 = nalez.delete()
        resp2 = historie.delete()
        resp3 = soubory.delete()

        if resp1:
            logger.debug("Nalez byl smazan: " + str(resp1 + resp2 + resp3))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        else:
            logger.warning("Dokument nebyl smazan: " + str(ident_cely))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)

        return redirect("core:home")
    else:
        return render(request, "core/smazat.html", {"objekt": nalez})


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
                logger_s.debug("zadost.post.error", error=_("Nelze vytvořit spolupráci sám se sebou"))
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
                logger_s.debug("zadost.post.error", error=_("Spoluprace jiz existuje"), email=uzivatel_email)
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
                logger_s.debug("zadost.post.success", hv_id=hv.pk, s_id=s.pk, hist_id=hist.pk, message=ZADOST_O_SPOLUPRACI_VYTVORENA)
                # TODO send email to archeolog
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


class UzivatelSpolupraceListView(
    ExportMixin, LoginRequiredMixin, SingleTableMixin, FilterView
):
    table_class = UzivatelSpolupraceTable
    model = UzivatelSpoluprace
    template_name = "pas/uzivatel_spoluprace_list.html"
    filterset_class = UzivatelSpolupraceFilter
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_formats"] = ["csv", "json", "xlsx"]
        return context

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
        return redirect("pas:spoluprace_list")
    else:
        warnings = spoluprace.check_pred_aktivaci()
        logger.debug(warnings)
        context = {"object": spoluprace}
        if warnings:
            context["warnings"] = warnings
            messages.add_message(request, messages.ERROR, SPOLUPRACI_NELZE_AKTIVOVAT)
    context["title"] = _("Aktivace spolupráce")
    form_check = CheckStavNotChangedForm(initial={"old_stav": spoluprace.stav})
    context["form_check"] = form_check
    context["header"] = (
        _("Aktivace spolupráce mezi ")
        + spoluprace.vedouci.email
        + " a "
        + spoluprace.spolupracovnik.email
    )
    context["button"] = _("Aktivovat spolupráci")
    return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def deaktivace(request, pk):
    spoluprace = get_object_or_404(UzivatelSpoluprace, id=pk)
    if request.method == "POST":
        spoluprace.set_neaktivni(request.user)
        messages.add_message(request, messages.SUCCESS, SPOLUPRACE_BYLA_DEAKTIVOVANA)
        return redirect("pas:spoluprace_list")
    else:
        warnings = spoluprace.check_pred_deaktivaci()
        logger.debug(warnings)
        context = {"object": spoluprace}
        if warnings:
            context["warnings"] = warnings
            messages.add_message(request, messages.ERROR, SPOLUPRACI_NELZE_DEAKTIVOVAT)
    context["title"] = _("Deaktivace spolupráce")
    form_check = CheckStavNotChangedForm(initial={"old_stav": spoluprace.stav})
    context["form_check"] = form_check
    context["header"] = (
        _("Deaktivace spolupráce mezi ")
        + spoluprace.vedouci.email
        + " a "
        + spoluprace.spolupracovnik.email
    )
    context["button"] = _("Deaktivovat spolupráci")
    return render(request, "core/transakce.html", context)


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
        else:
            logger.warning("Spoluprace nebyla smazana: " + str(pk))
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)

        return redirect("pas:spoluprace_list")
    else:
        return render(
            request, "core/smazat.html", {"objekt": spoluprace, "spoluprace": True}
        )


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
def post_pas2kat(request):
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

def get_required_fields(zaznam=None,next=0):
    required_fields = []
    if zaznam:
        stav = zaznam.stav
    else:
        stav=1
    if stav >= SN_ZAPSANY-next:
        required_fields = [
            "projekt",
        ]
    if stav > SN_ZAPSANY-next:
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