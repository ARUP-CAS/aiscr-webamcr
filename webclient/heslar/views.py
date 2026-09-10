import logging

from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError, ProgrammingError
from django.db.models import IntegerField, Value
from django.http import JsonResponse
from django.utils.translation import get_language
from fedora_management.views import AdminRecordProcessingView
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


def _souradnice_ze_starych_parametru(request):
    """
    Převede zastaralé parametry ``long``/``lat`` (EPSG:4326) na JTSK.

    Endpoint dřív bral WGS84; kontrakt se změnil naráz, takže prohlížeč
    s cachovaným starším skriptem posílá stále původní jména. Bez tohohle
    přemostění by dostal prázdnou odpověď a uživatel by jen viděl, že se
    katastr „nedoplnil“.

    :param request: HTTP GET požadavek.
    :return: Dvojice ``(x, y)`` v EPSG:5514, nebo ``None`` když staré
        parametry chybí nebo je nejde převést.
    """
    from core.coordTransform import transform_geom_to_sjtsk

    try:
        lon = float(request.GET["long"])
        lat = float(request.GET["lat"])
    except (KeyError, ValueError):
        return None

    wkt, stav = transform_geom_to_sjtsk(f"POINT({lon} {lat})")
    if stav != "OK" or not wkt:
        return None

    logger.warning(
        "heslar.views.zjisti_katastr_souradnic.zastarale_parametry",
        extra={"reason": "Volající posílá long/lat; jde nejspíš o cachovaný starší mapa_projekty.js."},
    )
    bod = GEOSGeometry(wkt, srid=5514)
    return bod.x, bod.y


def zjisti_katastr_souradnic(request):
    """
    Vrátí katastr obsahující zadaný bod v EPSG:5514 (S-JTSK).

    Volá se AJAX z ``mapa_projekty.js`` po kliknutí do Leaflet mapy (mapa
    je v JTSK CRS ``mapa_settings_jtsk.js``). Vstupem jsou GET parametry
    ``x`` a ``y`` v EPSG:5514 v konvenci projektu (záporné hodnoty).

    Přechodně se přijímají i původní parametry ``long``/``lat``. Kontrakt se
    měnil z WGS84 na JTSK v jednom kroku, takže prohlížeč s cachovaným starším
    ``mapa_projekty.js`` posílá pořád stará jména – dostal by prázdný objekt
    a políčko katastru by zůstalo nevyplněné bez jakékoli hlášky. Souřadnice
    se v takovém případě převedou přes ``core.coordTransform``; až cache
    doběhne, dá se větev odstranit.

    :param request: GET s parametry ``x`` a ``y`` v EPSG:5514, nebo přechodně
        ``long`` a ``lat`` v EPSG:4326.

        :return: JsonResponse s ``id`` a ``value`` katastru, nebo prázdný.
    """
    try:
        x_val = float(request.GET["x"])
        y_val = float(request.GET["y"])
    except (KeyError, ValueError):
        souradnice = _souradnice_ze_starych_parametru(request)
        if souradnice is None:
            logger.warning(
                "heslar.views.zjisti_katastr_souradnic.invalid_params",
                extra={"GET": dict(request.GET)},
            )
            return JsonResponse({})
        x_val, y_val = souradnice
    bod = GEOSGeometry(f"POINT({x_val} {y_val})", srid=5514)
    nalezene_katastry = RuianKatastr.objects.filter(hranice__contains=bod)
    if nalezene_katastry.count() == 1:
        return JsonResponse(
            {
                "id": nalezene_katastry.first().pk,
                "value": str(nalezene_katastry.first()),
            }
        )
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


#: Prefix Redis klíčů jobů hromadného přepočtu katastrů. Redis je sdílený
#: napříč celou aplikací (``import_data_*``, ``update_metadata_*``,
#: ``update_pid_*``…), takže endpoint nesmí sáhnout na klíč, který mu nepatří.
UPDATE_KATASTRY_PREFIX = "update_katastry_"

#: Expirace jobu v Redis. Nedokončený job zmizí sám, stejně jako u importu dat.
UPDATE_KATASTRY_REDIS_EXPIRATION = 6 * 60 * 60


class ContinueKatastrProcessing(UserPassesTestMixin, AdminRecordProcessingView):
    """
    Async processor pro hromadný přepočet katastrů u Projekt/AZ/SN.

    Volá se z admin stránky ``/admin/update-katastry/`` opakovaným polováním
    z JS – každé volání zpracuje další záznam v Redis frontě (klíč
    ``update_katastry_<token>``).

    Vlastní protokol (čtení fronty, posun indexu, progres, ošetření chyb)
    dodává :class:`~fedora_management.views.AdminRecordProcessingView`; tahle
    třída doplňuje jen oprávnění a to, co se s jedním záznamem stane.
    """

    job_id_prefix = UPDATE_KATASTRY_PREFIX
    job_expirace = UPDATE_KATASTRY_REDIS_EXPIRATION

    def test_func(self):
        """
        Endpoint smí volat jen superuživatel, stejně jako zakládání úlohy.

        Job vzniká v ``core.admin_sites.update_katastry_file_upload`` pod
        podmínkou ``request.user.is_superuser``; kdyby pokračování stačilo
        běžnému přihlášenému uživateli, dala by se cizí úloha posouvat
        i dokončovat. Zpracování navíc mění data a metadata ve Fedoře.

        :return: ``True``, když je přihlášený uživatel superuživatel.
        """
        return bool(self.request.user.is_authenticated and self.request.user.is_superuser)

    def process_record(self, record, result, **kwargs):
        """
        Přepočítá katastr jednoho záznamu a doplní výsledek do odpovědi.

        :param record: Instance Projekt/ArcheologickyZaznam/SamostatnyNalez.
        :param result: Slovník s průběhem, který se vrací do JSON odpovědi.
        :param kwargs: Klíčové argumenty z URL.
        :return: Doplněný slovník ``result``.
        """
        from django.utils.translation import gettext as _t
        from heslar.ruian_sync import reassign as reassign_mod

        changed = self._process(record, reassign_mod)
        result["result"] = (
            _t("heslar.views.ContinueKatastrProcessing.changed")
            if changed
            else _t("heslar.views.ContinueKatastrProcessing.no_change")
        )
        return result

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
