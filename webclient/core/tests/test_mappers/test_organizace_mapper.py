from unittest.mock import patch

from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataBatchOrderingError,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
    ImportDataLimitChoicesError,
    OrganizaceMapper,
)
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from heslar.hesla import HESLAR_LICENCE, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar, HeslarNazev
from uzivatel.models import Organizace

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

HESLAR_ORGTYP_IDENT = "HES-ORGTYP-001"
HESLAR_PRISTUPNOST_IDENT = "HES-PRIST-001"
HESLAR_LICENCE_IDENT = "HES-LIC-001"

VALID_ROW = {
    "ident_cely": "ORG-000001",
    "nazev": "Archeologický ústav",
    "nazev_en": "Institute of Archaeology",
    "nazev_zkraceny": "ARÚP",
    "nazev_zkraceny_en": "ARUP",
    "oao": "True",
    "mesicu_do_zverejneni": "3",
    "email": "info@arup.cas.cz",
    "telefon": "+420 123 456 789",
    "adresa": "Letenská 4, Praha 1",
    "ico": "12345678",
    "zanikla": "False",
    "cteni_dokumentu": "False",
    "ror": "https://ror.org/example",
    "web": "https://www.arup.cas.cz",
    "soucast": None,
    "typ_organizace": HESLAR_ORGTYP_IDENT,
    "zverejneni_pristupnost": HESLAR_PRISTUPNOST_IDENT,
    "licence": HESLAR_LICENCE_IDENT,
}


HESLAR_NAZEV_IDS = {
    "Typ organizace": HESLAR_ORGANIZACE_TYP,
    "Typ organizaceV": HESLAR_ORGANIZACE_TYP,
    "Přístupnost": HESLAR_PRISTUPNOST,
    "PřístupnostV": HESLAR_PRISTUPNOST,
    "Licence": HESLAR_LICENCE,
    "LicenceV": HESLAR_LICENCE,
}


def _create_heslar_nazev_a_heslar(nazev_heslare_nazev, heslo, ident_cely=None):
    """
    Pomocná funkce pro vytvoření HeslarNazev a Heslar pro testovací fixtures.

    :param nazev_heslare_nazev: Název hesláře.
    :param heslo: Heslo záznamu.
    :param ident_cely: Volitelný ident_cely pro Heslar.
    :return: Dvojice (HeslarNazev, Heslar).
    """
    heslar_nazev_kwargs = {"nazev": nazev_heslare_nazev}
    heslar_nazev_id = HESLAR_NAZEV_IDS.get(nazev_heslare_nazev)
    if heslar_nazev_id is not None:
        heslar_nazev_kwargs["pk"] = heslar_nazev_id
    heslar_nazev = HeslarNazev.objects.create(**heslar_nazev_kwargs)
    if ident_cely is None:
        ident_cely = f"HES-{nazev_heslare_nazev[:10].replace(' ', '')}-001"
    heslar = Heslar.objects.create(
        ident_cely=ident_cely,
        nazev_heslare=heslar_nazev,
        heslo=heslo,
        heslo_en=heslo,
    )
    return heslar_nazev, heslar


def _create_required_heslar_fixtures():
    """Vytvoří povinné Heslar fixtures pro platný řádek Organizace."""
    _create_heslar_nazev_a_heslar("Typ organizace", "Veřejná", HESLAR_ORGTYP_IDENT)
    _create_heslar_nazev_a_heslar("Přístupnost", "Veřejná přístupnost", HESLAR_PRISTUPNOST_IDENT)
    _create_heslar_nazev_a_heslar("Licence", "CC BY", HESLAR_LICENCE_IDENT)


class OrganizaceMapperInsertValidTest(TestCase):
    """Testy pro OrganizaceMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří Heslar fixture pro typ_organizace."""
        _create_required_heslar_fixtures()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_text_fields_serialized(self):
        """map() správně serializuje textová pole včetně primárního klíče."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["ident_cely"], "ORG-000001")
        self.assertEqual(result["nazev"], "Archeologický ústav")
        self.assertEqual(result["nazev_en"], "Institute of Archaeology")
        self.assertEqual(result["nazev_zkraceny"], "ARÚP")
        self.assertEqual(result["nazev_zkraceny_en"], "ARUP")
        self.assertEqual(result["email"], "info@arup.cas.cz")
        self.assertEqual(result["telefon"], "+420 123 456 789")
        self.assertEqual(result["adresa"], "Letenská 4, Praha 1")
        self.assertEqual(result["ico"], "12345678")
        self.assertEqual(result["ror"], "https://ror.org/example")
        self.assertEqual(result["web"], "https://www.arup.cas.cz")

    def test_map_boolean_fields_pass_through(self):
        """map() správně zpracuje booleovská pole."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertTrue(result["oao"])
        self.assertFalse(result["zanikla"])
        self.assertFalse(result["cteni_dokumentu"])

    def test_map_mesicu_do_zverejneni_string_zero(self):
        """map() zachová řetězcovou nulu v mesicu_do_zverejneni jako platnou hodnotu."""
        row = VALID_ROW.copy()
        row["mesicu_do_zverejneni"] = "0"
        mapper = OrganizaceMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["mesicu_do_zverejneni"], 0)

    def test_map_mesicu_do_zverejneni_numeric_zero(self):
        """map() zachová numerickou nulu z pandas/JSON v mesicu_do_zverejneni jako platnou hodnotu."""
        row = VALID_ROW.copy()
        row["mesicu_do_zverejneni"] = 0
        mapper = OrganizaceMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["mesicu_do_zverejneni"], 0)

    def test_map_typ_organizace_raw_value(self):
        """map() vrátí serializovanou hodnotu typ_organizace jako ident_cely řetězec."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["typ_organizace"], HESLAR_ORGTYP_IDENT)

    def test_map_typ_organizace_instance_value(self):
        """map() s instance_values=True, serialize=False vrátí instanci Heslar pro typ_organizace."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["typ_organizace"], Heslar)
        self.assertEqual(result["typ_organizace"].ident_cely, HESLAR_ORGTYP_IDENT)

    def test_map_typ_organizace_wrong_heslar_message_uses_verbose_name(self):
        """ImportDataLimitChoicesError pro typ_organizace vypíše verbose_name pole místo ID hesláře."""
        wrong_heslar_nazev = HeslarNazev.objects.create(nazev="Jiný heslář")
        wrong_heslar = Heslar.objects.create(
            ident_cely="HES-WRONG-001",
            nazev_heslare=wrong_heslar_nazev,
            heslo="Chybná hodnota",
            heslo_en="Wrong value",
        )
        row = VALID_ROW.copy()
        row["typ_organizace"] = wrong_heslar.ident_cely
        mapper = OrganizaceMapper(row)

        with self.assertRaises(ImportDataLimitChoicesError) as ctx:
            mapper.map(INSERT, serialize=True, include_primary_key=True)

        message = str(ctx.exception)
        self.assertEqual(ctx.exception.import_field_verbose_name, "typ_organizace")
        self.assertIn(str(_("core.import_data_mappers.OrganizaceMapper.typ_organizace.limit_choices")), message)
        self.assertIn("core_admin.ImportDataLimitChoicesError.message.part_2", message)
        self.assertIn("core_admin.ImportDataLimitChoicesError.message.part_3", message)
        self.assertIn("typ_organizace", message)
        self.assertNotIn(f"nazev_heslare: {HESLAR_ORGANIZACE_TYP}", message)

    def test_map_fk_fields(self):
        """map() vrátí None pro volitelnou nadřazenou organizaci a hodnoty pro povinné FK."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["soucast"])
        self.assertEqual(result["zverejneni_pristupnost"], HESLAR_PRISTUPNOST_IDENT)
        self.assertEqual(result["licence"], HESLAR_LICENCE_IDENT)

    def test_map_nan_text_field_treated_as_none(self):
        """map() převede 'nan' v textovém poli na None."""
        row = VALID_ROW.copy()
        row["nazev_en"] = "nan"
        mapper = OrganizaceMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["nazev_en"])

    def test_map_includes_all_expected_keys(self):
        """map() vrátí přesně klíče definované v fields plus FK pole z get_mapping()."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = set(OrganizaceMapper.fields) | {
            "soucast",
            "typ_organizace",
            "zverejneni_pristupnost",
            "licence",
        }
        self.assertEqual(set(result.keys()), expected_keys)


class OrganizaceMapperInvalidStructureTest(TestCase):
    """Testy pro OrganizaceMapper — neplatná struktura dat."""

    def setUp(self):
        """Vytvoří Heslar fixture pro typ_organizace."""
        _create_required_heslar_fixtures()

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_required_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím povinném sloupci nazev."""
        row = VALID_ROW.copy()
        del row["nazev"]
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_insert_raises_error(self):
        """map() INSERT vyvolá ImportDataIncorrectStructureError při chybějícím ident_cely (require_primary_key_value=True)."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = OrganizaceMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_primary_key_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)

    def test_update_excess_columns_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při nadbytečném sloupci."""
        row = VALID_ROW.copy()
        row["extra"] = "hodnota"
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class OrganizaceMapperCreateRecordsInsertTest(TestCase):
    """Testy pro OrganizaceMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří Heslar fixture pro typ_organizace."""
        _create_required_heslar_fixtures()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí Organizace."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], Organizace)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_fields_set_correctly(self):
        """create_records() nastaví textová a booleovská pole na instanci Organizace."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        organizace = mapper.create_records(INSERT)[0]
        self.assertEqual(organizace.ident_cely, "ORG-000001")
        self.assertEqual(organizace.nazev, "Archeologický ústav")
        self.assertEqual(organizace.nazev_en, "Institute of Archaeology")
        self.assertEqual(organizace.nazev_zkraceny, "ARÚP")
        self.assertEqual(organizace.email, "info@arup.cas.cz")
        self.assertTrue(organizace.oao)
        self.assertFalse(organizace.zanikla)

    def test_create_records_keeps_numeric_zero_mesicu_do_zverejneni(self):
        """create_records() nepřevede numerickou nulu v mesicu_do_zverejneni na None."""
        row = VALID_ROW.copy()
        row["mesicu_do_zverejneni"] = 0
        mapper = OrganizaceMapper(row)
        organizace = mapper.create_records(INSERT)[0]
        self.assertEqual(organizace.mesicu_do_zverejneni, 0)

    def test_create_records_typ_organizace_resolved(self):
        """create_records() nastaví typ_organizace jako instanci Heslar."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        organizace = mapper.create_records(INSERT)[0]
        self.assertIsInstance(organizace.typ_organizace, Heslar)
        self.assertEqual(organizace.typ_organizace.ident_cely, HESLAR_ORGTYP_IDENT)


class OrganizaceMapperCreateRecordsUpdateTest(TestCase):
    """Testy pro OrganizaceMapper.create_records — akce UPDATE."""

    def setUp(self):
        """Vytvoří potřebné Heslar záznamy a existující Organizace pro test aktualizace."""
        _, self.typ_org = _create_heslar_nazev_a_heslar("Typ organizace", "Veřejná", HESLAR_ORGTYP_IDENT)
        _, self.pristupnost = _create_heslar_nazev_a_heslar(
            "Přístupnost", "Veřejná přístupnost", HESLAR_PRISTUPNOST_IDENT
        )
        _, self.licence = _create_heslar_nazev_a_heslar("Licence", "CC BY", HESLAR_LICENCE_IDENT)
        self.organizace = Organizace(
            ident_cely="ORG-000001",
            nazev="Starý název",
            nazev_zkraceny="STARÝ",
            nazev_zkraceny_en="OLD",
            typ_organizace=self.typ_org,
            zverejneni_pristupnost=self.pristupnost,
            licence=self.licence,
        )
        self.organizace.suppress_signal = True
        self.organizace.save()

    def test_create_records_update_returns_existing_instance(self):
        """create_records() UPDATE vrátí seznam s existující instancí Organizace."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        records = mapper.create_records(UPDATE)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].pk, self.organizace.pk)

    def test_create_records_update_sets_new_field_values(self):
        """create_records() UPDATE přepíše pole na instanci Organizace."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        organizace = mapper.create_records(UPDATE)[0]
        self.assertEqual(organizace.nazev, "Archeologický ústav")
        self.assertEqual(organizace.email, "info@arup.cas.cz")
        self.assertTrue(organizace.oao)


class OrganizaceMapperImportValidationTest(TestCase):
    """Testy pro OrganizaceMapper.import_validation."""

    def setUp(self):
        """Vytvoří potřebné Heslar záznamy a existující Organizace pro validační testy."""
        _, self.typ_org = _create_heslar_nazev_a_heslar("Typ organizaceV", "Veřejná", HESLAR_ORGTYP_IDENT)
        _, self.pristupnost = _create_heslar_nazev_a_heslar(
            "PřístupnostV", "Veřejná přístupnost", HESLAR_PRISTUPNOST_IDENT
        )
        _, self.licence = _create_heslar_nazev_a_heslar("LicenceV", "CC BY", HESLAR_LICENCE_IDENT)
        self.organizace = Organizace(
            ident_cely="ORG-000001",
            nazev="Archeologický ústav",
            nazev_zkraceny="ARÚP",
            nazev_zkraceny_en="ARUP",
            typ_organizace=self.typ_org,
            zverejneni_pristupnost=self.pristupnost,
            licence=self.licence,
        )
        self.organizace.suppress_signal = True
        self.organizace.save()

    def test_insert_new_record_returns_primary_key_dict(self):
        """import_validation() INSERT vrátí slovník s primárním klíčem pro neexistující záznam."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "ORG-999999"
        mapper = OrganizaceMapper(row)
        result = mapper.import_validation(INSERT)
        self.assertEqual(result, {"ident_cely": "ORG-999999"})

    def test_insert_duplicate_raises_integrity_error(self):
        """import_validation() INSERT vyvolá ImportDataIntegrityError, pokud záznam již existuje."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"ident_cely": "ORG-000001"})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "ORG-999999"
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s primárním klíčem pro existující záznam."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"ident_cely": "ORG-000001"})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["ident_cely"] = "ORG-999999"
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class OrganizaceMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro OrganizaceMapper.check_required_fields."""

    def setUp(self):
        """Vytvoří Heslar fixture pro typ_organizace."""
        _create_required_heslar_fixtures()

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = OrganizaceMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_required_field_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole nazev None."""
        row = VALID_ROW.copy()
        row["nazev"] = None
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_empty_string_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole nazev prázdný řetězec."""
        row = VALID_ROW.copy()
        row["nazev"] = ""
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_required_field_nan_string_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné pole nazev_zkraceny 'nan'."""
        row = VALID_ROW.copy()
        row["nazev_zkraceny"] = "nan"
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_typ_organizace_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je povinné FK pole typ_organizace None."""
        row = VALID_ROW.copy()
        row["typ_organizace"] = None
        mapper = OrganizaceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_optional_field_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud jsou volitelná pole None."""
        row = VALID_ROW.copy()
        row["nazev_en"] = None
        row["email"] = None
        row["telefon"] = None
        row["adresa"] = None
        row["ico"] = None
        row["ror"] = None
        row["web"] = None
        mapper = OrganizaceMapper(row)
        mapper.check_required_fields(INSERT)

    def test_optional_field_empty_string_passes(self):
        """check_required_fields() projde bez výjimky, pokud je volitelné pole prázdný řetězec."""
        row = VALID_ROW.copy()
        row["email"] = ""
        mapper = OrganizaceMapper(row)
        mapper.check_required_fields(INSERT)


class OrganizaceMapperValidateBatchOrderingTest(TestCase):
    """Testy pro OrganizaceMapper.validate_batch_ordering — detekce dopředných referencí v soucast."""

    def _row(self, ident_cely, soucast=None):
        """Sestaví minimální řádkový slovník s ident_cely a soucast."""
        return {"ident_cely": ident_cely, "soucast": soucast}

    def test_empty_payloads_passes(self):
        """Prázdný seznam dávky neprojde bez výjimky."""
        OrganizaceMapper.validate_batch_ordering([])

    def test_no_soucast_references_passes(self):
        """Záznamy bez soucast neprojdou žádnou kontrolou a validace projde."""
        payloads = [self._row("ORG-000001"), self._row("ORG-000002"), self._row("ORG-000003")]
        OrganizaceMapper.validate_batch_ordering(payloads)

    def test_soucast_none_passes(self):
        """Záznam se soucast=None neprojde kontrolou pořadí."""
        payloads = [self._row("ORG-000001", soucast=None), self._row("ORG-000002")]
        OrganizaceMapper.validate_batch_ordering(payloads)

    def test_soucast_nan_float_passes(self):
        """Záznam se soucast=float('nan') (pandas prázdná hodnota) neprojde kontrolou pořadí."""
        payloads = [self._row("ORG-000001", soucast=float("nan")), self._row("ORG-000002")]
        OrganizaceMapper.validate_batch_ordering(payloads)

    def test_parent_before_child_in_batch_passes(self):
        """Pokud je nadřazená organizace definována dříve v CSV než podřízená, validace projde."""
        payloads = [
            self._row("ORG-PARENT"),
            self._row("ORG-CHILD", soucast="ORG-PARENT"),
        ]
        OrganizaceMapper.validate_batch_ordering(payloads)

    def test_child_before_parent_in_batch_raises_error(self):
        """Dopředná reference: child definován dříve než parent v CSV — musí vyvolat BatchOrderingError."""
        payloads = [
            self._row("ORG-CHILD", soucast="ORG-PARENT"),
            self._row("ORG-PARENT"),
        ]
        with self.assertRaises(ImportDataBatchOrderingError) as ctx:
            OrganizaceMapper.validate_batch_ordering(payloads)
        self.assertEqual(ctx.exception.child_ident_cely, "ORG-CHILD")
        self.assertEqual(ctx.exception.parent_ident_cely, "ORG-PARENT")
        self.assertEqual(ctx.exception.field_name, "soucast")

    def test_error_message_contains_all_placeholders(self):
        """Zpráva výjimky obsahuje child_ident_cely, parent_ident_cely i field_name."""
        payloads = [self._row("ORG-CHILD", soucast="ORG-PARENT"), self._row("ORG-PARENT")]
        with self.assertRaises(ImportDataBatchOrderingError) as ctx:
            OrganizaceMapper.validate_batch_ordering(payloads)
        message = str(ctx.exception)
        self.assertIn("ORG-CHILD", message)
        self.assertIn("ORG-PARENT", message)
        self.assertIn("soucast", message)

    def test_soucast_referencing_existing_db_record_passes(self):
        """Pokud soucast odkazuje na organizaci, která již existuje v DB, validace projde (i když není v CSV dříve)."""
        payloads = [self._row("ORG-CHILD", soucast="ORG-EXISTING")]
        with patch("core.import_data_mappers.Organizace.objects") as mock_objects:
            mock_objects.filter.return_value.exists.return_value = True
            OrganizaceMapper.validate_batch_ordering(payloads)
        mock_objects.filter.assert_called_once_with(ident_cely="ORG-EXISTING")

    def test_multiple_children_with_shared_parent_passes(self):
        """Více potomků odkazujících na jednoho předka, který je definován jako první, projde validací."""
        payloads = [
            self._row("ORG-PARENT"),
            self._row("ORG-CHILD-1", soucast="ORG-PARENT"),
            self._row("ORG-CHILD-2", soucast="ORG-PARENT"),
        ]
        OrganizaceMapper.validate_batch_ordering(payloads)

    def test_first_forward_reference_in_chain_raises_error(self):
        """Z řetězce dopředných referencí se vyvolá chyba pro první porušení."""
        payloads = [
            self._row("ORG-CHILD", soucast="ORG-MIDDLE"),
            self._row("ORG-MIDDLE", soucast="ORG-PARENT"),
            self._row("ORG-PARENT"),
        ]
        with self.assertRaises(ImportDataBatchOrderingError) as ctx:
            OrganizaceMapper.validate_batch_ordering(payloads)
        self.assertEqual(ctx.exception.child_ident_cely, "ORG-CHILD")
        self.assertEqual(ctx.exception.parent_ident_cely, "ORG-MIDDLE")
