from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DokumentLetMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from django.test import TestCase
from dokument.models import Let

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "ident_cely": "L-2024-001",
    "uzivatelske_oznaceni": "Let č. 1",
    "datum": "2024-06-01",
    "hodina_zacatek": "08:00",
    "hodina_konec": "10:30",
    "fotoaparat": "Canon EOS",
    "pilot": "Jan Novák",
    "typ_letounu": "Cessna 172",
    "ucel_letu": "Průzkum",
    "letiste_start": None,
    "letiste_cil": None,
    "pozorovatel": None,
    "organizace": None,
    "pocasi": None,
    "dohlednost": None,
}


class DokumentLetMapperInsertValidTest(TestCase):
    """Testy pro DokumentLetMapper — platný dataset (INSERT)."""

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_text_fields_serialized(self):
        """map() správně serializuje textová pole."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["ident_cely"], "L-2024-001")
        self.assertEqual(result["uzivatelske_oznaceni"], "Let č. 1")
        self.assertEqual(result["datum"], "2024-06-01")
        self.assertEqual(result["hodina_zacatek"], "08:00")
        self.assertEqual(result["hodina_konec"], "10:30")
        self.assertEqual(result["fotoaparat"], "Canon EOS")
        self.assertEqual(result["pilot"], "Jan Novák")
        self.assertEqual(result["typ_letounu"], "Cessna 172")
        self.assertEqual(result["ucel_letu"], "Průzkum")

    def test_map_all_fk_fields_none(self):
        """map() vrátí None pro všechna nullable FK pole."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["letiste_start"])
        self.assertIsNone(result["letiste_cil"])
        self.assertIsNone(result["pozorovatel"])
        self.assertIsNone(result["organizace"])
        self.assertIsNone(result["pocasi"])
        self.assertIsNone(result["dohlednost"])

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče odpovídající fields a FK polím mapperu."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = set(DokumentLetMapper.fields) | {
            "letiste_start",
            "letiste_cil",
            "pozorovatel",
            "organizace",
            "pocasi",
            "dohlednost",
        }
        self.assertEqual(set(result.keys()), expected_keys)


class DokumentLetMapperInvalidStructureTest(TestCase):
    """Testy pro DokumentLetMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = DokumentLetMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_fk_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci letiste_start."""
        row = VALID_ROW.copy()
        del row["letiste_start"]
        mapper = DokumentLetMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = DokumentLetMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_primary_key_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = DokumentLetMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)

    def test_update_excess_column_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při nadbytečném sloupci."""
        row = VALID_ROW.copy()
        row["extra"] = "hodnota"
        mapper = DokumentLetMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class DokumentLetMapperCreateRecordsInsertTest(TestCase):
    """Testy pro DokumentLetMapper.create_records — akce INSERT."""

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí Let."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], Let)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_fields_set_correctly(self):
        """create_records() nastaví textová pole na instanci Let."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        let = mapper.create_records(INSERT)[0]
        self.assertEqual(let.ident_cely, "L-2024-001")
        self.assertEqual(let.uzivatelske_oznaceni, "Let č. 1")
        self.assertEqual(let.fotoaparat, "Canon EOS")
        self.assertEqual(let.pilot, "Jan Novák")
        self.assertEqual(let.typ_letounu, "Cessna 172")
        self.assertEqual(let.ucel_letu, "Průzkum")

    def test_create_records_fk_fields_none(self):
        """create_records() nastaví nullable FK pole na None."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        let = mapper.create_records(INSERT)[0]
        self.assertIsNone(let.letiste_start)
        self.assertIsNone(let.letiste_cil)
        self.assertIsNone(let.pozorovatel)
        self.assertIsNone(let.organizace)
        self.assertIsNone(let.pocasi)
        self.assertIsNone(let.dohlednost)


class DokumentLetMapperCreateRecordsUpdateTest(TestCase):
    """Testy pro DokumentLetMapper.create_records — akce UPDATE."""

    def setUp(self):
        """Vytvoří testovací fixture Let pro testy create_records UPDATE."""
        self.let = Let.objects.create(
            ident_cely="L-2024-001",
            uzivatelske_oznaceni="Původní označení",
            pilot="Původní pilot",
        )

    def test_create_records_update_returns_existing_instance(self):
        """create_records() UPDATE vrátí seznam s existující instancí Let."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        records = mapper.create_records(UPDATE)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].pk, self.let.pk)

    def test_create_records_update_sets_new_field_values(self):
        """create_records() UPDATE přepíše pole na instanci Let."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        let = mapper.create_records(UPDATE)[0]
        self.assertEqual(let.uzivatelske_oznaceni, "Let č. 1")
        self.assertEqual(let.pilot, "Jan Novák")
        self.assertEqual(let.typ_letounu, "Cessna 172")


class DokumentLetMapperImportValidationTest(TestCase):
    """Testy pro DokumentLetMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací fixture Let pro testy import_validation."""
        self.let = Let.objects.create(
            ident_cely="L-2024-001",
            uzivatelske_oznaceni="Let č. 1",
        )

    def test_insert_new_record_returns_primary_key_dict(self):
        """import_validation() INSERT vrátí slovník s primárním klíčem pro neexistující záznam."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "L-2024-999"
        mapper = DokumentLetMapper(row)
        result = mapper.import_validation(INSERT)
        self.assertEqual(result, {"ident_cely": "L-2024-999"})

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"ident_cely": "L-2024-001"})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "L-2024-999"
        mapper = DokumentLetMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"ident_cely": "L-2024-001"})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "L-2024-999"
        mapper = DokumentLetMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class DokumentLetMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro DokumentLetMapper.check_required_fields."""

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = DokumentLetMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = DokumentLetMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_ident_cely_empty_string_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely prázdný řetězec."""
        row = VALID_ROW.copy()
        row["ident_cely"] = ""
        mapper = DokumentLetMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_optional_fields_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud jsou volitelná pole None."""
        row = VALID_ROW.copy()
        row["uzivatelske_oznaceni"] = None
        row["datum"] = None
        row["hodina_zacatek"] = None
        row["hodina_konec"] = None
        row["fotoaparat"] = None
        row["pilot"] = None
        row["typ_letounu"] = None
        row["ucel_letu"] = None
        mapper = DokumentLetMapper(row)
        mapper.check_required_fields(INSERT)

    def test_optional_fk_fields_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud jsou FK pole None (null=True)."""
        row = VALID_ROW.copy()
        row["letiste_start"] = None
        row["letiste_cil"] = None
        row["pozorovatel"] = None
        row["organizace"] = None
        row["pocasi"] = None
        row["dohlednost"] = None
        mapper = DokumentLetMapper(row)
        mapper.check_required_fields(INSERT)
