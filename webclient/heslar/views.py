import logging

from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError, ProgrammingError
from django.db.models import IntegerField, Value
from django.http import JsonResponse
from django.utils.translation import get_language
from heslar.hesla import HESLAR_DOKUMENT_FORMAT, HESLAR_DOKUMENT_TYP, HESLAR_PRISTUPNOST
from heslar.hesla_dynamicka import MODEL_3D_DOKUMENT_FORMATS, MODEL_3D_DOKUMENT_TYPES
from heslar.models import Heslar, HeslarHierarchie, HeslarNazev, RuianKatastr

logger = logging.getLogger(__name__)


class RuianKatastrAutocomplete(autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro autocomplete ruian katastru.
    """

    def get_queryset(self):
        qs = RuianKatastr.objects.all()
        if self.q:
            new_qs = qs.filter(nazev__istartswith=self.q).annotate(qs_order=Value(0, IntegerField()))
            new_qs2 = (
                qs.filter(nazev__icontains=self.q)
                .exclude(nazev__istartswith=self.q)
                .annotate(qs_order=Value(2, IntegerField()))
            )
            qs = new_qs.union(new_qs2).order_by("qs_order", "nazev")
        return qs


def merge_heslare(first, second):
    """
    Pomocní funkce pro vytvoření dvoustupňového selectu.
    """
    data = [("", "")]
    # logger.debug(get_language())
    try:
        for k in first:
            druhy_kategorie = []
            for druh in second:
                if druh["hierarchie__heslo_nadrazene"] == k["id"]:
                    if get_language() == "en":
                        druhy_kategorie.append((druh["id"], druh["heslo_en"]))
                    else:
                        druhy_kategorie.append((druh["id"], druh["heslo"]))
            if get_language() == "en":
                data.append((k["heslo_en"], tuple(druhy_kategorie)))
            else:
                data.append((k["heslo"], tuple(druhy_kategorie)))
    except ProgrammingError as err:
        # This error will always be shown before
        logger.debug("heslar.views.merge_heslare.error", extra={"err": err})
    except OperationalError as err:
        # This error will always be shown before
        logger.debug("heslar.views.merge_heslare.error", extra={"err": err})
    return data


def heslar_12(druha, prvni_kat, id=False):
    """
    Funkce pro vytvoření dvoustupňového selectu.
    """
    druha = (
        Heslar.objects.filter(nazev_heslare=druha)
        .order_by("razeni")
        .values("id", "hierarchie__heslo_nadrazene", "heslo", "heslo_en")
    )
    if id:
        kategorie = Heslar.objects.filter(nazev_heslare=prvni_kat, id__in=id)
    else:
        kategorie = Heslar.objects.filter(nazev_heslare=prvni_kat)
    prvni = kategorie.order_by("razeni").values("id", "heslo", "heslo_en")
    return merge_heslare(prvni, druha)


def zjisti_katastr_souradnic(request):
    """
    Funkce pohledu pro vrácení katastru podle souradnic.
    """
    nalezene_katastry = RuianKatastr.objects.filter(
        hranice__contains=Point(float(request.GET.get("long", 0)), float(request.GET.get("lat", 0)))
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
    """
    Funkce pohledu pro zjištení výchozí hodnoty z heslaře.
    """
    nadrazene = request.GET.get("nadrazene", 0)
    vychozi_hodnota = HeslarHierarchie.objects.filter(heslo_nadrazene=nadrazene, typ="výchozí hodnota")
    if vychozi_hodnota.exists():
        queryset = vychozi_hodnota.values_list("heslo_podrazene", flat=True)
        list = []
        for id in queryset:
            list.append({"id": id})
        return JsonResponse(data=list, status=200, safe=False)
    else:
        return JsonResponse(data={}, status=400)


def zjisti_nadrazenou_hodnotu(request):
    """
    Funkce pohledu pro zjištení nadřazené hodnoty z heslaře.
    """
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
    return JsonResponse(data=list, status=200, safe=False)


class DokumentTypAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro autocomplete dokument typu.
    """

    def get_queryset(self):
        qs = Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP).filter(id__in=MODEL_3D_DOKUMENT_TYPES)
        if self.q:
            qs = qs.filter(nazev__icontains=self.q)
        return qs


class DokumentFormatAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro autocomplete dokument formatu.
    """

    def get_queryset(self):
        qs = Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT).filter(id__in=MODEL_3D_DOKUMENT_FORMATS)
        if self.q:
            qs = qs.filter(nazev__icontains=self.q)
        return qs


class PristupnostAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro autocomplete pristupnosti.
    """

    def get_queryset(self):
        qs = Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST)
        if self.q:
            qs = qs.filter(nazev__icontains=self.q)
        return qs


class HeslarAutocompleteView(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro autocomplete pristupnosti.
    """

    def get_queryset(self):
        qs = Heslar.objects.all()
        heslar_nazev = self.forwarded.get("heslar_nazev", None)
        if self.q:
            qs = qs.filter(heslo__icontains=self.q)
        if heslar_nazev:
            qs = qs.filter(nazev_heslare=heslar_nazev)
        return qs


class HeslarNazevAutocompleteView(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """
    Třída pohledu pro autocomplete pristupnosti.
    """

    def get_queryset(self):
        qs = HeslarNazev.objects.all()
        if self.q:
            qs = qs.filter(nazev__icontains=self.q)
        return qs


def heslar_list(heslo_nazev, filter={}, use_exclude=False):
    hesla = Heslar.objects.filter(nazev_heslare=heslo_nazev)
    if use_exclude:
        hesla_filtered = hesla.exclude(**filter)
    else:
        hesla_filtered = hesla.filter(**filter)
    if get_language() == "en":
        return list(hesla_filtered.values_list("id", "heslo_en"))
    else:
        return list(hesla_filtered.values_list("id", "heslo"))
