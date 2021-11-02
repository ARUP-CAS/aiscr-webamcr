import logging

from core.constants import KLADYZM10, KLADYZM50, PIAN_POTVRZEN, PIAN_NEPOTVRZEN
from core.exceptions import NeznamaGeometrieError, MaximalIdentNumberError
from core.ident_cely import get_temporary_pian_ident
from core.message_constants import (
    PIAN_USPESNE_ODPOJEN,
    PIAN_USPESNE_POTVRZEN,
    PIAN_USPESNE_SMAZAN,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_VYTVOREN,
    MAXIMUM_IDENT_DOSAZEN,
)
from core.models import over_opravneni_with_exception
from dal import autocomplete
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.geos import LineString, Point, Polygon
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
    pian = get_object_or_404(Pian, ident_cely=ident_cely)
    over_opravneni_with_exception(pian, request)
    form = PianCreateForm(request.POST, instance=pian, prefix=ident_cely,)
    if form.is_valid():
        logger.debug("Form is valid")
        form.save()
        if form.changed_data:
            messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
    else:
        logger.warning("Form is not valid")
        logger.debug(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
@require_http_methods(["GET", "POST"])
def odpojit(request, dj_ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    over_opravneni_with_exception(dj.archeologicky_zaznam, request)
    pian_djs = DokumentacniJednotka.objects.filter(pian=dj.pian)
    delete_pian = (
        True if pian_djs.count() < 2 and dj.pian.stav == PIAN_NEPOTVRZEN else False
    )
    pian = dj.pian
    if request.method == "POST":
        dj.pian = None
        dj.save()
        logger.debug("Pian odpojen: " + pian.ident_cely)
        messages.add_message(request, messages.SUCCESS, PIAN_USPESNE_ODPOJEN)
        if delete_pian:
            pian.delete()
            logger.debug("Pian smazán: " + pian.ident_cely)
            messages.add_message(request, messages.SUCCESS, PIAN_USPESNE_SMAZAN)
        return redirect("arch_z:detail", ident_cely=dj.archeologicky_zaznam.ident_cely)
    else:
        context = {
            "objekt": pian,
            "header": _("Skutečně odpojit pian ")
            + pian.ident_cely
            + _(" z dokumentační jednotky ")
            + dj.ident_cely
            + "?",
            "title": _("Odpojení pianu"),
            "button": _("Odpojit pian"),
        }

        return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def potvrdit(request, dj_ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    over_opravneni_with_exception(dj.archeologicky_zaznam, request)
    pian = dj.pian
    if request.method == "POST":
        try:
            pian.set_permanent_ident_cely()
        except MaximalIdentNumberError:
            messages.add_message(request, messages.ERROR, MAXIMUM_IDENT_DOSAZEN)
        else:
            pian.set_potvrzeny(request.user)
            logger.debug("Pian potvrzen: " + pian.ident_cely)
            messages.add_message(request, messages.SUCCESS, PIAN_USPESNE_POTVRZEN)
            return redirect(
                "arch_z:detail", ident_cely=dj.archeologicky_zaznam.ident_cely
            )

    context = {
        "objekt": pian,
        "header": _("Skutečně potvrdit pian ") + pian.ident_cely + "?",
        "title": _("Potvrzení pianu"),
        "button": _("Potvrdit pian"),
    }

    return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["POST"])
def create(request, dj_ident_cely):
    dj = get_object_or_404(DokumentacniJednotka, ident_cely=dj_ident_cely)
    over_opravneni_with_exception(dj.archeologicky_zaznam, request)
    form = PianCreateForm(request.POST)
    if form.is_valid():
        logger.debug("Form is valid")
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
        logger.debug("GEOM: " + str(form.data["geom"]))
        zm10s = (
            Kladyzm.objects.filter(kategorie=KLADYZM10)
            .exclude(objectid=1094)
            .filter(the_geom__contains=point)
        )
        zm50s = (
            Kladyzm.objects.filter(kategorie=KLADYZM50)
            .exclude(objectid=1094)
            .filter(the_geom__contains=point)
        )
        if zm10s.count() == 1 and zm50s.count() == 1:
            pian.zm10 = zm10s[0]
            pian.zm50 = zm50s[0]
            try:
                pian.ident_cely = get_temporary_pian_ident(zm50s[0])
            except MaximalIdentNumberError as e:
                messages.add_message(request, messages.ERROR, e.message)
            else:
                pian.save()
                pian.set_vymezeny(request.user)
                dj.pian = pian
                dj.save()
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_VYTVOREN)
        else:
            logger.error("Nelze priradit ZM10 nebo ZM50 k pianu.")
            logger.error("ZM10s" + str(zm10s))
            logger.error("ZM50s" + str(zm50s))
            messages.add_message(
                request, messages.SUCCESS, ZAZNAM_SE_NEPOVEDLO_VYTVORIT
            )
        redirect("dj:detail", ident_cely=dj_ident_cely)
    else:
        logger.warning("Form is not valid")
        logger.warning(form.errors)
        messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_VYTVORIT)

    return redirect(request.META.get("HTTP_REFERER"))


class PianAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Pian.objects.all()
        if self.q:
            qs = qs.filter(ident_cely__icontains=self.q)
        return qs

    def get(self, request, *args, **kwargs):
        over_opravneni_with_exception(request=request)
        return super().get(request, *args, **kwargs)
