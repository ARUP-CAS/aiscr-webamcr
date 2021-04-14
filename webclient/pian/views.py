import logging

from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from pian.models import Pian

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request):
    context = {}
    return render(request, "pian/detail.html", context)


class PianAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Pian.objects.all()
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return qs
