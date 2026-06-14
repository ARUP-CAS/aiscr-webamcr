from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DokumentMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
)
from django.test import TestCase
from dokument.models import Dokument, DokumentExtraData

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "C-TX-000001",
    "doi": None,
    "stav": "1",
    "rok_vzniku": None,
    "datum_zverejneni": None,
    "oznaceni_originalu": None,
    "popis": None,
    "poznamka": None,
    "cislo_objektu": None,
    "meritko": None,
    "vyska": None,
    "sirka": None,
    "pocet_variant_originalu": None,
    "odkaz": None,
    "datum_vzniku": None,
    "udalost": None,
    "region": None,
    "rok_od": None,
    "rok_do": None,
    "duveryhodnost": None,
    "geom_system": "wgs84",
    "geom": None,
    "geom_sjtsk": None,
    "let": None,
    "typ_dokumentu": "HES-TYPDOK-001",
    "material_originalu": "HES-MATORIG-001",
    "rada": "HES-RADA-001",
    "organizace": "HES-ORG-001",
    "pristupnost": "HES-PRIST-001",
    "ulozeni_originalu": None,
    "licence": None,
    "format": None,
    "zachovalost": None,
    "nahrada": None,
    "udalost_typ": None,
    "zeme": None,
}

MAP_SAFE_ROW = {
    "ident_cely": "C-TX-000001",
    "doi": None,
    "stav": "1",
    "rok_vzniku": None,
    "datum_zverejneni": None,
    "oznaceni_originalu": None,
    "popis": None,
    "poznamka": None,
    "cislo_objektu": None,
    "meritko": None,
    "vyska": None,
    "sirka": None,
    "pocet_variant_originalu": None,
    "odkaz": None,
    "datum_vzniku": None,
    "udalost": None,
    "region": None,
    "rok_od": None,
    "rok_do": None,
    "duveryhodnost": None,
    "geom_system": "wgs84",
    "geom": None,
    "geom_sjtsk": None,
    "let": None,
    "typ_dokumentu": None,
    "material_originalu": None,
    "rada": None,
    "organizace": None,
    "pristupnost": None,
    "ulozeni_originalu": None,
    "licence": None,
    "format": None,
    "zachovalost": None,
    "nahrada": None,
    "udalost_typ": None,
    "zeme": None,
}


class DokumentMapperInvalidStructureTest(TestCase):
    """Testy pro DokumentMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = DokumentMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = DokumentMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = DokumentMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class DokumentMapperMapInvalidValueTest(TestCase):
    """Testy pro DokumentMapper.map — neplatné hodnoty datových typů."""

    def test_invalid_datum_zverejneni_format_raises_error(self):
        """map() vyvolá ImportDataError při neplatném formátu datum_zverejneni."""
        row = MAP_SAFE_ROW.copy()
        row["datum_zverejneni"] = "2021-xxx-13"
        mapper = DokumentMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class DokumentMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro DokumentMapper.check_required_fields — bez DB."""

    def test_stav_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je stav None (not null)."""
        row = VALID_ROW.copy()
        row["stav"] = None
        mapper = DokumentMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = DokumentMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_doi_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je doi None (nullable pole)."""
        row = VALID_ROW.copy()
        row["doi"] = None
        mapper = DokumentMapper(row)
        mapper.check_required_fields(INSERT)

    def test_popis_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je popis None (nullable pole)."""
        row = VALID_ROW.copy()
        row["popis"] = None
        mapper = DokumentMapper(row)
        mapper.check_required_fields(INSERT)


class DokumentMapperMapValidTest(TestCase):
    """Testy pro DokumentMapper — platný dataset pro map()."""

    def test_map_returns_dict(self):
        """map() vrátí slovník pro platný řádek."""
        mapper = DokumentMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_includes_all_expected_keys(self):
        """map() vrátí všechny očekávané klíče."""
        mapper = DokumentMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = {
            "ident_cely",
            "doi",
            "stav",
            "rok_vzniku",
            "datum_zverejneni",
            "oznaceni_originalu",
            "popis",
            "poznamka",
            "cislo_objektu",
            "meritko",
            "vyska",
            "sirka",
            "pocet_variant_originalu",
            "odkaz",
            "datum_vzniku",
            "udalost",
            "region",
            "rok_od",
            "rok_do",
            "duveryhodnost",
            "geom_system",
            "geom",
            "geom_sjtsk",
            "let",
            "typ_dokumentu",
            "material_originalu",
            "rada",
            "organizace",
            "pristupnost",
            "ulozeni_originalu",
            "licence",
            "format",
            "zachovalost",
            "nahrada",
            "udalost_typ",
            "zeme",
        }
        self.assertEqual(set(result.keys()), expected_keys)


class DokumentMapperGetRecordHistoryTest(TestCase):
    """Testy pro DokumentMapper.get_record_history — bez DB."""

    def test_dokument_returns_itself(self):
        """get_record_history() vrátí přímo Dokument, pokud je předán jako záznam."""
        dokument = Dokument()
        result = DokumentMapper.get_record_history(dokument)
        self.assertIs(result, dokument)

    def test_extra_data_returns_dokument(self):
        """get_record_history() vrátí dokument navázaný na DokumentExtraData."""
        dokument = Dokument()
        extra_data = DokumentExtraData()
        extra_data.dokument = dokument
        result = DokumentMapper.get_record_history(extra_data)
        self.assertIs(result, dokument)


class DokumentMapperColumnMappingTest(TestCase):
    """Testy pro DokumentMapper — mapování názvů sloupců na pole modelu."""

    def test_column_to_field_mapping_maps_region_to_region_extra(self):
        """column_to_field_mapping mapuje sloupec 'region' na pole modelu 'region_extra'."""
        self.assertEqual(DokumentMapper.column_to_field_mapping.get("region"), "region_extra")
