import logging

from core import constants as c
from core.constants import PROJEKT_FILE_TYPE
from core.models import SouborVazby
from django.contrib.gis.geos import Point
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from heslar import hesla
from heslar.models import Heslar

from .forms import FormWithCaptcha, OznamovatelForm, ProjektOznameniForm, UploadFileForm

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def index(request):

    # TODO rewrite so that multiple files can be uploaded
    # https://www.brennantymrak.com/articles/django-dynamic-formsets-javascript

    if request.method == "POST":
        form_ozn = OznamovatelForm(request.POST)
        form_projekt = ProjektOznameniForm(request.POST)
        form_file = UploadFileForm(request.POST, request.FILES)
        form_captcha = FormWithCaptcha(request.POST)

        if form_ozn.is_valid() and form_projekt.is_valid() and form_file.is_valid():
            logger.debug("Form is valid")

            # Create child objects to the project object
            sv = SouborVazby(typ_vazby=PROJEKT_FILE_TYPE)
            sv.save()

            o = form_ozn.save()
            logger.debug("Saving object: " + str(o))
            p = form_projekt.save(commit=False)
            p.stav = c.PROJEKT_STAV_OZNAMENY
            p.typ_projektu = Heslar.objects.get(id=hesla.PROJEKT_ZACHRANNY_ID)
            p.oznamovatel = o
            p.soubory = sv
            # TODO retrieve gps coordinates from the request and create a point from them
            # longitude = request.POST[]
            # latitude = request.POST[]
            p.geom = Point(5, 23)
            p.save()
            logger.debug("Saving object: " + str(p))

            # soubor = request.FILES.get("soubor")

            # s = Soubor(
            #    path=soubor,
            #    vazba=sv,
            #    #nazev_zkraceny=
            #    nazev_puvodni=soubor.name,
            #    # vlastnik= ??
            #    mimetype="aaa"
            #    size_bytes=soubor.size,
            #    typ_souboru=OTHER_PROJECT_FILES,
            # )
            # s.save()

            context = {"ident_cely": p.ident_cely, "email": o.email}
            return render(request, "oznameni/success.html", {"context": context})
        else:
            logger.debug("One of the forms is not valid")
            logger.debug(form_ozn.errors)
            logger.debug(form_projekt.errors)
            logger.debug(form_file.errors)

    else:
        form_ozn = OznamovatelForm()
        form_projekt = ProjektOznameniForm()
        form_file = UploadFileForm()
        form_captcha = FormWithCaptcha()

    return render(
        request,
        "oznameni/index.html",
        {
            "form_oznamovatel": form_ozn,
            "form_projekt": form_projekt,
            "form_file": form_file,
            "form_captcha": form_captcha,
        },
    )
