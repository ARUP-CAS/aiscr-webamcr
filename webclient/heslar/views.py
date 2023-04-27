from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.db import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.db.models import Value, IntegerField
from django.core.exceptions import ObjectDoesNotExist

from heslar.hesla import HESLAR_DOKUMENT_TYP, MODEL_3D_DOKUMENT_TYPES, HESLAR_DOKUMENT_FORMAT, HESLAR_PRISTUPNOST
from heslar.models import Heslar, RuianKatastr, HeslarHierarchie
import logging


logger = logging.getLogger(__name__)


class RuianKatastrAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = RuianKatastr.objects.all()
        if self.q:
            new_qs = qs.filter(nazev__istartswith=self.q).annotate(qs_order=Value(0, IntegerField()))
            new_qs2 =qs.filter(nazev__icontains=self.q).exclude(nazev__istartswith=self.q).annotate(qs_order=Value(2, IntegerField()))
            qs = new_qs.union(new_qs2).order_by("qs_order","nazev")
        return qs


def merge_heslare(first, second):
    data = [("", "")]
    try:
        for k in first:
            druhy_kategorie = []
            for druh in second:
                if druh["hierarchie__heslo_nadrazene"] == k["id"]:
                    druhy_kategorie.append((druh["id"], druh["heslo"]))
            data.append((k["heslo"], tuple(druhy_kategorie)))
    except ProgrammingError as err:
        # This error will always be shown before
        logger.debug("heslar.views.merge_heslare.error", extra={"err": err})
    return data


def heslar_12(druha, prvni_kat,id=False):
    druha = (
        Heslar.objects.filter(nazev_heslare=druha)
        .order_by("razeni")
        .values("id", "hierarchie__heslo_nadrazene", "heslo")
    )
    if id:
        kategorie=Heslar.objects.filter(nazev_heslare=prvni_kat,id__in=id)
    else:
        kategorie=Heslar.objects.filter(nazev_heslare=prvni_kat)
    prvni = kategorie.order_by("razeni").values("id", "heslo")
    return merge_heslare(prvni, druha)


def zjisti_katastr_souradnic(request):
    nalezene_katastry = RuianKatastr.objects.filter(
        hranice__contains=Point(
            float(request.GET.get("long", 0)), float(request.GET.get("lat", 0))
        )
    )
    if nalezene_katastry.count() == 1:
        return JsonResponse(
            {
                "id": nalezene_katastry.first().pk,
                "value": str(nalezene_katastry.first()),
            }
        )
    else:
        return JsonResponse({})

def zjisti_vychozi_hodnotu(request):
    nadrazene = request.GET.get("nadrazene", 0)
    vychozi_hodnota = HeslarHierarchie.objects.filter(heslo_nadrazene=nadrazene, typ="výchozí hodnota")
    if vychozi_hodnota.exists():
        queryset = vychozi_hodnota.values_list('heslo_podrazene', flat=True)
        list = []
        for id in queryset:
            list.append({"id":id})
        return JsonResponse(
            data=list,
            status=200,
            safe=False
        )
    else:
        return JsonResponse(data = {},status=400)


def zjisti_nadrazenou_hodnotu(request):
    podrazene = request.GET.get("podrazene", 0)
    i = 0
    while i < int(request.GET.get("iterace", 1)):
        try:
            nadrazene = HeslarHierarchie.objects.get(heslo_podrazene=podrazene, typ="podřízenost").heslo_nadrazene
            podrazene = nadrazene.id
            i += 1
        except ObjectDoesNotExist as err:
            logger.debug("heslar.views.zjisti_nadrazenou_hodnotu.does_not_exist", extra={"err": err})
            return JsonResponse(data={}, status=400)
    list = [{"id": nadrazene.id}]
    return JsonResponse(
        data=list,
        status=200,
        safe=False
    )


class DokumentTypAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP).filter(
            id__in=MODEL_3D_DOKUMENT_TYPES
        )
        return qs


class DokumentFormatAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT).filter(
            heslo__startswith="3D"
        )
        return qs


class PristupnostAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST)
        return qs
