from arch_z.models import ExterniOdkaz
from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ExterniOdkazMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from core.tests.test_mappers.fixtures import create_externi_zdroj_fixture
from django.test import TestCase
from ez.models import ExterniZdroj

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "paginace": "1-5",
    "archeologicky_zaznam": None,
    "externi_zdroj": "BIB-C-EZ-000001",
}


class ExterniOdkazMapperInsertValidTest(TestCase):
    """Testy pro ExterniOdkazMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací fixture ExterniZdroj."""
        self.externi_zdroj = create_externi_zdroj_fixture()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_paginace_serialized(self):
        """map() správně serializuje pole paginace."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["paginace"], "1-5")

    def test_map_archeologicky_zaznam_none(self):
        """map() vrátí None pro archeologicky_zaznam, pokud je vstupní hodnota None."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["archeologicky_zaznam"])

    def test_map_externi_zdroj_raw_value_serialized(self):
        """map() vrátí serializovanou hodnotu externi_zdroj jako řetězec."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["externi_zdroj"], "BIB-C-EZ-000001")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče odpovídající polím paginace, archeologicky_zaznam a externi_zdroj."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(set(result.keys()), {"paginace", "archeologicky_zaznam", "externi_zdroj"})


class ExterniOdkazMapperInvalidStructureTest(TestCase):
    """Testy pro ExterniOdkazMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ExterniOdkazMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_paginace_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci paginace."""
        row = VALID_ROW.copy()
        del row["paginace"]
        mapper = ExterniOdkazMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_externi_zdroj_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci externi_zdroj."""
        row = VALID_ROW.copy()
        del row["externi_zdroj"]
        mapper = ExterniOdkazMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ExterniOdkazMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_id_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError, pokud chybí primární klíč id."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class ExterniOdkazMapperCreateRecordsInsertTest(TestCase):
    """Testy pro ExterniOdkazMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací fixture ExterniZdroj."""
        self.externi_zdroj = create_externi_zdroj_fixture()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí ExterniOdkaz."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], ExterniOdkaz)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_paginace_set_correctly(self):
        """create_records() nastaví paginace na správnou hodnotu."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertEqual(record.paginace, "1-5")

    def test_create_records_fk_externi_zdroj_resolved(self):
        """create_records() nastaví externi_zdroj jako instanci ExterniZdroj."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.externi_zdroj, ExterniZdroj)
        self.assertEqual(record.externi_zdroj.ident_cely, "BIB-C-EZ-000001")


class ExterniOdkazMapperImportValidationTest(TestCase):
    """Testy pro ExterniOdkazMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací fixture ExterniZdroj a uloží instanci ExterniOdkaz pro UPDATE testy."""
        self.externi_zdroj = create_externi_zdroj_fixture()

    def test_insert_without_id_returns_none(self):
        """import_validation() INSERT vrátí None, pokud id není v hodnotovém slovníku (require_primary_key_value=False)."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertIsNone(result)

    def test_update_missing_id_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam s daným id neexistuje."""
        row = VALID_ROW.copy()
        row["id"] = "exto-999999"
        mapper = ExterniOdkazMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)


class ExterniOdkazMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ExterniOdkazMapper.check_required_fields."""

    def setUp(self):
        """Vytvoří testovací fixture ExterniZdroj."""
        self.externi_zdroj = create_externi_zdroj_fixture()

    def test_valid_row_raises_error_for_none_archeologicky_zaznam(self):
        """check_required_fields() vyvolá ImportDataError, pokud je archeologicky_zaznam None (not null FK)."""
        mapper = ExterniOdkazMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_paginace_none_raises_error_for_none_archeologicky_zaznam(self):
        """check_required_fields() vyvolá ImportDataError kvůli None archeologicky_zaznam (not null FK)."""
        row = VALID_ROW.copy()
        row["paginace"] = None
        mapper = ExterniOdkazMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_externi_zdroj_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je externi_zdroj None (not null)."""
        row = VALID_ROW.copy()
        row["externi_zdroj"] = None
        mapper = ExterniOdkazMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
