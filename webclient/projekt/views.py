import logging
from datetime import datetime

from arch_z.models import Akce
from core.constants import (
    AZ_STAV_ZAPSANY,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
)
from core.message_constants import (
    PROJEKT_USPESNE_ARCHIVOVAN,
    PROJEKT_USPESNE_PRIHLASEN,
    PROJEKT_USPESNE_SCHVALEN,
    PROJEKT_USPESNE_UKONCEN_V_TERENU,
    PROJEKT_USPESNE_UZAVREN,
    PROJEKT_USPESNE_VRACEN,
    PROJEKT_USPESNE_ZAHAJEN_V_TERENU,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from heslar.hesla import TYP_PROJEKTU_ZACHRANNY_ID
from oznameni.models import Oznamovatel
from projekt.forms import (
    PrihlaseniProjektForm,
    UkoncitVTerenuForm,
    VratitProjektForm,
    ZahajitVTerenuForm,
)
from projekt.models import Projekt

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    oznamovatel = get_object_or_404(Oznamovatel, projekt=projekt)
    akce = Akce.objects.filter(projekt=projekt)

    show_oznamovatel = projekt.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID
    show_prihlasit = projekt.stav == PROJEKT_STAV_ZAPSANY
    show_vratit = PROJEKT_STAV_ARCHIVOVANY >= projekt.stav > PROJEKT_STAV_OZNAMENY
    show_schvalit = projekt.stav == PROJEKT_STAV_OZNAMENY
    show_zahajit = projekt.stav == PROJEKT_STAV_PRIHLASENY
    show_ukoncit = projekt.stav == PROJEKT_STAV_ZAHAJENY_V_TERENU
    show_uzavrit = projekt.stav == PROJEKT_STAV_UKONCENY_V_TERENU
    show_archivovat = projekt.stav == PROJEKT_STAV_UZAVRENY

    context["projekt"] = projekt
    context["oznamovatel"] = oznamovatel
    context["akce"] = akce
    context["show"] = {
        "oznamovatel": show_oznamovatel,
        "prihlasit_link": show_prihlasit,
        "vratit_link": show_vratit,
        "schvalit_link": show_schvalit,
        "zahajit_teren_link": show_zahajit,
        "ukoncit_teren_link": show_ukoncit,
        "uzavrit_link": show_uzavrit,
        "archivovat_link": show_archivovat,
    }

    return render(request, "projekt/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    return HttpResponse("Not implemented yet")


class ProjektListView(LoginRequiredMixin, ListView):
    model = Projekt
    paginate_by = 10  # if pagination is desired
    queryset = (
        Projekt.objects.select_related("kulturni_pamatka")
        .select_related("typ_projektu")
        .select_related("hlavni_katastr")
        .select_related("organizace")
        .select_related("vedouci_projektu")
        .prefetch_related("hlavni_katastr__okres")
        .order_by("id")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["filter"] = ProjektFilter(
        #     self.request.GET,
        #     queryset=self.get_queryset()
        # )
        return context


@login_required
@require_http_methods(["GET", "POST"])
def schvalit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        if projekt.stav == PROJEKT_STAV_OZNAMENY:
            projekt.set_schvaleny(request.user)
            projekt.save()
            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_SCHVALEN)
            return redirect("/projekt/detail/" + ident_cely)
        else:
            return render(request, "403.html")
    return render(request, "projekt/schvalit.html", {"projekt": projekt})


@login_required
@require_http_methods(["GET", "POST"])
def prihlasit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        form = PrihlaseniProjektForm(request.POST, instance=projekt)
        if projekt.stav == PROJEKT_STAV_ZAPSANY:
            if form.is_valid():
                projekt = form.save(commit=False)
                projekt.set_prihlaseny(request.user)
                projekt.save()
                messages.add_message(
                    request, messages.SUCCESS, PROJEKT_USPESNE_PRIHLASEN
                )
                return redirect("/projekt/detail/" + ident_cely)
            else:
                logger.debug("The form is not valid")
                logger.debug(form.errors)
        else:
            return render(request, "403.html")
    else:
        form = PrihlaseniProjektForm(instance=projekt)
    return render(request, "projekt/prihlasit.html", {"form": form, "projekt": projekt})


@login_required
@require_http_methods(["GET", "POST"])
def zahajit_v_terenu(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        form = ZahajitVTerenuForm(request.POST, instance=projekt)
        if projekt.stav == PROJEKT_STAV_PRIHLASENY:
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
            return render(request, "403.html")
    else:
        form = ZahajitVTerenuForm(instance=projekt)
    return render(
        request, "projekt/zahajit_v_terenu.html", {"form": form, "projekt": projekt}
    )


@login_required
@require_http_methods(["GET", "POST"])
def ukoncit_v_terenu(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        form = UkoncitVTerenuForm(request.POST, instance=projekt)
        if projekt.stav == PROJEKT_STAV_ZAHAJENY_V_TERENU:
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
            return render(request, "403.html")
    else:
        form = UkoncitVTerenuForm(instance=projekt)
    return render(
        request, "projekt/ukonceni_v_terenu.html", {"form": form, "projekt": projekt}
    )


@login_required
@require_http_methods(["GET", "POST"])
def uzavrit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        if projekt.stav == PROJEKT_STAV_UKONCENY_V_TERENU:
            projekt.set_uzavreny(request.user)
            projekt.save()

            # Check business rules
            result = projekt.check_pred_uzavrenim()
            logger.debug(result)

            # Move all events to state A2
            akce = Akce.objects.filter(projekt=projekt)
            for a in akce:
                if a.archeologicky_zaznam.stav == AZ_STAV_ZAPSANY:
                    logger.debug("Setting event to state A2")
                    a.set_odeslana(request.user)

            messages.add_message(request, messages.SUCCESS, PROJEKT_USPESNE_UZAVREN)
            return redirect("/projekt/detail/" + ident_cely)
        else:
            return render(request, "403.html")
    return render(request, "projekt/uzavrit.html", {"projekt": projekt})


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        if projekt.stav == PROJEKT_STAV_UZAVRENY:
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
            return render(request, "403.html")
    return render(request, "projekt/archivovat.html", {"projekt": projekt})


@login_required
@require_http_methods(["GET", "POST"])
def navrhnout_ke_zruseni(request, ident_cely):
    return HttpResponse("Not implemented yet")


@login_required
@require_http_methods(["GET", "POST"])
def zrusit(request, ident_cely):
    return HttpResponse("Not implemented yet")


@login_required
@require_http_methods(["GET", "POST"])
def vratit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        form = VratitProjektForm(request.POST)
        if PROJEKT_STAV_ARCHIVOVANY >= projekt.stav > PROJEKT_STAV_OZNAMENY:
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
            return render(request, "403.html")
    else:
        form = VratitProjektForm()
    return render(request, "projekt/vratit.html", {"form": form, "projekt": projekt})
