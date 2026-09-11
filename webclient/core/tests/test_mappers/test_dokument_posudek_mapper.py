from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DokumentPosudekMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from core.tests.test_mappers.fixtures import create_dokument_fixture
from django.test import TestCase
from dokument.models import Dokument, DokumentPosudek
from heslar.hesla import HESLAR_POSUDEK_TYP
from heslar.models import Heslar, HeslarNazev

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "dokument": "C-TX-000001",
    "posudek": "HES-POS-001",
}


def _create_heslar_fixtures():
    """Vytvoří testovací data HeslarNazev a Heslar pro cizí klíč posudek."""
    heslar_nazev = HeslarNazev.objects.create(pk=HESLAR_POSUDEK_TYP, nazev="Posudek typ")
    heslar = Heslar.objects.create(
        ident_cely="HES-POS-001",
        heslo="Revizní posudek",
        heslo_en="Revision report",
        nazev_heslare=heslar_nazev,
    )
    return heslar_nazev, heslar


class DokumentPosudekMapperInsertValidTest(TestCase):
    """Testy pro DokumentPosudekMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data Dokument a Heslar pro platný INSERT dataset."""
        self.dokument = create_dokument_fixture()
        self.heslar_nazev, self.heslar = _create_heslar_fixtures()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_dokument_raw_value(self):
        """map() vrátí serializovanou hodnotu dokument jako řetězec."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["dokument"], "C-TX-000001")

    def test_map_posudek_raw_value(self):
        """map() vrátí serializovanou hodnotu posudek jako řetězec."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["posudek"], "HES-POS-001")

    def test_map_dokument_instance_value(self):
        """map() s instance_values=True vrátí instanci Dokument (serialize=False)."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["dokument"], Dokument)
        self.assertEqual(result["dokument"].ident_cely, "C-TX-000001")

    def test_map_posudek_instance_value(self):
        """map() s instance_values=True vrátí instanci Heslar (serialize=False)."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["posudek"], Heslar)
        self.assertEqual(result["posudek"].ident_cely, "HES-POS-001")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče dokument a posudek."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(set(result.keys()), {"dokument", "posudek"})


class DokumentPosudekMapperInvalidStructureTest(TestCase):
    """Testy pro DokumentPosudekMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = DokumentPosudekMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_dokument_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci dokument."""
        row = VALID_ROW.copy()
        del row["dokument"]
        mapper = DokumentPosudekMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_posudek_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci posudek."""
        row = VALID_ROW.copy()
        del row["posudek"]
        mapper = DokumentPosudekMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = DokumentPosudekMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class DokumentPosudekMapperCreateRecordsInsertTest(TestCase):
    """Testy pro DokumentPosudekMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data Dokument a Heslar pro testy create_records."""
        self.dokument = create_dokument_fixture()
        self.heslar_nazev, self.heslar = _create_heslar_fixtures()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí DokumentPosudek."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], DokumentPosudek)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_dokument_resolved(self):
        """create_records() nastaví dokument jako instanci Dokument."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.dokument, Dokument)
        self.assertEqual(record.dokument.ident_cely, "C-TX-000001")

    def test_create_records_posudek_resolved(self):
        """create_records() nastaví posudek jako instanci Heslar."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.posudek, Heslar)
        self.assertEqual(record.posudek.ident_cely, "HES-POS-001")


class DokumentPosudekMapperImportValidationTest(TestCase):
    """Testy pro DokumentPosudekMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data Dokument a Heslar pro testy import_validation."""
        self.dokument = create_dokument_fixture()
        self.heslar_nazev, self.heslar = _create_heslar_fixtures()

    def test_insert_new_record_returns_primary_key_dict(self):
        """import_validation() INSERT vrátí slovník s primárními klíči pro neexistující záznam."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertEqual(result, {"dokument__ident_cely": "C-TX-000001", "posudek__ident_cely": "HES-POS-001"})

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        DokumentPosudek.objects.create(dokument=self.dokument, posudek=self.heslar)
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s primárními klíči pro existující záznam."""
        DokumentPosudek.objects.create(dokument=self.dokument, posudek=self.heslar)
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"dokument__ident_cely": "C-TX-000001", "posudek__ident_cely": "HES-POS-001"})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        mapper = DokumentPosudekMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class DokumentPosudekMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro DokumentPosudekMapper.check_required_fields."""

    def test_dokument_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je dokument None (not null FK)."""
        row = VALID_ROW.copy()
        row["dokument"] = None
        mapper = DokumentPosudekMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_posudek_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je posudek None (not null FK)."""
        row = VALID_ROW.copy()
        row["posudek"] = None
        mapper = DokumentPosudekMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
