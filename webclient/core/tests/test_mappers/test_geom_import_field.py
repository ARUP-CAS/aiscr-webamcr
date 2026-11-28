from core.import_data_mappers import GeomImportField, ImportDataError
from django.contrib.gis.geos import GEOSGeometry
from django.test import SimpleTestCase


class GeomImportFieldTest(SimpleTestCase):
    """Testy převodu textové hodnoty na geometrii v ``GeomImportField``."""

    def test_malformed_value_raises_import_data_error(self):
        """Text, který GEOS ani GDAL nepřečte, vyvolá chybu řádku místo pádu validace."""
        for value in ("NOT A GEOMETRY", "POINT(1 2", '{"type":1}'):
            with self.subTest(value=value):
                field = GeomImportField(4326)
                with self.assertRaises(ImportDataError):
                    field.value = value

    def test_valid_wkt_returns_geometry(self):
        """Platné WKT se převede na geometrii se SRID pole."""
        field = GeomImportField(4326)
        field.value = "SRID=4326;POINT(14.5 50.0)"
        self.assertIsInstance(field.value, GEOSGeometry)
        self.assertEqual(field.value.srid, 4326)
