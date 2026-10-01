from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    HeslarDataceMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
    ImportDataMissingHeslarValueError,
)
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from heslar.hesla import HESLAR_OBDOBI
from heslar.models import Heslar, HeslarDatace, HeslarNazev

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "obdobi": "HES-OBD-001",
    "rok_od_min": "-200",
    "rok_od_max": "-100",
    "rok_do_min": "100",
    "rok_do_max": "200",
    "poznamka": "testovací datace",
}


def _create_heslar_fixture():
    """Vytvoří testovací data HeslarNazev a Heslar pro FK obdobi v HeslarDataceMapper.

    :return: Uloženou instanci Heslar s ident_cely='HES-OBD-001' v heslári HESLAR_OBDOBI.
    """
    heslar_nazev = HeslarNazev.objects.get_or_create(pk=HESLAR_OBDOBI, defaults={"nazev": "Období"})[0]
    heslar = Heslar.objects.get_or_create(
        ident_cely="HES-OBD-001",
        defaults={"heslo": "Doba železná", "heslo_en": "Iron Age", "nazev_heslare": heslar_nazev},
    )[0]
    return heslar


class HeslarDataceMapperInsertValidTest(TestCase):
    """Testy pro HeslarDataceMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro platný INSERT dataset."""
        self.heslar = _create_heslar_fixture()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_obdobi_serialized_as_ident_cely(self):
        """map() vrátí serializovanou hodnotu obdobi jako řetězec ident_cely."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["obdobi"], "HES-OBD-001")

    def test_map_integer_fields_converted(self):
        """map() převede řetězcové hodnoty rok polí na celá čísla včetně záporných (BCE data)."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["rok_od_min"], -200)
        self.assertEqual(result["rok_od_max"], -100)
        self.assertEqual(result["rok_do_min"], 100)
        self.assertEqual(result["rok_do_max"], 200)

    def test_map_poznamka_serialized(self):
        """map() správně serializuje pole poznamka."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["poznamka"], "testovací datace")

    def test_map_obdobi_instance_value(self):
        """map() s instance_values=True vrátí instanci Heslar pro pole obdobi."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["obdobi"], Heslar)
        self.assertEqual(result["obdobi"].ident_cely, "HES-OBD-001")

    def test_map_poznamka_none(self):
        """map() přijme None v nepovinném poli poznamka."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = HeslarDataceMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["poznamka"])

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče definované v fields + obdobi."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = set(HeslarDataceMapper.fields) | {"obdobi"}
        self.assertEqual(set(result.keys()), expected_keys)


class HeslarDataceMapperInvalidStructureTest(TestCase):
    """Testy pro HeslarDataceMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = HeslarDataceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_required_column_rok_od_min_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci rok_od_min."""
        row = VALID_ROW.copy()
        del row["rok_od_min"]
        mapper = HeslarDataceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_poznamka_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci poznamka."""
        row = VALID_ROW.copy()
        del row["poznamka"]
        mapper = HeslarDataceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = HeslarDataceMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class HeslarDataceMapperCreateRecordsTest(TestCase):
    """Testy pro HeslarDataceMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy create_records INSERT."""
        self.heslar = _create_heslar_fixture()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí HeslarDatace."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], HeslarDatace)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (pk je None nebo odpovídá Heslar pk, ale záznam neexistuje v DB)."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        mapper.create_records(INSERT)
        self.assertFalse(HeslarDatace.objects.filter(obdobi=self.heslar).exists())

    def test_create_records_integer_fields_set_correctly(self):
        """create_records() nastaví celočíselná pole včetně záporných hodnot (BCE data)."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        datace = mapper.create_records(INSERT)[0]
        self.assertEqual(datace.rok_od_min, -200)
        self.assertEqual(datace.rok_od_max, -100)
        self.assertEqual(datace.rok_do_min, 100)
        self.assertEqual(datace.rok_do_max, 200)

    def test_create_records_poznamka_set_correctly(self):
        """create_records() nastaví pole poznamka na instanci HeslarDatace."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        datace = mapper.create_records(INSERT)[0]
        self.assertEqual(datace.poznamka, "testovací datace")

    def test_create_records_foreign_key_resolved(self):
        """create_records() nastaví obdobi jako instanci Heslar."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        datace = mapper.create_records(INSERT)[0]
        self.assertIsInstance(datace.obdobi, Heslar)
        self.assertEqual(datace.obdobi.ident_cely, "HES-OBD-001")


class HeslarDataceMapperImportValidationTest(TestCase):
    """Testy pro HeslarDataceMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy import_validation."""
        self.heslar = _create_heslar_fixture()

    def test_insert_without_existing_record_returns_filter_dict(self):
        """import_validation() INSERT vrátí slovník s primárním klíčem pro neexistující záznam."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertEqual(result, {"obdobi__ident_cely": "HES-OBD-001"})

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        datace = HeslarDatace(
            obdobi=self.heslar,
            rok_od_min=-200,
            rok_od_max=-100,
            rok_do_min=100,
            rok_do_max=200,
        )
        datace.suppress_signal = True
        datace.save()
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_update_existing_record_returns_filter_dict(self):
        """import_validation() UPDATE vrátí slovník s primárním klíčem pro existující záznam."""
        datace = HeslarDatace(
            obdobi=self.heslar,
            rok_od_min=-200,
            rok_od_max=-100,
            rok_do_min=100,
            rok_do_max=200,
        )
        datace.suppress_signal = True
        datace.save()
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"obdobi__ident_cely": "HES-OBD-001"})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)


class HeslarDataceMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro HeslarDataceMapper.check_required_fields."""

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = HeslarDataceMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_rok_od_min_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole rok_od_min None."""
        row = VALID_ROW.copy()
        row["rok_od_min"] = None
        mapper = HeslarDataceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_rok_od_max_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole rok_od_max None."""
        row = VALID_ROW.copy()
        row["rok_od_max"] = None
        mapper = HeslarDataceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_rok_do_min_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole rok_do_min None."""
        row = VALID_ROW.copy()
        row["rok_do_min"] = None
        mapper = HeslarDataceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_rok_do_max_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole rok_do_max None."""
        row = VALID_ROW.copy()
        row["rok_do_max"] = None
        mapper = HeslarDataceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je nepovinné pole poznamka None."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = HeslarDataceMapper(row)
        mapper.check_required_fields(INSERT)


class HeslarDataceMapperObdobiValueFromOtherHeslareTest(TestCase):
    """Testy pro HeslarDataceMapper — hodnota obdobi patří do jiného hesláře než HESLAR_OBDOBI.

    Pokrývá ``ImportDataMissingHeslarValueError`` v ``LookupImportField._process_value``:
    pokud lookup je omezen přes ``nazev_heslare`` a hodnota není v cílovém hesláři nalezena,
    musí být vyvolána tato specifická výjimka místo obecné ``ImportDataMissingReferencedValueError``.
    """

    def setUp(self):
        """Vytvoří fixturu pouze pro HESLAR_OBDOBI bez požadovaného ident_cely.

        Hodnota ``HES-OTHER-001`` reprezentuje záznam patřící konceptuálně do jiného hesláře —
        v rámci HESLAR_OBDOBI se nevyskytuje, takže lookup selže právě podmínkou ``nazev_heslare``.
        """
        HeslarNazev.objects.get_or_create(pk=HESLAR_OBDOBI, defaults={"nazev": "Období"})

    def test_obdobi_value_from_other_heslare_raises_missing_heslar_value_error(self):
        """map() vyvolá ImportDataMissingHeslarValueError pro obdobi mimo HESLAR_OBDOBI."""
        row = VALID_ROW.copy()
        row["obdobi"] = "HES-OTHER-001"
        mapper = HeslarDataceMapper(row)
        with self.assertRaises(ImportDataMissingHeslarValueError) as ctx:
            mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(ctx.exception.field_name, "ident_cely")
        self.assertEqual(ctx.exception.heslar_name, HESLAR_OBDOBI)
        self.assertEqual(ctx.exception.value, "HES-OTHER-001")
        self.assertEqual(
            ctx.exception.target_field_verbose_name,
            _("core.import_data_mappers.HeslarDataceMapper.obdobi.limit_choices"),
        )
        self.assertEqual(ctx.exception.import_field_verbose_name, "obdobi")

    def test_obdobi_value_from_other_heslare_message_contains_context(self):
        """Zpráva výjimky obsahuje hodnotu, název pole i název hesláře."""
        row = VALID_ROW.copy()
        row["obdobi"] = "HES-OTHER-001"
        mapper = HeslarDataceMapper(row)
        with self.assertRaises(ImportDataMissingHeslarValueError) as ctx:
            mapper.map(INSERT, serialize=True, include_primary_key=True)
        message = str(ctx.exception)
        self.assertIn("HES-OTHER-001", message)
        self.assertIn("ident_cely", message)
        self.assertNotIn("core_admin.ImportDataMissingHeslarValueError.message.part_3", message)
        self.assertNotIn(str(HESLAR_OBDOBI), message)
        self.assertIn("core_admin.ImportDataMissingHeslarValueError.message.part_4", message)
        self.assertIn(str(_("core.import_data_mappers.HeslarDataceMapper.obdobi.limit_choices")), message)
        self.assertIn("core_admin.ImportDataMissingHeslarValueError.message.part_5", message)
        self.assertIn("obdobi", message)
