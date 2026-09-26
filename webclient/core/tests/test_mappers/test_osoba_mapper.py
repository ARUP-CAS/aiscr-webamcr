from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
    OsobaMapper,
)
from django.test import TestCase
from uzivatel.models import Osoba

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "ident_cely": "OS-000001",
    "vypis_cely": "Novák, Jan (1985–2020)",
    "vypis": "Jan Novák",
    "jmeno": "Jan",
    "prijmeni": "Novák",
    "rodne_prijmeni": "Novák",
    "rok_narozeni": "1985",
    "rok_umrti": "2020",
    "orcid": "0000-0001-2345-6789",
    "wikidata": "Q12345",
}


class OsobaMapperInsertValidTest(TestCase):
    """Testy pro OsobaMapper — platný dataset (INSERT)."""

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = OsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_text_fields_serialized(self):
        """map() správně serializuje textová pole včetně primárního klíče."""
        mapper = OsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["ident_cely"], "OS-000001")
        self.assertEqual(result["vypis_cely"], "Novák, Jan (1985–2020)")
        self.assertEqual(result["vypis"], "Jan Novák")
        self.assertEqual(result["jmeno"], "Jan")
        self.assertEqual(result["prijmeni"], "Novák")
        self.assertEqual(result["rodne_prijmeni"], "Novák")
        self.assertEqual(result["orcid"], "0000-0001-2345-6789")
        self.assertEqual(result["wikidata"], "Q12345")

    def test_map_rok_narozeni_converted_to_int(self):
        """map() převede rok_narozeni na integer."""
        mapper = OsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["rok_narozeni"], 1985)

    def test_map_rok_umrti_converted_to_int(self):
        """map() převede rok_umrti na integer."""
        mapper = OsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["rok_umrti"], 2020)

    def test_map_optional_fields_none(self):
        """map() přijme None v nepovinných polích."""
        row = VALID_ROW.copy()
        row["vypis"] = None
        row["jmeno"] = None
        row["rodne_prijmeni"] = None
        row["rok_narozeni"] = None
        row["rok_umrti"] = None
        row["orcid"] = None
        row["wikidata"] = None
        mapper = OsobaMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["vypis"])
        self.assertIsNone(result["jmeno"])
        self.assertIsNone(result["rodne_prijmeni"])
        self.assertIsNone(result["rok_narozeni"])
        self.assertIsNone(result["rok_umrti"])
        self.assertIsNone(result["orcid"])
        self.assertIsNone(result["wikidata"])

    def test_map_rok_narozeni_nan_treated_as_none(self):
        """map() převede 'nan' v rok_narozeni na None."""
        row = VALID_ROW.copy()
        row["rok_narozeni"] = "nan"
        mapper = OsobaMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["rok_narozeni"])

    def test_map_includes_all_expected_keys(self):
        """map() vrátí přesně klíče definované v fields (ident_cely je součástí fields)."""
        mapper = OsobaMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = set(OsobaMapper.fields)
        self.assertEqual(set(result.keys()), expected_keys)


class OsobaMapperInvalidStructureTest(TestCase):
    """Testy pro OsobaMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_required_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím povinném sloupci."""
        row = VALID_ROW.copy()
        del row["vypis_cely"]
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_insert_raises_error(self):
        """map() INSERT vyvolá ImportDataIncorrectStructureError při chybějícím ident_cely (require_primary_key_value=True)."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = OsobaMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_primary_key_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)

    def test_update_excess_columns_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při nadbytečném sloupci."""
        row = VALID_ROW.copy()
        row["extra"] = "hodnota"
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class OsobaMapperCreateRecordsInsertTest(TestCase):
    """Testy pro OsobaMapper.create_records — akce INSERT."""

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí Osoba."""
        mapper = OsobaMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], Osoba)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = OsobaMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_fields_set_correctly(self):
        """create_records() nastaví všechna pole na instanci Osoba."""
        mapper = OsobaMapper(VALID_ROW.copy())
        osoba = mapper.create_records(INSERT)[0]
        self.assertEqual(osoba.ident_cely, "OS-000001")
        self.assertEqual(osoba.vypis_cely, "Novák, Jan (1985–2020)")
        self.assertEqual(osoba.vypis, "Jan Novák")
        self.assertEqual(osoba.jmeno, "Jan")
        self.assertEqual(osoba.prijmeni, "Novák")
        self.assertEqual(osoba.rodne_prijmeni, "Novák")
        self.assertEqual(osoba.rok_narozeni, 1985)
        self.assertEqual(osoba.rok_umrti, 2020)
        self.assertEqual(osoba.orcid, "0000-0001-2345-6789")
        self.assertEqual(osoba.wikidata, "Q12345")


class OsobaMapperCreateRecordsUpdateTest(TestCase):
    """Testy pro OsobaMapper.create_records — akce UPDATE."""

    def setUp(self):
        """Vytvoří existující záznam Osoba pro test aktualizace."""
        self.osoba = Osoba(
            ident_cely="OS-000001",
            vypis_cely="Starý, Záznam (2000)",
            vypis="Starý záznam",
            jmeno="Starý",
            prijmeni="Záznam",
        )
        self.osoba.suppress_signal = True
        self.osoba.save()

    def test_create_records_update_returns_existing_instance(self):
        """create_records() UPDATE vrátí seznam s existující instancí Osoba."""
        mapper = OsobaMapper(VALID_ROW.copy())
        records = mapper.create_records(UPDATE)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].pk, self.osoba.pk)

    def test_create_records_update_sets_new_field_values(self):
        """create_records() UPDATE přepíše pole na instanci Osoba."""
        mapper = OsobaMapper(VALID_ROW.copy())
        osoba = mapper.create_records(UPDATE)[0]
        self.assertEqual(osoba.vypis_cely, "Novák, Jan (1985–2020)")
        self.assertEqual(osoba.prijmeni, "Novák")
        self.assertEqual(osoba.rok_narozeni, 1985)


class OsobaMapperImportValidationTest(TestCase):
    """Testy pro OsobaMapper.import_validation."""

    def setUp(self):
        """Vytvoří existující záznam Osoba pro validační testy."""
        self.osoba = Osoba(
            ident_cely="OS-000001",
            vypis_cely="Novák, Jan (1985–2020)",
            vypis="Jan Novák",
            jmeno="Jan",
            prijmeni="Novák",
        )
        self.osoba.suppress_signal = True
        self.osoba.save()

    def test_insert_new_record_returns_primary_key_dict(self):
        """import_validation() INSERT vrátí slovník s primárním klíčem pro neexistující záznam."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "OS-999999"
        mapper = OsobaMapper(row)
        result = mapper.import_validation(INSERT)
        self.assertEqual(result, {"ident_cely": "OS-999999"})

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        mapper = OsobaMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = OsobaMapper(VALID_ROW.copy())
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"ident_cely": "OS-000001"})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "OS-999999"
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = OsobaMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"ident_cely": "OS-000001"})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "OS-999999"
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class OsobaMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro OsobaMapper.check_required_fields."""

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = OsobaMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_required_field_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole prijmeni None."""
        row = VALID_ROW.copy()
        row["prijmeni"] = None
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_empty_string_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole prijmeni prázdný řetězec."""
        row = VALID_ROW.copy()
        row["prijmeni"] = ""
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_nan_string_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole vypis_cely 'nan'."""
        row = VALID_ROW.copy()
        row["vypis_cely"] = "nan"
        mapper = OsobaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_optional_field_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud jsou nepovinná pole None."""
        row = VALID_ROW.copy()
        row["rodne_prijmeni"] = None
        row["rok_narozeni"] = None
        row["rok_umrti"] = None
        row["orcid"] = None
        row["wikidata"] = None
        mapper = OsobaMapper(row)
        mapper.check_required_fields(INSERT)

    def test_optional_field_empty_string_passes(self):
        """check_required_fields() projde bez výjimky, pokud je nepovinné pole prázdný řetězec."""
        row = VALID_ROW.copy()
        row["rodne_prijmeni"] = ""
        mapper = OsobaMapper(row)
        mapper.check_required_fields(INSERT)
