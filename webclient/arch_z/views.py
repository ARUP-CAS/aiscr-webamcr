import logging

from arch_z.models import ArcheologickyZaznam
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from dokument.models import Dokument

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request, ident_cely):
    context = {}
    zaznam = get_object_or_404(ArcheologickyZaznam, ident_cely=ident_cely)
    # TODO continue here
    dokumenty = Dokument.objects.all()[:10]

    context["zaznam"] = zaznam
    context["dokumenty"] = dokumenty

    return render(request, "arch_z/detail.html", context)
