import logging

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django_filters import CharFilter, FilterSet

logger = logging.getLogger(__name__)


class GeomIntersectsFilterMixin(FilterSet):
    """
    Mixin pro prostorové filtrování výpisu podle obdélníku (případně polygonu) nakresleného
    na mapě v záložce filtru. Hodnota se předává jako WKT v souřadnicovém systému WGS84
    (EPSG:4326) ve skrytém poli ``geom_filter``.

    Aplikuje se lookup ``__intersects`` (tj. **jakýkoli překryv** s vybranou plochou, nikoli plné
    obsažení jako u ``__within``) – díky tomu se do výběru dostanou i záznamy zasahující přes okraj.

    Při nevalidní WKT hodnotě filtr **nevrací žádné záznamy** (fail-closed), aby uživatel nedostal
    nefiltrovaný výpis v domnění, že je mapový výběr aplikován.

    Každý potomek nastaví :attr:`geom_filter_lookup` na cestu k geometrickému poli modelu
    (např. ``"geom"`` pro přímou bodovou geometrii nebo
    ``"archeologicky_zaznam__dokumentacni_jednotky_akce__pian__geom"`` pro geometrii přes Pian).

    Volitelně lze nastavit :attr:`geom_filter_presnost_lookup` na cestu k poli přesnosti PIANu.
    Pak se PIAN s přesností „poloha podle katastru“ vybírá podle svého reprezentativního bodu
    (``ST_PointOnSurface``), nikoli podle celého katastrálního polygonu – shodně s tím, jak je
    takový PIAN zobrazen v mapě (WYSIWYG: co je vidět jako bod, podle bodu se i vybírá).
    """

    geom_filter_lookup = "geom"
    geom_filter_presnost_lookup = None

    geom_filter = CharFilter(method="filter_geom")

    def filter_geom(self, queryset, name, value):
        """
        Filtruje queryset podle geometrie nakreslené na mapě.

        :param queryset: Queryset k prostorovému filtrování.
        :param name: Název filtru (``geom_filter``), nevyužívá se.
        :param value: WKT geometrie v EPSG:4326 ze skrytého pole; prázdná hodnota filtr přeskočí.

            :return: Vrací queryset omezený na záznamy protínající zadanou geometrii, nebo prázdný
                queryset, pokud je hodnota nevalidní.
        """
        if not value:
            return queryset
        try:
            geom = GEOSGeometry(value, srid=4326)
        except (GEOSException, ValueError, TypeError) as exc:
            logger.warning("core.filters.GeomIntersectsFilterMixin.filter_geom.invalid_wkt", extra={"error": str(exc)})
            return queryset.none()

        if not self.geom_filter_presnost_lookup:
            return queryset.filter(**{f"{self.geom_filter_lookup}__intersects": geom})

        # WYSIWYG: katastrální PIAN se vybírá podle reprezentativního bodu (jako je zobrazen v mapě),
        # ostatní PIANy podle skutečné geometrie.
        #
        # Kvůli výkonu nejdřív hrubě omezíme přes ``__intersects`` nad skutečnou geometrií – to využívá
        # prostorový GiST index. Reprezentativní bod (``ST_PointOnSurface``, který index použít neumí)
        # se pak počítá jen na již proříznuté množině. U katastrálního PIANu je bod na jeho polygonu,
        # takže hrubý filtr nic neodfiltruje navíc.
        from django.contrib.gis.db.models.functions import PointOnSurface
        from django.db.models import Q
        from heslar.hesla_dynamicka import PIAN_PRESNOST_KATASTR

        queryset = queryset.filter(**{f"{self.geom_filter_lookup}__intersects": geom})
        queryset = queryset.annotate(_geom_filter_pos=PointOnSurface(self.geom_filter_lookup))
        return queryset.filter(
            ~Q(**{self.geom_filter_presnost_lookup: PIAN_PRESNOST_KATASTR}) | Q(_geom_filter_pos__intersects=geom)
        )
