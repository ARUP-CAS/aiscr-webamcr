from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
    UzivatelSpolupraceMapper,
)
from django.contrib.auth import get_user_model
from django.test import TestCase
from heslar.hesla import HESLAR_LICENCE, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar, HeslarNazev
from pas.models import UzivatelSpoluprace
from uzivatel.models import Organizace

User = get_user_model()

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE


def _create_user_fixtures():
    """Vytvoří Heslar, Organizace a dva uživatele pro testovací účely."""
    hn_typ = HeslarNazev.objects.create(pk=HESLAR_ORGANIZACE_TYP, nazev="Typ organizace")
    hn_prist = HeslarNazev.objects.create(pk=HESLAR_PRISTUPNOST, nazev="Přístupnost")
    hn_lic = HeslarNazev.objects.create(pk=HESLAR_LICENCE, nazev="Licence")
    heslar_typ = Heslar.objects.create(
        ident_cely="HES-ORGTYP-001", heslo="Veřejná", heslo_en="Public", nazev_heslare=hn_typ
    )
    heslar_prist = Heslar.objects.create(
        ident_cely="HES-PRIST-001", heslo="Veřejná", heslo_en="Public", nazev_heslare=hn_prist
    )
    heslar_lic = Heslar.objects.create(ident_cely="HES-LIC-001", heslo="CC BY", heslo_en="CC BY", nazev_heslare=hn_lic)
    organizace = Organizace(
        ident_cely="ORG-T-001",
        nazev="Testovací ústav",
        nazev_zkraceny="TU",
        nazev_zkraceny_en="TI",
        typ_organizace=heslar_typ,
        zverejneni_pristupnost=heslar_prist,
        licence=heslar_lic,
    )
    organizace.suppress_signal = True
    organizace.save()

    from django.contrib.auth.hashers import make_password

    vedouci, spolupracovnik = User.objects.bulk_create(
        [
            User(
                ident_cely="U-TEST-001",
                email="vedouci@test.cz",
                organizace=organizace,
                password=make_password(None),
            ),
            User(
                ident_cely="U-TEST-002",
                email="spolupracovnik@test.cz",
                organizace=organizace,
                password=make_password(None),
            ),
        ]
    )
    return vedouci, spolupracovnik


class UzivatelSpolupraceMapperInsertValidTest(TestCase):
    """Testy pro UzivatelSpolupraceMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data User a Organizace pro platný INSERT dataset."""
        self.vedouci, self.spolupracovnik = _create_user_fixtures()
        self.valid_row = {
            "stav": "1",
            "vedouci": self.vedouci.ident_cely,
            "spolupracovnik": self.spolupracovnik.ident_cely,
        }

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_stav_serialized_as_int(self):
        """map() převede stav na celé číslo."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["stav"], 1)

    def test_map_vedouci_raw_value(self):
        """map() vrátí serializovanou hodnotu vedouci jako řetězec ident_cely."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["vedouci"], self.vedouci.ident_cely)

    def test_map_spolupracovnik_raw_value(self):
        """map() vrátí serializovanou hodnotu spolupracovnik jako řetězec ident_cely."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["spolupracovnik"], self.spolupracovnik.ident_cely)

    def test_map_vedouci_instance_value(self):
        """map() s instance_values=True vrátí instanci User pro pole vedouci."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["vedouci"], User)
        self.assertEqual(result["vedouci"].ident_cely, self.vedouci.ident_cely)

    def test_map_spolupracovnik_instance_value(self):
        """map() s instance_values=True vrátí instanci User pro pole spolupracovnik."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["spolupracovnik"], User)
        self.assertEqual(result["spolupracovnik"].ident_cely, self.spolupracovnik.ident_cely)

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče {"stav", "vedouci", "spolupracovnik"}."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(set(result.keys()), {"stav", "vedouci", "spolupracovnik"})


class UzivatelSpolupraceMapperInvalidStructureTest(TestCase):
    """Testy pro UzivatelSpolupraceMapper — neplatná struktura dat."""

    def setUp(self):
        """Vytvoří testovací data User a Organizace pro testy neplatné struktury."""
        self.valid_row = {
            "stav": "1",
            "vedouci": "U-TEST-001",
            "spolupracovnik": "U-TEST-002",
        }

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = self.valid_row.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = UzivatelSpolupraceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_vedouci_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci vedouci."""
        row = self.valid_row.copy()
        del row["vedouci"]
        mapper = UzivatelSpolupraceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_spolupracovnik_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci spolupracovnik."""
        row = self.valid_row.copy()
        del row["spolupracovnik"]
        mapper = UzivatelSpolupraceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = UzivatelSpolupraceMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_primary_key_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči id."""
        row = self.valid_row.copy()
        mapper = UzivatelSpolupraceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class UzivatelSpolupraceMapperCreateRecordsInsertTest(TestCase):
    """Testy pro UzivatelSpolupraceMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data User a Organizace pro testy create_records."""
        self.vedouci, self.spolupracovnik = _create_user_fixtures()
        self.valid_row = {
            "stav": "1",
            "vedouci": self.vedouci.ident_cely,
            "spolupracovnik": self.spolupracovnik.ident_cely,
        }

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí UzivatelSpoluprace."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], UzivatelSpoluprace)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_vedouci_resolved(self):
        """create_records() nastaví vedouci jako instanci User."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        spoluprace = mapper.create_records(INSERT)[0]
        self.assertIsInstance(spoluprace.vedouci, User)
        self.assertEqual(spoluprace.vedouci.ident_cely, self.vedouci.ident_cely)

    def test_create_records_spolupracovnik_resolved(self):
        """create_records() nastaví spolupracovnik jako instanci User."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        spoluprace = mapper.create_records(INSERT)[0]
        self.assertIsInstance(spoluprace.spolupracovnik, User)
        self.assertEqual(spoluprace.spolupracovnik.ident_cely, self.spolupracovnik.ident_cely)


class UzivatelSpolupraceMapperImportValidationTest(TestCase):
    """Testy pro UzivatelSpolupraceMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data User a Organizace pro testy import_validation."""
        self.vedouci, self.spolupracovnik = _create_user_fixtures()
        self.valid_row = {
            "stav": "1",
            "vedouci": self.vedouci.ident_cely,
            "spolupracovnik": self.spolupracovnik.ident_cely,
        }
        self.spoluprace = UzivatelSpoluprace.objects.create(
            vedouci=self.vedouci,
            spolupracovnik=self.spolupracovnik,
            stav=1,
        )

    def test_insert_without_id_returns_none(self):
        """import_validation() INSERT bez id vrátí None (_get_filter_kwargs_primary_key vrátí None)."""
        mapper = UzivatelSpolupraceMapper(self.valid_row.copy())
        result = mapper.import_validation(INSERT)
        self.assertIsNone(result)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s primárním klíčem pro existující záznam."""
        row = self.valid_row.copy()
        row["id"] = f"spol-{self.spoluprace.pk}"
        mapper = UzivatelSpolupraceMapper(row)
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"id": self.spoluprace.pk})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = self.valid_row.copy()
        row["id"] = "spol-999999"
        mapper = UzivatelSpolupraceMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)


class UzivatelSpolupraceMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro UzivatelSpolupraceMapper.check_required_fields."""

    def setUp(self):
        """Vytvoří testovací data User a Organizace pro testy check_required_fields."""
        self.valid_row = {
            "stav": "1",
            "vedouci": "U-TEST-001",
            "spolupracovnik": "U-TEST-002",
        }

    def test_vedouci_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je vedouci None (not null FK)."""
        row = self.valid_row.copy()
        row["vedouci"] = None
        mapper = UzivatelSpolupraceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_spolupracovnik_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je spolupracovnik None (not null FK)."""
        row = self.valid_row.copy()
        row["spolupracovnik"] = None
        mapper = UzivatelSpolupraceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_stav_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je stav None (not null pole bez default)."""
        row = self.valid_row.copy()
        row["stav"] = None
        mapper = UzivatelSpolupraceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
