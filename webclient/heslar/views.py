import logging

from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError, ProgrammingError
from django.db.models import IntegerField, Value
from django.http import JsonResponse
from django.utils.translation import get_language
from django.views import View
from heslar.hesla import HESLAR_DOKUMENT_FORMAT, HESLAR_DOKUMENT_TYP, HESLAR_PRISTUPNOST
from heslar.hesla_dynamicka import MODEL_3D_DOKUMENT_FORMATS, MODEL_3D_DOKUMENT_TYPES
from heslar.models import Heslar, HeslarHierarchie, HeslarNazev, RuianKatastr

logger = logging.getLogger(__name__)


class RuianKatastrAutocomplete(autocomplete.Select2QuerySetView):
    """Třída pohledu pro autocomplete ruian katastru."""

    def get_queryset(self):
        """
        Vrací queryset. v aplikaci.

        :return: Vrací proměnná ``qs``.
        """
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
    Vytvoří dvoustupňový select z dvou sad hesel.

    :param first: První sada hesel s ID a názvy
    :param second: Druhá sada hesel hierarchicky podřazena první sadě

    :return: Seznam dvojic (název, možnosti) pro dvoustupňový select
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
        # Tato chyba se vždy zobrazí dříve.
        logger.debug("heslar.views.merge_heslare.error", extra={"error": err})
    except OperationalError as err:
        # Tato chyba se vždy zobrazí dříve.
        logger.debug("heslar.views.merge_heslare.error", extra={"error": err})
    return data


def heslar_12(druha, prvni_kat, id=False):
    """
    Funkce pro vytvoření dvoustupňového selectu.

    :param druha: Parametr ``druha`` se předává do volání ``filter()``, ``merge_heslare()``, vstupuje do návratové hodnoty.
    :param prvni_kat: Parametr ``prvni_kat`` se předává do volání ``filter()``.
    :param id: Identifikátor ``id`` používaný pro dohledání cílového záznamu.

        :return: Vrací výsledek volání ``merge_heslare()``.
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

    :param request: Parametr ``request`` se předává do volání ``filter()``, ``Point()``, pracuje se s atributy ``GET``.

        :return: Vrací výsledek volání ``JsonResponse()``.
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

    :param request: Parametr ``request`` se předává do volání ``int()``, pracuje se s atributy ``GET``.

        :return: Vrací výsledek volání ``JsonResponse()``.
    """
    try:
        nadrazene = int(request.GET.get("nadrazene"))
    except ValueError:
        nadrazene = 0
    vychozi_hodnota = HeslarHierarchie.objects.filter(heslo_nadrazene=nadrazene, typ="výchozí hodnota")
    if vychozi_hodnota.exists():
        queryset = vychozi_hodnota.values_list("heslo_podrazene", flat=True)
        list = []
        for id in queryset:
            list.append({"id": id})
        return JsonResponse(data=list, status=200, safe=False)
    else:
        return JsonResponse(data={}, status=200)


def zjisti_nadrazenou_hodnotu(request):
    """
    Funkce pohledu pro zjištení nadřazené hodnoty z heslaře.

    :param request: Parametr ``request`` se předává do volání ``int()``, pracuje se s atributy ``GET``.

        :return: Vrací výsledek volání ``JsonResponse()``.
    """
    podrazene = request.GET.get("podrazene", 0)
    i = 0
    while i < int(request.GET.get("iterace", 1)):
        try:
            nadrazene = HeslarHierarchie.objects.get(heslo_podrazene=podrazene, typ="podřízenost").heslo_nadrazene
            podrazene = nadrazene.id
            i += 1
        except ObjectDoesNotExist as err:
            logger.debug("heslar.views.zjisti_nadrazenou_hodnotu.does_not_exist", extra={"error": err})
            return JsonResponse(data={}, status=400)
    list = [{"id": nadrazene.id}]
    return JsonResponse(data=list, status=200, safe=False)


class DokumentTypAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Třída pohledu pro autocomplete dokument typu."""

    def get_queryset(self):
        """
        Vrací queryset. v aplikaci.

        :return: Vrací proměnná ``qs``.
        """
        qs = Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_TYP).filter(id__in=MODEL_3D_DOKUMENT_TYPES)
        if self.q:
            qs = qs.filter(nazev__icontains=self.q)
        return qs


class DokumentFormatAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Třída pohledu pro autocomplete dokument formatu."""

    def get_queryset(self):
        """
        Vrací queryset. v aplikaci.

        :return: Vrací proměnná ``qs``.
        """
        qs = Heslar.objects.filter(nazev_heslare=HESLAR_DOKUMENT_FORMAT).filter(id__in=MODEL_3D_DOKUMENT_FORMATS)
        if self.q:
            qs = qs.filter(nazev__icontains=self.q)
        return qs


class PristupnostAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Třída pohledu pro autocomplete pristupnosti."""

    def get_queryset(self):
        """
        Vrací queryset. v aplikaci.

        :return: Vrací proměnná ``qs``.
        """
        qs = Heslar.objects.filter(nazev_heslare=HESLAR_PRISTUPNOST)
        if self.q:
            qs = qs.filter(nazev__icontains=self.q)
        return qs


class HeslarAutocompleteView(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Třída pohledu pro autocomplete pristupnosti."""

    def get_queryset(self):
        """
        Vrací queryset. v aplikaci.

        :return: Vrací proměnná ``qs``.
        """
        qs = Heslar.objects.all()
        heslar_nazev = self.forwarded.get("heslar_nazev", None)
        if self.q:
            qs = qs.filter(heslo__icontains=self.q)
        if heslar_nazev:
            qs = qs.filter(nazev_heslare=heslar_nazev)
        return qs


class HeslarNazevAutocompleteView(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    """Třída pohledu pro autocomplete pristupnosti."""

    def get_queryset(self):
        """
        Vrací queryset. v aplikaci.

        :return: Vrací proměnná ``qs``.
        """
        qs = HeslarNazev.objects.all()
        if self.q:
            qs = qs.filter(nazev__icontains=self.q)
        return qs


def heslar_list(heslo_nazev, filter={}, use_exclude=False):
    """
    Vrací seznam hesel z heslaře filtrovaných podle kritérií.

    :param heslo_nazev: Název heslaře, ze kterého se načítají hesla
    :param filter: Slovník kritérií pro filtrování záznamů
    :param use_exclude: Má-li být použita metoda exclude namíste filter

    :return: Seznam dvojic (ID, název hesla) ve zvolném jazyce
    """
    hesla = Heslar.objects.filter(nazev_heslare=heslo_nazev)
    if use_exclude:
        hesla_filtered = hesla.exclude(**filter)
    else:
        hesla_filtered = hesla.filter(**filter)
    if get_language() == "en":
        return list(hesla_filtered.values_list("id", "heslo_en"))
    else:
        return list(hesla_filtered.values_list("id", "heslo"))


class ContinueKatastrProcessing(LoginRequiredMixin, View):
    """
    Async processor pro hromadný přepočet katastrů u Projekt/AZ/SN.

    Volá se z admin stránky ``/admin/update-katastry/`` opakovaným polováním
    z JS – každé volání zpracuje další záznam v Redis frontě (klíč
    ``update_katastry_<random>``). Pro jeden ``ident_cely`` načte záznam,
    podle typu (Projekt/AZ/SN) zavolá příslušnou ``reassign_*`` funkci a
    vrátí JSON s progresem a výsledkem.
    """

    def get(self, request, **kwargs):
        """
        Zpracuje další záznam ve frontě a vrátí JSON s progresem.

        :param request: HTTP GET požadavek.
        :param kwargs: Klíčové argumenty včetně ``job_id``.

            :return: ``JsonResponse`` se strukturou ``{progress, remaining, ident_cely, result, detail}``.
        """
        from core.connectors import RedisConnector
        from core.ident_cely import get_record_from_ident
        from core.repository_connector import FedoraError
        from django.http import Http404
        from django.utils.translation import gettext as _t
        from heslar.ruian_sync import reassign as reassign_mod

        r = RedisConnector().get_connection()
        job_id = kwargs.get("job_id")
        raw = r.get(job_id)
        if raw is None:
            return JsonResponse({"progress": 100, "remaining": 0, "result": "expired"})

        job_data = raw.decode("utf-8")
        iterator, *ident_list = job_data.split(";")
        iterator = int(iterator)
        item_count = max(len(ident_list), 1)
        result = {
            "progress": (iterator + 1) / item_count * 100,
            "remaining": len(ident_list) - iterator,
            "detail": None,
            "is_error": False,
        }
        if iterator >= len(ident_list):
            return JsonResponse(result)

        ident_cely = ident_list[iterator]
        result["ident_cely"] = ident_cely
        r.set(job_id, f"{iterator + 1};{';'.join(ident_list)}")

        try:
            record = get_record_from_ident(ident_cely)
        except Http404:
            record = None
        if record is None:
            logger.debug("heslar.views.ContinueKatastrProcessing.not_found", extra={"ident_cely": ident_cely})
            result["result"] = _t("heslar.views.ContinueKatastrProcessing.record_not_found")
            result["is_error"] = True
            return JsonResponse(result)

        try:
            changed = self._process(record, reassign_mod)
            result["result"] = (
                _t("heslar.views.ContinueKatastrProcessing.changed")
                if changed
                else _t("heslar.views.ContinueKatastrProcessing.no_change")
            )
        except FedoraError as err:
            logger.debug(
                "heslar.views.ContinueKatastrProcessing.fedora_error",
                extra={"ident_cely": ident_cely, "error": err},
            )
            result["result"] = _t("heslar.views.ContinueKatastrProcessing.error")
            result["is_error"] = True
        return JsonResponse(result)

    @staticmethod
    def _process(record, reassign_mod) -> bool:
        """
        Vyvolá příslušnou ``reassign_*`` funkci podle typu záznamu.

        Záznam se zapíše pouze pokud došlo ke změně oproti původnímu stavu
        (porovnává se ``hlavni_katastr_id`` resp. ``katastr_id``).

        :param record: Instance Projekt/ArcheologickyZaznam/SamostatnyNalez.
        :param reassign_mod: Modul ``heslar.ruian_sync.reassign`` (předáno
            kvůli lazy importu).

            :return: ``True`` pokud reassign vrátil katastr odlišný od původního.
        """
        from arch_z.models import ArcheologickyZaznam
        from pas.models import SamostatnyNalez
        from projekt.models import Projekt

        if isinstance(record, Projekt):
            old_id = record.hlavni_katastr_id
            new_kat = reassign_mod.reassign_projekt(record)
            return new_kat is not None and new_kat.pk != old_id
        if isinstance(record, ArcheologickyZaznam):
            old_main = record.hlavni_katastr_id
            old_set = set(record.katastry.values_list("id", flat=True))
            reassign_mod.reassign_az(record)
            record.refresh_from_db()
            new_set = set(record.katastry.values_list("id", flat=True))
            return record.hlavni_katastr_id != old_main or new_set != old_set
        if isinstance(record, SamostatnyNalez):
            old_id = record.katastr_id
            new_kat = reassign_mod.reassign_sn(record)
            return new_kat is not None and new_kat.pk != old_id
        logger.debug(
            "heslar.views.ContinueKatastrProcessing._process.unsupported",
            extra={"type": type(record).__name__},
        )
        return False
