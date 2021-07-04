import logging

from core.constants import (
    ARCHIVACE_SN,
    ODESLANI_SN,
    POTVRZENI_SN,
    SN_ODESLANY,
    SN_POTVRZENY,
    SN_ZAPSANY,
    SPOLUPRACE_NEAKTIVNI,
    SPOLUPRACE_ZADOST,
    UZIVATEL_SPOLUPRACE_RELATION_TYPE,
    ZAPSANI_SN,
)
from core.ident_cely import get_sn_ident
from core.message_constants import (
    SPOLUPRACE_BYLA_AKTIVOVANA,
    SPOLUPRACE_BYLA_DEAKTIVOVANA,
    SPOLUPRACI_NELZE_AKTIVOVAT,
    SPOLUPRACI_NELZE_DEAKTIVOVAT,
    VYBERTE_PROSIM_POLOHU,
    ZADOST_O_SPOLUPRACI_VYTVORENA,
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.utils import get_cadastre_from_point
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from heslar.hesla import PRISTUPNOST_ARCHEOLOG_ID
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from pas.filters import SamostatnyNalezFilter, UzivatelSpolupraceFilter
from pas.forms import CreateSamostatnyNalezForm, CreateZadostForm
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pas.tables import SamostatnyNalezTable, UzivatelSpolupraceTable
from uzivatel.models import User

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index(request):
    return render(request, "pas/index.html")


@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    if request.method == "POST":
        form = CreateSamostatnyNalezForm(request.POST)
        if form.is_valid():
            logger.debug("Forms are valid")
            sn = form.save(commit=False)
            sn.ident_cely = get_sn_ident(sn.projekt)
            sn.stav = SN_ZAPSANY
            sn.katastr = get_cadastre_from_point(sn.geom)
            sn.pristupnost = Heslar.objects.get(id=PRISTUPNOST_ARCHEOLOG_ID)
            sn.save()
            sn.set_zapsany(request.user)
            form.save_m2m()
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
            return redirect("pas:detail", ident_cely=sn.ident_cely)

        else:
            logger.warning("Form is not valid")
            logger.debug(form.errors)
            if "geom" in form.errors:
                messages.add_message(request, messages.ERROR, VYBERTE_PROSIM_POLOHU)
    else:
        form = CreateSamostatnyNalezForm(user=request.user)
    return render(
        request,
        "pas/create.html",
        {
            "form": form,
            "title": _("Nový samostatný nález"),
            "header": _("Nový samostatný nález"),
            "button": _("Vytvořit samostatný nález"),
        },
    )


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
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
    context["sn"] = sn
    context["form"] = CreateSamostatnyNalezForm(instance=sn, readonly=True)
    context["history_dates"] = get_history_dates(sn.historie)
    context["show"] = get_detail_template_shows(sn)
    logger.debug(context)
    if sn.soubory:
        context["soubory"] = sn.soubory.soubory.all()
    else:
        context["soubory"] = None
    return render(request, "pas/detail.html", context)


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
        form = CreateZadostForm(request.POST)
        if form.is_valid():
            archeolog_email = form.cleaned_data["email_archeologa"]
            archeolog = get_object_or_404(User, email=archeolog_email)
            exists = UzivatelSpoluprace.objects.filter(
                vedouci=archeolog, spolupracovnik=request.user
            ).exists()

            if archeolog == request.user:
                logger.debug("Nelze vytvorit spolupraci sam se sebou")
                messages.add_message(
                    request, messages.ERROR, _("Nelze vytvořit spolupráci sám se sebou")
                )
            elif exists:
                logger.debug("Spoluprace jiz existuje")
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "Spolupráce s archeologem s emailem "
                        + archeolog_email
                        + " již existuje."
                    ),
                )
            else:
                hv = HistorieVazby(typ_vazby=UZIVATEL_SPOLUPRACE_RELATION_TYPE)
                hv.save()
                s = UzivatelSpoluprace(
                    vedouci=archeolog,
                    spolupracovnik=request.user,
                    stav=SPOLUPRACE_NEAKTIVNI,
                    historie=hv,
                )
                s.save()
                Historie(
                    typ_zmeny=SPOLUPRACE_ZADOST,
                    uzivatel=request.user,
                    vazba=hv,
                ).save()
                messages.add_message(
                    request, messages.SUCCESS, ZADOST_O_SPOLUPRACI_VYTVORENA
                )
                # TODO send email to archeolog
                return redirect("pas:spoluprace_list")
        else:
            print("Form is no valid")
            logger.debug(form.errors)
    else:
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
            context["warnings"] = []
            messages.add_message(request, messages.ERROR, SPOLUPRACI_NELZE_AKTIVOVAT)
            context["warnings"].append(warnings)
        else:
            pass
    context["title"] = _("Aktivace spolupráce")
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
            context["warnings"] = []
            messages.add_message(request, messages.ERROR, SPOLUPRACI_NELZE_DEAKTIVOVAT)
            context["warnings"].append(warnings)
        else:
            pass
    context["title"] = _("Deaktivace spolupráce")
    context["header"] = (
        _("Deaktivace spolupráce mezi ")
        + spoluprace.vedouci.email
        + " a "
        + spoluprace.spolupracovnik.email
    )
    context["button"] = _("Deaktivovat spolupráci")
    return render(request, "core/transakce.html", context)


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
    show = {
        "vratit_link": show_vratit,
        "odeslat_link": show_odeslat,
        "potvrdit_link": show_potvrdit,
        "archivovat_link": show_archivovat,
    }
    return show
