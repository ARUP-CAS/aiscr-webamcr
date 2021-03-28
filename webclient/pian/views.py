import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
# Create your views here.


logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def detail(request):
    context = {}
    return render(request, "detail.html", context)