from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    ProjektMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "C-202401-000001",
    "stav": "1",
    "lokalizace": "Pole za vsí",
    "parcelni_cislo": "1234/5",
    "geom": None,
    "geom_system": "wgs84",
    "geom_sjtsk": None,
    "podnet": None,
    "planovane_zahajeni": None,
    "uzivatelske_oznaceni": None,
    "oznaceni_stavby": None,
    "kulturni_pamatka_cislo": None,
    "kulturni_pamatka_popis": None,
    "datum_zahajeni": None,
    "datum_ukonceni": None,
    "termin_odevzdani_nz": None,
    "typ_projektu": "HES-PROJTYP-001",
    "hlavni_katastr": "123456",
    "vedouci_projektu": None,
    "organizace": None,
    "kulturni_pamatka": None,
}


class ProjektMapperInvalidStructureTest(TestCase):
    """Testy pro ProjektMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_hlavni_katastr_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci hlavni_katastr."""
        row = VALID_ROW.copy()
        del row["hlavni_katastr"]
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ProjektMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_unknown_column_in_update_raises_error(self):
        """_check_column_structure() UPDATE vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper._check_column_structure(UPDATE, include_primary_key=True)


class ProjektMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ProjektMapper.check_required_fields — bez DB."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_stav_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je stav None (not null)."""
        row = VALID_ROW.copy()
        row["stav"] = None
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_lokalizace_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je lokalizace None (nullable pole)."""
        row = VALID_ROW.copy()
        row["lokalizace"] = None
        mapper = ProjektMapper(row)
        mapper.check_required_fields(INSERT)

    def test_vedouci_projektu_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je vedouci_projektu None (nullable FK)."""
        row = VALID_ROW.copy()
        row["vedouci_projektu"] = None
        mapper = ProjektMapper(row)
        mapper.check_required_fields(INSERT)
