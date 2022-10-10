from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.http import JsonResponse
from django.db.models import Value, IntegerField

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
    for k in first:
        druhy_kategorie = []
        for druh in second:
            if druh["hierarchie__heslo_nadrazene"] == k["id"]:
                druhy_kategorie.append((druh["id"], druh["heslo"]))
        data.append((k["heslo"], tuple(druhy_kategorie)))
    return data


def heslar_12(druha, prvni_kat):
    druha = (
        Heslar.objects.filter(nazev_heslare=druha)
        .order_by("razeni")
        .values("id", "hierarchie__heslo_nadrazene", "heslo")
    )
    prvni = (
        Heslar.objects.filter(nazev_heslare=prvni_kat)
        .order_by("razeni")
        .values("id", "heslo")
    )
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
        logger.debug(queryset)
        list = []
        for id in queryset:
            list.append({"id":id})
        logger.debug(list)
        return JsonResponse(
            data = list,
            status=200,
            safe=False
        )
    else:
        return JsonResponse(data = {},status=400)


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
