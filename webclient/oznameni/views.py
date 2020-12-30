import logging

from core import constants as c
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from heslar import hesla
from heslar.models import Heslar

from .forms import OznamovatelForm, ProjektOznameniForm, UploadFileForm

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def index(request):

    # TODO rewrite so that multiple files can be uploaded
    # https://www.brennantymrak.com/articles/django-dynamic-formsets-javascript

    if request.method == "POST":
        form_ozn = OznamovatelForm(request.POST)
        form_projekt = ProjektOznameniForm(request.POST)
        form_file = UploadFileForm(request.POST, request.FILES)

        if form_ozn.is_valid() and form_projekt.is_valid() and form_file.is_valid():
            logger.debug("Form is valid")

            o = form_ozn.save()
            logger.debug("Saving object: " + str(o))
            p = form_projekt.save(commit=False)
            p.stav = c.PROJEKT_STAV_OZNAMENY
            p.typ_projektu = Heslar.objects.get(id=hesla.PROJEKT_ZACHRANNY_ID)
            p.oznamovatel = o
            # TODO ulozit bod v mape do p.geom
            p.save()
            logger.debug("Saving object: " + str(p))

            # TODO form_file.save()

            response = HttpResponse("<body>Ahoj</body>", status=200)
            return response
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
