from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DokumentJazykMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from core.tests.test_mappers.fixtures import create_dokument_fixture
from django.test import TestCase
from dokument.models import Dokument, DokumentJazyk
from heslar.hesla import HESLAR_JAZYK
from heslar.models import Heslar, HeslarNazev

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "dokument": "C-TX-000001",
    "jazyk": "HES-JAZYK-001",
}


def _create_heslar_fixtures():
    """Vytvoří testovací data HeslarNazev a Heslar pro cizí klíč jazyk."""
    heslar_nazev = HeslarNazev.objects.create(pk=HESLAR_JAZYK, nazev="Jazyk")
    heslar = Heslar.objects.create(
        ident_cely="HES-JAZYK-001",
        heslo="CS",
        heslo_en="CS",
        nazev_heslare=heslar_nazev,
    )
    return heslar_nazev, heslar


class DokumentJazykMapperInsertValidTest(TestCase):
    """Testy pro DokumentJazykMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data Dokument a Heslar pro platný INSERT dataset."""
        self.dokument = create_dokument_fixture()
        self.heslar_nazev, self.heslar = _create_heslar_fixtures()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_dokument_raw_value(self):
        """map() vrátí serializovanou hodnotu dokument jako řetězec."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["dokument"], "C-TX-000001")

    def test_map_jazyk_raw_value(self):
        """map() vrátí serializovanou hodnotu jazyk jako řetězec."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["jazyk"], "HES-JAZYK-001")

    def test_map_dokument_instance_value(self):
        """map() s instance_values=True vrátí instanci Dokument (serialize=False)."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["dokument"], Dokument)
        self.assertEqual(result["dokument"].ident_cely, "C-TX-000001")

    def test_map_jazyk_instance_value(self):
        """map() s instance_values=True vrátí instanci Heslar (serialize=False)."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["jazyk"], Heslar)
        self.assertEqual(result["jazyk"].ident_cely, "HES-JAZYK-001")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče dokument a jazyk."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(set(result.keys()), {"dokument", "jazyk"})


class DokumentJazykMapperInvalidStructureTest(TestCase):
    """Testy pro DokumentJazykMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = DokumentJazykMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_dokument_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci dokument."""
        row = VALID_ROW.copy()
        del row["dokument"]
        mapper = DokumentJazykMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_jazyk_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci jazyk."""
        row = VALID_ROW.copy()
        del row["jazyk"]
        mapper = DokumentJazykMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = DokumentJazykMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class DokumentJazykMapperCreateRecordsInsertTest(TestCase):
    """Testy pro DokumentJazykMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data Dokument a Heslar pro testy create_records."""
        self.dokument = create_dokument_fixture()
        self.heslar_nazev, self.heslar = _create_heslar_fixtures()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí DokumentJazyk."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], DokumentJazyk)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_dokument_resolved(self):
        """create_records() nastaví dokument jako instanci Dokument."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.dokument, Dokument)
        self.assertEqual(record.dokument.ident_cely, "C-TX-000001")

    def test_create_records_jazyk_resolved(self):
        """create_records() nastaví jazyk jako instanci Heslar."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.jazyk, Heslar)
        self.assertEqual(record.jazyk.ident_cely, "HES-JAZYK-001")


class DokumentJazykMapperImportValidationTest(TestCase):
    """Testy pro DokumentJazykMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data Dokument a Heslar pro testy import_validation."""
        self.dokument = create_dokument_fixture()
        self.heslar_nazev, self.heslar = _create_heslar_fixtures()

    def test_insert_new_record_returns_primary_key_dict(self):
        """import_validation() INSERT vrátí slovník s primárními klíči pro neexistující záznam."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertEqual(result, {"dokument__ident_cely": "C-TX-000001", "jazyk__ident_cely": "HES-JAZYK-001"})

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        DokumentJazyk.objects.create(dokument=self.dokument, jazyk=self.heslar)
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s primárními klíči pro existující záznam."""
        DokumentJazyk.objects.create(dokument=self.dokument, jazyk=self.heslar)
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"dokument__ident_cely": "C-TX-000001", "jazyk__ident_cely": "HES-JAZYK-001"})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        mapper = DokumentJazykMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class DokumentJazykMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro DokumentJazykMapper.check_required_fields."""

    def test_dokument_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je dokument None (not null FK)."""
        row = VALID_ROW.copy()
        row["dokument"] = None
        mapper = DokumentJazykMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_jazyk_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je jazyk None (not null FK)."""
        row = VALID_ROW.copy()
        row["jazyk"] = None
        mapper = DokumentJazykMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
