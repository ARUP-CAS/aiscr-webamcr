from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DokumentOsobaMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from core.tests.test_mappers.fixtures import create_dokument_fixture
from django.test import TestCase
from dokument.models import Dokument, DokumentOsoba
from uzivatel.models import Osoba

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "dokument": "C-TX-000001",
    "osoba": "OS-000001",
}


class DokumentOsobaMapperInsertValidTest(TestCase):
    """Testy pro DokumentOsobaMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data Dokument a Osoba pro platný INSERT dataset."""
        self.dokument = create_dokument_fixture()
        self.osoba = Osoba(ident_cely="OS-000001", vypis_cely="Test Osoba", vypis="Test", jmeno="Test", prijmeni="Test")
        self.osoba.suppress_signal = True
        self.osoba.save()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_dokument_raw_value(self):
        """map() vrátí serializovanou hodnotu dokument jako řetězec."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["dokument"], "C-TX-000001")

    def test_map_osoba_raw_value(self):
        """map() vrátí serializovanou hodnotu osoba jako řetězec."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["osoba"], "OS-000001")

    def test_map_dokument_instance_value(self):
        """map() s instance_values=True vrátí instanci Dokument (serialize=False)."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["dokument"], Dokument)
        self.assertEqual(result["dokument"].ident_cely, "C-TX-000001")

    def test_map_osoba_instance_value(self):
        """map() s instance_values=True vrátí instanci Osoba (serialize=False)."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["osoba"], Osoba)
        self.assertEqual(result["osoba"].ident_cely, "OS-000001")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče dokument a osoba."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(set(result.keys()), {"dokument", "osoba"})


class DokumentOsobaMapperInvalidStructureTest(TestCase):
    """Testy pro DokumentOsobaMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = DokumentOsobaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_dokument_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci dokument."""
        row = VALID_ROW.copy()
        del row["dokument"]
        mapper = DokumentOsobaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_osoba_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci osoba."""
        row = VALID_ROW.copy()
        del row["osoba"]
        mapper = DokumentOsobaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = DokumentOsobaMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class DokumentOsobaMapperCreateRecordsInsertTest(TestCase):
    """Testy pro DokumentOsobaMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data Dokument a Osoba pro testy create_records."""
        self.dokument = create_dokument_fixture()
        self.osoba = Osoba(ident_cely="OS-000001", vypis_cely="Test Osoba", vypis="Test", jmeno="Test", prijmeni="Test")
        self.osoba.suppress_signal = True
        self.osoba.save()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí DokumentOsoba."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], DokumentOsoba)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_dokument_resolved(self):
        """create_records() nastaví dokument jako instanci Dokument."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.dokument, Dokument)
        self.assertEqual(record.dokument.ident_cely, "C-TX-000001")

    def test_create_records_osoba_resolved(self):
        """create_records() nastaví osoba jako instanci Osoba."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.osoba, Osoba)
        self.assertEqual(record.osoba.ident_cely, "OS-000001")


class DokumentOsobaMapperImportValidationTest(TestCase):
    """Testy pro DokumentOsobaMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data Dokument a Osoba pro testy import_validation."""
        self.dokument = create_dokument_fixture()
        self.osoba = Osoba(ident_cely="OS-000001", vypis_cely="Test Osoba", vypis="Test", jmeno="Test", prijmeni="Test")
        self.osoba.suppress_signal = True
        self.osoba.save()

    def test_insert_new_record_returns_primary_key_dict(self):
        """import_validation() INSERT vrátí slovník s primárními klíči pro neexistující záznam."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertEqual(result, {"dokument__ident_cely": "C-TX-000001", "osoba__ident_cely": "OS-000001"})

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        DokumentOsoba.objects.create(dokument=self.dokument, osoba=self.osoba)
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s primárními klíči pro existující záznam."""
        DokumentOsoba.objects.create(dokument=self.dokument, osoba=self.osoba)
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"dokument__ident_cely": "C-TX-000001", "osoba__ident_cely": "OS-000001"})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        mapper = DokumentOsobaMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class DokumentOsobaMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro DokumentOsobaMapper.check_required_fields."""

    def test_dokument_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je dokument None (not null FK)."""
        row = VALID_ROW.copy()
        row["dokument"] = None
        mapper = DokumentOsobaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_osoba_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je osoba None (not null FK)."""
        row = VALID_ROW.copy()
        row["osoba"] = None
        mapper = DokumentOsobaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
