import logging

import simplejson as json
from core.constants import OBLAST_CECHY, PROJEKT_STAV_ARCHIVOVANY, PROJEKT_STAV_OZNAMENY, PROJEKT_STAV_VYTVORENY
from core.coordTransform import convertToJTSK
from core.decorators import odstavka_in_progress
from core.forms import CheckStavNotChangedForm
from core.ident_cely import get_temporary_project_ident
from core.message_constants import ZAZNAM_SE_NEPOVEDLO_EDITOVAT, ZAZNAM_USPESNE_EDITOVAN
from core.repository_connector import FedoraTransaction
from core.utils import SessionIdentifier, get_cadastre_from_point
from core.views import check_stav_changed
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, View
from heslar.hesla_dynamicka import TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar
from projekt.models import Projekt
from services.mailer import Mailer

from .forms import FormWithCaptcha, OznamovatelForm, OznamovatelProjektForm, ProjektOznameniForm

logger = logging.getLogger(__name__)


class OznameniView(View):
    def dispatch(self, request, *args, **kwargs):
        self.session_identifier = SessionIdentifier(request)
        self.ident_cely = kwargs.pop("ident_cely", None)
        return super().dispatch(request, *args, **kwargs)


@method_decorator(odstavka_in_progress, name="dispatch")
class OznameniZapsatView(OznameniView):
    """
    Třída pohledu pro 1. stranu oznámení.
    """

    def post(self, request):
        """
        Funkce pohledu pro oznámení. Oznámení je dvoustupňové.
        V prvém kroku uživatel zadává údaje a v druhém je potvrzuje a případně uploaduje soubory.
        """
        logger.debug("oznameni.views.index.start")
        if "oznamovatel" in request.POST:
            logger.debug("oznameni.views.index.first_part_start")
            if self.ident_cely:
                logger.debug("oznameni.views.index.first_part_start.ident_set", extra={"ident_cely": self.ident_cely})
                projekt = get_object_or_404(Projekt, ident_cely=self.ident_cely)
                form_ozn = OznamovatelForm(request.POST, instance=projekt.oznamovatel)
                form_projekt = ProjektOznameniForm(request.POST, instance=projekt)
            else:
                logger.debug("oznameni.views.index.first_part_start.ident_not_set")
                form_ozn = OznamovatelForm(request.POST)
                form_projekt = ProjektOznameniForm(request.POST)
            form_captcha = FormWithCaptcha(request.POST) if not settings.SKIP_RECAPTCHA else None
            ozn_valid = form_ozn.is_valid()
            projekt_valid = form_projekt.is_valid()
            logger.debug("oznameni.views.index.form_ozn.valid", extra={"valid": ozn_valid})
            logger.debug("oznameni.views.index.form_projekt.valid", extra={"valid": projekt_valid})
            captcha_valid = True
            if not settings.SKIP_RECAPTCHA:
                try:
                    captcha_valid = form_captcha.is_valid()
                except Exception:
                    captcha_valid = False
                    logger.exception("oznameni.views.index.form_captcha.validate_failed")
                logger.debug("oznameni.views.index.form_captcha.valid", extra={"valid": captcha_valid})
            if ozn_valid and projekt_valid and captcha_valid:
                logger.debug("oznameni.views.index.all_forms_valid")
                oznamovatel = form_ozn.save(commit=False)
                projekt: Projekt = form_projekt.save(commit=False)
                projekt.suppress_signal = True
                projekt.typ_projektu = Heslar.objects.get(pk=TYP_PROJEKTU_ZACHRANNY_ID)
                dalsi_katastry = form_projekt.cleaned_data["katastry"]
                projekt.geom = Point(
                    float(request.POST.get("coordinate_x1")),
                    float(request.POST.get("coordinate_x2")),
                )
                projekt.geom_sjtsk = Point(
                    *convertToJTSK(float(request.POST.get("coordinate_x1")), float(request.POST.get("coordinate_x2")))
                )
                projekt.geom_system = "5514"
                projekt.hlavni_katastr = get_cadastre_from_point(projekt.geom)
                logger.debug(
                    "oznameni.views.index.hlavni_katastr",
                    extra={
                        "katastr": projekt.hlavni_katastr,
                    },
                )
                # Uložení instance je zde záměrně vypnuté.
                if projekt.hlavni_katastr is not None and not self.ident_cely:
                    projekt.ident_cely = get_temporary_project_ident(projekt.hlavni_katastr.okres.kraj.rada_id)
                else:
                    logger.debug("oznameni.views.index.unknown_location", extra={"geom": str(projekt.geom)})
                projekt.save()
                oznamovatel.projekt = projekt
                oznamovatel.save()
                projekt.set_vytvoreny()
                projekt.katastry.add(*[i for i in dalsi_katastry])
                projekt.save()
                self.session_identifier.set_ident(projekt.ident_cely)
                # Uložení vlastnictví projektu pro anonymního uživatele
                self.session_identifier.set_project_ownership(projekt.ident_cely)
                return redirect("oznameni:index2", ident_cely=projekt.ident_cely)
            else:
                extra = {"form_error": form_ozn.errors, "error": form_projekt.errors}
                if not settings.SKIP_RECAPTCHA:
                    extra["error"] = form_captcha.errors
                logger.debug("oznameni.views.index.form_not_valid", extra=extra)
                return render(
                    request,
                    "oznameni/index.html",
                    {
                        "form_oznamovatel": form_ozn,
                        "form_projekt": form_projekt,
                        "form_captcha": form_captcha,
                    },
                )
        raise PermissionDenied

    @method_decorator(never_cache)
    def get(self, request):
        if self.ident_cely:
            cache_project = self.session_identifier.get_ident()
            logger.debug("oznameni.views.index.get.start", extra={"ident_cely": self.ident_cely})

            logger.debug(
                "oznameni.views.index.get.cookie",
                extra={"ident_cely": self.ident_cely, "projekt": cache_project},
            )
            if cache_project is not None and self.ident_cely == cache_project:
                projekty = Projekt.objects.filter(ident_cely=self.ident_cely, stav=PROJEKT_STAV_VYTVORENY)
                if not projekty:
                    logger.debug(
                        "oznameni.views.index.get.permission_denied",
                        extra={"ident_cely": self.ident_cely, "projekt": cache_project},
                    )
                    raise PermissionDenied
                else:
                    projekt = projekty[0]
                    form_ozn = OznamovatelForm(instance=projekt.oznamovatel)
                    form_projekt = ProjektOznameniForm(instance=projekt, change=True)
                    form_captcha = FormWithCaptcha() if not settings.SKIP_RECAPTCHA else None
                    logger.debug(
                        "oznameni.views.index.get.projekt",
                        extra={
                            "ident_cely": self.ident_cely,
                            "projekt": projekt.ident_cely,
                        },
                    )
            else:
                logger.debug(
                    "oznameni.views.index.get.permission_denied",
                    extra={"ident_cely": self.ident_cely, "projekt": cache_project},
                )
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


@method_decorator(odstavka_in_progress, name="dispatch")
class OznameniDokumentaceView(OznameniView):
    """
    Třída pohledu pro 2. stranu oznámení.
    """

    def post(self, request):
        if "ident_cely" in request.POST:
            logger.debug("oznameni.views.index.second_part.start", extra={"ident_cely": request.POST["ident_cely"]})
            projekt = Projekt.objects.get(ident_cely=request.POST["ident_cely"])
            fedora_transaction = FedoraTransaction()
            projekt.active_transaction = fedora_transaction
            projekt.set_oznameny()
            projekt.close_active_transaction_when_finished = True
            projekt.save()
            if projekt.ident_cely[2].upper() == OBLAST_CECHY:
                Mailer.send_eo01(project=projekt)
            else:
                Mailer.send_eo02(project=projekt)
            logger.debug(
                "oznameni.views.index.second_part.end",
                extra={"ident_cely": request.POST["ident_cely"], "transaction": fedora_transaction.uid},
            )
            return redirect("oznameni:index3", ident_cely=projekt.ident_cely)
        raise PermissionDenied

    @method_decorator(never_cache)
    def get(self, request):
        if self.ident_cely:
            cache_project = self.session_identifier.get_ident()
            logger.debug(
                "oznameni.views.index.get.start", extra={"ident_cely": self.ident_cely, "projekt": cache_project}
            )
            if cache_project is not None and self.ident_cely == cache_project:
                projekt = Projekt.objects.filter(ident_cely=self.ident_cely, stav=PROJEKT_STAV_VYTVORENY).first()
                if not projekt:
                    logger.debug(
                        "oznameni.views.index.get.permission_denied",
                        extra={"ident_cely": self.ident_cely, "projekt": cache_project},
                    )
                    raise PermissionDenied
                else:
                    queryset = projekt.soubory.soubory.all()
                    seznam_mock = [obj.getMock() for obj in queryset]
                    json_mock = json.dumps(seznam_mock, ensure_ascii=False)
                    self.session_identifier.set_ident(projekt.ident_cely)
                    return render(request, "oznameni/index_2.html", {"projekt": projekt, "seznam_mock": json_mock})

            else:
                logger.debug(
                    "oznameni.views.index.get.permission_denied",
                    extra={"ident_cely": self.ident_cely, "projekt": cache_project},
                )
                raise PermissionDenied
        return redirect("oznameni:index")


@method_decorator(odstavka_in_progress, name="dispatch")
class OznameniPotvrzeniView(OznameniView):
    """
    Třída pohledu pro potvrzení oznámení.
    """

    @method_decorator(never_cache)
    def get(self, request):
        if self.ident_cely:
            cache_project = self.session_identifier.get_ident()
            logger.debug(
                "oznameni.views.index.get.start", extra={"ident_cely": self.ident_cely, "projekt": cache_project}
            )
            if cache_project is not None and self.ident_cely == cache_project:
                projekty = Projekt.objects.filter(ident_cely=self.ident_cely, stav=PROJEKT_STAV_OZNAMENY)
                if not projekty:
                    logger.debug(
                        "oznameni.views.index.get.permission_denied",
                        extra={"ident_cely": self.ident_cely, "projekt": cache_project},
                    )
                    raise PermissionDenied
                else:
                    self.session_identifier.set_ident(self.ident_cely, 300)
                    context = {"ident_cely": self.ident_cely}
                    return render(request, "oznameni/success.html", context)

            else:
                logger.debug(
                    "oznameni.views.index.get.permission_denied",
                    extra={"ident_cely": self.ident_cely, "projekt": cache_project},
                )
                raise PermissionDenied
        return redirect("oznameni:index")


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
        form = OznamovatelProjektForm(request.POST, instance=oznameni, required_next=True)
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
        form = OznamovatelProjektForm(instance=oznameni, required_next=True)

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
    Třída pohledu pro vytvoření oznamovatele pomocí modalu.
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
        form = OznamovatelProjektForm(required_next=True, add_oznamovatel=True)
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
        form = OznamovatelProjektForm(request.POST, required_next=True, add_oznamovatel=True)
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
