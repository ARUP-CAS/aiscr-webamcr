"""Testy návratových stavů funkcí pro transformaci geometrie."""

from unittest import TestCase

from core.coordTransform import transform_geom, transform_geom_to_sjtsk, transform_geom_to_wgs84


class TransformGeomReturnStatusTest(TestCase):
    """Ověřuje návratový kontrakt transformací WKT geometrie."""

    def test_transform_geom_returns_ok_for_valid_wkt(self):
        """Obecná transformace vrací převedený WKT a stav ``OK`` pro platný vstup."""
        converted, status = transform_geom("POINT (14.5 50.0)", lambda x, y: (x, y))

        self.assertEqual(converted, "POINT (14.5 50.0)")
        self.assertEqual(status, "OK")

    def test_transform_geom_returns_error_for_non_string_input(self):
        """Obecná transformace vrací prázdný řetězec a chybový stav pro neřetězcový vstup."""
        converted, status = transform_geom(None, lambda x, y: (x, y))

        self.assertEqual(converted, "")
        self.assertEqual(status, "Not strig")

    def test_transform_geom_to_sjtsk_returns_ok_for_valid_wkt(self):
        """Transformace do S-JTSK vrací převedený WKT a stav ``OK`` pro platný vstup."""
        converted, status = transform_geom_to_sjtsk("POINT (14.5 50.0)")

        self.assertIsInstance(converted, str)
        self.assertNotEqual(converted, "")
        self.assertEqual(status, "OK")

    def test_transform_geom_to_sjtsk_returns_error_for_non_string_input(self):
        """Transformace do S-JTSK vrací prázdný řetězec a chybový stav pro neřetězcový vstup."""
        converted, status = transform_geom_to_sjtsk(None)

        self.assertEqual(converted, "")
        self.assertEqual(status, "Not strig")

    def test_transform_geom_to_wgs84_returns_ok_for_valid_wkt(self):
        """Transformace do WGS84 vrací převedený WKT a stav ``OK`` pro platný vstup."""
        converted, status = transform_geom_to_wgs84("POINT (-598288 -1160780)")

        self.assertIsInstance(converted, str)
        self.assertNotEqual(converted, "")
        self.assertEqual(status, "OK")

    def test_transform_geom_to_wgs84_returns_error_for_non_string_input(self):
        """Transformace do WGS84 vrací prázdný řetězec a chybový stav pro neřetězcový vstup."""
        converted, status = transform_geom_to_wgs84(None)

        self.assertEqual(converted, "")
        self.assertEqual(status, "Not strig")
