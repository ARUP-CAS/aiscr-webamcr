import logging

import simplejson as json
from django.utils.translation import gettext as _
from core.constants import (
    PRIDANI_OZNAMOVATELE_PROJ,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_VYTVORENY,
)
from core.ident_cely import get_temporary_project_ident
from core.message_constants import ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_USPESNE_EDITOVAN
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
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from core.forms import CheckStavNotChangedForm
from core.views import check_stav_changed
from historie.models import Historie
from core.decorators import odstavka_in_progress

from .forms import FormWithCaptcha, OznamovatelForm, ProjektOznameniForm
from .models import Oznamovatel
from services.mailer import Mailer

logger = logging.getLogger(__name__)


@odstavka_in_progress
@require_http_methods(["GET", "POST"])
def index(request, test_run=False):
    # First step of the form
    if request.method == "POST" and "oznamovatel" in request.POST:
        if request.POST.get("ident_cely"):
            projekt = get_object_or_404(
                Projekt, ident_cely=request.POST.get("ident_cely")
            )
            form_ozn = OznamovatelForm(request.POST, instance=projekt.oznamovatel)
            form_projekt = ProjektOznameniForm(request.POST, instance=projekt)
            ident_cely = projekt.ident_cely
        else:
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
            if p.ident_cely[2:3] == "C":
                Mailer.sendEO01(project=p)
            else:
                Mailer.sendEO02(project=p)
            response = render(request, "oznameni/index_2.html", context)
            response.set_cookie("project", hash(p.ident_cely), 3600)
            return response
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
    elif request.method == "GET" and "ident_cely" in request.GET:
        cookie_project = request.COOKIES.get("project", None)
        ident = request.GET.get("ident_cely")
        logger.debug(ident)
        hash_from_ident = hash(ident)
        logger.debug(hash_from_ident)
        logger.debug(cookie_project)
        if cookie_project is not None and str(hash_from_ident) == str(cookie_project):
            projekty = Projekt.objects.filter(
                ident_cely=request.GET.get("ident_cely"), stav=PROJEKT_STAV_VYTVORENY
            )
            if projekty is None:
                raise PermissionDenied
            else:
                projekt = projekty[0]
                form_ozn = OznamovatelForm(instance=projekt.oznamovatel)
                form_projekt = ProjektOznameniForm(instance=projekt, change=True)
                form_captcha = FormWithCaptcha()
        else:
            raise PermissionDenied
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
def edit(request, ident_cely):
    projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    oznameni = projekt.oznamovatel
    if projekt.stav == PROJEKT_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    if request.method == "POST":
        form = OznamovatelForm(request.POST, instance=oznameni, required_next=True)
        if form.is_valid():
            oznameni = form.save(commit=False)
            oznameni.projekt=projekt
            oznameni.save()
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


class OznamovatelCreateView(TemplateView, LoginRequiredMixin):
    template_name = "core/transakce_modal.html"

    def get_context_data(self, **kwargs):
        ident_cely = self.kwargs.get("ident_cely")
        projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        context = {
            "object": projekt,
            "title": _("projekt.modalForm.pridaniOznamovatele.title.text"),
            "id_tag": "pridat-oznamovatele-form",
            "button": _("projekt.modalForm.pridaniOznamovatele.submit.button"),
            "form_check": form_check,
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if check_stav_changed(request, context["object"]):
            return JsonResponse(
                {"redirect": context["object"].get_absolute_url()},
                status=403,
            )
        form = OznamovatelForm(required_next=True, add_oznamovatel=True)
        context["form"] = form
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        projekt = context["object"]
        if check_stav_changed(request, projekt):
            return JsonResponse(
                {"redirect": projekt.get_absolute_url()},
                status=403,
            )
        form = OznamovatelForm(request.POST, required_next=True, add_oznamovatel=True)
        if form.is_valid():
            ozn = form.save(commit=False)
            ozn.projekt = projekt
            ozn.save()
            Historie(
                typ_zmeny=PRIDANI_OZNAMOVATELE_PROJ,
                uzivatel=request.user,
                vazba=projekt.historie,
            ).save()

            logger.debug("Pridan oznamovatel do projektu: " + str(projekt.ident_cely))
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

        return JsonResponse({"redirect": projekt.get_absolute_url()})