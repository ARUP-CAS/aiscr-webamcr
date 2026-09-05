from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ExterniZdrojMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from django.test import TestCase
from ez.models import ExterniZdroj
from heslar.hesla import HESLAR_DOKUMENT_TYP, HESLAR_EXTERNI_ZDROJ_TYP
from heslar.models import Heslar, HeslarNazev

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "ident_cely": "EZ-000001",
    "doi": "10.1234/test",
    "stav": 1,
    "rok_vydani_vzniku": "2020",
    "nazev": "Testovací název",
    "sbornik_nazev": None,
    "edice_rada": None,
    "casopis_denik_nazev": None,
    "casopis_rocnik": None,
    "isbn": None,
    "issn": None,
    "misto": None,
    "vydavatel": None,
    "datum_rd": None,
    "paginace_titulu": None,
    "link": None,
    "organizace": None,
    "poznamka": None,
    "typ": "HES-EZ-TYP-001",
    "typ_dokumentu": None,
}


def _create_heslar_fixtures():
    """Vytvoří testovací data HeslarNazev a Heslar pro cizí klíče ExterniZdroj."""
    heslar_nazev_typ = HeslarNazev.objects.create(pk=HESLAR_EXTERNI_ZDROJ_TYP, nazev="Typ externího zdroje")
    heslar_typ = Heslar.objects.create(
        ident_cely="HES-EZ-TYP-001",
        heslo="Článek",
        heslo_en="Article",
        nazev_heslare=heslar_nazev_typ,
    )
    heslar_nazev_dok = HeslarNazev.objects.create(pk=HESLAR_DOKUMENT_TYP, nazev="Typ dokumentu")
    heslar_dok = Heslar.objects.create(
        ident_cely="HES-DOK-TYP-001",
        heslo="Zpráva",
        heslo_en="Report",
        nazev_heslare=heslar_nazev_dok,
    )
    return heslar_typ, heslar_dok


class ExterniZdrojMapperInsertValidTest(TestCase):
    """Testy pro ExterniZdrojMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací fixture ExterniZdroj pro platný INSERT dataset."""
        _create_heslar_fixtures()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_text_fields_serialized(self):
        """map() správně serializuje textová pole včetně primárního klíče."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["ident_cely"], "EZ-000001")
        self.assertEqual(result["doi"], "10.1234/test")
        self.assertEqual(result["rok_vydani_vzniku"], "2020")
        self.assertEqual(result["nazev"], "Testovací název")

    def test_map_optional_fields_none(self):
        """map() přijme None v nepovinných polích."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["sbornik_nazev"])
        self.assertIsNone(result["edice_rada"])
        self.assertIsNone(result["casopis_denik_nazev"])
        self.assertIsNone(result["isbn"])
        self.assertIsNone(result["issn"])
        self.assertIsNone(result["misto"])
        self.assertIsNone(result["vydavatel"])
        self.assertIsNone(result["datum_rd"])
        self.assertIsNone(result["paginace_titulu"])
        self.assertIsNone(result["link"])
        self.assertIsNone(result["organizace"])
        self.assertIsNone(result["poznamka"])
        self.assertIsNone(result["typ_dokumentu"])

    def test_map_typ_raw_value(self):
        """map() vrátí serializovanou hodnotu typ jako řetězec ident_cely."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["typ"], "HES-EZ-TYP-001")

    def test_map_typ_instance_value(self):
        """map() s instance_values=True vrátí instanci Heslar pro pole typ."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["typ"], Heslar)
        self.assertEqual(result["typ"].ident_cely, "HES-EZ-TYP-001")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče definované v fields + typ + typ_dokumentu."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = set(ExterniZdrojMapper.fields) | {"typ", "typ_dokumentu"}
        self.assertEqual(set(result.keys()), expected_keys)


class ExterniZdrojMapperInvalidStructureTest(TestCase):
    """Testy pro ExterniZdrojMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_required_column_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím ident_cely (require_primary_key_value=True)."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_nazev_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci nazev."""
        row = VALID_ROW.copy()
        del row["nazev"]
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_typ_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci typ."""
        row = VALID_ROW.copy()
        del row["typ"]
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ExterniZdrojMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_primary_key_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)

    def test_update_excess_columns_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při nadbytečném sloupci."""
        row = VALID_ROW.copy()
        row["extra"] = "hodnota"
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class ExterniZdrojMapperCreateRecordsInsertTest(TestCase):
    """Testy pro ExterniZdrojMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací fixture ExterniZdroj pro testy create_records INSERT."""
        _create_heslar_fixtures()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí ExterniZdroj."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], ExterniZdroj)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_fields_set_correctly(self):
        """create_records() nastaví textová pole na instanci ExterniZdroj."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        ez = mapper.create_records(INSERT)[0]
        self.assertEqual(ez.ident_cely, "EZ-000001")
        self.assertEqual(ez.doi, "10.1234/test")
        self.assertEqual(ez.rok_vydani_vzniku, "2020")
        self.assertEqual(ez.nazev, "Testovací název")

    def test_create_records_foreign_key_resolved(self):
        """create_records() nastaví typ jako instanci Heslar."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        ez = mapper.create_records(INSERT)[0]
        self.assertIsInstance(ez.typ, Heslar)
        self.assertEqual(ez.typ.ident_cely, "HES-EZ-TYP-001")

    def test_create_records_optional_fk_none(self):
        """create_records() nastaví nepovinný FK typ_dokumentu na None."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        ez = mapper.create_records(INSERT)[0]
        self.assertIsNone(ez.typ_dokumentu)


class ExterniZdrojMapperCreateRecordsUpdateTest(TestCase):
    """Testy pro ExterniZdrojMapper.create_records — akce UPDATE."""

    def setUp(self):
        """Vytvoří testovací fixture ExterniZdroj pro testy create_records UPDATE."""
        heslar_typ, _ = _create_heslar_fixtures()
        self.heslar_typ = heslar_typ
        self.ez = ExterniZdroj(
            ident_cely="EZ-000001",
            nazev="Původní název",
            stav=1,
            typ=heslar_typ,
        )
        self.ez.suppress_signal = True
        self.ez.save()

    def test_create_records_update_returns_existing_instance(self):
        """create_records() UPDATE vrátí seznam s existující instancí ExterniZdroj."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        records = mapper.create_records(UPDATE)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].pk, self.ez.pk)

    def test_create_records_update_sets_new_field_values(self):
        """create_records() UPDATE přepíše textová pole na instanci ExterniZdroj."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        ez = mapper.create_records(UPDATE)[0]
        self.assertEqual(ez.nazev, "Testovací název")
        self.assertEqual(ez.doi, "10.1234/test")
        self.assertEqual(ez.rok_vydani_vzniku, "2020")

    def test_create_records_update_resolves_foreign_key(self):
        """create_records() UPDATE zachová hodnotu cizího klíče typ."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        ez = mapper.create_records(UPDATE)[0]
        self.assertEqual(ez.typ.ident_cely, self.heslar_typ.ident_cely)


class ExterniZdrojMapperImportValidationTest(TestCase):
    """Testy pro ExterniZdrojMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací fixture ExterniZdroj pro testy import_validation."""
        heslar_typ, _ = _create_heslar_fixtures()
        self.ez = ExterniZdroj(
            ident_cely="EZ-000001",
            nazev="Testovací název",
            stav=1,
            typ=heslar_typ,
        )
        self.ez.suppress_signal = True
        self.ez.save()

    def test_insert_new_record_returns_primary_key_dict(self):
        """import_validation() INSERT vrátí slovník s primárním klíčem pro neexistující záznam."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "EZ-999999"
        mapper = ExterniZdrojMapper(row)
        result = mapper.import_validation(INSERT)
        self.assertEqual(result, {"ident_cely": "EZ-999999"})

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"ident_cely": "EZ-000001"})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "EZ-999999"
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"ident_cely": "EZ-000001"})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "EZ-999999"
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class ExterniZdrojMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ExterniZdrojMapper.check_required_fields."""

    def setUp(self):
        """Vytvoří testovací fixture ExterniZdroj pro testy check_required_fields."""
        _create_heslar_fixtures()

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = ExterniZdrojMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_required_field_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_ident_cely_empty_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely prázdný řetězec."""
        row = VALID_ROW.copy()
        row["ident_cely"] = ""
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_ident_cely_nan_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely 'nan'."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "nan"
        mapper = ExterniZdrojMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_optional_field_nazev_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je nepovinné pole nazev None."""
        row = VALID_ROW.copy()
        row["nazev"] = None
        mapper = ExterniZdrojMapper(row)
        mapper.check_required_fields(INSERT)

    def test_optional_field_poznamka_empty_passes(self):
        """check_required_fields() projde bez výjimky, pokud je nepovinné pole poznamka prázdný řetězec."""
        row = VALID_ROW.copy()
        row["poznamka"] = ""
        mapper = ExterniZdrojMapper(row)
        mapper.check_required_fields(INSERT)
