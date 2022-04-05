from dal import autocomplete
from django.contrib.gis.geos import Point
from django.http import JsonResponse
from django.db.models import Value, IntegerField

from heslar.models import Heslar, RuianKatastr


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
