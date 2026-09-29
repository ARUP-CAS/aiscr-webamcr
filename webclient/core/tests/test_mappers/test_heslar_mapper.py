from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    HeslarMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from django.test import TestCase
from heslar.models import Heslar, HeslarNazev

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "ident_cely": "HES-000001",
    "heslo": "Nález",
    "heslo_en": "Find",
    "popis": "Popis nálezu",
    "popis_en": "Find description",
    "zkratka": "NÁL",
    "razeni": "5",
    "nazev_heslare": "Druh nálezu",
}


class HeslarMapperInsertValidTest(TestCase):
    """Testy pro HeslarMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev pro platný INSERT dataset."""
        self.heslar_nazev = HeslarNazev.objects.create(nazev="Druh nálezu")

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = HeslarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_text_fields_serialized(self):
        """map() správně serializuje textová pole včetně primárního klíče."""
        mapper = HeslarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["ident_cely"], "HES-000001")
        self.assertEqual(result["heslo"], "Nález")
        self.assertEqual(result["heslo_en"], "Find")
        self.assertEqual(result["popis"], "Popis nálezu")
        self.assertEqual(result["popis_en"], "Find description")
        self.assertEqual(result["zkratka"], "NÁL")

    def test_map_razeni_converted_to_int(self):
        """map() převede razeni na integer."""
        mapper = HeslarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["razeni"], 5)

    def test_map_nazev_heslare_raw_value(self):
        """map() vrátí serializovanou hodnotu nazev_heslare jako řetězec."""
        mapper = HeslarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["nazev_heslare"], "Druh nálezu")

    def test_map_nazev_heslare_instance_value(self):
        """map() s instance_values=True vrátí instanci HeslarNazev (serialize=False, aby nebyla serializována)."""
        mapper = HeslarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["nazev_heslare"], HeslarNazev)
        self.assertEqual(result["nazev_heslare"].nazev, "Druh nálezu")

    def test_map_optional_fields_none(self):
        """map() přijme None v nepovinných polích."""
        row = VALID_ROW.copy()
        row["popis"] = None
        row["popis_en"] = None
        row["zkratka"] = None
        row["razeni"] = None
        mapper = HeslarMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["popis"])
        self.assertIsNone(result["popis_en"])
        self.assertIsNone(result["zkratka"])
        self.assertIsNone(result["razeni"])

    def test_map_razeni_nan_treated_as_none(self):
        """map() převede 'nan' v razeni na None."""
        row = VALID_ROW.copy()
        row["razeni"] = "nan"
        mapper = HeslarMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["razeni"])

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče definované v fields + nazev_heslare + ident_cely."""
        mapper = HeslarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = set(HeslarMapper.fields) | {"nazev_heslare"}
        self.assertEqual(set(result.keys()), expected_keys)


class HeslarMapperInvalidStructureTest(TestCase):
    """Testy pro HeslarMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_required_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím povinném sloupci."""
        row = VALID_ROW.copy()
        del row["heslo"]
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_nazev_heslare_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím nazev_heslare."""
        row = VALID_ROW.copy()
        del row["nazev_heslare"]
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_insert_raises_error(self):
        """map() INSERT vyvolá ImportDataIncorrectStructureError při chybějícím ident_cely (require_primary_key_value=True)."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = HeslarMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_primary_key_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)

    def test_update_excess_columns_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při nadbytečném sloupci."""
        row = VALID_ROW.copy()
        row["extra"] = "hodnota"
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class HeslarMapperCreateRecordsInsertTest(TestCase):
    """Testy pro HeslarMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev pro testy create_records INSERT."""
        self.heslar_nazev = HeslarNazev.objects.create(nazev="Druh nálezu")

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí Heslar."""
        mapper = HeslarMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], Heslar)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = HeslarMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_fields_set_correctly(self):
        """create_records() nastaví všechna textová pole na instanci Heslar."""
        mapper = HeslarMapper(VALID_ROW.copy())
        heslar = mapper.create_records(INSERT)[0]
        self.assertEqual(heslar.ident_cely, "HES-000001")
        self.assertEqual(heslar.heslo, "Nález")
        self.assertEqual(heslar.heslo_en, "Find")
        self.assertEqual(heslar.popis, "Popis nálezu")
        self.assertEqual(heslar.popis_en, "Find description")
        self.assertEqual(heslar.zkratka, "NÁL")
        self.assertEqual(heslar.razeni, 5)

    def test_create_records_foreign_key_resolved(self):
        """create_records() nastaví nazev_heslare jako instanci HeslarNazev."""
        mapper = HeslarMapper(VALID_ROW.copy())
        heslar = mapper.create_records(INSERT)[0]
        self.assertIsInstance(heslar.nazev_heslare, HeslarNazev)
        self.assertEqual(heslar.nazev_heslare.nazev, self.heslar_nazev.nazev)

    def test_create_records_optional_fields_none(self):
        """create_records() nastaví nepovinná pole na None."""
        row = VALID_ROW.copy()
        row["popis"] = None
        row["popis_en"] = None
        row["zkratka"] = None
        row["razeni"] = None
        mapper = HeslarMapper(row)
        heslar = mapper.create_records(INSERT)[0]
        self.assertIsNone(heslar.popis)
        self.assertIsNone(heslar.popis_en)
        self.assertIsNone(heslar.zkratka)
        self.assertIsNone(heslar.razeni)


class HeslarMapperCreateRecordsUpdateTest(TestCase):
    """Testy pro HeslarMapper.create_records — akce UPDATE."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy create_records UPDATE."""
        self.heslar_nazev = HeslarNazev.objects.create(nazev="Druh nálezu")
        self.heslar_nazev_novy = HeslarNazev.objects.create(nazev="Nový heslář")
        self.heslar = Heslar.objects.create(
            ident_cely="HES-000001",
            heslo="Původní",
            heslo_en="Original",
            nazev_heslare=self.heslar_nazev,
            razeni=1,
        )

    def test_create_records_update_returns_existing_instance(self):
        """create_records() UPDATE vrátí seznam s existující instancí Heslar."""
        mapper = HeslarMapper(VALID_ROW.copy())
        records = mapper.create_records(UPDATE)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].pk, self.heslar.pk)

    def test_create_records_update_sets_new_field_values(self):
        """create_records() UPDATE přepíše pole na instanci Heslar."""
        mapper = HeslarMapper(VALID_ROW.copy())
        heslar = mapper.create_records(UPDATE)[0]
        self.assertEqual(heslar.heslo, "Nález")
        self.assertEqual(heslar.heslo_en, "Find")
        self.assertEqual(heslar.razeni, 5)

    def test_create_records_update_resolves_foreign_key(self):
        """create_records() UPDATE nastaví novou hodnotu cizího klíče."""
        row = VALID_ROW.copy()
        row["nazev_heslare"] = "Nový heslář"
        mapper = HeslarMapper(row)
        heslar = mapper.create_records(UPDATE)[0]
        self.assertEqual(heslar.nazev_heslare.pk, self.heslar_nazev_novy.pk)


class HeslarMapperImportValidationTest(TestCase):
    """Testy pro HeslarMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy import_validation."""
        self.heslar_nazev = HeslarNazev.objects.create(nazev="Druh nálezu")
        self.heslar = Heslar.objects.create(
            ident_cely="HES-000001",
            heslo="Nález",
            heslo_en="Find",
            nazev_heslare=self.heslar_nazev,
        )

    def test_insert_new_record_returns_primary_key_dict(self):
        """import_validation() INSERT vrátí slovník s primárním klíčem pro neexistující záznam."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "HES-999999"
        mapper = HeslarMapper(row)
        result = mapper.import_validation(INSERT)
        self.assertEqual(result, {"ident_cely": "HES-999999"})

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        mapper = HeslarMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = HeslarMapper(VALID_ROW.copy())
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"ident_cely": "HES-000001"})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "HES-999999"
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = HeslarMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"ident_cely": "HES-000001"})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "HES-999999"
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class HeslarMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro HeslarMapper.check_required_fields."""

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = HeslarMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_required_field_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole None."""
        row = VALID_ROW.copy()
        row["heslo"] = None
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_empty_string_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole prázdný řetězec."""
        row = VALID_ROW.copy()
        row["heslo"] = ""
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_nan_string_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole 'nan'."""
        row = VALID_ROW.copy()
        row["heslo_en"] = "nan"
        mapper = HeslarMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_optional_field_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je nepovinné pole None."""
        row = VALID_ROW.copy()
        row["popis"] = None
        row["zkratka"] = None
        row["razeni"] = None
        mapper = HeslarMapper(row)
        mapper.check_required_fields(INSERT)

    def test_optional_field_empty_string_passes(self):
        """check_required_fields() projde bez výjimky, pokud je nepovinné pole prázdný řetězec."""
        row = VALID_ROW.copy()
        row["popis"] = ""
        mapper = HeslarMapper(row)
        mapper.check_required_fields(INSERT)
