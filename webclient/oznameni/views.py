import logging

import simplejson as json
from django.utils.translation import gettext as _
from core.constants import (
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_VYTVORENY,
    OBLAST_CECHY,
)
from core.ident_cely import get_temporary_project_ident
from core.message_constants import ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_USPESNE_EDITOVAN
from core.repository_connector import FedoraTransaction
from core.utils import get_cadastre_from_point
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from heslar.hesla_dynamicka import TYP_PROJEKTU_ZACHRANNY_ID
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
from django.conf import settings

logger = logging.getLogger(__name__)


@odstavka_in_progress
@require_http_methods(["GET", "POST"])
def index(request, test_run=False):
    """
    Funkce pohledu pro oznámení. Oznámení je dvoustupňové.
    V prvém kroku uživatel zadáva údaje a v druhém je potvrzuje a případně uploaduje soubory.
    """
    logger.debug(f"oznameni.views.index.start", extra={"text_run": test_run})
    try:
        request_test = request.GET["test"].lower()
    except:
        request_test = 'false'
    test_run = test_run or request_test == "true"
    # First step of the form
    if request.method == "POST" and "oznamovatel" in request.POST:
        logger.debug(f"oznameni.views.index.first_part_start")
        ident_cely = request.POST.get("ident_cely", None)
        if ident_cely:
            logger.debug(f"oznameni.views.index.first_part_start.ident_set", extra={"ident_cely": ident_cely})
            projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
            form_ozn = OznamovatelForm(request.POST, instance=projekt.oznamovatel)
            form_projekt = ProjektOznameniForm(request.POST, instance=projekt)
        else:
            logger.debug(f"oznameni.views.index.first_part_start.ident_not_set")
            form_ozn = OznamovatelForm(request.POST)
            form_projekt = ProjektOznameniForm(request.POST)
        form_captcha = FormWithCaptcha(request.POST)
        logger.debug("oznameni.views.index.form_ozn.valid", extra={"valid": form_ozn.is_valid()})
        logger.debug("oznameni.views.index.form_projekt.valid", extra={"valid": form_projekt.is_valid()})
        logger.debug("oznameni.views.index.form_captcha.valid", extra={"valid": form_captcha.is_valid()})
        if (
            form_ozn.is_valid()
            and form_projekt.is_valid()
            and (test_run or settings.SKIP_RECAPTCHA or form_captcha.is_valid())
        ):
            logger.debug("oznameni.views.index.all_forms_valid")
            oznamovatel = form_ozn.save(commit=False)
            projekt: Projekt = form_projekt.save(commit=False)
            fedora_transaction = FedoraTransaction()
            projekt.suppress_signal = True
            projekt.active_transaction = fedora_transaction
            projekt.typ_projektu = Heslar.objects.get(pk=TYP_PROJEKTU_ZACHRANNY_ID)
            dalsi_katastry = form_projekt.cleaned_data["katastry"]
            projekt.geom = Point(
                float(request.POST.get("coordinate_x1")),
                float(request.POST.get("coordinate_x2")),
            )
            projekt.hlavni_katastr = get_cadastre_from_point(projekt.geom)
            logger.debug("oznameni.views.index.hlavni_katastr", extra={"hlavni_katastr": projekt.hlavni_katastr,
                                                                       "transaction": getattr(fedora_transaction,
                                                                                              "uid", None)})
            # p.save()
            if projekt.hlavni_katastr is not None and not ident_cely:
                projekt.ident_cely = get_temporary_project_ident(
                    projekt.hlavni_katastr.okres.kraj.rada_id
                )
            else:
                logger.debug("oznameni.views.index.unknow_location", extra={"point": str(projekt.geom)})
            projekt.save()
            oznamovatel.projekt = projekt
            oznamovatel.save()
            projekt.set_vytvoreny()
            projekt.katastry.add(*[i for i in dalsi_katastry])
            projekt.save()

            confirmation = {
                "oznamovatel": oznamovatel.oznamovatel,
                "zastupce": oznamovatel.odpovedna_osoba,
                "adresa": oznamovatel.adresa,
                "telefon": oznamovatel.telefon,
                "email": oznamovatel.email,
                "katastr": projekt.hlavni_katastr,
                "dalsi_katastry": dalsi_katastry,
                "ident_cely": projekt.ident_cely,
                "planovane_zahajeni": projekt.planovane_zahajeni,
                "podnet": projekt.podnet,
                "lokalizace": projekt.lokalizace,
                "parcelni_cislo": projekt.parcelni_cislo,
                "oznaceni_stavby": projekt.oznaceni_stavby,
            }

            context = {"confirm": confirmation}
            if projekt.ident_cely[2].upper() == OBLAST_CECHY:
                Mailer.send_eo01(project=projekt)
            else:
                Mailer.send_eo02(project=projekt)
            response = render(request, "oznameni/index_2.html", context)
            response.set_cookie("project", hash(projekt.ident_cely), 3600)
            return response
        else:
            extra = {"form_ozn_errors": form_ozn.errors, "form_projekt_errors": form_projekt.errors}
            if not test_run:
                extra["form_captcha_errors"] = form_captcha.errors
            logger.debug("oznameni.views.index.form_not_valid", extra=extra)

    # Part 2 of the announcement form
    elif request.method == "POST" and "ident_cely" in request.POST:
        logger.debug(f"oznameni.views.index.second_part.start", extra={"ident_cely": request.POST["ident_cely"]})
        projekt = Projekt.objects.get(ident_cely=request.POST["ident_cely"])
        fedora_transaction = FedoraTransaction()
        projekt.active_transaction = fedora_transaction
        projekt.set_oznameny()
        projekt.close_active_transaction_when_finished = True
        projekt.save()
        context = {"ident_cely": request.POST["ident_cely"]}
        logger.debug(f"oznameni.views.index.second_part.end",
                     extra={"ident_cely": request.POST["ident_cely"], "transaction": fedora_transaction.uid})
        return render(request, "oznameni/success.html", context)
    elif request.method == "GET" and "ident_cely" in request.GET:
        cookie_project = request.COOKIES.get("project", None)
        ident = request.GET.get("ident_cely")
        logger.debug(f"oznameni.views.index.get.start", extra={"ident_cely": ident})
        hash_from_ident = hash(ident)
        logger.debug(f"oznameni.views.index.get.cookie",
                     extra={"ident_cely": ident, "cookie_project": cookie_project, "hash_from_ident": hash_from_ident})
        if cookie_project is not None and str(hash_from_ident) == str(cookie_project):
            projekty = Projekt.objects.filter(
                ident_cely=request.GET.get("ident_cely"), stav=PROJEKT_STAV_VYTVORENY
            )
            if not projekty:
                logger.debug(f"oznameni.views.index.get.permission_denied",
                             extra={"ident_cely": ident, "cookie_project": cookie_project,
                                    "hash_from_ident": hash_from_ident})
                raise PermissionDenied
            else:
                projekt = projekty[0]
                form_ozn = OznamovatelForm(instance=projekt.oznamovatel)
                form_projekt = ProjektOznameniForm(instance=projekt, change=True)
                form_captcha = FormWithCaptcha() if not settings.SKIP_RECAPTCHA else None
                logger.debug(f"oznameni.views.index.get.projekt",
                             extra={"ident_cely": ident, "cookie_project": cookie_project,
                                    "hash_from_ident": hash_from_ident, "projekt": projekt.ident_cely})
        else:
            logger.debug(f"oznameni.views.index.get.permission_denied",
                         extra={"ident_cely": ident, "cookie_project": cookie_project,
                                "hash_from_ident": hash_from_ident})
            raise PermissionDenied
    else:
        form_ozn = OznamovatelForm()
        form_projekt = ProjektOznameniForm()
        form_captcha = FormWithCaptcha() if not settings.SKIP_RECAPTCHA else None

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
    """
    Funkce pohledu pro editaci oznamovatele.
    """
    projekt: Projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
    oznameni = projekt.oznamovatel
    if projekt.stav == PROJEKT_STAV_ARCHIVOVANY:
        raise PermissionDenied()
    if request.method == "POST":
        form = OznamovatelForm(request.POST, instance=oznameni, required_next=True)
        if form.is_valid():
            oznameni = form.save(commit=False)
            oznameni.projekt = projekt
            oznameni.save()
            fedora_transaction = FedoraTransaction()
            projekt.active_transaction = fedora_transaction
            projekt.close_active_transaction_when_finished = True
            projekt.save()
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
    """
    Funkce pohledu pro získaní katastru podle bodu pro oznámení.
    """
    body = json.loads(request.body.decode("utf-8"))
    # logger.debug(body)
    geom = Point(float(body["x1"]), float(body["x2"]))
    katastr = get_cadastre_from_point(geom)
    # logger.debug(katastr)
    if len(str(katastr)) > 0:
        return JsonResponse({"cadastre": str(katastr)}, status=200)
    else:
        return JsonResponse({"cadastre": ""}, status=200)


class OznamovatelCreateView(LoginRequiredMixin, TemplateView):
    """
    Třída pohledu pro vytvoření oznamovetele pomocí modalu.
    """
    template_name = "core/transakce_modal.html"

    def get_context_data(self, **kwargs):
        ident_cely = self.kwargs.get("ident_cely")
        projekt = get_object_or_404(Projekt, ident_cely=ident_cely)
        form_check = CheckStavNotChangedForm(initial={"old_stav": projekt.stav})
        context = {
            "object": projekt,
            "title": _("oznameni.views.oznamovatelCreateView.title"),
            "id_tag": "pridat-oznamovatele-form",
            "button": _("oznameni.views.oznamovatelCreateView.submitButton"),
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
        projekt: Projekt = context["object"]
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

            fedora_transaction = FedoraTransaction()
            projekt.active_transaction = fedora_transaction
            projekt.close_active_transaction_when_finished = True
            projekt.save()

            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

        return JsonResponse({"redirect": projekt.get_absolute_url()})