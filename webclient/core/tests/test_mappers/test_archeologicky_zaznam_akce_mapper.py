from unittest.mock import patch

from arch_z.models import Akce, ArcheologickyZaznam
from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ArcheologickyZaznamAkceMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
)
from cron.tests._import_test_fixtures import (
    create_akce,
    create_archeologicky_zaznam,
    create_heslar_fixtures,
    create_ruian_with_pian,
    create_specifikace_data,
)
from django.test import TestCase
from projekt.models import Projekt

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "ident_cely": "C-202401-000001A",
    "stav": "1",
    "typ": "N",
    "projekt": None,
    "pristupnost": "HES-PRIST-001",
    "hlavni_katastr": "123456",
    "uzivatelske_oznaceni": None,
    "lokalizace_okolnosti": None,
    "je_nz": "false",
    "odlozena_nz": "false",
    "hlavni_vedouci": None,
    "organizace": None,
    "specifikace_data": "HES-SPECDAT-001",
    "datum_zahajeni": None,
    "datum_ukonceni": None,
    "hlavni_typ": None,
    "vedlejsi_typ": None,
    "ulozeni_nalezu": None,
    "ulozeni_dokumentace": None,
    "souhrn_upresneni": None,
}

MAP_SAFE_ROW = {
    "ident_cely": "C-202401-000001A",
    "stav": "1",
    "typ": None,
    "projekt": None,
    "pristupnost": None,
    "hlavni_katastr": None,
    "uzivatelske_oznaceni": None,
    "lokalizace_okolnosti": None,
    "je_nz": "false",
    "odlozena_nz": "false",
    "hlavni_vedouci": None,
    "organizace": None,
    "specifikace_data": None,
    "datum_zahajeni": None,
    "datum_ukonceni": None,
    "hlavni_typ": None,
    "vedlejsi_typ": None,
    "ulozeni_nalezu": None,
    "ulozeni_dokumentace": None,
    "souhrn_upresneni": None,
}


class ArcheologickyZaznamAkceMapperInvalidStructureTest(TestCase):
    """Testy pro ArcheologickyZaznamAkceMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ArcheologickyZaznamAkceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = ArcheologickyZaznamAkceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ArcheologickyZaznamAkceMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class ArcheologickyZaznamAkceMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ArcheologickyZaznamAkceMapper.check_required_fields — bez DB."""

    def test_stav_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je stav None (not null)."""
        row = VALID_ROW.copy()
        row["stav"] = None
        mapper = ArcheologickyZaznamAkceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = ArcheologickyZaznamAkceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_je_nz_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je je_nz None (má výchozí hodnotu)."""
        row = VALID_ROW.copy()
        row["je_nz"] = None
        mapper = ArcheologickyZaznamAkceMapper(row)
        mapper.check_required_fields(INSERT)

    def test_uzivatelske_oznaceni_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je uzivatelske_oznaceni None (nullable pole)."""
        row = VALID_ROW.copy()
        row["uzivatelske_oznaceni"] = None
        mapper = ArcheologickyZaznamAkceMapper(row)
        mapper.check_required_fields(INSERT)


class ArcheologickyZaznamAkceMapperMapValidTest(TestCase):
    """Testy pro ArcheologickyZaznamAkceMapper — platný dataset pro map()."""

    def test_map_returns_dict(self):
        """map() vrátí slovník pro platný řádek."""
        mapper = ArcheologickyZaznamAkceMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_includes_all_expected_keys(self):
        """map() vrátí všechny očekávané klíče."""
        mapper = ArcheologickyZaznamAkceMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = {
            "ident_cely",
            "stav",
            "typ",
            "projekt",
            "pristupnost",
            "hlavni_katastr",
            "uzivatelske_oznaceni",
            "lokalizace_okolnosti",
            "je_nz",
            "odlozena_nz",
            "hlavni_vedouci",
            "organizace",
            "specifikace_data",
            "datum_zahajeni",
            "datum_ukonceni",
            "hlavni_typ",
            "vedlejsi_typ",
            "ulozeni_nalezu",
            "ulozeni_dokumentace",
            "souhrn_upresneni",
        }
        self.assertEqual(set(result.keys()), expected_keys)


class ArcheologickyZaznamAkceMapperImportValidationTest(TestCase):
    """Testy pro ArcheologickyZaznamAkceMapper.import_validation."""

    def test_import_validation_rejects_samostatna_akce_with_project(self):
        """import_validation() odmítne ``typ=N`` s vyplněným projektem."""
        row = MAP_SAFE_ROW.copy()
        row["typ"] = Akce.TYP_AKCE_SAMOSTATNA
        row["projekt"] = "C-202300001"
        mapper = ArcheologickyZaznamAkceMapper(row)

        with self.assertRaisesRegex(
            ImportDataError, "core_admin.ImportDataError.message.akce_typ_check.typ_n_requires_empty_projekt"
        ):
            mapper.import_validation(INSERT)

    def test_import_validation_rejects_projektova_akce_without_project(self):
        """import_validation() odmítne ``typ=R`` bez projektu."""
        row = MAP_SAFE_ROW.copy()
        row["typ"] = Akce.TYP_AKCE_PROJEKTOVA
        row["projekt"] = None
        mapper = ArcheologickyZaznamAkceMapper(row)

        with self.assertRaisesRegex(
            ImportDataError, "core_admin.ImportDataError.message.akce_typ_check.typ_r_requires_filled_projekt"
        ):
            mapper.import_validation(INSERT)


class ArcheologickyZaznamAkceMapperRecordPostprocessingTest(TestCase):
    """Testy pro ArcheologickyZaznamAkceMapper.record_postprocessing — bez DB."""

    def test_insert_sets_typ_zaznamu_akce(self):
        """record_postprocessing() nastaví typ_zaznamu na TYP_ZAZNAMU_AKCE při INSERT pro ArcheologickyZaznam."""
        az = ArcheologickyZaznam()
        ArcheologickyZaznamAkceMapper.record_postprocessing(az, INSERT, None)
        self.assertEqual(az.typ_zaznamu, ArcheologickyZaznam.TYP_ZAZNAMU_AKCE)

    def test_update_does_not_set_typ_zaznamu(self):
        """record_postprocessing() nenastaví typ_zaznamu při UPDATE pro ArcheologickyZaznam."""
        az = ArcheologickyZaznam()
        original_typ = az.typ_zaznamu
        ArcheologickyZaznamAkceMapper.record_postprocessing(az, UPDATE, None)
        self.assertEqual(az.typ_zaznamu, original_typ)

    def test_non_az_record_not_modified(self):
        """record_postprocessing() nemodifikuje záznam, který není instancí ArcheologickyZaznam."""
        akce = Akce()
        # Akce nemá atribut typ_zaznamu, postprocessing by neměl vyvolat výjimku
        ArcheologickyZaznamAkceMapper.record_postprocessing(akce, INSERT, None)


class ArcheologickyZaznamAkceMapperGetRecordHistoryTest(TestCase):
    """Testy pro ArcheologickyZaznamAkceMapper.get_record_history — bez DB."""

    def test_az_returns_itself(self):
        """get_record_history() vrátí přímo ArcheologickyZaznam, pokud je předán jako záznam."""
        az = ArcheologickyZaznam()
        result = ArcheologickyZaznamAkceMapper.get_record_history(az)
        self.assertIs(result, az)

    def test_akce_returns_az(self):
        """get_record_history() vrátí archeologicky_zaznam navázaný na Akce."""
        az = ArcheologickyZaznam()
        akce = Akce()
        akce.archeologicky_zaznam = az
        result = ArcheologickyZaznamAkceMapper.get_record_history(akce)
        self.assertIs(result, az)


class ArcheologickyZaznamAkceMapperGetUpdatedIdentCelyTest(TestCase):
    """Testy pro ArcheologickyZaznamAkceMapper._get_updated_ident_cely_record_list — bez DB."""

    def test_akce_returns_az_and_projekt(self):
        """_get_updated_ident_cely_record_list() vrátí [archeologicky_zaznam, projekt] pro Akce."""
        az = ArcheologickyZaznam()
        projekt = Projekt()
        akce = Akce()
        akce.archeologicky_zaznam = az
        akce.projekt = projekt
        result = ArcheologickyZaznamAkceMapper._get_updated_ident_cely_record_list(akce)
        self.assertEqual(result, [az, projekt])


class ArcheologickyZaznamAkceMapperCreateRecordsDeleteTest(TestCase):
    """Testy pro ArcheologickyZaznamAkceMapper.create_records — akce DELETE."""

    AZ_IDENT = "C-202401-DEL-001A"

    @classmethod
    def setUpTestData(cls):
        """Vytvoří testovací ArcheologickyZaznam a Akce v DB."""
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            heslars = create_heslar_fixtures("azakce_del")
            katastr, _ = create_ruian_with_pian("azakce_del", "P-AZ-AK-DEL-001", heslars)
            specifikace_data = create_specifikace_data("azakce_del")
            az = create_archeologicky_zaznam(cls.AZ_IDENT, katastr, heslars["pristupnost"])
            cls.az = az
            cls.akce = create_akce(az, specifikace_data=specifikace_data)

    def _delete_row(self):
        return {"ident_cely": self.AZ_IDENT}

    def test_create_records_delete_returns_two_records(self):
        """create_records(DELETE) vrátí seznam dvou záznamů [Akce, ArcheologickyZaznam]."""
        mapper = ArcheologickyZaznamAkceMapper(self._delete_row())
        result = mapper.create_records(DELETE)
        self.assertEqual(len(result), 2)

    def test_create_records_delete_first_record_is_akce(self):
        """create_records(DELETE) vrátí Akce jako první — child se maže před parentem."""
        mapper = ArcheologickyZaznamAkceMapper(self._delete_row())
        result = mapper.create_records(DELETE)
        self.assertIsInstance(result[0], Akce)

    def test_create_records_delete_second_record_is_az(self):
        """create_records(DELETE) vrátí ArcheologickyZaznam jako druhý."""
        mapper = ArcheologickyZaznamAkceMapper(self._delete_row())
        result = mapper.create_records(DELETE)
        self.assertIsInstance(result[1], ArcheologickyZaznam)

    def test_create_records_delete_az_has_correct_ident_cely(self):
        """ArcheologickyZaznam v result má ident_cely shodné se vstupem."""
        mapper = ArcheologickyZaznamAkceMapper(self._delete_row())
        result = mapper.create_records(DELETE)
        self.assertEqual(result[1].ident_cely, self.AZ_IDENT)
