import logging

from arch_z.models import Akce
from core.constants import PROJEKT_STAV_OZNAMENY
from core.message_constants import PROJEKT_USPESNE_PRIHLASEN
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from heslar.hesla import TYP_PROJEKTU_ZACHRANNY_ID
from oznameni.models import Oznamovatel
from projekt.forms import PrihlaseniProjektForm
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

    context["projekt"] = projekt
    context["oznamovatel"] = oznamovatel
    context["akce"] = akce
    context["show"] = {"oznamovatel": show_oznamovatel}

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
def prihlasit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)

    if request.method == "POST":
        form = PrihlaseniProjektForm(request.POST)

        if projekt.stav == PROJEKT_STAV_OZNAMENY:

            if form.is_valid():
                projekt = form.save(commit=False)
                projekt.set_prihlaseny(request.user)
                projekt.save()

                messages.add_message(
                    request, messages.SUCCESS, PROJEKT_USPESNE_PRIHLASEN
                )

                return redirect("projekt/detail/", ident_cely)
            else:
                logger.debug("The form is not valid")
                logger.debug(form.errors)

        else:
            return render(request, "403.html")
    else:
        form = PrihlaseniProjektForm()

    return render(request, "projekt/prihlasit.html", {"form": form, "projekt": projekt})


@login_required
@require_http_methods(["GET", "POST"])
def zahajit_v_terenu(request, ident_cely):
    return HttpResponse("Not implemented yet")


@login_required
@require_http_methods(["GET", "POST"])
def ukoncit_v_terenu(request, ident_cely):
    return HttpResponse("Not implemented yet")


@login_required
@require_http_methods(["GET", "POST"])
def uzavrit(request, ident_cely):
    return HttpResponse("Not implemented yet")


@login_required
@require_http_methods(["GET", "POST"])
def archivovat(request, ident_cely):
    return HttpResponse("Not implemented yet")


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
    return HttpResponse("Not implemented yet")
