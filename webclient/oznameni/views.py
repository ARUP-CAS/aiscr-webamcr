import logging

from core import constants as c
from core.constants import OTHER_PROJECT_FILES, OZNAMENI_PROJ
from core.ident_cely import get_temporary_project_ident
from core.models import Soubor
from core.utils import calculate_crc_32, get_cadastre_from_point, get_mime_type
from django.contrib.gis.geos import Point
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from heslar import hesla
from heslar.models import Heslar
from historie.models import Historie
from projekt.models import ProjektKatastr
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

            o = form_ozn.save()
            p = form_projekt.save(commit=False)
            p.stav = c.PROJEKT_STAV_OZNAMENY
            p.typ_projektu = Heslar.objects.get(id=hesla.PROJEKT_ZACHRANNY_ID)
            p.oznamovatel = o
            longitude = request.POST.get("longitude")
            latitude = request.POST.get("latitude")
            p.geom = Point(float(longitude), float(latitude))
            katastr = get_cadastre_from_point(p.geom)
            p.save()
            if katastr is not None:
                ProjektKatastr(katastr=katastr, projekt=p, hlavni=True).save()
                p.ident_cely = get_temporary_project_ident(
                    p, katastr.okres.kraj.rada_id
                )
                p.save()
            else:
                logger.warning(
                    "Unknown cadastre location for point {}".format(str(p.geom))
                )

            owner = get_object_or_404(AuthUser, email="amcr@arup.cas.cz")
            Historie(
                typ_zmeny=OZNAMENI_PROJ,
                uzivatel=owner,
                vazba=p.historie,
            ).save()
            soubor = request.FILES.get("soubor")
            if soubor:
                checksum = calculate_crc_32(soubor)
                # After calculating checksum, must move pointer to the beginning
                soubor.file.seek(0)
                old_name = soubor.name
                soubor.name = checksum + "_" + soubor.name
                s = Soubor(
                    path=soubor,
                    vazba=p.soubory,
                    nazev=soubor.name,
                    # Short name is new name without checksum
                    nazev_zkraceny=old_name,
                    nazev_puvodni=old_name,
                    vlastnik=owner,
                    mimetype=get_mime_type(old_name),
                    size_bytes=soubor.size,
                    typ_souboru=OTHER_PROJECT_FILES,
                )
                try:
                    logger.debug("Saving file object: " + str(s))
                    s.save()
                except IntegrityError:
                    # TODO how to handle this? Should just ignore?
                    logger.warning("Could not save file {}".format(s.nazev))
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

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import simplejson as json

@csrf_exempt
@require_http_methods(["POST"])
def post_poi2kat(request):
    body = json.loads(request.body.decode('utf-8'))
    #logger.debug(body)
    geom = Point(float(body['corY']), float(body['corX']))
    katastr = get_cadastre_from_point(geom)
    #logger.debug(katastr)
    if(len(str(katastr))>0):
        return JsonResponse({"cadastre":str(katastr)}, status = 200)
    else:
        return JsonResponse({"cadastre":""}, status = 200)