"""
Testy kontraktu deduplikace ve filtrech výběrů.

Výpisy stránkované přes :class:`core.utils.TwoQueryPaginator` (a výpisy bez
``distinct("pk", *sort)`` v ``get_queryset``, tj. projekt a dokument) spoléhají na to,
že queryset vrátí každý primární klíč nejvýše jednou. Filtr procházející víceřádkovou
relací (M2M nebo reverzní FK) jinak znásobí řádky, což posune stránkování a rozbije
počty. Deduplikaci proto musí zajistit sám filtr – buď ``distinct=True``, nebo
``.distinct()`` ve vlastní metodě.

Tyto testy ten kontrakt vynucují, aby ho nový filtr nemohl nechtěně porušit.
"""

import inspect

from arch_z.filters import AkceFilter
from django.test import SimpleTestCase
from dokument.filters import DokumentFilter, Model3DFilter
from ez.filters import ExterniZdrojFilter
from lokalita.filters import LokalitaFilter
from pas.filters import SamostatnyNalezFilter, UzivatelSpolupraceFilter
from projekt.filters import ProjektFilter

#: Všechny filtrsety výběrů.
FILTERSETS = (
    ProjektFilter,
    AkceFilter,
    LokalitaFilter,
    SamostatnyNalezFilter,
    UzivatelSpolupraceFilter,
    ExterniZdrojFilter,
    Model3DFilter,
    DokumentFilter,
)

#: Filtrsety, jejichž ``get_queryset`` nededuplikuje přes ``distinct("pk", *sort)``.
#: Právě u nich musí deduplikaci zajistit filtr sám – jinde ji řeší už queryset.
FILTERSETS_BEZ_DEDUPLIKACE_QUERYSETU = (
    ProjektFilter,
    Model3DFilter,
    DokumentFilter,
)

#: Metodové filtry z :data:`FILTERSETS_BEZ_DEDUPLIKACE_QUERYSETU`, které ``.distinct()``
#: nepotřebují. Nový záznam sem patří jen tehdy, když metoda prokazatelně nejoinuje
#: víceřádkovou relaci – jinak rozbije stránkování.
METHOD_FILTERS_BEZ_DEDUPLIKACE = {
    # geom leží na samotném projektu, resp. na OneToOne dokument.extra_data
    ("ProjektFilter", "geom_filter"),
    ("Model3DFilter", "geom_filter"),
    ("DokumentFilter", "geom_filter"),
    # planovane_zahajeni: přímé pole projektu
    ("ProjektFilter", "planovane_zahajeni"),
    # oblast: filtruje projekt.ident_cely
    ("ProjektFilter", "oblast"),
    # uzemni_prislusnost: filtruje dokument.ident_cely
    ("DokumentFilter", "uzemni_prislusnost"),
    # popisne_udaje (varianta DokumentFilter): přímá pole + licence (FK) + extra_data (OneToOne)
    ("DokumentFilter", "popisne_udaje"),
    # soubor_*: filtrují prázdnou metodou (noop), skutečné filtrování dělá jediný
    # korelovaný Exists v DokumentFilter.filter_queryset – žádný JOIN, žádné duplicity
    ("DokumentFilter", "soubor_typ"),
    ("DokumentFilter", "soubor_velikost_od"),
    ("DokumentFilter", "soubor_velikost_do"),
    ("DokumentFilter", "soubor_pocet_stran_od"),
    ("DokumentFilter", "soubor_pocet_stran_do"),
}


def je_cesta_viceradkova(model, cesta):
    """
    Zjistí, zda cesta ``field_name`` prochází alespoň jednou víceřádkovou relací.

    :param model: Model, od kterého se cesta vyhodnocuje.
    :param cesta: Hodnota ``field_name`` filtru (bez koncového lookupu).

        :return: ``True``, pokud cesta obsahuje M2M nebo reverzní FK.
    """
    aktualni = model
    for cast in cesta.split("__"):
        try:
            pole = aktualni._meta.get_field(cast)
        except Exception:
            # Koncový lookup (icontains apod.) nebo nerozpoznaná část – cesta končí.
            return False
        if pole.many_to_many or pole.one_to_many:
            return True
        souvisejici = getattr(pole, "related_model", None)
        if souvisejici is None:
            return False
        aktualni = souvisejici
    return False


def cesty_filtru(filtr):
    """
    Vrátí seznam cest ``field_name`` filtru; ``RangeFilter`` jich může mít víc.

    :param filtr: Instance filtru z ``base_filters``.

        :return: Seznam cest, případně prázdný seznam.
    """
    nazev = filtr.field_name
    if isinstance(nazev, (list, tuple)):
        return list(nazev)
    return [nazev] if nazev else []


class FiltrDeduplikaceTest(SimpleTestCase):
    """Ověřuje, že filtry přes víceřádkové relace deduplikují."""

    def test_deklarativni_filtry_maji_distinct(self):
        """Filtr s ``field_name`` přes víceřádkovou relaci musí mít ``distinct=True``."""
        chybejici = []
        for filterset in FILTERSETS:
            model = filterset._meta.model
            for nazev, filtr in filterset.base_filters.items():
                if getattr(filtr, "method", None):
                    continue  # metodové filtry řeší test níže
                if filtr.distinct:
                    continue
                for cesta in cesty_filtru(filtr):
                    if je_cesta_viceradkova(model, cesta):
                        chybejici.append(f"{filterset.__name__}.{nazev} (field_name={cesta!r})")
        self.assertEqual(
            chybejici,
            [],
            "Filtry procházejí víceřádkovou relací bez distinct=True – znásobí řádky "
            f"a rozbijí stránkování: {chybejici}",
        )

    def test_metodove_filtry_deduplikuji_nebo_jsou_vyjimkou(self):
        """Metodový filtr musí volat ``.distinct()``, nebo být uvedený mezi výjimkami."""
        chybejici = []
        for filterset in FILTERSETS_BEZ_DEDUPLIKACE_QUERYSETU:
            for nazev, filtr in filterset.base_filters.items():
                metoda = getattr(filtr, "method", None)
                if not metoda or not isinstance(metoda, str):
                    continue
                if (filterset.__name__, nazev) in METHOD_FILTERS_BEZ_DEDUPLIKACE:
                    continue
                funkce = getattr(filterset, metoda, None)
                if funkce is None:
                    continue
                try:
                    zdroj = inspect.getsource(funkce)
                except (OSError, TypeError):
                    continue
                if ".distinct(" not in zdroj:
                    chybejici.append(f"{filterset.__name__}.{nazev} (metoda {metoda}())")
        self.assertEqual(
            chybejici,
            [],
            "Metodové filtry nevolají .distinct() a nejsou mezi výjimkami. Pokud metoda "
            "nejoinuje víceřádkovou relaci, doplňte ji do METHOD_FILTERS_BEZ_DEDUPLIKACE "
            f"i s odůvodněním: {chybejici}",
        )

    def test_vyjimky_odpovidaji_existujicim_filtrum(self):
        """Seznam výjimek nesmí obsahovat filtry, které už neexistují."""
        existujici = {(fs.__name__, nazev) for fs in FILTERSETS_BEZ_DEDUPLIKACE_QUERYSETU for nazev in fs.base_filters}
        zastarale = sorted(METHOD_FILTERS_BEZ_DEDUPLIKACE - existujici)
        self.assertEqual(
            zastarale,
            [],
            f"METHOD_FILTERS_BEZ_DEDUPLIKACE odkazuje na neexistující filtry: {zastarale}",
        )
