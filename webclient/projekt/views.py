import logging

from arch_z.models import Akce
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
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

    logger.info("Actions of the project: " + str(len(akce)))

    context["projekt"] = projekt
    context["oznamovatel"] = oznamovatel
    context["akce"] = akce

    return render(request, "projekt/detail.html", context)
