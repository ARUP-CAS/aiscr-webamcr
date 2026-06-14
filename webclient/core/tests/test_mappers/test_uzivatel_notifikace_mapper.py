from unittest.mock import patch

from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
    UzivatelNotifikaceMapper,
)
from django.test import TestCase
from heslar.hesla import HESLAR_LICENCE, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar, HeslarNazev
from uzivatel.models import Organizace, User, UserNotificationType

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "uzivatel": "U-000001",
    "notifikace": "S-E-N-001",
}


class UzivatelNotifikaceMapperInvalidStructureTest(TestCase):
    """Testy pro UzivatelNotifikaceMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = UzivatelNotifikaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_uzivatel_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci uzivatel."""
        row = VALID_ROW.copy()
        del row["uzivatel"]
        mapper = UzivatelNotifikaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_notifikace_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci notifikace."""
        row = VALID_ROW.copy()
        del row["notifikace"]
        mapper = UzivatelNotifikaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = UzivatelNotifikaceMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class UzivatelNotifikaceMapperValidationTest(TestCase):
    """Testy pro UzivatelNotifikaceMapper — validace aktuálního stavu relace."""

    @classmethod
    def setUpTestData(cls):
        """Vytvoří minimálního uživatele a typ notifikace pro validační testy relace."""
        from django.contrib.auth.models import Group

        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            typ_org_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
            )
            typ_org, _ = Heslar.objects.get_or_create(
                ident_cely="HES-UN-TYPORG-001",
                defaults={"nazev_heslare": typ_org_nazev, "heslo": "Typ", "heslo_en": "Type"},
            )
            pristupnost_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
            )
            pristupnost, _ = Heslar.objects.get_or_create(
                ident_cely="HES-UN-PRIST-001",
                defaults={"nazev_heslare": pristupnost_nazev, "heslo": "Veřejný", "heslo_en": "Public"},
            )
            licence_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
            licence, _ = Heslar.objects.get_or_create(
                ident_cely="HES-UN-LIC-001",
                defaults={"nazev_heslare": licence_nazev, "heslo": "Licence", "heslo_en": "Licence"},
            )
            cls.organizace = Organizace.objects.create(
                ident_cely="ORG-UN-001",
                nazev="Organizace notifikace",
                nazev_zkraceny="ORGUN",
                nazev_zkraceny_en="ORGUN",
                typ_organizace=typ_org,
                zverejneni_pristupnost=pristupnost,
                licence=licence,
            )
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="uzivatel-notifikace@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-NOT-001",
                first_name="Import",
                last_name="Notifikace",
            )
            cls.notification_type = UserNotificationType.objects.create(ident_cely="S-E-N-TEST-001")

    def test_insert_validation_passes_when_notification_is_missing(self):
        """INSERT validace projde, pokud uživatel daný typ notifikace zatím nemá."""
        mapper = UzivatelNotifikaceMapper(
            {"uzivatel": self.user.ident_cely, "notifikace": self.notification_type.ident_cely}
        )

        result = mapper.import_validation(INSERT)

        self.assertEqual(result, {"ident_cely": self.user.ident_cely})

    def test_insert_validation_rejects_existing_notification_noop(self):
        """INSERT validace odmítne no-op řádek, pokud uživatel daný typ notifikace už má."""
        self.user.notification_types.add(self.notification_type)
        mapper = UzivatelNotifikaceMapper(
            {"uzivatel": self.user.ident_cely, "notifikace": self.notification_type.ident_cely}
        )

        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(INSERT)

    def test_delete_validation_passes_when_notification_exists(self):
        """DELETE validace projde, pokud uživatel daný typ notifikace má."""
        self.user.notification_types.add(self.notification_type)
        mapper = UzivatelNotifikaceMapper(
            {"uzivatel": self.user.ident_cely, "notifikace": self.notification_type.ident_cely}
        )

        result = mapper.import_validation(DELETE)

        self.assertEqual(result, {"ident_cely": self.user.ident_cely})

    def test_delete_validation_rejects_missing_notification_noop(self):
        """DELETE validace odmítne no-op řádek, pokud uživatel daný typ notifikace nemá."""
        mapper = UzivatelNotifikaceMapper(
            {"uzivatel": self.user.ident_cely, "notifikace": self.notification_type.ident_cely}
        )

        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)

    def test_update_validation_rejects_unsupported_action(self):
        """UPDATE není podporovaná akce pro relační mapper notifikací."""
        mapper = UzivatelNotifikaceMapper(
            {"uzivatel": self.user.ident_cely, "notifikace": self.notification_type.ident_cely}
        )

        with self.assertRaises(ImportDataError):
            mapper.import_validation(UPDATE)

    def test_create_records_rejects_unknown_action(self):
        """create_records() selže pro akci mimo podporované konstanty mapperu."""
        mapper = UzivatelNotifikaceMapper(
            {"uzivatel": self.user.ident_cely, "notifikace": self.notification_type.ident_cely}
        )

        with self.assertRaises(ImportDataError):
            mapper.create_records("replace")
