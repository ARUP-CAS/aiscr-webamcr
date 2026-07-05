import logging

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django_filters import CharFilter, FilterSet

logger = logging.getLogger(__name__)


class GeomWithinFilterMixin(FilterSet):
    """
    Mixin pro prostorové filtrování výpisu podle obdélníku (případně polygonu) nakresleného
    na mapě v záložce filtru. Hodnota se předává jako WKT v souřadnicovém systému WGS84
    (EPSG:4326) ve skrytém poli ``geom_filter`` a aplikuje se lookup ``__intersects``.

    Každý potomek nastaví :attr:`geom_filter_lookup` na cestu k geometrickému poli modelu
    (např. ``"geom"`` pro přímou bodovou geometrii nebo
    ``"archeologicky_zaznam__dokumentacni_jednotky_akce__pian__geom"`` pro geometrii přes Pian).
    """

    geom_filter_lookup = "geom"

    geom_filter = CharFilter(method="filter_geom")

    def filter_geom(self, queryset, name, value):
        """
        Filtruje queryset podle geometrie nakreslené na mapě.

        :param queryset: Queryset k prostorovému filtrování.
        :param name: Název filtru (``geom_filter``), nevyužívá se.
        :param value: WKT geometrie v EPSG:4326 ze skrytého pole; prázdná hodnota filtr přeskočí.

            :return: Vrací queryset omezený na záznamy protínající zadanou geometrii.
        """
        if not value:
            return queryset
        try:
            geom = GEOSGeometry(value, srid=4326)
        except (GEOSException, ValueError, TypeError) as exc:
            logger.warning("core.filters.GeomWithinFilterMixin.filter_geom.invalid_wkt", extra={"error": str(exc)})
            return queryset
        return queryset.filter(**{f"{self.geom_filter_lookup}__intersects": geom})
