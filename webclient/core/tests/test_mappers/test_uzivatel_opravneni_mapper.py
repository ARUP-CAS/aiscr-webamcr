from unittest.mock import patch

from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
    UzivatelOpravneniMapper,
)
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.hesla import HESLAR_LICENCE, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar, HeslarNazev
from uzivatel.models import Organizace, User

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "uzivatel": "U-000001",
    "skupina": "archeolog",
}


class UzivatelOpravneniMapperInvalidStructureTest(TestCase):
    """Testy pro UzivatelOpravneniMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = UzivatelOpravneniMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_uzivatel_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci uzivatel."""
        row = VALID_ROW.copy()
        del row["uzivatel"]
        mapper = UzivatelOpravneniMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_skupina_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci skupina."""
        row = VALID_ROW.copy()
        del row["skupina"]
        mapper = UzivatelOpravneniMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = UzivatelOpravneniMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class UzivatelOpravneniMapperValidationTest(TestCase):
    """Testy pro UzivatelOpravneniMapper — validace aktuálního stavu relace."""

    @classmethod
    def setUpTestData(cls):
        """Vytvoří minimálního uživatele a skupinu pro validační testy relace."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            typ_org_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
            )
            typ_org, _ = Heslar.objects.get_or_create(
                ident_cely="HES-UO-TYPORG-001",
                defaults={"nazev_heslare": typ_org_nazev, "heslo": "Typ", "heslo_en": "Type"},
            )
            pristupnost_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
            )
            pristupnost, _ = Heslar.objects.get_or_create(
                ident_cely="HES-UO-PRIST-001",
                defaults={"nazev_heslare": pristupnost_nazev, "heslo": "Veřejný", "heslo_en": "Public"},
            )
            licence_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
            licence, _ = Heslar.objects.get_or_create(
                ident_cely="HES-UO-LIC-001",
                defaults={"nazev_heslare": licence_nazev, "heslo": "Licence", "heslo_en": "Licence"},
            )
            cls.organizace = Organizace.objects.create(
                ident_cely="ORG-UO-001",
                nazev="Organizace oprávnění",
                nazev_zkraceny="ORGUO",
                nazev_zkraceny_en="ORGUO",
                typ_organizace=typ_org,
                zverejneni_pristupnost=pristupnost,
                licence=licence,
            )
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="uzivatel-opravneni@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-OPR-001",
                first_name="Import",
                last_name="Opravneni",
            )
            cls.group = Group.objects.create(name="import-opravneni")

    def test_insert_validation_passes_when_group_is_missing(self):
        """INSERT validace projde, pokud uživatel skupinu zatím nemá."""
        mapper = UzivatelOpravneniMapper({"uzivatel": self.user.ident_cely, "skupina": self.group.name})

        result = mapper.import_validation(INSERT)

        self.assertEqual(result, {"ident_cely": self.user.ident_cely})

    def test_insert_validation_rejects_existing_group_noop(self):
        """INSERT validace odmítne no-op řádek, pokud uživatel skupinu už má."""
        self.user.groups.add(self.group)
        mapper = UzivatelOpravneniMapper({"uzivatel": self.user.ident_cely, "skupina": self.group.name})

        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_delete_validation_passes_when_group_exists(self):
        """DELETE validace projde, pokud uživatel skupinu má."""
        self.user.groups.add(self.group)
        mapper = UzivatelOpravneniMapper({"uzivatel": self.user.ident_cely, "skupina": self.group.name})

        result = mapper.import_validation(DELETE)

        self.assertEqual(result, {"ident_cely": self.user.ident_cely})

    def test_delete_validation_rejects_missing_group_noop(self):
        """DELETE validace odmítne no-op řádek, pokud uživatel skupinu nemá."""
        mapper = UzivatelOpravneniMapper({"uzivatel": self.user.ident_cely, "skupina": self.group.name})

        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)

    def test_update_validation_rejects_unsupported_action(self):
        """UPDATE není podporovaná akce pro relační mapper oprávnění."""
        mapper = UzivatelOpravneniMapper({"uzivatel": self.user.ident_cely, "skupina": self.group.name})

        with self.assertRaises(ImportDataError):
            mapper.import_validation(UPDATE)

    def test_create_records_rejects_unknown_action(self):
        """create_records() selže pro akci mimo podporované konstanty mapperu."""
        mapper = UzivatelOpravneniMapper({"uzivatel": self.user.ident_cely, "skupina": self.group.name})

        with self.assertRaises(ImportDataError):
            mapper.create_records("replace")
