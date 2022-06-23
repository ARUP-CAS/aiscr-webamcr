import logging

import simplejson as json
from core.constants import PROJEKT_STAV_ARCHIVOVANY
from core.ident_cely import get_temporary_project_ident
from core.message_constants import ZAZNAM_USPESNE_EDITOVAN
from core.utils import get_cadastre_from_point
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from heslar.hesla import TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar
from projekt.models import Projekt

from .forms import FormWithCaptcha, OznamovatelForm, ProjektOznameniForm
from .models import Oznamovatel

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def index(request, test_run=False):
    # First step of the form
    if request.method == "POST" and "oznamovatel" in request.POST:
        form_ozn = OznamovatelForm(request.POST)
        form_projekt = ProjektOznameniForm(request.POST)
        form_captcha = FormWithCaptcha(request.POST)
        logger.debug(f"oznameni.views.index form_ozn.is_valid {form_ozn.is_valid()}")
        logger.debug(
            f"oznameni.views.index form_projekt.is_valid {form_projekt.is_valid()}"
        )

        if (
            form_ozn.is_valid()
            and form_projekt.is_valid()
            and (test_run or form_captcha.is_valid())
        ):
            logger.debug("Oznameni Form is valid")
            o = form_ozn.save(commit=False)
            p = form_projekt.save(commit=False)
            p.typ_projektu = Heslar.objects.get(pk=TYP_PROJEKTU_ZACHRANNY_ID)
            dalsi_katastry = form_projekt.cleaned_data["katastry"]
            p.geom = Point(
                float(request.POST.get("longitude")),
                float(request.POST.get("latitude")),
            )
            p.hlavni_katastr = get_cadastre_from_point(p.geom)
            logger.debug(p)
            p.save()
            if p.hlavni_katastr is not None:
                p.ident_cely = get_temporary_project_ident(
                    p, p.hlavni_katastr.okres.kraj.rada_id
                )
            else:
                logger.warning(
                    "Unknown cadastre location for point {}".format(str(p.geom))
                )
            p.save()
            o.projekt = p
            o.save()
            p.set_vytvoreny()
            p.katastry.add(*[i for i in dalsi_katastry])

            confirmation = {
                "oznamovatel": o.oznamovatel,
                "zastupce": o.odpovedna_osoba,
                "adresa": o.adresa,
                "telefon": o.telefon,
                "email": o.email,
                "katastr": p.hlavni_katastr,
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
            if not test_run:
                logger.debug(form_captcha.errors)

    # Part 2 of the announcement form
    elif request.method == "POST" and "ident_cely" in request.POST:
        p = Projekt.objects.get(ident_cely=request.POST["ident_cely"])
        p.set_oznameny()
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


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, pk):
    oznameni = Oznamovatel.objects.get(id=pk)
    projekt = get_object_or_404(Projekt, ident_cely=oznameni.projekt.ident_cely)
    if projekt.stav == PROJEKT_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    if request.method == "POST":
        form = OznamovatelForm(request.POST, instance=oznameni, required_next=True)
        if form.is_valid():
            form.save()
            if form.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
            return redirect("/projekt/detail/" + oznameni.projekt.ident_cely)
        else:
            logger.debug("The form is not valid")
            logger.debug(form.errors)

    else:
        form = OznamovatelForm(instance=oznameni, required_next=True)

    return render(request, "oznameni/edit.html", {"form": form, "oznameni": oznameni})


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
