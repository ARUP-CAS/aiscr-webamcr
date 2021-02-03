import logging

from arch_z.models import Akce
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from oznameni.models import Oznamovatel
from projekt.models import Projekt

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    oznamovatel = get_object_or_404(Oznamovatel, projekt=projekt)
    akce = Akce.objects.filter(projekt=projekt)

    context["projekt"] = projekt
    context["oznamovatel"] = oznamovatel
    context["akce"] = akce

    return render(request, "projekt/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, ident_cely):
    return HttpResponse("Not implemented yet")


class ProjektListView(LoginRequiredMixin, ListView):
    model = Projekt
    paginate_by = 50  # if pagination is desired
    queryset = Projekt.objects.prefetch_related("katastry")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@login_required
@require_http_methods(["GET", "POST"])
def prihlasit(request, ident_cely):
    return HttpResponse("Not implemented yet")


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
