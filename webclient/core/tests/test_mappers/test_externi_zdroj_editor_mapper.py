from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ExterniZdrojEditorMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from core.tests.test_mappers.fixtures import create_externi_zdroj_fixture
from django.test import TestCase
from ez.models import ExterniZdroj, ExterniZdrojEditor
from uzivatel.models import Osoba

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "poradi": "1",
    "externi_zdroj": "BIB-C-EZ-000001",
    "editor": "OS-000001",
}


class ExterniZdrojEditorMapperInsertValidTest(TestCase):
    """Testy pro ExterniZdrojEditorMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací fixtures ExterniZdroj a Osoba."""
        self.externi_zdroj = create_externi_zdroj_fixture()
        self.editor = Osoba(
            ident_cely="OS-000001",
            jmeno="Jan",
            prijmeni="Novák",
            vypis="Jan Novák",
            vypis_cely="Novák, Jan",
        )
        self.editor.suppress_signal = True
        self.editor.save()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_poradi_converted_to_int(self):
        """map() převede poradi na integer."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["poradi"], 1)

    def test_map_fk_raw_values_serialized(self):
        """map() vrátí serializované hodnoty cizích klíčů jako řetězce."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["externi_zdroj"], "BIB-C-EZ-000001")
        self.assertEqual(result["editor"], "OS-000001")

    def test_map_fk_instance_values(self):
        """map() s instance_values=True vrátí instance modelů pro cizí klíče."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["externi_zdroj"], ExterniZdroj)
        self.assertIsInstance(result["editor"], Osoba)
        self.assertEqual(result["externi_zdroj"].ident_cely, "BIB-C-EZ-000001")
        self.assertEqual(result["editor"].ident_cely, "OS-000001")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče odpovídající polím poradi, externi_zdroj a editor."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(set(result.keys()), {"poradi", "externi_zdroj", "editor"})


class ExterniZdrojEditorMapperInvalidStructureTest(TestCase):
    """Testy pro ExterniZdrojEditorMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ExterniZdrojEditorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_poradi_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci poradi."""
        row = VALID_ROW.copy()
        del row["poradi"]
        mapper = ExterniZdrojEditorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_externi_zdroj_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci externi_zdroj."""
        row = VALID_ROW.copy()
        del row["externi_zdroj"]
        mapper = ExterniZdrojEditorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_editor_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci editor."""
        row = VALID_ROW.copy()
        del row["editor"]
        mapper = ExterniZdrojEditorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ExterniZdrojEditorMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_delete_missing_editor_raises_error(self):
        """map() DELETE vyvolá ImportDataIncorrectStructureError při chybějícím editor (součást tuple PK)."""
        row = {"externi_zdroj": "BIB-C-EZ-000001"}
        mapper = ExterniZdrojEditorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(DELETE, serialize=True, include_primary_key=True)


class ExterniZdrojEditorMapperCreateRecordsInsertTest(TestCase):
    """Testy pro ExterniZdrojEditorMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací fixtures ExterniZdroj a Osoba."""
        self.externi_zdroj = create_externi_zdroj_fixture()
        self.editor = Osoba(
            ident_cely="OS-000001",
            jmeno="Jan",
            prijmeni="Novák",
            vypis="Jan Novák",
            vypis_cely="Novák, Jan",
        )
        self.editor.suppress_signal = True
        self.editor.save()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí ExterniZdrojEditor."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], ExterniZdrojEditor)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_poradi_set_correctly(self):
        """create_records() nastaví poradi na správnou celočíselnou hodnotu."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertEqual(record.poradi, 1)

    def test_create_records_fk_externi_zdroj_resolved(self):
        """create_records() nastaví externi_zdroj jako instanci ExterniZdroj."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.externi_zdroj, ExterniZdroj)
        self.assertEqual(record.externi_zdroj.ident_cely, "BIB-C-EZ-000001")

    def test_create_records_fk_editor_resolved(self):
        """create_records() nastaví editor jako instanci Osoba."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.editor, Osoba)
        self.assertEqual(record.editor.ident_cely, "OS-000001")


class ExterniZdrojEditorMapperImportValidationTest(TestCase):
    """Testy pro ExterniZdrojEditorMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací fixtures ExterniZdroj a Osoba."""
        self.externi_zdroj = create_externi_zdroj_fixture()
        self.editor = Osoba(
            ident_cely="OS-000001",
            jmeno="Jan",
            prijmeni="Novák",
            vypis="Jan Novák",
            vypis_cely="Novák, Jan",
        )
        self.editor.suppress_signal = True
        self.editor.save()

    def test_insert_new_record_returns_pk_dict(self):
        """import_validation() INSERT vrátí slovník s primárními klíči pro neexistující záznam."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertIsInstance(result, dict)
        self.assertIn("externi_zdroj__ident_cely", result)
        self.assertIn("editor__ident_cely", result)

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        ExterniZdrojEditor.objects.create(
            externi_zdroj=self.externi_zdroj,
            editor=self.editor,
            poradi=1,
        )
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_delete_existing_record_returns_pk_dict(self):
        """import_validation() DELETE vrátí slovník s primárními klíči pro existující záznam."""
        ExterniZdrojEditor.objects.create(
            externi_zdroj=self.externi_zdroj,
            editor=self.editor,
            poradi=1,
        )
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertIsInstance(result, dict)
        self.assertIn("externi_zdroj__ident_cely", result)
        self.assertIn("editor__ident_cely", result)

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class ExterniZdrojEditorMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ExterniZdrojEditorMapper.check_required_fields."""

    def setUp(self):
        """Vytvoří testovací fixtures ExterniZdroj a Osoba."""
        self.externi_zdroj = create_externi_zdroj_fixture()
        self.editor = Osoba(
            ident_cely="OS-000001",
            jmeno="Jan",
            prijmeni="Novák",
            vypis="Jan Novák",
            vypis_cely="Novák, Jan",
        )
        self.editor.suppress_signal = True
        self.editor.save()

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = ExterniZdrojEditorMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_poradi_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je poradi None (not null pole)."""
        row = VALID_ROW.copy()
        row["poradi"] = None
        mapper = ExterniZdrojEditorMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_externi_zdroj_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je externi_zdroj None (not null)."""
        row = VALID_ROW.copy()
        row["externi_zdroj"] = None
        mapper = ExterniZdrojEditorMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_editor_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je editor None (not null)."""
        row = VALID_ROW.copy()
        row["editor"] = None
        mapper = ExterniZdrojEditorMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
