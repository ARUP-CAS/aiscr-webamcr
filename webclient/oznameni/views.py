import logging

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import OznamovatelForm, ProjektOznameniForm, UploadFileForm

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def index(request):

    if request.method == "POST":
        form_ozn = OznamovatelForm(request.POST)
        form_projekt = ProjektOznameniForm(request.POST)
        form_file = UploadFileForm(request.POST, request.FILES)

        if form_ozn.is_valid() and form_projekt.is_valid() and form_file.is_valid():
            logger.debug("Form is valid")
            return HttpResponse(status=200)
        else:
            logger.debug("One of the forms is not valid")
            logger.debug(form_ozn.errors)
            logger.debug(form_projekt.errors)
            logger.debug(form_file.errors)

    else:
        form_ozn = OznamovatelForm()
        form_projekt = ProjektOznameniForm()
        form_file = UploadFileForm()

    return render(
        request,
        "oznameni/index.html",
        {
            "form_oznamovatel": form_ozn,
            "form_projekt": form_projekt,
            "form_file": form_file,
        },
    )
