from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
    TvarMapper,
)
from core.tests.test_mappers.fixtures import create_dokument_fixture
from django.test import TestCase
from dokument.models import Dokument, Tvar
from heslar.hesla import HESLAR_LETFOTO_TVAR
from heslar.models import Heslar, HeslarNazev

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "poznamka": "test",
    "dokument": "C-TX-000001",
    "tvar": "HES-TVAR-001",
}


class TvarMapperInsertValidTest(TestCase):
    """Testy pro TvarMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data Dokument, HeslarNazev a Heslar pro platný INSERT dataset."""
        self.dokument = create_dokument_fixture()
        self.heslar_nazev = HeslarNazev.objects.create(pk=HESLAR_LETFOTO_TVAR, nazev="Letfoto tvar")
        self.heslar_tvar = Heslar.objects.create(
            ident_cely="HES-TVAR-001",
            heslo="Tvar leteckého snímku",
            heslo_en="Aerial photo shape",
            nazev_heslare=self.heslar_nazev,
        )

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = TvarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_poznamka_serialized(self):
        """map() správně serializuje textové pole poznamka."""
        mapper = TvarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["poznamka"], "test")

    def test_map_dokument_raw_value(self):
        """map() vrátí serializovanou hodnotu dokument jako řetězec ident_cely."""
        mapper = TvarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["dokument"], "C-TX-000001")

    def test_map_tvar_raw_value(self):
        """map() vrátí serializovanou hodnotu tvar jako řetězec ident_cely."""
        mapper = TvarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["tvar"], "HES-TVAR-001")

    def test_map_dokument_instance_value(self):
        """map() s instance_values=True vrátí instanci Dokument pro pole dokument."""
        mapper = TvarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["dokument"], Dokument)
        self.assertEqual(result["dokument"].ident_cely, "C-TX-000001")

    def test_map_tvar_instance_value(self):
        """map() s instance_values=True vrátí instanci Heslar pro pole tvar."""
        mapper = TvarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["tvar"], Heslar)
        self.assertEqual(result["tvar"].ident_cely, "HES-TVAR-001")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče {"poznamka", "dokument", "tvar"}."""
        mapper = TvarMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(set(result.keys()), {"poznamka", "dokument", "tvar"})


class TvarMapperInvalidStructureTest(TestCase):
    """Testy pro TvarMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = TvarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_dokument_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci dokument."""
        row = VALID_ROW.copy()
        del row["dokument"]
        mapper = TvarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_tvar_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci tvar."""
        row = VALID_ROW.copy()
        del row["tvar"]
        mapper = TvarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_poznamka_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci poznamka."""
        row = VALID_ROW.copy()
        del row["poznamka"]
        mapper = TvarMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = TvarMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class TvarMapperCreateRecordsInsertTest(TestCase):
    """Testy pro TvarMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data Dokument, HeslarNazev a Heslar pro testy create_records."""
        self.dokument = create_dokument_fixture()
        self.heslar_nazev = HeslarNazev.objects.create(pk=HESLAR_LETFOTO_TVAR, nazev="Letfoto tvar")
        self.heslar_tvar = Heslar.objects.create(
            ident_cely="HES-TVAR-001",
            heslo="Tvar leteckého snímku",
            heslo_en="Aerial photo shape",
            nazev_heslare=self.heslar_nazev,
        )

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí Tvar."""
        mapper = TvarMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], Tvar)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = TvarMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_poznamka_set_correctly(self):
        """create_records() nastaví pole poznamka na instanci Tvar."""
        mapper = TvarMapper(VALID_ROW.copy())
        tvar = mapper.create_records(INSERT)[0]
        self.assertEqual(tvar.poznamka, "test")

    def test_create_records_dokument_resolved(self):
        """create_records() nastaví dokument jako instanci Dokument."""
        mapper = TvarMapper(VALID_ROW.copy())
        tvar = mapper.create_records(INSERT)[0]
        self.assertIsInstance(tvar.dokument, Dokument)
        self.assertEqual(tvar.dokument.ident_cely, self.dokument.ident_cely)

    def test_create_records_tvar_resolved(self):
        """create_records() nastaví tvar jako instanci Heslar."""
        mapper = TvarMapper(VALID_ROW.copy())
        tvar = mapper.create_records(INSERT)[0]
        self.assertIsInstance(tvar.tvar, Heslar)
        self.assertEqual(tvar.tvar.ident_cely, self.heslar_tvar.ident_cely)


class TvarMapperImportValidationTest(TestCase):
    """Testy pro TvarMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data Dokument, HeslarNazev, Heslar a Tvar pro testy import_validation."""
        self.dokument = create_dokument_fixture()
        self.heslar_nazev = HeslarNazev.objects.create(pk=HESLAR_LETFOTO_TVAR, nazev="Letfoto tvar")
        self.heslar_tvar = Heslar.objects.create(
            ident_cely="HES-TVAR-001",
            heslo="Tvar leteckého snímku",
            heslo_en="Aerial photo shape",
            nazev_heslare=self.heslar_nazev,
        )
        self.tvar = Tvar.objects.create(
            dokument=self.dokument,
            tvar=self.heslar_tvar,
            poznamka="test",
        )

    def test_insert_without_id_returns_none(self):
        """import_validation() INSERT bez id vrátí None (_get_filter_kwargs_primary_key vrátí None)."""
        mapper = TvarMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertIsNone(result)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s primárním klíčem pro existující záznam."""
        row = VALID_ROW.copy()
        row["id"] = f"tvar-{self.tvar.pk}"
        mapper = TvarMapper(row)
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"id": self.tvar.pk})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["id"] = "tvar-999999"
        mapper = TvarMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)


class TvarMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro TvarMapper.check_required_fields."""

    def test_dokument_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je dokument None (not null FK)."""
        row = VALID_ROW.copy()
        row["dokument"] = None
        mapper = TvarMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_tvar_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je tvar None (not null FK)."""
        row = VALID_ROW.copy()
        row["tvar"] = None
        mapper = TvarMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je poznamka None (nullable pole)."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = TvarMapper(row)
        mapper.check_required_fields(INSERT)
