import logging

import simplejson as json
from arch_z.models import Akce
from core.constants import (
    ARCHIVACE_PROJ,
    AZ_STAV_ZAPSANY,
    OZNAMENI_PROJ,
    PRIHLASENI_PROJ,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
    ROLE_ADMIN_ID,
    ROLE_ARCHIVAR_ID,
    SCHVALENI_OZNAMENI_PROJ,
    UKONCENI_V_TERENU_PROJ,
    UZAVRENI_PROJ,
    ZAHAJENI_V_TERENU_PROJ,
    ZAPSANI_PROJ,
    D_STAV_ZAPSANY,
    VRACENI_NAVRHU_ZRUSENI,
    VRACENI_ZRUSENI,
    NAVRZENI_KE_ZRUSENI_PROJ,
    RUSENI_PROJ,
)
from core.decorators import allowed_user_groups
from core.forms import VratitForm
from core.message_constants import (
    PROJEKT_NELZE_ARCHIVOVAT,
    PROJEKT_NELZE_NAVRHNOUT_KE_ZRUSENI,
    PROJEKT_NELZE_SMAZAT,
    PROJEKT_NELZE_UZAVRIT,
    PROJEKT_USPESNE_ARCHIVOVAN,
    PROJEKT_USPESNE_NAVRZEN_KE_ZRUSENI,
    PROJEKT_USPESNE_PRIHLASEN,
    PROJEKT_USPESNE_SCHVALEN,
    PROJEKT_USPESNE_UKONCEN_V_TERENU,
    PROJEKT_USPESNE_UZAVREN,
    PROJEKT_USPESNE_VRACEN,
    PROJEKT_USPESNE_ZAHAJEN_V_TERENU,
    PROJEKT_USPESNE_ZRUSEN,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.utils import get_points_from_envelope
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django_tables2.export import ExportMixin
from heslar.hesla import TYP_PROJEKTU_PRUZKUM_ID, TYP_PROJEKTU_ZACHRANNY_ID
from oznameni.forms import OznamovatelForm
from projekt.filters import ProjektFilter
from projekt.forms import (
    CreateProjektForm,
    EditProjektForm,
    NavrhnoutZruseniProjektForm,
    PrihlaseniProjektForm,
    UkoncitVTerenuForm,
    ZahajitVTerenuForm,
)
from projekt.models import Projekt
from projekt.tables import ProjektTable
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def index(request):
    return render(request, "projekt/index.html")


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    projekt = get_object_or_404(
        Projekt.objects.select_related(
            "kulturni_pamatka", "typ_projektu", "vedouci_projektu", "organizace"
        ),
        ident_cely=ident_cely,
    )
    context["projekt"] = projekt
    typ_projektu = projekt.typ_projektu
    if typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID and projekt.has_oznamovatel():
        context["oznamovatel"] = projekt.oznamovatel
    elif typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID:
        context["samostatne_nalezy"] = projekt.samostatne_nalezy.select_related(
            "obdobi", "druh_nalezu", "specifikace", "nalezce", "katastr"
        ).all()
    else:
        logger.debug("Projekt neni typu zachranny ani pruzkum " + str(typ_projektu))

    akce = Akce.objects.filter(projekt=projekt).select_related(
        "archeologicky_zaznam__pristupnost", "hlavni_typ"
    )
    context["akce"] = akce
    soubory = projekt.soubory.soubory.all()
    context["soubory"] = soubory
    context["dalsi_katastry"] = ",".join(
        projekt.katastry.all().values_list("nazev", flat=True)
    )
    context["history_dates"] = get_history_dates(projekt.historie)
    context["show"] = get_detail_template_shows(projekt, request.user)

    return render(request, "projekt/detail.html", context)


# @csrf_exempt
@login_required
@require_http_methods(["POST"])
def post_ajax_get_point(request):
    body = json.loads(request.body.decode("utf-8"))
    # logger.debug(body)
    projekty = get_points_from_envelope(
        body["SouthEast"]["lng"],
        body["SouthEast"]["lat"],
        body["NorthWest"]["lng"],
        body["NorthWest"]["lat"],
    )
    # logger.debug("pocet projektu: "+str(len(projekty)))
    back = []
    for projekt in projekty:
        # logger.debug('%s %s %s',projekt.ident_cely,projekt.lat,projekt.lng)
        back.append(
            {
                "id": projekt.id,
                "ident_cely": projekt.ident_cely,
                "lat": projekt.lat,
                "lng": projekt.lng,
            }
        )
    if len(projekty) > 0:
        return JsonResponse({"points": back}, status=200)
    else:
        return JsonResponse({"points": []}, status=200)


@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    if request.method == "POST":
        form_projekt = CreateProjektForm(request.POST)
        form_oznamovatel = OznamovatelForm(request.POST)
        if form_projekt.is_valid():
            logger.debug("Form is valid")
            lat = form_projekt.cleaned_data["latitude"]
            long = form_projekt.cleaned_data["longitude"]
            p = form_projekt.save(commit=False)
            if long and lat:
                p.geom = Point(long, lat)
            p.set_permanent_ident_cely()
            p.save()
            p.set_zapsany(request.user)
            form_projekt.save_m2m()
            if p.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
                # Vytvoreni oznamovatele
                if form_oznamovatel.is_valid():
                    oznamovatel = form_oznamovatel.save(commit=False)
                    oznamovatel.projekt = p
                    oznamovatel.save()
                    messages.add_message(
                        request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN
                    )
                    return redirect("projekt:detail", ident_cely=p.ident_cely)
                else:
                    logger.debug("The form oznamovatel is not valid!")
                    logger.debug(form_oznamovatel.errors)
            else:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
                return redirect("projekt:detail", ident_cely=p.ident_cely)
        else:
            logger.debug("The form projekt is not valid!")
            logger.debug(form_projekt.errors)
    else:
        form_projekt = CreateProjektForm()
        form_oznamovatel = OznamovatelForm()
    return render(
        request,
        "projekt/create.html",
        {
            "form_projekt": form_projekt,
            "form_oznamovatel": form_oznamovatel,
            "title": _("Zápis projektu"),
            "header": _("Zápis projektu"),
            "button": _("Zapsat projekt"),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        form = EditProjektForm(request.POST, instance=projekt)
        if form.is_valid():
            logger.debug("Form is valid")
            lat = form.cleaned_data["latitude"]
            long = form.cleaned_data["longitude"]
            # Workaroud to not check if long and lat has been changed, only geom is interesting
            form.fields["latitude"].initial = lat
            form.fields["longitude"].initial = long
            p = form.save()
            old_geom = p.geom
            new_geom = Point(long, lat)
            geom_changed = False
            if old_geom is None or new_geom.coords != old_geom.coords:
                p.geom = new_geom
                p.save()
                geom_changed = True
                logger.debug("Geometry successfully updated: " + str(p.geom))
            else:
                logger.warning("Projekt geom not updated.")
            if form.changed_data or geom_changed:
                logger.debug(form.changed_data)
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("projekt:detail", ident_cely=ident_cely)
        else:
            logger.debug("The form is not valid!")
            logger.debug(form.errors)

    else:
        form = EditProjektForm(instance=projekt)
        if projekt.geom is not None:
            form.fields["latitude"].initial = projekt.geom.coords[1]
            form.fields["longitude"].initial = projekt.geom.coords[0]
        else:
            logger.warning("Projekt geom is empty.")
    return render(
        request,
        "projekt/edit.html",
        {"form_projekt": form, "projekt": projekt},
    )


@login_required
@allowed_user_groups([ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID])
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        resp = projekt.delete()
        logger.debug("Projekt smazan: " + str(resp))
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        return redirect("/projekt/list")
    else:
        warnings = projekt.check_pred_smazanim()
        logger.debug(warnings)
        context = {"objekt": projekt}
        if warnings:
            context["warnings"] = warnings
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_SMAZAT)

        return render(request, "core/smazat.html", context)


@login_required
@require_http_methods(["POST"])
def odebrat_sloupec_z_vychozich(request):
    if request.method == "POST":
        if "projekt_vychozi_skryte_sloupce" not in request.session:
            request.session["projekt_vychozi_skryte_sloupce"] = []
        sloupec = json.loads(request.body.decode("utf8"))["sloupec"]
        zmena = json.loads(request.body.decode("utf8"))["zmena"]
        skryte_sloupce = request.session["projekt_vychozi_skryte_sloupce"]
        if zmena == "zobraz":
            try:
                skryte_sloupce.remove(sloupec)
            except ValueError:
                logger.error(
                    f"projekt.odebrat_sloupec_z_vychozich nelze odebrat sloupec {sloupec}"
                )
                HttpResponse(f"Nelze odebrat sloupec {sloupec}", status=400)
        else:
            skryte_sloupce.append(sloupec)
        request.session.modified = True
    return HttpResponse("Odebráno")


class ProjektListView(ExportMixin, LoginRequiredMixin, SingleTableMixin, FilterView):
    table_class = ProjektTable
    model = Projekt
    template_name = "projekt/projekt_list.html"
    filterset_class = ProjektFilter
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["export_formats"] = ["csv", "json", "xlsx"]
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related(
            "kulturni_pamatka",
            "typ_projektu",
            "hlavni_katastr",
            "organizace",
            "vedouci_projektu",
            "hlavni_katastr__okres",
        ).defer("geom")
        return qs


@login_required
@require_http_methods(["GET", "POST"])
def schvalit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_OZNAMENY:
        raise PermissionDenied()
    if request.method == "POST":
        projekt.set_schvaleny(request.user)
        projekt.set_permanent_ident_cely()
        logger.debug(
            "Projektu "
            + ident_cely
            + " byl prirazen permanentni ident "
            + projekt.ident_cely
        )
        projekt.save()
        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_SCHVALEN)
        return redirect("/projekt/detail/" + projekt.ident_cely)
    context = {
        "object": projekt,
        "title": _("Schválení projektu"),
        "header": _("Schválení projektu"),
        "button": _("Schválit projekt"),
    }
    return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def prihlasit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_ZAPSANY:
        raise PermissionDenied()
    if request.method == "POST":
        form = PrihlaseniProjektForm(request.POST, instance=projekt)
        if form.is_valid():
            projekt = form.save(commit=False)
            projekt.set_prihlaseny(request.user)
            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_PRIHLASEN)
            return redirect("/projekt/detail/" + ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = PrihlaseniProjektForm(
            instance=projekt, initial={"organizace": request.user.organizace}
        )
    return render(request, "projekt/prihlasit.html", {"form": form, "projekt": projekt})


@login_required
@require_http_methods(["GET", "POST"])
def zahajit_v_terenu(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_PRIHLASENY:
        raise PermissionDenied()
    if request.method == "POST":
        form = ZahajitVTerenuForm(request.POST, instance=projekt)

        if form.is_valid():
            projekt = form.save(commit=False)
            projekt.set_zahajeny_v_terenu(request.user)
            messages.add_message(
                request, messages.SUCCESS, PROJEKT_USPESNE_ZAHAJEN_V_TERENU
            )
            return redirect("/projekt/detail/" + ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = ZahajitVTerenuForm(instance=projekt)
    return render(
        request,
        "projekt/transakce_v_terenu.html",
        {
            "form": form,
            "object": projekt,
            "title": "Zahájení v terénu",
            "header": "Zahájení v terénu",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def ukoncit_v_terenu(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_ZAHAJENY_V_TERENU:
        raise PermissionDenied()
    if request.method == "POST":
        form = UkoncitVTerenuForm(request.POST, instance=projekt)
        if form.is_valid():
            projekt = form.save(commit=False)
            projekt.set_ukoncen_v_terenu(request.user)
            messages.add_message(
                request, messages.SUCCESS, PROJEKT_USPESNE_UKONCEN_V_TERENU
            )
            return redirect("/projekt/detail/" + ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = UkoncitVTerenuForm(instance=projekt)
    return render(
        request,
        "projekt/transakce_v_terenu.html",
        {
            "form": form,
            "object": projekt,
            "title": "Ukončení v terénu",
            "header": "Ukončení v terénu",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def uzavrit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_UKONCENY_V_TERENU:
        raise PermissionDenied()
    if request.method == "POST":
        # Move all events to state A2
        akce = Akce.objects.filter(projekt=projekt)
        for a in akce:
            if a.archeologicky_zaznam.stav == AZ_STAV_ZAPSANY:
                logger.debug("Setting event to state A2")
                a.archeologicky_zaznam.set_odeslany(request.user)
                for dokument_cast in a.archeologicky_zaznam.casti_dokumentu.all():
                    if dokument_cast.dokument.stav == D_STAV_ZAPSANY:
                        logger.debug("Setting dokument to state D2")
                        dokument_cast.dokument.set_odeslany(request.user)
        projekt.set_uzavreny(request.user)
        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_UZAVREN)
        return redirect("/projekt/detail/" + ident_cely)
    else:
        # Check business rules
        warnings = projekt.check_pred_uzavrenim()
        logger.debug(warnings)
        context = {"object": projekt}
        if warnings:
            context["warnings"] = []
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_UZAVRIT)
            for item in warnings.items():
                context["warnings"].append(item)
        else:
            pass
        context["title"] = _("Uzavření projektu")
        context["header"] = _("Uzavření projektu")
        context["button"] = _("Uzavřít projekt")

        return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav != PROJEKT_STAV_UZAVRENY:
        raise PermissionDenied()
    if request.method == "POST":
        projekt.set_archivovany(request.user)
        projekt.save()
        # Removing personal information from the projekt announcement
        projekt.oznamovatel.remove_data()

        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_ARCHIVOVAN)
        return redirect("/projekt/detail/" + ident_cely)
    else:
        warnings = projekt.check_pred_archivaci()
        logger.debug(warnings)
        context = {"object": projekt}
        if warnings:
            context["warnings"] = []
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_ARCHIVOVAT)
            for key, value in warnings.items():
                context["warnings"].append((key, value))
        else:
            pass
    context["title"] = _("Archivace projektu")
    context["header"] = _("Archivace projektu")
    context["button"] = _("Archivovat projekt")
    return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def navrhnout_ke_zruseni(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if not PROJEKT_STAV_ARCHIVOVANY > projekt.stav > PROJEKT_STAV_OZNAMENY:
        raise PermissionDenied()
    if request.method == "POST":
        form = NavrhnoutZruseniProjektForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            projekt.set_navrzen_ke_zruseni(request.user, duvod)
            projekt.save()
            messages.add_message(
                request, messages.SUCCESS, PROJEKT_USPESNE_NAVRZEN_KE_ZRUSENI
            )
            return redirect("/projekt/detail/" + ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        warnings = projekt.check_pred_navrzeni_k_zruseni()
        logger.debug(warnings)
        context = {"projekt": projekt}
        if warnings:
            context["warnings"] = []
            messages.add_message(
                request, messages.ERROR, PROJEKT_NELZE_NAVRHNOUT_KE_ZRUSENI
            )
            for key, value in warnings.items():
                context["warnings"].append((key, value))
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        else:
            pass

        context["form"] = NavrhnoutZruseniProjektForm()
    return render(request, "projekt/navrhnout_zruseni.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def zrusit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if projekt.stav not in [PROJEKT_STAV_NAVRZEN_KE_ZRUSENI, PROJEKT_STAV_OZNAMENY]:
        raise PermissionDenied()
    if request.method == "POST":
        projekt.set_zruseny(request.user)
        projekt.save()
        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_ZRUSEN)
        return redirect("/projekt/detail/" + ident_cely)
    else:
        context = {
            "object": projekt,
            "title": _("Zrušení projektu"),
            "header": _("Zrušení projektu"),
            "button": _("Zrušit projekt"),
        }
    return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if not PROJEKT_STAV_ARCHIVOVANY >= projekt.stav > PROJEKT_STAV_ZAPSANY:
        raise PermissionDenied()
    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            projekt.set_vracen(request.user, projekt.stav - 1, duvod)
            projekt.save()
            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_VRACEN)
            return redirect("/projekt/detail/" + ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitForm()
    return render(request, "core/vratit.html", {"form": form, "objekt": projekt})


@login_required
@require_http_methods(["GET", "POST"])
def vratit_navrh_zruseni(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)

    if projekt.stav not in [
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
        PROJEKT_STAV_ZRUSENY,
    ]:
        raise PermissionDenied()

    if request.method == "POST":
        form = VratitForm(request.POST)
        if form.is_valid():
            duvod = form.cleaned_data["reason"]
            projekt.set_znovu_zapsan(request.user, duvod)
            projekt.save()
            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_VRACEN)
            return redirect("/projekt/detail/" + ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = VratitForm()
    return render(request, "core/vratit.html", {"form": form, "objekt": projekt})


def get_history_dates(historie_vazby):
    # Transakce do stavu "Zapsan" jsou 2
    historie = {
        "datum_oznameni": historie_vazby.get_last_transaction_date(OZNAMENI_PROJ),
        "datum_zapsani": historie_vazby.get_last_transaction_date(
            [
                VRACENI_NAVRHU_ZRUSENI,
                SCHVALENI_OZNAMENI_PROJ,
                ZAPSANI_PROJ,
                VRACENI_ZRUSENI,
            ]
        ),
        "datum_prihlaseni": historie_vazby.get_last_transaction_date(PRIHLASENI_PROJ),
        "datum_zahajeni_v_terenu": historie_vazby.get_last_transaction_date(
            ZAHAJENI_V_TERENU_PROJ
        ),
        "datum_ukonceni_v_terenu": historie_vazby.get_last_transaction_date(
            UKONCENI_V_TERENU_PROJ
        ),
        "datum_uzavreni": historie_vazby.get_last_transaction_date(UZAVRENI_PROJ),
        "datum_archivace": historie_vazby.get_last_transaction_date(ARCHIVACE_PROJ),
        "datum_navrhu_ke_zruseni": historie_vazby.get_last_transaction_date(
            NAVRZENI_KE_ZRUSENI_PROJ
        ),
        "datum_zruseni": historie_vazby.get_last_transaction_date(
            RUSENI_PROJ
        ),
    }
    return historie


def get_detail_template_shows(projekt, user):
    show_oznamovatel = (
        projekt.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID
        and projekt.has_oznamovatel()
    )
    show_prihlasit = projekt.stav == PROJEKT_STAV_ZAPSANY
    show_vratit = PROJEKT_STAV_ARCHIVOVANY >= projekt.stav > PROJEKT_STAV_ZAPSANY
    show_schvalit = projekt.stav == PROJEKT_STAV_OZNAMENY
    show_zahajit = projekt.stav == PROJEKT_STAV_PRIHLASENY
    show_ukoncit = projekt.stav == PROJEKT_STAV_ZAHAJENY_V_TERENU
    show_uzavrit = projekt.stav == PROJEKT_STAV_UKONCENY_V_TERENU
    show_archivovat = projekt.stav == PROJEKT_STAV_UZAVRENY
    show_navrzen_ke_zruseni = projekt.stav not in [
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
        PROJEKT_STAV_ZRUSENY,
        PROJEKT_STAV_ARCHIVOVANY,
        PROJEKT_STAV_OZNAMENY,
    ]
    show_zrusit = projekt.stav in [
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    ]
    show_znovu_zapsat = projekt.stav in [
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
        PROJEKT_STAV_ZRUSENY,
    ]
    show_samostatne_nalezy = projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID
    archivar_group = Group.objects.get(id=ROLE_ARCHIVAR_ID)
    admin_group = Group.objects.get(id=ROLE_ADMIN_ID)
    if user.hlavni_role == archivar_group or user.hlavni_role == admin_group:
        show_pridat_akci = (
            PROJEKT_STAV_PRIHLASENY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY
        )
    else:
        show_pridat_akci = (
            PROJEKT_STAV_PRIHLASENY < projekt.stav < PROJEKT_STAV_UZAVRENY
        )
    show_edit = projekt.stav not in [
        PROJEKT_STAV_ARCHIVOVANY,
    ]
    show = {
        "oznamovatel": show_oznamovatel,
        "prihlasit_link": show_prihlasit,
        "vratit_link": show_vratit,
        "schvalit_link": show_schvalit,
        "zahajit_teren_link": show_zahajit,
        "ukoncit_teren_link": show_ukoncit,
        "uzavrit_link": show_uzavrit,
        "archivovat_link": show_archivovat,
        "navrhnout_zruseni_link": show_navrzen_ke_zruseni,
        "zrusit_link": show_zrusit,
        "znovu_zapsat_link": show_znovu_zapsat,
        "samostatne_nalezy": show_samostatne_nalezy,
        "pridat_akci": show_pridat_akci,
        "editovat": show_edit,
    }
    return show
