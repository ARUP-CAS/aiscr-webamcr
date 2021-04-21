import logging
import mimetypes
import os
from datetime import datetime

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
    SCHVALENI_OZNAMENI_PROJ,
    UKONCENI_V_TERENU_PROJ,
    UZAVRENI_PROJ,
    ZAHAJENI_V_TERENU_PROJ,
)
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
    ZAZNAM_SE_NEPOVEDLO_SMAZAT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_SMAZAN,
)
from core.models import Soubor
from core.utils import get_points_from_envelope
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from heslar.hesla import TYP_PROJEKTU_PRUZKUM_ID, TYP_PROJEKTU_ZACHRANNY_ID
from oznameni.models import Oznamovatel
from projekt.filters import ProjektFilter
from projekt.forms import (
    EditProjektForm,
    NavrhnoutZruseniProjektForm,
    PrihlaseniProjektForm,
    UkoncitVTerenuForm,
    ZahajitVTerenuForm,
)
from projekt.models import Projekt
from projekt.tables import ProjektTable

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    projekt = get_object_or_404(
        Projekt.objects.select_related(
            "kulturni_pamatka", "typ_projektu", "vedouci_projektu", "organizace"
        ).defer("geom"),
        ident_cely=ident_cely,
    )
    context["projekt"] = projekt
    typ_projektu = projekt.typ_projektu
    if typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
        oznamovatel = get_object_or_404(Oznamovatel, projekt=projekt)
        context["oznamovatel"] = oznamovatel
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
    context["show"] = get_detail_template_shows(projekt)

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
def edit(request, ident_cely):
    projekt = Projekt.objects.get(ident_cely=ident_cely)
    if request.method == "POST":
        form = EditProjektForm(request.POST, instance=projekt)
        if form.is_valid():
            logger.debug("Form is valid")
            logger.debug(request.POST)
            if projekt.geom is not None:
                form.fields["latitude"].initial = projekt.geom.coords[1]
                form.fields["longitude"].initial = projekt.geom.coords[0]

            form.save()
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.debug("The form is not valid!")
            logger.debug(form.errors)

    else:
        form = EditProjektForm(instance=projekt)
        if projekt.geom is not None:
            form.fields["latitude"].initial = projekt.geom.coords[1]
            form.fields["longitude"].initial = projekt.geom.coords[0]
    return render(
        request,
        "projekt/edit.html",
        {"form_projekt": form, "projekt": projekt},
    )


@login_required
@require_http_methods(["GET", "POST"])
def smazat(request, ident_cely):
    projekt = Projekt.objects.get(ident_cely=ident_cely)
    if request.method == "POST":
        resp = projekt.delete()
        logger.debug("Projekt smazan: " + str(resp))
        messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)
        return redirect("/projekt/list")
    else:
        warnings = projekt.check_pred_smazanim()
        logger.debug(warnings)
        context = {"object": projekt}
        if warnings:
            context["warnings"] = warnings
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_SMAZAT)

        return render(request, "projekt/smazat.html", context)


class ProjektListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    table_class = ProjektTable
    model = Projekt
    template_name = "projekt/projekt_list.html"
    filterset_class = ProjektFilter

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related(
            "kulturni_pamatka",
            "typ_projektu",
            "hlavni_katastr",
            "organizace",
            "vedouci_projektu",
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
        projekt.save()
        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_SCHVALEN)
        return redirect("/projekt/detail/" + ident_cely)
    return render(request, "projekt/schvalit.html", {"projekt": projekt})


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
            projekt.save()
            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_PRIHLASEN)
            return redirect("/projekt/detail/" + ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)
    else:
        form = PrihlaseniProjektForm(instance=projekt)
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
            projekt.save()
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
        request, "projekt/zahajit_v_terenu.html", {"form": form, "projekt": projekt}
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
            projekt.save()
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
        request, "projekt/ukonceni_v_terenu.html", {"form": form, "projekt": projekt}
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
        projekt.set_uzavreny(request.user)
        projekt.save()
        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_UZAVREN)
        return redirect("/projekt/detail/" + ident_cely)
    else:
        # Check business rules
        warnings = projekt.check_pred_uzavrenim()
        logger.debug(warnings)
        context = {"projekt": projekt}
        if warnings:
            context["warnings"] = []
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_UZAVRIT)
            for key, value in warnings.items():
                context["warnings"].append((key, value))
        else:
            pass

        return render(request, "projekt/uzavrit.html", context)


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
        value = "Údaj odstraněn (" + str(datetime.today().date()) + ")"
        o = projekt.oznamovatel
        o.oznamovatel = value
        o.odpovedna_osoba = value
        o.adresa = value
        o.telefon = value
        o.email = value
        o.save()

        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_ARCHIVOVAN)
        return redirect("/projekt/detail/" + ident_cely)
    else:
        warnings = projekt.check_pred_archivaci()
        logger.debug(warnings)
        context = {"projekt": projekt}
        if warnings:
            context["warnings"] = []
            messages.add_message(request, messages.ERROR, PROJEKT_NELZE_ARCHIVOVAT)
            for key, value in warnings.items():
                context["warnings"].append((key, value))
        else:
            pass
    return render(request, "projekt/archivovat.html", context)


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
        else:
            pass

        context["form"] = NavrhnoutZruseniProjektForm()
    return render(request, "projekt/navrhnout_zruseni.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def zrusit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if (
        not projekt.stav == PROJEKT_STAV_NAVRZEN_KE_ZRUSENI
        or projekt.stav == PROJEKT_STAV_OZNAMENY
    ):
        raise PermissionDenied()
    if request.method == "POST":
        projekt.set_zruseny(request.user)
        projekt.save()
        messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_ZRUSEN)
        return redirect("/projekt/detail/" + ident_cely)
    else:
        pass
    return render(request, "projekt/zrusit.html", {"projekt": projekt})


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if not PROJEKT_STAV_ARCHIVOVANY >= projekt.stav > PROJEKT_STAV_OZNAMENY:
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

    if PROJEKT_STAV_NAVRZEN_KE_ZRUSENI != projekt.stav:
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


@login_required
@require_http_methods(["GET"])
def upload_file(request, ident_cely):
    return render(request, "projekt/upload_file.html", {"ident_cely": ident_cely})


@login_required
@require_http_methods(["POST", "GET"])
def delete_file(request, pk):
    s = get_object_or_404(Soubor, pk=pk)
    projekt = s.vazba.projekt_set.all()[0]
    if request.method == "POST":
        items_deleted = s.delete()
        if not items_deleted:
            # Not sure if 404 is the only correct option
            logger.debug("Soubor " + str(items_deleted) + " nebyl smazan.")
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_SMAZAT)
            return redirect("/projekt/detail/" + projekt.ident_cely)
        else:
            logger.debug("Byl smazán soubor: " + str(items_deleted))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_SMAZAN)

        return redirect("/projekt/detail/" + projekt.ident_cely)
    else:
        return render(request, "projekt/delete_file.html", {"soubor": s})


@login_required
@require_http_methods(["GET"])
def download_file(request, pk):
    soubor = get_object_or_404(Soubor, id=pk)
    path = os.path.join(settings.MEDIA_ROOT, soubor.path.name)
    if os.path.exists(path):
        content_type = mimetypes.guess_type(soubor.path.name)[
            0
        ]  # Use mimetypes to get file type
        response = HttpResponse(soubor.path, content_type=content_type)
        response["Content-Length"] = str(len(soubor.path))
        response["Content-Disposition"] = "inline; filename=" + os.path.basename(
            soubor.nazev
        )
        return response
    else:
        logger.debug(
            "File " + str(soubor.nazev) + " does not exists at location " + str(path)
        )
    raise Http404


def get_history_dates(historie_vazby):
    historie = {
        "datum_oznameni": historie_vazby.get_last_transaction_date(OZNAMENI_PROJ),
        "datum_zapsani": historie_vazby.get_last_transaction_date(
            SCHVALENI_OZNAMENI_PROJ
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
    }
    return historie


def get_detail_template_shows(projekt):
    show_oznamovatel = projekt.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID
    show_prihlasit = projekt.stav == PROJEKT_STAV_ZAPSANY
    show_vratit = PROJEKT_STAV_ARCHIVOVANY >= projekt.stav > PROJEKT_STAV_OZNAMENY
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
        PROJEKT_STAV_OZNAMENY,
        PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    ]
    show_znovu_zapsat = projekt.stav == PROJEKT_STAV_NAVRZEN_KE_ZRUSENI
    show_samostatne_nalezy = projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID
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
    }
    return show
