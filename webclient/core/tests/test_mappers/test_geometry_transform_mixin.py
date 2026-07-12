"""Testy pro ``GeometryTransformMixin.transform_geometries``.

Pokrývá obě opravené chyby:
- Bug 1: porovnání ``geom_system`` jako string (dříve int ``4326``/``5514`` → vždy False).
- Bug 2: výsledek transformace je tuple ``(wkt, status)``; vstup musí být WKT string,
  nikoli ``GEOSGeometry`` objekt.

Dále pokrývá přepočet odvozené geometrie při UPDATE, včetně doplnění hodnot
chybějících v souboru z existujícího záznamu v databázi.
"""

from types import SimpleNamespace
from unittest.mock import patch

from core.forms import ImportDataAdminForm
from core.import_data_mappers import ProjektMapper
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

WKT_WGS84 = "POINT (14.5 50.0)"
WKT_SJTSK = "POINT (-598288 -1160780)"


def _mapping(geom_system, geom=None, geom_sjtsk=None):
    return {"geom_system": geom_system, "geom": geom, "geom_sjtsk": geom_sjtsk}


class GeometryTransformMixinStringComparisonTest(TestCase):
    """Ověřuje, že geom_system se porovnává jako řetězec, nikoli číslo."""

    def test_string_4326_triggers_sjtsk_transform(self):
        """geom_system='4326' (string) spustí transformaci WGS84→SJTSK."""
        mapping = _mapping("4326", geom=WKT_WGS84)
        with patch(
            "core.import_data_mappers.transform_geom_to_sjtsk", return_value=(WKT_SJTSK, "OK")
        ) as mock_transform:
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        mock_transform.assert_called_once_with(WKT_WGS84)
        self.assertEqual(mapping["geom_sjtsk"], WKT_SJTSK)

    def test_empty_geom_with_4326_does_not_trigger_transform(self):
        """geom_system='4326' ale geom=None nespustí transformaci."""
        mapping = _mapping("4326", geom=None)
        with patch(
            "core.import_data_mappers.transform_geom_to_sjtsk", return_value=(WKT_SJTSK, "OK")
        ) as mock_transform:
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        mock_transform.assert_not_called()
        self.assertIsNone(mapping["geom_sjtsk"])

    def test_string_5514_triggers_wgs84_transform(self):
        """geom_system='5514' (string) spustí transformaci SJTSK→WGS84."""
        mapping = _mapping("5514", geom_sjtsk=WKT_SJTSK)
        with patch(
            "core.import_data_mappers.transform_geom_to_wgs84", return_value=(WKT_WGS84, "OK")
        ) as mock_transform:
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        mock_transform.assert_called_once_with(WKT_SJTSK)
        self.assertEqual(mapping["geom"], WKT_WGS84)

    def test_wgs84_string_label_does_not_trigger_transform(self):
        """geom_system='wgs84' (textový label) nevyvolá žádnou transformaci."""
        mapping = _mapping("wgs84", geom=WKT_WGS84)
        with patch("core.import_data_mappers.transform_geom_to_sjtsk") as mock_sjtsk, patch(
            "core.import_data_mappers.transform_geom_to_wgs84"
        ) as mock_wgs84:
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        mock_sjtsk.assert_not_called()
        mock_wgs84.assert_not_called()

    def test_none_geom_system_does_not_trigger_transform(self):
        """geom_system=None nevyvolá žádnou transformaci."""
        mapping = _mapping(None, geom=WKT_WGS84)
        with patch("core.import_data_mappers.transform_geom_to_sjtsk") as mock_sjtsk:
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        mock_sjtsk.assert_not_called()


class GeometryTransformMixinTupleUnpackTest(TestCase):
    """Ověřuje správné rozbalení tuple z transformačních funkcí."""

    def test_geom_sjtsk_set_to_wkt_string_not_tuple(self):
        """geom_sjtsk se nastaví na WKT string, nikoli celý tuple (wkt, status)."""
        mapping = _mapping("4326", geom=WKT_WGS84)
        with patch("core.import_data_mappers.transform_geom_to_sjtsk", return_value=(WKT_SJTSK, "OK")):
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        self.assertEqual(mapping["geom_sjtsk"], WKT_SJTSK)
        self.assertNotIsInstance(mapping["geom_sjtsk"], tuple)

    def test_geom_set_to_wkt_string_not_tuple(self):
        """geom se nastaví na WKT string, nikoli celý tuple (wkt, status)."""
        mapping = _mapping("5514", geom_sjtsk=WKT_SJTSK)
        with patch("core.import_data_mappers.transform_geom_to_wgs84", return_value=(WKT_WGS84, "OK")):
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        self.assertEqual(mapping["geom"], WKT_WGS84)
        self.assertNotIsInstance(mapping["geom"], tuple)

    def test_failed_transform_does_not_overwrite_geom_sjtsk(self):
        """Pokud transformace selže (status != 'OK'), geom_sjtsk se nepřepíše."""
        mapping = _mapping("4326", geom=WKT_WGS84, geom_sjtsk="original")
        with patch("core.import_data_mappers.transform_geom_to_sjtsk", return_value=("", "parse error")):
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        self.assertEqual(mapping["geom_sjtsk"], "original")

    def test_failed_transform_does_not_overwrite_geom(self):
        """Pokud transformace selže (status != 'OK'), geom se nepřepíše."""
        mapping = _mapping("5514", geom="original", geom_sjtsk=WKT_SJTSK)
        with patch("core.import_data_mappers.transform_geom_to_wgs84", return_value=("", "Not strig")):
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        self.assertEqual(mapping["geom"], "original")


class GeometryTransformMixinGEOSGeometryInputTest(TestCase):
    """Ověřuje, že GEOSGeometry objekt se správně převede na WKT string před transformací."""

    def test_geos_geometry_geom_value_converted_to_wkt(self):
        """Pokud je geom GEOSGeometry objekt, předá se transformační funkci jeho .wkt."""
        geom_obj = GEOSGeometry(WKT_WGS84, srid=4326)
        mapping = _mapping("4326", geom=geom_obj)
        captured = {}
        with patch(
            "core.import_data_mappers.transform_geom_to_sjtsk",
            side_effect=lambda wkt: captured.update({"wkt": wkt}) or (WKT_SJTSK, "OK"),
        ):
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        self.assertIsInstance(captured["wkt"], str)
        self.assertNotIsInstance(captured["wkt"], GEOSGeometry.__class__)

    def test_geos_geometry_geom_sjtsk_value_converted_to_wkt(self):
        """Pokud je geom_sjtsk GEOSGeometry objekt, předá se transformační funkci jeho .wkt."""
        geom_obj = GEOSGeometry(WKT_SJTSK, srid=5514)
        mapping = _mapping("5514", geom_sjtsk=geom_obj)
        captured = {}
        with patch(
            "core.import_data_mappers.transform_geom_to_wgs84",
            side_effect=lambda wkt: captured.update({"wkt": wkt}) or (WKT_WGS84, "OK"),
        ):
            ProjektMapper.transform_geometries(None, mapping, INSERT)
        self.assertIsInstance(captured["wkt"], str)


def _fake_mapper(db_record):
    """Vytvoří náhradu mapperu vracející ``db_record`` místo dotazu do databáze."""
    return SimpleNamespace(_get_geometry_db_record=lambda: db_record)


class GeometryTransformMixinUpdateTest(TestCase):
    """Ověřuje přepočet odvozené geometrie při akci UPDATE."""

    def test_update_with_full_geometry_columns_recomputes_sjtsk(self):
        """UPDATE s geom_system='4326' a geom v souboru přepočítá geom_sjtsk bez dotazu do DB."""
        mapping = _mapping("4326", geom=WKT_WGS84)
        with patch(
            "core.import_data_mappers.transform_geom_to_sjtsk", return_value=(WKT_SJTSK, "OK")
        ) as mock_transform:
            ProjektMapper.transform_geometries(None, mapping, UPDATE)
        mock_transform.assert_called_once_with(WKT_WGS84)
        self.assertEqual(mapping["geom_sjtsk"], WKT_SJTSK)

    def test_update_with_full_geometry_columns_recomputes_wgs84(self):
        """UPDATE s geom_system='5514' a geom_sjtsk v souboru přepočítá geom bez dotazu do DB."""
        mapping = _mapping("5514", geom_sjtsk=WKT_SJTSK)
        with patch(
            "core.import_data_mappers.transform_geom_to_wgs84", return_value=(WKT_WGS84, "OK")
        ) as mock_transform:
            ProjektMapper.transform_geometries(None, mapping, UPDATE)
        mock_transform.assert_called_once_with(WKT_SJTSK)
        self.assertEqual(mapping["geom"], WKT_WGS84)

    def test_update_geom_only_reads_geom_system_from_db(self):
        """UPDATE pouze s geom v souboru doplní geom_system z DB a přepočítá geom_sjtsk."""
        mapping = {"geom": WKT_WGS84}
        mapper = _fake_mapper(SimpleNamespace(geom_system="4326", geom=None, geom_sjtsk=None))
        with patch(
            "core.import_data_mappers.transform_geom_to_sjtsk", return_value=(WKT_SJTSK, "OK")
        ) as mock_transform:
            ProjektMapper.transform_geometries(mapper, mapping, UPDATE)
        mock_transform.assert_called_once_with(WKT_WGS84)
        self.assertEqual(mapping["geom_sjtsk"], WKT_SJTSK)

    def test_update_geom_system_only_reads_geometry_from_db(self):
        """UPDATE pouze s geom_system v souboru vezme zdrojovou geometrii z DB a přepočítá odvozenou."""
        mapping = {"geom_system": "4326"}
        mapper = _fake_mapper(SimpleNamespace(geom_system="5514", geom=WKT_WGS84, geom_sjtsk=None))
        with patch(
            "core.import_data_mappers.transform_geom_to_sjtsk", return_value=(WKT_SJTSK, "OK")
        ) as mock_transform:
            ProjektMapper.transform_geometries(mapper, mapping, UPDATE)
        mock_transform.assert_called_once_with(WKT_WGS84)
        self.assertEqual(mapping["geom_sjtsk"], WKT_SJTSK)

    def test_update_clearing_geom_clears_geom_sjtsk(self):
        """UPDATE s prázdným geom (geom_system='4326') vynuluje i odvozený geom_sjtsk."""
        mapping = _mapping("4326", geom=None, geom_sjtsk=WKT_SJTSK)
        with patch("core.import_data_mappers.transform_geom_to_sjtsk") as mock_transform:
            ProjektMapper.transform_geometries(None, mapping, UPDATE)
        mock_transform.assert_not_called()
        self.assertIsNone(mapping["geom_sjtsk"])

    def test_update_clearing_geom_sjtsk_clears_geom(self):
        """UPDATE s prázdným geom_sjtsk (geom_system='5514') vynuluje i odvozený geom."""
        mapping = _mapping("5514", geom=WKT_WGS84, geom_sjtsk=None)
        with patch("core.import_data_mappers.transform_geom_to_wgs84") as mock_transform:
            ProjektMapper.transform_geometries(None, mapping, UPDATE)
        mock_transform.assert_not_called()
        self.assertIsNone(mapping["geom"])

    def test_update_without_geometry_columns_does_nothing(self):
        """UPDATE bez geometrických sloupců neprovede transformaci ani dotaz do DB."""
        mapping = {"nazev": "Testovací projekt"}
        with patch("core.import_data_mappers.transform_geom_to_sjtsk") as mock_sjtsk, patch(
            "core.import_data_mappers.transform_geom_to_wgs84"
        ) as mock_wgs84:
            ProjektMapper.transform_geometries(None, mapping, UPDATE)
        mock_sjtsk.assert_not_called()
        mock_wgs84.assert_not_called()
        self.assertEqual(mapping, {"nazev": "Testovací projekt"})

    def test_update_failed_transform_does_not_overwrite(self):
        """Pokud transformace při UPDATE selže, odvozená geometrie se nepřepíše."""
        mapping = _mapping("4326", geom=WKT_WGS84, geom_sjtsk="original")
        with patch("core.import_data_mappers.transform_geom_to_sjtsk", return_value=("", "parse error")):
            ProjektMapper.transform_geometries(None, mapping, UPDATE)
        self.assertEqual(mapping["geom_sjtsk"], "original")

    def test_update_missing_record_in_db_does_not_crash(self):
        """UPDATE s geometrií v souboru a neexistujícím záznamem v DB neselže."""
        mapping = {"geom": WKT_WGS84}
        mapper = _fake_mapper(None)
        with patch("core.import_data_mappers.transform_geom_to_sjtsk") as mock_transform:
            ProjektMapper.transform_geometries(mapper, mapping, UPDATE)
        mock_transform.assert_not_called()
        self.assertNotIn("geom_sjtsk", mapping)
