from core.constants import DOKUMENTACNI_JEDNOTKA_RELATION_TYPE
from core.forms import ImportDataAdminForm
from core.import_data_mappers import ImportDataError, ImportDataIncorrectStructureError, KomponentaAktivitaMapper
from django.test import TestCase
from heslar.hesla import HESLAR_AKTIVITA
from heslar.models import Heslar, HeslarNazev
from komponenta.models import Komponenta, KomponentaVazby

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE


class KomponentaAktivitaMapperInsertValidTest(TestCase):
    """Testy pro KomponentaAktivitaMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data Heslar, KomponentaVazby a Komponenta pro platný INSERT dataset."""
        self.heslar_nazev = HeslarNazev.objects.create(pk=HESLAR_AKTIVITA, nazev="aktivita")
        self.heslar_aktivita = Heslar.objects.create(
            ident_cely="HES-AKT-001",
            heslo="obývání",
            heslo_en="occupation",
            nazev_heslare=self.heslar_nazev,
        )
        self.vazby = KomponentaVazby.objects.create(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
        self.komponenta = Komponenta(ident_cely="K-000001", komponenta_vazby=self.vazby)
        self.komponenta.suppress_signal = True
        self.komponenta.save()
        self.valid_row = {
            "komponenta": self.komponenta.ident_cely,
            "aktivita": self.heslar_aktivita.ident_cely,
        }

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = KomponentaAktivitaMapper(self.valid_row.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_komponenta_raw_value(self):
        """map() vrátí serializovanou hodnotu komponenta jako řetězec ident_cely."""
        mapper = KomponentaAktivitaMapper(self.valid_row.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["komponenta"], self.komponenta.ident_cely)

    def test_map_aktivita_raw_value(self):
        """map() vrátí serializovanou hodnotu aktivita jako řetězec ident_cely."""
        mapper = KomponentaAktivitaMapper(self.valid_row.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["aktivita"], self.heslar_aktivita.ident_cely)

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče {"komponenta", "aktivita"}."""
        mapper = KomponentaAktivitaMapper(self.valid_row.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(set(result.keys()), {"komponenta", "aktivita"})


class KomponentaAktivitaMapperInvalidStructureTest(TestCase):
    """Testy pro KomponentaAktivitaMapper — neplatná struktura dat."""

    def setUp(self):
        """Vytvoří testovací data Heslar, KomponentaVazby a Komponenta pro testy neplatné struktury."""
        self.heslar_nazev = HeslarNazev.objects.create(pk=HESLAR_AKTIVITA, nazev="aktivita")
        self.heslar_aktivita = Heslar.objects.create(
            ident_cely="HES-AKT-001",
            heslo="obývání",
            heslo_en="occupation",
            nazev_heslare=self.heslar_nazev,
        )
        self.vazby = KomponentaVazby.objects.create(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
        self.komponenta = Komponenta(ident_cely="K-000001", komponenta_vazby=self.vazby)
        self.komponenta.suppress_signal = True
        self.komponenta.save()
        self.valid_row = {
            "komponenta": self.komponenta.ident_cely,
            "aktivita": self.heslar_aktivita.ident_cely,
        }

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = self.valid_row.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = KomponentaAktivitaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_komponenta_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci komponenta."""
        row = self.valid_row.copy()
        del row["komponenta"]
        mapper = KomponentaAktivitaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_aktivita_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci aktivita."""
        row = self.valid_row.copy()
        del row["aktivita"]
        mapper = KomponentaAktivitaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = KomponentaAktivitaMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_delete_missing_aktivita_raises_error(self):
        """map() DELETE vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči aktivita."""
        row = {"komponenta": self.valid_row["komponenta"]}
        mapper = KomponentaAktivitaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(DELETE, serialize=True, include_primary_key=True)


class KomponentaAktivitaMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro KomponentaAktivitaMapper.check_required_fields."""

    def setUp(self):
        """Vytvoří testovací data Heslar, KomponentaVazby a Komponenta pro testy check_required_fields."""
        self.heslar_nazev = HeslarNazev.objects.create(pk=HESLAR_AKTIVITA, nazev="aktivita")
        self.heslar_aktivita = Heslar.objects.create(
            ident_cely="HES-AKT-001",
            heslo="obývání",
            heslo_en="occupation",
            nazev_heslare=self.heslar_nazev,
        )
        self.valid_row = {
            "komponenta": "K-000001",
            "aktivita": self.heslar_aktivita.ident_cely,
        }

    def test_komponenta_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je komponenta None (not null FK)."""
        row = self.valid_row.copy()
        row["komponenta"] = None
        mapper = KomponentaAktivitaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_aktivita_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je aktivita None (not null FK)."""
        row = self.valid_row.copy()
        row["aktivita"] = None
        mapper = KomponentaAktivitaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
