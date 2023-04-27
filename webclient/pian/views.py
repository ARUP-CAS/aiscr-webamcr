import logging


from core.constants import KLADYZM10, KLADYZM50, PIAN_NEPOTVRZEN
from core.exceptions import MaximalIdentNumberError, NeznamaGeometrieError
from core.ident_cely import get_temporary_pian_ident
from core.message_constants import (
    MAXIMUM_IDENT_DOSAZEN,
    PIAN_NEVALIDNI_GEOMETRIE,
    PIAN_USPESNE_ODPOJEN,
    PIAN_USPESNE_POTVRZEN,
    PIAN_USPESNE_SMAZAN,
    PIAN_VALIDACE_VYPNUTA,
    VALIDATION_EMPTY,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from core.utils import (
    get_validation_messages,
    update_all_katastr_within_akce_or_lokalita,
)
from dal import autocomplete
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import LineString, Point, Polygon
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from heslar.hesla import GEOMETRY_BOD, GEOMETRY_LINIE, GEOMETRY_PLOCHA
from heslar.models import Heslar
from pian.forms import PianCreateForm
from pian.models import Kladyzm, Pian

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def detail(request, ident_cely):
    dj_ident_cely = request.POST["dj_ident_cely"]
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    pian = get_object_or_404(Pian, ident_cely=ident_cely)
    form = PianCreateForm(
        request.POST,
        instance=pian,
    )
    c = connection.cursor()
    validation_results = ""
    validation_geom = ""
    logger.debug("pian.views.detail.start")
    try:
        dict1 = dict(request.POST)
        logger.debug("pian.views.detail", extra={"post": dict1.items()})
        for key in dict1.keys():
            if key == "geom":
                validation_geom = dict1.get(key)[0]
                c.execute("BEGIN")
                c.callproc("validateGeom", [validation_geom])
                validation_results = c.fetchone()[0]
                logger.debug("pian.views.detail", extra={"validation_results": validation_results,
                                                         "validation_geom": validation_geom, "key": key})
                c.execute("COMMIT")
    except Exception:
        validation_results = PIAN_VALIDACE_VYPNUTA
    finally:
        c.close()
    if validation_geom == "undefined":
        messages.add_message(
            request,
            messages.ERROR,
            PIAN_NEVALIDNI_GEOMETRIE + " " + get_validation_messages(VALIDATION_EMPTY),
        )
    elif validation_results == PIAN_VALIDACE_VYPNUTA:
        messages.add_message(request, messages.ERROR, PIAN_VALIDACE_VYPNUTA)
    elif validation_results != "valid":
        messages.add_message(
            request,
            messages.ERROR,
            PIAN_NEVALIDNI_GEOMETRIE
            + " "
            + get_validation_messages(validation_results),
        )
    elif form.is_valid():
        logger.debug("pian.views.detail.form.valid", extra={"pian_ident_cely": pian.ident_cely})
        form.save()
        update_all_katastr_within_akce_or_lokalita(dj_ident_cely)
        if form.changed_data:
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
    else:
        logger.debug("pian.views.detail.form.not_valid", extra={"form_errors": form.errors})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    response = redirect(dj.get_absolute_url())
    response.set_cookie("show-form", f"detail_dj_form_{dj_ident_cely}", max_age=1000)
    response.set_cookie(
        "set-active",
        f"el_div_dokumentacni_jednotka_{dj_ident_cely.replace('-', '_')}",
        max_age=1000,
    )
    return response


@login_required
@require_http_methods(["GET", "POST"])
def odpojit(request, dj_ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    pian_djs = DokumentacniJednotka.objects.filter(pian=dj.pian)
    delete_pian = (
        True if pian_djs.count() < 2 and dj.pian.stav == PIAN_NEPOTVRZEN else False
    )
    pian = dj.pian
    if request.method == "POST":
        dj.archeologicky_zaznam.get_absolute_url()
        dj.pian = None
        dj.save()
        update_all_katastr_within_akce_or_lokalita(dj_ident_cely)
        logger.debug("pian.views.odpojit.odpojen", extra={"pian_ident_cely": pian.ident_cely})
        if delete_pian:
            pian.delete()
            logger.debug("pian.views.odpojit.smazan", extra={"pian_ident_cely": pian.ident_cely})
            messages.add_message(request, messages.SUCCESS, PIAN_USPESNE_SMAZAN)
        else:
            messages.add_message(request, messages.SUCCESS, PIAN_USPESNE_ODPOJEN)
        response = JsonResponse({"redirect": dj.get_absolute_url()})
        response.set_cookie(
            "show-form", f"detail_dj_form_{dj.ident_cely}", max_age=1000
        )
        response.set_cookie(
            "set-active",
            f"el_div_dokumentacni_jednotka_{dj.ident_cely.replace('-', '_')}",
            max_age=1000,
        )
        return response
    else:
        context = {
            "object": pian,
            "title": _("pian.modalForm.odpojeniPian.title.text"),
            "id_tag": "odpojit-pian-form",
            "button": _("pian.modalForm.odpojeniPian.submit.button"),
            "text": _("Skutečně odpojit pian ")
            + pian.ident_cely
            + _(" z dokumentační jednotky ")
            + dj.ident_cely
            + "?",
        }
        return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def potvrdit(request, dj_ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    pian = dj.pian
    if request.method == "POST":
        redirect_view = dj.archeologicky_zaznam.get_absolute_url(dj_ident_cely)
        try:
            pian.set_permanent_ident_cely()
        except MaximalIdentNumberError:
            messages.add_message(request, messages.ERROR, MAXIMUM_IDENT_DOSAZEN)
            logger.debug("pian.views.potvrdit", extra={"pian_ident_cely": pian.ident_cely})
            return JsonResponse(
                {"redirect": redirect_view},
                status=403,
            )
        else:
            pian.set_potvrzeny(request.user)
            logger.debug("pian.views.potvrdit.potvrzen", extra={"pian_ident_cely": pian.ident_cely})
            messages.add_message(request, messages.SUCCESS, PIAN_USPESNE_POTVRZEN)
            response = JsonResponse({"redirect": dj.get_absolute_url()})
            response.set_cookie(
                "show-form", f"detail_dj_form_{dj.ident_cely}", max_age=1000
            )
            response.set_cookie(
                "set-active",
                f"el_div_dokumentacni_jednotka_{dj.ident_cely.replace('-', '_')}",
                max_age=1000,
            )
            return response
    context = {
        "object": pian,
        "title": _("pian.modalForm.potvrditPian.title.text"),
        "id_tag": "potvrdit-pian-form",
        "button": _("pian.modalForm.potvrditPian.submit.button"),
        "text": _("Skutečně potvrdit pian ") + pian.ident_cely + "?",
    }
    return render(request, "core/transakce_modal.html", context)


@login_required
@require_http_methods(["POST"])
def create(request, dj_ident_cely):
    logger.debug("pian.views.create.start")
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    form = PianCreateForm(request.POST)
    c = connection.cursor()
    validation_results = ""
    try:
        c.execute("BEGIN")
        c.callproc("validateGeom", [str(form.data["geom"])])
        validation_results = c.fetchone()[0]
        c.execute("COMMIT")
        logger.debug("pian.views.create.commit", extra={"validation_results": validation_results,
                                                        "geom": str(form.data["geom"])})
    except Exception as ex:
        logger.warning("pian.views.create.validation_exception", extra={"exception": ex})
        validation_results = PIAN_VALIDACE_VYPNUTA
    finally:
        c.close()
    if validation_results == PIAN_VALIDACE_VYPNUTA:
        messages.add_message(request, messages.ERROR, PIAN_VALIDACE_VYPNUTA)
    elif validation_results != "valid":
        messages.add_message(
            request,
            messages.ERROR,
            PIAN_NEVALIDNI_GEOMETRIE
            + " "
            + get_validation_messages(validation_results),
        )
        logger.debug("pian.views.create", extra={"message": PIAN_NEVALIDNI_GEOMETRIE})
    elif form.is_valid():
        logger.debug("pian.views.create.form_valid")
        pian = form.save(commit=False)
        # Assign base map references
        if type(pian.geom) == Point:
            pian.typ = Heslar.objects.get(id=GEOMETRY_BOD)
            point = pian.geom
        elif type(pian.geom) == LineString:
            pian.typ = Heslar.objects.get(id=GEOMETRY_LINIE)
            point = pian.geom.interpolate(0.5)
        elif type(pian.geom) == Polygon:
            pian.typ = Heslar.objects.get(id=GEOMETRY_PLOCHA)
            point = Centroid(pian.geom)
        else:
            raise NeznamaGeometrieError()
        logger.debug("pian.views.create.geom", extra={"geom": str(form.data["geom"])})
        zm10s = (
            Kladyzm.objects.filter(kategorie=KLADYZM10)            
            .filter(the_geom__contains=point)
        )
        zm50s = (
            Kladyzm.objects.filter(kategorie=KLADYZM50)
            .filter(the_geom__contains=point)
        )
        if zm10s.count() == 1 and zm50s.count() == 1:
            pian.zm10 = zm10s[0]
            pian.zm50 = zm50s[0]
            try:
                pian.ident_cely = get_temporary_pian_ident(zm50s[0])
            except MaximalIdentNumberError as e:
                logger.warning("pian.views.create.error", extra={"message": messages.ERROR, "exception": e.message})
                messages.add_message(request, messages.ERROR, e.message)
            else:
                pian.save()
                pian.set_vymezeny(request.user)
                dj.pian = pian
                dj.save()
                update_all_katastr_within_akce_or_lokalita(dj_ident_cely)
                logger.warning("pian.views.create.error", extra={"message": ZAZNAM_USPESNE_VYTVOREN, "dj_pk": dj.pk})
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
        else:
            logger.info("pian.views.create.assignment_error", extra={"zm10s": zm10s, "zm50s": zm50s})
            messages.add_message(
                request, messages.SUCCESS, ZAZNAM_SE_NEPOVEDLO_VYTVORIT
            )
        redirect("dj:detail", ident_cely=dj_ident_cely)
    else:
        logger.info("pian.views.create.not_valid", extra={"errors": form.errors})
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)

    response = redirect(dj.get_absolute_url())
    response.set_cookie("show-form", f"detail_dj_form_{dj.ident_cely}", max_age=1000)
    response.set_cookie(
        "set-active",
        f"el_div_dokumentacni_jednotka_{dj.ident_cely.replace('-', '_')}",
        max_age=1000,
    )
    return response


class PianAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Pian.objects.all().order_by("ident_cely")
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q).exclude(presnost__zkratka="4")
        return qs
