from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    SamostatnyNalezMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "X-C-SN-000001",
    "igsn": None,
    "stav": "1",
    "evidencni_cislo": "EV-001",
    "lokalizace": "Pole za vsí",
    "geom_system": "wgs84",
    "geom": None,
    "geom_sjtsk": None,
    "hloubka": None,
    "datum_nalezu": None,
    "predano": "false",
    "presna_datace": None,
    "pocet": None,
    "poznamka": None,
    "projekt": None,
    "pristupnost": "HES-PRIST-001",
    "katastr": "123456",
    "okolnosti": None,
    "nalezce": None,
    "predano_organizace": None,
    "obdobi": None,
    "druh_nalezu": None,
    "specifikace": None,
}


class SamostatnyNalezMapperInvalidStructureTest(TestCase):
    """Testy pro SamostatnyNalezMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = SamostatnyNalezMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = SamostatnyNalezMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_katastr_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci katastr."""
        row = VALID_ROW.copy()
        del row["katastr"]
        mapper = SamostatnyNalezMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = SamostatnyNalezMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_unknown_column_in_update_raises_error(self):
        """_check_column_structure() UPDATE vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = SamostatnyNalezMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper._check_column_structure(UPDATE, include_primary_key=True)


class SamostatnyNalezMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro SamostatnyNalezMapper.check_required_fields — bez DB."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = SamostatnyNalezMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_projekt_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je projekt None (not null FK)."""
        row = VALID_ROW.copy()
        row["projekt"] = None
        mapper = SamostatnyNalezMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je poznamka None (nullable pole)."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        row["projekt"] = "C-202401-000001"
        mapper = SamostatnyNalezMapper(row)
        mapper.check_required_fields(INSERT)
