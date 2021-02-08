import logging

import simplejson as json
from core.constants import OTHER_PROJECT_FILES
from core.ident_cely import get_temporary_project_ident
from core.models import Soubor
from core.utils import calculate_crc_32, get_cadastre_from_point, get_mime_type
from django.contrib.gis.geos import Point
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from heslar.hesla import TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar
from projekt.models import Projekt, ProjektKatastr
from uzivatel.models import User

from .forms import FormWithCaptcha, OznamovatelForm, ProjektOznameniForm

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def index(request):
    # First step of the form
    if request.method == "POST" and "oznamovatel" in request.POST:
        form_ozn = OznamovatelForm(request.POST)
        form_projekt = ProjektOznameniForm(request.POST)
        form_captcha = FormWithCaptcha(request.POST)

        if form_ozn.is_valid() and form_projekt.is_valid() and form_captcha.is_valid():
            logger.debug("Form is valid")
            o = form_ozn.save()
            p = form_projekt.save(commit=False)
            p.typ_projektu = Heslar.objects.get(pk=TYP_PROJEKTU_ZACHRANNY_ID)
            dalsi_katastry = form_projekt.cleaned_data["katastry"]
            p.geom = Point(
                float(request.POST.get("longitude")),
                float(request.POST.get("latitude")),
            )
            katastr = get_cadastre_from_point(p.geom)
            p.save()
            p.set_oznameny(o)
            p.save()
            p.katastry.add(*[int(i) for i in dalsi_katastry])
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

            confirmation = {
                "oznamovatel": o.oznamovatel,
                "zastupce": o.odpovedna_osoba,
                "adresa": o.adresa,
                "telefon": o.telefon,
                "email": o.email,
                "katastr": katastr,
                "dalsi_katastry": dalsi_katastry,
                "ident_cely": p.ident_cely,
                "planovane_zahajeni": p.planovane_zahajeni,
                "podnet": p.podnet,
                "lokalizace": p.lokalizace,
                "parcelni_cislo": p.parcelni_cislo,
                "oznaceni_stavby": p.oznaceni_stavby,
            }

            context = {"confirm": confirmation}
            return render(request, "oznameni/index_2.html", context)
        else:
            logger.debug("One of the forms is not valid")
            logger.debug(form_ozn.errors)
            logger.debug(form_projekt.errors)
            logger.debug(form_captcha.errors)

    # Part 2 of the announcement form
    elif request.method == "POST" and "ident_cely" in request.POST:
        context = {"ident_cely": request.POST["ident_cely"]}
        return render(request, "oznameni/success.html", context)

    else:
        form_ozn = OznamovatelForm()
        form_projekt = ProjektOznameniForm()
        form_captcha = FormWithCaptcha()

    return render(
        request,
        "oznameni/index.html",
        {
            "form_oznamovatel": form_ozn,
            "form_projekt": form_projekt,
            "form_captcha": form_captcha,
        },
    )


@require_http_methods(["POST"])
def post_upload(request):
    projekt = get_object_or_404(Projekt, ident_cely=request.POST["projektID"])
    soubor = request.FILES.get("file")
    if soubor:
        checksum = calculate_crc_32(soubor)
        # After calculating checksum, must move pointer to the beginning
        soubor.file.seek(0)
        old_name = soubor.name
        soubor.name = checksum + "_" + soubor.name
        s = Soubor(
            path=soubor,
            vazba=projekt.soubory,
            nazev=soubor.name,
            # Short name is new name without checksum
            nazev_zkraceny=old_name,
            nazev_puvodni=old_name,
            vlastnik=get_object_or_404(User, email="amcr@arup.cas.cz"),
            mimetype=get_mime_type(old_name),
            size_bytes=soubor.size,
            typ_souboru=OTHER_PROJECT_FILES,
        )
        try:
            logger.debug("Saving file object: " + str(s))
            s.save()
            return JsonResponse({"filename": s.nazev_zkraceny}, status=200)
        except IntegrityError:
            logger.warning("Could not save file {}".format(s.nazev))
    else:
        logger.warning("No file attached to the announcement form.")

    return JsonResponse({"filename": ""}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def post_poi2kat(request):
    body = json.loads(request.body.decode("utf-8"))
    # logger.debug(body)
    geom = Point(float(body["corY"]), float(body["corX"]))
    katastr = get_cadastre_from_point(geom)
    # logger.debug(katastr)
    if len(str(katastr)) > 0:
        return JsonResponse({"cadastre": str(katastr)}, status=200)
    else:
        return JsonResponse({"cadastre": ""}, status=200)
