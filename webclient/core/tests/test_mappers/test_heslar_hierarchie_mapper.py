from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    HeslarHierarchieMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from django.test import TestCase
from heslar.models import Heslar, HeslarHierarchie, HeslarNazev

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "typ": "podřízenost",
    "heslo_nadrazene": "HES-HIER-001",
    "heslo_podrazene": "HES-HIER-002",
}


class HeslarHierarchieMapperInsertValidTest(TestCase):
    """Testy pro HeslarHierarchieMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro platný INSERT dataset."""
        self.heslar_nazev = HeslarNazev.objects.create(nazev="Druh hierarchie")
        self.heslar_nadrazene = Heslar.objects.create(
            ident_cely="HES-HIER-001",
            heslo="Nadřazené heslo",
            heslo_en="Parent term",
            nazev_heslare=self.heslar_nazev,
        )
        self.heslar_podrazene = Heslar.objects.create(
            ident_cely="HES-HIER-002",
            heslo="Podřazené heslo",
            heslo_en="Child term",
            nazev_heslare=self.heslar_nazev,
        )

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_typ_as_text(self):
        """map() správně serializuje pole typ jako textový řetězec."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["typ"], "podřízenost")

    def test_map_heslo_nadrazene_raw_value(self):
        """map() vrátí serializovanou hodnotu heslo_nadrazene jako ident_cely řetězec."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["heslo_nadrazene"], "HES-HIER-001")

    def test_map_heslo_podrazene_raw_value(self):
        """map() vrátí serializovanou hodnotu heslo_podrazene jako ident_cely řetězec."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["heslo_podrazene"], "HES-HIER-002")

    def test_map_heslo_nadrazene_instance_value(self):
        """map() s instance_values=True vrátí instanci Heslar pro heslo_nadrazene."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["heslo_nadrazene"], Heslar)
        self.assertEqual(result["heslo_nadrazene"].ident_cely, "HES-HIER-001")

    def test_map_heslo_podrazene_instance_value(self):
        """map() s instance_values=True vrátí instanci Heslar pro heslo_podrazene."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["heslo_podrazene"], Heslar)
        self.assertEqual(result["heslo_podrazene"].ident_cely, "HES-HIER-002")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče definované v fields + heslo_nadrazene + heslo_podrazene."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = {"typ", "heslo_nadrazene", "heslo_podrazene"}
        self.assertEqual(set(result.keys()), expected_keys)


class HeslarHierarchieMapperInvalidStructureTest(TestCase):
    """Testy pro HeslarHierarchieMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_heslo_nadrazene_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci heslo_nadrazene."""
        row = VALID_ROW.copy()
        del row["heslo_nadrazene"]
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_heslo_podrazene_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci heslo_podrazene."""
        row = VALID_ROW.copy()
        del row["heslo_podrazene"]
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_typ_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci typ."""
        row = VALID_ROW.copy()
        del row["typ"]
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = HeslarHierarchieMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_primary_key_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči id."""
        row = VALID_ROW.copy()
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)

    def test_update_excess_column_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při nadbytečném sloupci."""
        row = VALID_ROW.copy()
        row["id"] = "hier-1"
        row["extra"] = "hodnota"
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class HeslarHierarchieMapperCreateRecordsInsertTest(TestCase):
    """Testy pro HeslarHierarchieMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy create_records."""
        self.heslar_nazev = HeslarNazev.objects.create(nazev="Druh hierarchie")
        self.heslar_nadrazene = Heslar.objects.create(
            ident_cely="HES-HIER-001",
            heslo="Nadřazené heslo",
            heslo_en="Parent term",
            nazev_heslare=self.heslar_nazev,
        )
        self.heslar_podrazene = Heslar.objects.create(
            ident_cely="HES-HIER-002",
            heslo="Podřazené heslo",
            heslo_en="Child term",
            nazev_heslare=self.heslar_nazev,
        )

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí HeslarHierarchie."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], HeslarHierarchie)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_heslo_nadrazene_resolved(self):
        """create_records() nastaví heslo_nadrazene jako instanci Heslar."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        hierarchie = mapper.create_records(INSERT)[0]
        self.assertIsInstance(hierarchie.heslo_nadrazene, Heslar)
        self.assertEqual(hierarchie.heslo_nadrazene.ident_cely, "HES-HIER-001")

    def test_create_records_heslo_podrazene_resolved(self):
        """create_records() nastaví heslo_podrazene jako instanci Heslar."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        hierarchie = mapper.create_records(INSERT)[0]
        self.assertIsInstance(hierarchie.heslo_podrazene, Heslar)
        self.assertEqual(hierarchie.heslo_podrazene.ident_cely, "HES-HIER-002")


class HeslarHierarchieMapperImportValidationTest(TestCase):
    """Testy pro HeslarHierarchieMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy import_validation."""
        self.heslar_nazev = HeslarNazev.objects.create(nazev="Druh hierarchie")
        self.heslar_nadrazene = Heslar.objects.create(
            ident_cely="HES-HIER-001",
            heslo="Nadřazené heslo",
            heslo_en="Parent term",
            nazev_heslare=self.heslar_nazev,
        )
        self.heslar_podrazene = Heslar.objects.create(
            ident_cely="HES-HIER-002",
            heslo="Podřazené heslo",
            heslo_en="Child term",
            nazev_heslare=self.heslar_nazev,
        )
        self.hierarchie = HeslarHierarchie.objects.create(
            heslo_nadrazene=self.heslar_nadrazene,
            heslo_podrazene=self.heslar_podrazene,
            typ="podřízenost",
        )

    def test_insert_without_id_returns_none(self):
        """import_validation() INSERT bez id vrátí None (_get_filter_kwargs_primary_key vrátí None)."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertIsNone(result)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s primárním klíčem pro existující záznam."""
        row = VALID_ROW.copy()
        row["id"] = f"hier-{self.hierarchie.pk}"
        mapper = HeslarHierarchieMapper(row)
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"id": self.hierarchie.pk})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["id"] = "hier-999999"
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s primárním klíčem pro existující záznam."""
        row = VALID_ROW.copy()
        row["id"] = f"hier-{self.hierarchie.pk}"
        mapper = HeslarHierarchieMapper(row)
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"id": self.hierarchie.pk})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["id"] = "hier-999999"
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class HeslarHierarchieMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro HeslarHierarchieMapper.check_required_fields."""

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = HeslarHierarchieMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_heslo_nadrazene_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je heslo_nadrazene None (not null FK)."""
        row = VALID_ROW.copy()
        row["heslo_nadrazene"] = None
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_heslo_podrazene_empty_string_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je heslo_podrazene prázdný řetězec."""
        row = VALID_ROW.copy()
        row["heslo_podrazene"] = ""
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_typ_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je typ None (not null v modelu)."""
        row = VALID_ROW.copy()
        row["typ"] = None
        mapper = HeslarHierarchieMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
