from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    HeslarOdkazMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from django.test import TestCase
from heslar.models import Heslar, HeslarNazev, HeslarOdkaz

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "zdroj": "Getty AAT",
    "nazev_kodu": "300015637",
    "kod": "aat:300015637",
    "uri": "http://vocab.getty.edu/aat/300015637",
    "scheme_uri": None,
    "skos_mapping_relation": "skos:exactMatch",
    "heslo": "HES-000001",
}


def _create_heslar_fixture():
    """Vytvoří testovací data HeslarNazev a Heslar pro FK heslo v HeslarOdkazMapper."""
    heslar_nazev = HeslarNazev.objects.create(nazev="Druh nálezu")
    heslar = Heslar.objects.create(
        ident_cely="HES-000001",
        heslo="Nález",
        heslo_en="Find",
        nazev_heslare=heslar_nazev,
    )
    return heslar


class HeslarOdkazMapperInsertValidTest(TestCase):
    """Testy pro HeslarOdkazMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro platný INSERT dataset."""
        self.heslar = _create_heslar_fixture()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_text_fields_serialized(self):
        """map() správně serializuje textová pole."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["zdroj"], "Getty AAT")
        self.assertEqual(result["nazev_kodu"], "300015637")
        self.assertEqual(result["kod"], "aat:300015637")
        self.assertEqual(result["uri"], "http://vocab.getty.edu/aat/300015637")
        self.assertEqual(result["skos_mapping_relation"], "skos:exactMatch")

    def test_map_heslo_raw_value(self):
        """map() vrátí serializovanou hodnotu heslo jako řetězec ident_cely."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["heslo"], "HES-000001")

    def test_map_heslo_instance_value(self):
        """map() s instance_values=True vrátí instanci Heslar pro pole heslo."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["heslo"], Heslar)
        self.assertEqual(result["heslo"].ident_cely, "HES-000001")

    def test_map_optional_fields_none(self):
        """map() přijme None v nepovinných polích."""
        row = VALID_ROW.copy()
        row["uri"] = None
        row["scheme_uri"] = None
        mapper = HeslarOdkazMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["uri"])
        self.assertIsNone(result["scheme_uri"])

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče definované v fields + heslo (bez id, protože require_primary_key_value=False)."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = set(HeslarOdkazMapper.fields) | {"heslo"}
        self.assertEqual(set(result.keys()), expected_keys)


class HeslarOdkazMapperInvalidStructureTest(TestCase):
    """Testy pro HeslarOdkazMapper — neplatná struktura dat."""

    def test_unknown_column_insert_raises_error(self):
        """map() INSERT vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_heslo_column_insert_raises_error(self):
        """map() INSERT vyvolá ImportDataIncorrectStructureError při chybějícím sloupci heslo."""
        row = VALID_ROW.copy()
        del row["heslo"]
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_insert_raises_error(self):
        """map() INSERT vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = HeslarOdkazMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_id_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím id."""
        row = VALID_ROW.copy()
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)

    def test_update_excess_column_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při nadbytečném sloupci."""
        row = VALID_ROW.copy()
        row["id"] = "hodk-1"
        row["extra"] = "hodnota"
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)

    def test_missing_regular_column_insert_raises_error(self):
        """map() INSERT vyvolá ImportDataIncorrectStructureError při chybějícím sloupci zdroj."""
        row = VALID_ROW.copy()
        del row["zdroj"]
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class HeslarOdkazMapperCreateRecordsInsertTest(TestCase):
    """Testy pro HeslarOdkazMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy create_records."""
        self.heslar = _create_heslar_fixture()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí HeslarOdkaz."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], HeslarOdkaz)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_fields_set_correctly(self):
        """create_records() nastaví textová pole na instanci HeslarOdkaz."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        odkaz = mapper.create_records(INSERT)[0]
        self.assertEqual(odkaz.zdroj, "Getty AAT")
        self.assertEqual(odkaz.nazev_kodu, "300015637")
        self.assertEqual(odkaz.kod, "aat:300015637")
        self.assertEqual(odkaz.skos_mapping_relation, "skos:exactMatch")

    def test_create_records_foreign_key_resolved(self):
        """create_records() nastaví heslo jako instanci Heslar."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        odkaz = mapper.create_records(INSERT)[0]
        self.assertIsInstance(odkaz.heslo, Heslar)
        self.assertEqual(odkaz.heslo.ident_cely, self.heslar.ident_cely)


class HeslarOdkazMapperImportValidationTest(TestCase):
    """Testy pro HeslarOdkazMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy import_validation."""
        self.heslar = _create_heslar_fixture()
        self.odkaz = HeslarOdkaz.objects.create(
            heslo=self.heslar,
            zdroj="Getty AAT",
            nazev_kodu="300015637",
            kod="aat:300015637",
            uri="http://vocab.getty.edu/aat/300015637",
            skos_mapping_relation="skos:exactMatch",
        )

    def test_insert_import_validation_returns_none(self):
        """import_validation() INSERT vrátí None, protože id není v value_dict (require_primary_key_value=False)."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertIsNone(result)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s id pro existující záznam."""
        row = VALID_ROW.copy()
        row["id"] = f"hodk-{self.odkaz.pk}"
        mapper = HeslarOdkazMapper(row)
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"id": self.odkaz.pk})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["id"] = "hodk-999999"
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s id pro existující záznam."""
        row = VALID_ROW.copy()
        row["id"] = f"hodk-{self.odkaz.pk}"
        mapper = HeslarOdkazMapper(row)
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"id": self.odkaz.pk})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["id"] = "hodk-999999"
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class HeslarOdkazMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro HeslarOdkazMapper.check_required_fields."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy check_required_fields."""
        _create_heslar_fixture()

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = HeslarOdkazMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_heslo_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je heslo None (povinné FK pole)."""
        row = VALID_ROW.copy()
        row["heslo"] = None
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_zdroj_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole zdroj None."""
        row = VALID_ROW.copy()
        row["zdroj"] = None
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_kod_empty_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole kod prázdný řetězec."""
        row = VALID_ROW.copy()
        row["kod"] = ""
        mapper = HeslarOdkazMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_optional_field_uri_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je nepovinné pole uri None."""
        row = VALID_ROW.copy()
        row["uri"] = None
        mapper = HeslarOdkazMapper(row)
        mapper.check_required_fields(INSERT)

    def test_optional_field_scheme_uri_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je nepovinné pole scheme_uri None."""
        row = VALID_ROW.copy()
        row["scheme_uri"] = None
        mapper = HeslarOdkazMapper(row)
        mapper.check_required_fields(INSERT)
