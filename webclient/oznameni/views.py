import logging

from core import constants as c
from core.constants import OTHER_PROJECT_FILES, PROJEKT_FILE_TYPE
from core.models import Soubor, SouborVazby
from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from heslar import hesla
from heslar.models import Heslar
from uzivatel.models import AuthUser

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
            logger.debug("Saving announcer object: " + str(o))
            p = form_projekt.save(commit=False)
            p.stav = c.PROJEKT_STAV_OZNAMENY
            p.typ_projektu = Heslar.objects.get(id=hesla.PROJEKT_ZACHRANNY_ID)
            p.oznamovatel = o
            p.soubory = sv
            longitude = request.POST.get("id_longitude")
            latitude = request.POST.get("id_latitude")
            # TODO map main cadastre based on the geom
            p.geom = Point(longitude, latitude)
            p.save()
            logger.debug("Saving project object: " + str(p))

            soubor = request.FILES.get("soubor")
            logger.debug("Soubor  : " + str(request.FILES))
            if soubor:
                s = Soubor(
                    path=soubor,
                    vazba=sv,
                    # TODO set correct short name
                    nazev_zkraceny="aaa",
                    nazev_puvodni=soubor.name,
                    # Default files owner amcr@arup.cas.cz
                    vlastnik=get_object_or_404(AuthUser, email="amcr@arup.cas.cz"),
                    # TODO set correct mimetype
                    mimetype="aaa",
                    size_bytes=soubor.size,
                    typ_souboru=OTHER_PROJECT_FILES,
                )
                logger.debug("Saving file object: " + str(s))
                s.save()
            else:
                logger.debug("No file attached to the announcement form.")

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
