"""
Testy mapperu alternativních distribucí souborů (``distribution.csv``, issue #3527).

Pokrývají strukturu sloupců podle akce, validaci názvu distribuce, dohledání dotčeného souboru,
zjištění existence distribuce ve Fedoře a přípravu záznamu pro fázi importu. Mapper nesmí měnit
databázi ani repozitář – kontroluje se i to. Dotaz do Fedory je v testech nahrazen mockem.
"""

from unittest.mock import patch

from core.constants import NAHRANI_DISTRIBUCE, ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DistribuceImportIntegrityError,
    DistribuceMapper,
    DistribuceMissingRepositoryUuidError,
    DistribuceMissingVazbaError,
    DistribuceUnsafeFilenameError,
    ImportDataDistributionPrefixCollisionError,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataInvalidDistributionError,
    ImportDataMissingReferencedValueError,
    ImportDataReservedDistributionError,
    ParadataMapper,
)
from core.models import Soubor
from core.repository_connector import FedoraNoResponseError, FedoraRepositoryConnector
from core.tests.test_mappers.fixtures import create_dokument_fixture, create_soubor_fixture
from django.contrib.auth.models import Group
from django.test import TestCase
from historie.models import Historie
from uzivatel.models import User

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "id": "soub-1",
    "nazev": "alto.xml",
    "mimetype": "text/xml",
    "distribution": "ocr/alto-xml",
}


class DistribuceMapperStructureTest(TestCase):
    """Testy struktury sloupců ``distribution.csv`` podle prováděné akce."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        with self.assertRaises(ImportDataIncorrectStructureError):
            DistribuceMapper(row).map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_distribution_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci distribution."""
        row = VALID_ROW.copy()
        del row["distribution"]
        with self.assertRaises(ImportDataIncorrectStructureError):
            DistribuceMapper(row).map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_id_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči id."""
        row = VALID_ROW.copy()
        del row["id"]
        with self.assertRaises(ImportDataIncorrectStructureError):
            DistribuceMapper(row).map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        with self.assertRaises(ImportDataIncorrectStructureError):
            DistribuceMapper({}).map(INSERT, serialize=True, include_primary_key=True)

    def test_delete_expects_only_id_and_distribution(self):
        """DELETE projde se sloupci id a distribution; sloupce nazev a mimetype jsou navíc."""
        DistribuceMapper({"id": "soub-1", "distribution": "ocr/alto-xml"}).map(DELETE, serialize=True)
        with self.assertRaises(ImportDataIncorrectStructureError):
            DistribuceMapper(VALID_ROW.copy()).map(DELETE, serialize=True)

    def test_insert_requires_nazev_and_mimetype(self):
        """INSERT bez sloupců nazev a mimetype neprojde kontrolou struktury."""
        with self.assertRaises(ImportDataIncorrectStructureError):
            DistribuceMapper({"id": "soub-1", "distribution": "ocr/alto-xml"}).map(INSERT, serialize=True)

    def test_map_returns_all_columns(self):
        """map() vrátí všechny sloupce importu včetně primárního klíče v původním formátu."""
        result = DistribuceMapper(VALID_ROW.copy()).map(INSERT, serialize=True, include_primary_key=True)

        self.assertEqual(set(result.keys()), {"id", "nazev", "mimetype", "distribution"})
        self.assertEqual(result["id"], "soub-1")
        self.assertEqual(result["distribution"], "ocr/alto-xml")


class DistribuceMapperNameValidationTest(TestCase):
    """Testy validace názvu distribuce, které nepotřebují existující soubor."""

    def test_reserved_names_rejected(self):
        """Vyhrazené názvy distribucí se odmítnou, včetně celého podstromu pod nimi.

        ``paradata/…`` by zapsalo do kontejneru paradat mimo ``ParadataMapper`` a ``orig/…``
        pod binární obsah souboru — obojí musí spadnout už při validaci CSV.
        """
        for distribution in (
            "orig",
            "paradata",
            "thumb/page",
            "thumb/page/1",
            "paradata/alto-xml",
            "paradata/ocr/alto-xml",
            "orig/x",
        ):
            with self.subTest(distribution=distribution):
                row = VALID_ROW.copy()
                row["distribution"] = distribution
                with self.assertRaises(ImportDataReservedDistributionError):
                    DistribuceMapper(row).import_validation(INSERT)

    def test_unsafe_segments_rejected(self):
        """Názvy s prázdným segmentem nebo průchodem adresáři se odmítnou už při validaci."""
        for distribution in ("ocr//alto-xml", "../orig", "ocr/../../orig", "ocr/./alto"):
            with self.subTest(distribution=distribution):
                row = VALID_ROW.copy()
                row["distribution"] = distribution
                with self.assertRaises(ImportDataInvalidDistributionError):
                    DistribuceMapper(row).import_validation(INSERT)

    def test_empty_distribution_rejected(self):
        """Prázdný název distribuce se odmítne jako chybějící povinná hodnota."""
        for distribution in (None, "", "   ", "/"):
            with self.subTest(distribution=distribution):
                row = VALID_ROW.copy()
                row["distribution"] = distribution
                with self.assertRaises(ImportDataError):
                    DistribuceMapper(row).import_validation(INSERT)

    def test_unsafe_filename_rejected(self):
        """Název souboru s průchodem adresáři nebo absolutní cestou se odmítne už při validaci."""
        for nazev in ("../secret", "..\\secret", "/etc/passwd", "sub/file.xml", ".", ".."):
            with self.subTest(nazev=nazev):
                row = VALID_ROW.copy()
                row["nazev"] = nazev
                with self.assertRaises(DistribuceUnsafeFilenameError):
                    DistribuceMapper(row).import_validation(INSERT)

    def test_paradata_unsafe_filename_rejected(self):
        """Paradata kontrolují název souboru stejně jako distribuce."""
        for nazev in ("../secret", "/etc/passwd", "sub/file.xml"):
            with self.subTest(nazev=nazev):
                row = {
                    "path": "/rest/AMCR/record/C-1/file/uuid-1",
                    "distribution": "ocr",
                    "nazev": nazev,
                    "mimetype": "text/xml",
                }
                with self.assertRaises(DistribuceUnsafeFilenameError):
                    ParadataMapper(row).import_validation(INSERT)


class DistribuceMapperValidationTest(TestCase):
    """Testy validace importu proti existujícím souborům a stavu distribucí ve Fedoře."""

    @classmethod
    def setUpTestData(cls):
        """Vytvoří dokument a soubor s cestou do Fedory."""
        cls.dokument = create_dokument_fixture(ident_cely="C-TX-DIST-001")
        cls.soubor = create_soubor_fixture(cls.dokument)

    def _row(self, **overrides):
        """Sestaví řádek importu ukazující na testovací soubor."""
        row = VALID_ROW.copy()
        row["id"] = f"soub-{self.soubor.pk}"
        row.update(overrides)
        return row

    def _fedora(self, exists=False):
        """Nahradí dotaz do Fedory na existenci distribuce pevnou odpovědí."""
        return patch.object(FedoraRepositoryConnector, "distribution_exists", return_value=exists)

    def test_insert_passes_when_distribution_missing(self):
        """INSERT projde, pokud distribuce daného názvu ve Fedoře není."""
        with self._fedora(exists=False):
            result = DistribuceMapper(self._row()).import_validation(INSERT)

        self.assertEqual(result, {"id": self.soubor.pk})

    def test_insert_rejects_existing_distribution(self):
        """INSERT odmítne distribuci, jejíž kontejner ve Fedoře existuje."""
        with self._fedora(exists=True):
            with self.assertRaises(DistribuceImportIntegrityError):
                DistribuceMapper(self._row()).import_validation(INSERT)

    def test_update_and_delete_pass_for_existing_distribution(self):
        """UPDATE i DELETE projdou, pokud kontejner distribuce ve Fedoře existuje."""
        with self._fedora(exists=True):
            self.assertEqual(DistribuceMapper(self._row()).import_validation(UPDATE), {"id": self.soubor.pk})
            row = {"id": f"soub-{self.soubor.pk}", "distribution": "ocr/alto-xml"}
            self.assertEqual(DistribuceMapper(row).import_validation(DELETE), {"id": self.soubor.pk})

    def test_update_and_delete_reject_missing_distribution(self):
        """UPDATE i DELETE odmítnou distribuci, jejíž kontejner ve Fedoře není."""
        with self._fedora(exists=False):
            with self.assertRaises(DistribuceImportIntegrityError):
                DistribuceMapper(self._row()).import_validation(UPDATE)
            with self.assertRaises(DistribuceImportIntegrityError):
                DistribuceMapper({"id": f"soub-{self.soubor.pk}", "distribution": "ocr/alto-xml"}).import_validation(
                    DELETE
                )

    def test_history_is_not_consulted(self):
        """Historie souboru nerozhoduje – zdrojem pravdy je výhradně Fedora."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        user = User.objects.create_user(  # type: ignore[attr-defined]
            email="distribuce-historie@example.cz",
            password="pass",
            is_active=True,
            organizace=self.dokument.organizace,
            ident_cely="U-DIST-002",
            first_name="Import",
            last_name="Historie",
        )
        Historie.objects.create(
            typ_zmeny=NAHRANI_DISTRIBUCE, uzivatel=user, poznamka="ocr/alto-xml", vazba=self.soubor.historie
        )

        # Historie tvrdí, že distribuce existuje, Fedora nikoli – rozhoduje Fedora.
        with self._fedora(exists=False):
            self.assertEqual(DistribuceMapper(self._row()).import_validation(INSERT), {"id": self.soubor.pk})

    def test_queries_fedora_with_file_uuid_and_distribution(self):
        """Dotaz do Fedory se ptá na UUID kontejneru souboru a normalizovaný název distribuce."""
        with patch.object(FedoraRepositoryConnector, "distribution_exists", return_value=False) as exists_mock:
            DistribuceMapper(self._row(distribution=" /ocr/alto-xml/ ")).import_validation(INSERT)

        exists_mock.assert_called_once_with(self.soubor.repository_uuid, "ocr/alto-xml")

    def test_fedora_outage_propagates(self):
        """Nedostupná Fedora validaci zastaví, místo aby se distribuce tvářila jako neexistující."""
        with patch.object(
            FedoraRepositoryConnector,
            "distribution_exists",
            side_effect=FedoraNoResponseError("url", "No Fedora response", None),
        ):
            with self.assertRaises(FedoraNoResponseError):
                DistribuceMapper(self._row()).import_validation(INSERT)

    def test_missing_soubor_rejected(self):
        """Neexistující soubor se odmítne jako chybějící reference."""
        with self._fedora(exists=False):
            with self.assertRaises(ImportDataMissingReferencedValueError):
                DistribuceMapper(self._row(id="soub-99999999")).import_validation(INSERT)

    def test_soubor_without_repository_uuid_rejected(self):
        """Soubor bez cesty do Fedory se odmítne dřív, než se na distribuci vůbec zeptáme."""
        soubor_bez_path = create_soubor_fixture(self.dokument, nazev="bez_path.pdf", with_path=False)

        with patch.object(FedoraRepositoryConnector, "distribution_exists") as exists_mock:
            with self.assertRaises(DistribuceMissingRepositoryUuidError):
                DistribuceMapper(self._row(id=f"soub-{soubor_bez_path.pk}")).import_validation(INSERT)
        exists_mock.assert_not_called()

    def test_soubor_without_vazba_rejected(self):
        """Soubor bez navázaného nadřazeného záznamu se odmítne dřív, než se na distribuci zeptáme Fedory."""
        soubor_bez_vazby = create_soubor_fixture(self.dokument, nazev="bez_navazaneho.pdf", with_navazany_objekt=False)

        with patch.object(FedoraRepositoryConnector, "distribution_exists") as exists_mock:
            with self.assertRaises(DistribuceMissingVazbaError):
                DistribuceMapper(self._row(id=f"soub-{soubor_bez_vazby.pk}")).import_validation(INSERT)
        exists_mock.assert_not_called()

    def test_duplicate_row_in_batch_rejected(self):
        """Táž dvojice (soubor, distribuce) se v jedné dávce nesmí opakovat."""
        seen: set = set()
        with self._fedora(exists=False):
            DistribuceMapper(self._row()).import_validation(INSERT, seen_in_batch=seen)

            with self.assertRaises(DistribuceImportIntegrityError):
                DistribuceMapper(self._row()).import_validation(INSERT, seen_in_batch=seen)

    def test_different_distribution_in_batch_passes(self):
        """Různé distribuce téhož souboru mohou být v jedné dávce."""
        seen: set = set()
        with self._fedora(exists=False):
            DistribuceMapper(self._row()).import_validation(INSERT, seen_in_batch=seen)
            DistribuceMapper(self._row(distribution="ocr/hocr")).import_validation(INSERT, seen_in_batch=seen)

        self.assertEqual(len(seen), 2)


class DistribuceMapperCreateRecordsTest(TestCase):
    """Testy přípravy záznamu pro fázi importu."""

    @classmethod
    def setUpTestData(cls):
        """Vytvoří dokument a soubor, na který se importní řádek odkazuje."""
        cls.dokument = create_dokument_fixture(ident_cely="C-TX-DIST-003")
        cls.soubor = create_soubor_fixture(cls.dokument)

    def _row(self, **overrides):
        """Sestaví řádek importu ukazující na testovací soubor."""
        row = VALID_ROW.copy()
        row["id"] = f"soub-{self.soubor.pk}"
        row.update(overrides)
        return row

    def test_returns_existing_soubor_with_transient_attributes(self):
        """create_records() vrátí existující soubor doplněný o přechodné atributy distribuce."""
        records = DistribuceMapper(self._row()).create_records(INSERT)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.pk, self.soubor.pk)
        self.assertEqual(record.distribution_name, "ocr/alto-xml")
        self.assertEqual(record.distribution_nazev, "alto.xml")
        self.assertEqual(record.distribution_mimetype, "text/xml")
        self.assertEqual(record.distribution_performed_action, INSERT)

    def test_normalizes_distribution_name(self):
        """Přechodný atribut nese normalizovaný název distribuce."""
        records = DistribuceMapper(self._row(distribution=" /ocr/alto-xml/ ")).create_records(INSERT)

        self.assertEqual(records[0].distribution_name, "ocr/alto-xml")

    def test_does_not_modify_database(self):
        """create_records() nesmí změnit databázový záznam souboru ani počet souborů."""
        pocet_pred = Soubor.objects.count()

        DistribuceMapper(self._row(nazev="jiny.xml")).create_records(UPDATE)

        self.assertEqual(Soubor.objects.count(), pocet_pred)
        self.assertEqual(Soubor.objects.get(pk=self.soubor.pk).nazev, self.soubor.nazev)

    def test_delete_returns_soubor_without_deleting_it(self):
        """Ani DELETE nesmaže soubor – distribuce se maže jen ve Fedoře."""
        records = DistribuceMapper({"id": f"soub-{self.soubor.pk}", "distribution": "ocr/alto-xml"}).create_records(
            DELETE
        )

        self.assertEqual(records[0].pk, self.soubor.pk)
        self.assertTrue(Soubor.objects.filter(pk=self.soubor.pk).exists())


class DistribuceMapperHistoryTargetsTest(TestCase):
    """Testy cílů historie a aktualizace metadat po importu distribuce."""

    @classmethod
    def setUpTestData(cls):
        """Vytvoří dokument a soubor pro dotazy na cíle historie a metadat."""
        cls.dokument = create_dokument_fixture(ident_cely="C-TX-DIST-004")
        cls.soubor = create_soubor_fixture(cls.dokument)

    def test_history_target_is_soubor(self):
        """Historie distribuce se zapisuje přímo k souboru."""
        self.assertIs(DistribuceMapper.get_record_history(self.soubor), self.soubor)

    def test_metadata_target_is_related_record(self):
        """Metadata se po importu distribuce obnovují u navázaného záznamu."""
        targets = DistribuceMapper.fedora_update_targets(self.soubor)

        self.assertEqual(targets, {(self.dokument.__class__, self.dokument.pk)})


class DistribuceMapperBatchCollisionTest(TestCase):
    """Testy dávkové kontroly křížení názvů distribucí v cestě (předko-potomk vztah)."""

    @staticmethod
    def _row(soubor_id, distribution):
        """Sestaví surový řádek dávky pro daný soubor a distribuci."""
        return {"id": soubor_id, "nazev": "x", "mimetype": "text/xml", "distribution": distribution}

    def test_no_collision_passes(self):
        """Sourozenecké i nesouvisející názvy projdou bez kolize."""
        payloads = [
            self._row("soub-1", "ocr"),
            self._row("soub-1", "alto-xml"),
            self._row("soub-1", "ocr-alto"),
        ]
        DistribuceMapper.validate_batch_ordering(payloads)

    def test_prefix_collision_rejected(self):
        """Název i jeho potomek pro tentýž soubor se odmítnou."""
        payloads = [self._row("soub-1", "ocr"), self._row("soub-1", "ocr/alto-xml")]
        with self.assertRaises(ImportDataDistributionPrefixCollisionError) as ctx:
            DistribuceMapper.validate_batch_ordering(payloads)
        self.assertEqual(ctx.exception.ancestor, "ocr")
        self.assertEqual(ctx.exception.descendant, "ocr/alto-xml")
        self.assertEqual(ctx.exception.soubor_ref, "soub-1")

    def test_collision_only_within_same_soubor(self):
        """Stejný název a jeho potomek pro různé soubory nekolizí – jmenný prostor je per soubor."""
        payloads = [self._row("soub-1", "ocr"), self._row("soub-2", "ocr/alto-xml")]
        DistribuceMapper.validate_batch_ordering(payloads)

    def test_whitespace_and_slashes_normalized_before_check(self):
        """Název se normalizuje, takže ``/ ocr /`` kolize s ``ocr/alto-xml`` zachytí."""
        payloads = [self._row("soub-1", " /ocr/ "), self._row("soub-1", "ocr/alto-xml")]
        with self.assertRaises(ImportDataDistributionPrefixCollisionError):
            DistribuceMapper.validate_batch_ordering(payloads)

    def test_empty_or_missing_distribution_ignored(self):
        """Řádky bez názvu distribize neúčastní kontroly a nevyvolají kolizi."""
        payloads = [
            self._row("soub-1", "ocr"),
            {"id": "soub-1", "nazev": "x", "mimetype": "text/xml", "distribution": ""},
            {"id": "soub-1", "nazev": "x", "mimetype": "text/xml"},
        ]
        DistribuceMapper.validate_batch_ordering(payloads)

    def test_paradata_inherits_collision_check(self):
        """ParadataMapper dědí kontrolu a sdružuje názvy podle sloupce ``path``."""
        payloads = [
            {"path": "/rest/AMCR/record/C-1/file/uuid-1", "distribution": "ocr"},
            {"path": "/rest/AMCR/record/C-1/file/uuid-1", "distribution": "ocr/alto-xml"},
        ]
        with self.assertRaises(ImportDataDistributionPrefixCollisionError):
            ParadataMapper.validate_batch_ordering(payloads)

    def test_paradata_no_collision_across_paths(self):
        """Paradata pro různé soubory se stejným názvem a potomkem nekolizí."""
        payloads = [
            {"path": "/rest/AMCR/record/C-1/file/uuid-1", "distribution": "ocr"},
            {"path": "/rest/AMCR/record/C-1/file/uuid-2", "distribution": "ocr/alto-xml"},
        ]
        ParadataMapper.validate_batch_ordering(payloads)
