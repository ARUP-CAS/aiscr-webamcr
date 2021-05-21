import logging

from core.constants import KLADYZM10, KLADYZM50
from core.exceptions import NeznamaGeometrieError
from core.message_constants import (
    PIAN_USPESNE_ODPOJEN,
    PIAN_USPESNE_SMAZAN,
    ZAZNAM_SE_NEPOVEDLO_EDITOVAT,
    ZAZNAM_SE_NEPOVEDLO_VYTVORIT,
    ZAZNAM_USPESNE_EDITOVAN,
    ZAZNAM_USPESNE_VYTVOREN,
)
from dal import autocomplete
from dj.models import DokumentacniJednotka
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import LineString, Point, Polygon
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from heslar.hesla import GEOMETRY_BOD, GEOMETRY_LINIE, GEOMETRY_PLOCHA
from heslar.models import Heslar
from pian.forms import PianCreateForm
from pian.models import Kladyzm, Pian

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def detail(request, ident_cely=None):
    pian = Pian.objects.get(ident_cely=ident_cely)
    if request.method == "POST":
        form = PianCreateForm(request.POST, instance=pian)
        if form.is_valid():
            logger.debug("Form is valid")
            pian = form.save()
            if form.changed_data:
                messages.add_message(request, messages.SUCCESS, ZAZNAM_USPESNE_EDITOVAN)
        else:
            logger.warning("Form is not valid")
            logger.debug(form.errors)
            messages.add_message(request, messages.ERROR, ZAZNAM_SE_NEPOVEDLO_EDITOVAT)
    else:
        form = PianCreateForm(instance=pian)

    return render(request, "pian/detail.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def odpojit(request, dj_ident_cely):
    dj = DokumentacniJednotka.objects.get(ident_cely=dj_ident_cely)
    pian_djs = DokumentacniJednotka.objects.filter(pian=dj.pian)
    delete_pian = True if pian_djs.count() < 2 else False
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
            "header": _("Skutečně odpojit pian")
            + pian.ident_cely
            + _(" z dokumentační jednotky ")
            + dj.ident_cely
            + "?",
            "title": _("Odpojení pianu"),
            "button": _("Odpojit pian"),
        }

        return render(request, "core/transakce.html", context)


@login_required
@require_http_methods(["POST"])
def create(request, dj_ident_cely):
    dj = DokumentacniJednotka.objects.get(ident_cely=dj_ident_cely)
    form = PianCreateForm(request.POST)
    if form.is_valid():
        logger.debug("Form is valid")
        pian = form.save(commit=False)
        # Assign base map references
        if type(pian.geom) == Point:
            pian.typ = Heslar.objects.get(id=GEOMETRY_BOD)
        elif type(pian.geom) == LineString:
            pian.typ = Heslar.objects.get(id=GEOMETRY_LINIE)
        elif type(pian.geom) == Polygon:
            pian.typ = Heslar.objects.get(id=GEOMETRY_PLOCHA)
        else:
            raise NeznamaGeometrieError()
        zm10s = Kladyzm.objects.filter(kategorie=KLADYZM10).filter(
            the_geom__contains=pian.geom
        )
        zm50s = Kladyzm.objects.filter(kategorie=KLADYZM50).filter(
            the_geom__contains=pian.geom
        )
        if zm10s.count() == 1 and zm50s.count() == 1:
            pian.zm10 = zm10s[0]
            pian.zm50 = zm50s[0]
            pian.save()
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
