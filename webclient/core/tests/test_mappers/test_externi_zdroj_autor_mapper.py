from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ExterniZdrojAutorMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from core.tests.test_mappers.fixtures import create_externi_zdroj_fixture
from django.test import TestCase
from ez.models import ExterniZdroj, ExterniZdrojAutor
from uzivatel.models import Osoba

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "poradi": "1",
    "externi_zdroj": "BIB-C-EZ-000001",
    "autor": "OS-000001",
}


class ExterniZdrojAutorMapperInsertValidTest(TestCase):
    """Testy pro ExterniZdrojAutorMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací fixtures ExterniZdroj a Osoba."""
        self.externi_zdroj = create_externi_zdroj_fixture()
        self.autor = Osoba(
            ident_cely="OS-000001",
            jmeno="Jan",
            prijmeni="Novák",
            vypis="Jan Novák",
            vypis_cely="Novák, Jan",
        )
        self.autor.suppress_signal = True
        self.autor.save()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_poradi_converted_to_int(self):
        """map() převede poradi na integer."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["poradi"], 1)

    def test_map_fk_raw_values_serialized(self):
        """map() vrátí serializované hodnoty cizích klíčů jako řetězce."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["externi_zdroj"], "BIB-C-EZ-000001")
        self.assertEqual(result["autor"], "OS-000001")

    def test_map_fk_instance_values(self):
        """map() s instance_values=True vrátí instance modelů pro cizí klíče."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["externi_zdroj"], ExterniZdroj)
        self.assertIsInstance(result["autor"], Osoba)
        self.assertEqual(result["externi_zdroj"].ident_cely, "BIB-C-EZ-000001")
        self.assertEqual(result["autor"].ident_cely, "OS-000001")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče odpovídající polím poradi, externi_zdroj a autor."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(set(result.keys()), {"poradi", "externi_zdroj", "autor"})


class ExterniZdrojAutorMapperInvalidStructureTest(TestCase):
    """Testy pro ExterniZdrojAutorMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ExterniZdrojAutorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_poradi_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci poradi."""
        row = VALID_ROW.copy()
        del row["poradi"]
        mapper = ExterniZdrojAutorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_externi_zdroj_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci externi_zdroj."""
        row = VALID_ROW.copy()
        del row["externi_zdroj"]
        mapper = ExterniZdrojAutorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_autor_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci autor."""
        row = VALID_ROW.copy()
        del row["autor"]
        mapper = ExterniZdrojAutorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ExterniZdrojAutorMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_delete_missing_autor_raises_error(self):
        """map() DELETE vyvolá ImportDataIncorrectStructureError při chybějícím autor (součást tuple PK)."""
        row = {"externi_zdroj": "BIB-C-EZ-000001"}
        mapper = ExterniZdrojAutorMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(DELETE, serialize=True, include_primary_key=True)


class ExterniZdrojAutorMapperCreateRecordsInsertTest(TestCase):
    """Testy pro ExterniZdrojAutorMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací fixtures ExterniZdroj a Osoba."""
        self.externi_zdroj = create_externi_zdroj_fixture()
        self.autor = Osoba(
            ident_cely="OS-000001",
            jmeno="Jan",
            prijmeni="Novák",
            vypis="Jan Novák",
            vypis_cely="Novák, Jan",
        )
        self.autor.suppress_signal = True
        self.autor.save()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí ExterniZdrojAutor."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], ExterniZdrojAutor)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_poradi_set_correctly(self):
        """create_records() nastaví poradi na správnou celočíselnou hodnotu."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertEqual(record.poradi, 1)

    def test_create_records_fk_externi_zdroj_resolved(self):
        """create_records() nastaví externi_zdroj jako instanci ExterniZdroj."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.externi_zdroj, ExterniZdroj)
        self.assertEqual(record.externi_zdroj.ident_cely, "BIB-C-EZ-000001")

    def test_create_records_fk_autor_resolved(self):
        """create_records() nastaví autor jako instanci Osoba."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        record = mapper.create_records(INSERT)[0]
        self.assertIsInstance(record.autor, Osoba)
        self.assertEqual(record.autor.ident_cely, "OS-000001")


class ExterniZdrojAutorMapperImportValidationTest(TestCase):
    """Testy pro ExterniZdrojAutorMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací fixtures ExterniZdroj a Osoba."""
        self.externi_zdroj = create_externi_zdroj_fixture()
        self.autor = Osoba(
            ident_cely="OS-000001",
            jmeno="Jan",
            prijmeni="Novák",
            vypis="Jan Novák",
            vypis_cely="Novák, Jan",
        )
        self.autor.suppress_signal = True
        self.autor.save()

    def test_insert_new_record_returns_pk_dict(self):
        """import_validation() INSERT vrátí slovník s primárními klíči pro neexistující záznam."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertIsInstance(result, dict)
        self.assertIn("externi_zdroj__ident_cely", result)
        self.assertIn("autor__ident_cely", result)

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        ExterniZdrojAutor.objects.create(
            externi_zdroj=self.externi_zdroj,
            autor=self.autor,
            poradi=1,
        )
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_delete_existing_record_returns_pk_dict(self):
        """import_validation() DELETE vrátí slovník s primárními klíči pro existující záznam."""
        ExterniZdrojAutor.objects.create(
            externi_zdroj=self.externi_zdroj,
            autor=self.autor,
            poradi=1,
        )
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertIsInstance(result, dict)
        self.assertIn("externi_zdroj__ident_cely", result)
        self.assertIn("autor__ident_cely", result)

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class ExterniZdrojAutorMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ExterniZdrojAutorMapper.check_required_fields."""

    def setUp(self):
        """Vytvoří testovací fixtures ExterniZdroj a Osoba."""
        self.externi_zdroj = create_externi_zdroj_fixture()
        self.autor = Osoba(
            ident_cely="OS-000001",
            jmeno="Jan",
            prijmeni="Novák",
            vypis="Jan Novák",
            vypis_cely="Novák, Jan",
        )
        self.autor.suppress_signal = True
        self.autor.save()

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = ExterniZdrojAutorMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_poradi_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je poradi None (not null pole)."""
        row = VALID_ROW.copy()
        row["poradi"] = None
        mapper = ExterniZdrojAutorMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_externi_zdroj_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je externi_zdroj None (not null)."""
        row = VALID_ROW.copy()
        row["externi_zdroj"] = None
        mapper = ExterniZdrojAutorMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_autor_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je autor None (not null)."""
        row = VALID_ROW.copy()
        row["autor"] = None
        mapper = ExterniZdrojAutorMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
