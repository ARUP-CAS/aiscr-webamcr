from arch_z.models import ArcheologickyZaznam
from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    LokalitaMapper,
)
from django.test import TestCase
from lokalita.models import Lokalita

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "C-L-000001",
    "igsn": None,
    "stav": "1",
    "pristupnost": "HES-PRIST-001",
    "hlavni_katastr": "123456",
    "nazev": "Testovací lokalita",
    "uzivatelske_oznaceni": None,
    "typ_lokality": "HES-LTYP-001",
    "druh": "HES-LDRUH-001",
    "zachovalost": None,
    "jistota": None,
    "popis": None,
    "poznamka": None,
}

MAP_SAFE_ROW = {
    "ident_cely": "C-L-000001",
    "igsn": None,
    "stav": "1",
    "pristupnost": None,
    "hlavni_katastr": None,
    "nazev": "Testovací lokalita",
    "uzivatelske_oznaceni": None,
    "typ_lokality": None,
    "druh": None,
    "zachovalost": None,
    "jistota": None,
    "popis": None,
    "poznamka": None,
}


class LokalitaMapperInvalidStructureTest(TestCase):
    """Testy pro LokalitaMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = LokalitaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = LokalitaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_nazev_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci nazev."""
        row = VALID_ROW.copy()
        del row["nazev"]
        mapper = LokalitaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = LokalitaMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class LokalitaMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro LokalitaMapper.check_required_fields — bez DB."""

    def test_stav_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je stav None (not null)."""
        row = VALID_ROW.copy()
        row["stav"] = None
        mapper = LokalitaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_nazev_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je nazev None (not null)."""
        row = VALID_ROW.copy()
        row["nazev"] = None
        mapper = LokalitaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_igsn_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je igsn None (nullable pole)."""
        row = VALID_ROW.copy()
        row["igsn"] = None
        mapper = LokalitaMapper(row)
        mapper.check_required_fields(INSERT)

    def test_popis_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je popis None (nullable pole)."""
        row = VALID_ROW.copy()
        row["popis"] = None
        mapper = LokalitaMapper(row)
        mapper.check_required_fields(INSERT)


class LokalitaMapperMapValidTest(TestCase):
    """Testy pro LokalitaMapper — platný dataset pro map()."""

    def test_map_returns_dict(self):
        """map() vrátí slovník pro platný řádek."""
        mapper = LokalitaMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_includes_all_expected_keys(self):
        """map() vrátí všechny očekávané klíče."""
        mapper = LokalitaMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = {
            "ident_cely",
            "igsn",
            "stav",
            "pristupnost",
            "hlavni_katastr",
            "nazev",
            "uzivatelske_oznaceni",
            "typ_lokality",
            "druh",
            "zachovalost",
            "jistota",
            "popis",
            "poznamka",
        }
        self.assertEqual(set(result.keys()), expected_keys)


class LokalitaMapperGetRecordHistoryTest(TestCase):
    """Testy pro LokalitaMapper.get_record_history — bez DB."""

    def test_lokalita_returns_archeologicky_zaznam(self):
        """get_record_history() vrátí archeologicky_zaznam navázaný na Lokalita."""
        az = ArcheologickyZaznam()
        lokalita = Lokalita()
        lokalita.archeologicky_zaznam = az
        result = LokalitaMapper.get_record_history(lokalita)
        self.assertIs(result, az)

    def test_az_returns_itself(self):
        """get_record_history() vrátí přímo ArcheologickyZaznam, pokud je předán jako záznam."""
        az = ArcheologickyZaznam()
        result = LokalitaMapper.get_record_history(az)
        self.assertIs(result, az)
