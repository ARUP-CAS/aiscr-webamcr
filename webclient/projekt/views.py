import logging

import simplejson as json
from arch_z.models import Akce
from core.utils import get_points_from_envelope
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from oznameni.models import Oznamovatel
from projekt.forms import ProjektForm
from projekt.models import Projekt

# from django.views.decorators.csrf import csrf_exempt

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
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    if request.method == "POST":
        form_projekt = ProjektForm(request.POST, instance=projekt)
        if form_projekt.is_valid():
            logger.debug("Form is valid")
            logger.debug(request.POST)
            form_projekt.fields["latitude"].initial = projekt.geom.coords[1]
            form_projekt.fields["longitude"].initial = projekt.geom.coords[0]

            return render(
                request,
                "projekt/edit.html",
                {
                    "form_projekt": form_projekt,
                },
            )
        else:
            logger.debug("form is not valid!")
            logger.debug(form_projekt.errors)

        return HttpResponse("Post Not implemented yet")
    elif request.method == "GET":

        form_projekt = ProjektForm(instance=projekt)
        form_projekt.fields["latitude"].initial = projekt.geom.coords[1]
        form_projekt.fields["longitude"].initial = projekt.geom.coords[0]

        return render(
            request,
            "projekt/edit.html",
            {
                "form_projekt": form_projekt,
            },
        )
    else:
        return HttpResponse("Function Not implemented yet")


class ProjektListView(LoginRequiredMixin, ListView):
    model = Projekt
    paginate_by = 50  # if pagination is desired
    # queryset = Projekt.objects.select_related("kulturni_pamatka").select_related(
    #    "typ_projektu"
    # )

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
