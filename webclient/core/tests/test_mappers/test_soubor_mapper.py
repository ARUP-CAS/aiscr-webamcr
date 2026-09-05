from unittest.mock import MagicMock, patch

from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataFileExtensionNotAllowedError,
    ImportDataIncorrectStructureError,
    SouborImportIntegrityError,
    SouborMapper,
)
from django.test import TestCase
from dokument.models import Dokument
from pas.models import SamostatnyNalez

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "nazev": "dokument.pdf",
    "vazba": "C-AZ-999999999",
}


class SouborMapperInvalidStructureTest(TestCase):
    """Testy pro SouborMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = SouborMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_nazev_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci nazev."""
        row = VALID_ROW.copy()
        del row["nazev"]
        mapper = SouborMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_vazba_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci vazba."""
        row = VALID_ROW.copy()
        del row["vazba"]
        mapper = SouborMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = SouborMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_id_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError, pokud chybí primární klíč id."""
        mapper = SouborMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class SouborMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro SouborMapper.check_required_fields — bez DB."""

    def test_nazev_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je nazev None (not null pole)."""
        row = VALID_ROW.copy()
        row["nazev"] = None
        mapper = SouborMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)


class SouborMapperImportValidationSeenInBatchTest(TestCase):
    """Testy pro SouborMapper.import_validation — detekce duplikátů v rámci jedné dávky."""

    def _make_mapper(self, nazev, vazba_pk):
        """Vytvoří SouborMapper s namockovaným map() vracejícím daný nazev a SouborVazby s daným pk."""
        mock_vazba = MagicMock()
        mock_vazba.pk = vazba_pk
        mapper = SouborMapper(VALID_ROW.copy())
        mapper.map = MagicMock(return_value={"nazev": nazev, "vazba": mock_vazba})
        return mapper

    @patch("core.import_data_mappers.Soubor.objects")
    def test_first_occurrence_returns_dict_and_adds_to_batch(self, mock_objects):
        """import_validation() INSERT vrátí slovník a přidá klíč do seen_in_batch.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        seen = set()
        result = self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=seen)
        self.assertIsInstance(result, dict)
        self.assertIn(("test.pdf", 1), seen)

    @patch("core.import_data_mappers.Soubor.objects")
    def test_duplicate_in_batch_raises_integrity_error(self, mock_objects):
        """import_validation() INSERT vyvolá SouborImportIntegrityError pro druhý řádek se shodným nazev+vazba.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        seen = set()
        self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=seen)
        with self.assertRaises(SouborImportIntegrityError):
            self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=seen)

    @patch("core.import_data_mappers.Soubor.objects")
    def test_same_name_different_vazba_does_not_raise(self, mock_objects):
        """import_validation() INSERT nehlásí chybu pro shodný nazev s jinou vazbou.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        seen = set()
        self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=seen)
        result = self._make_mapper("test.pdf", 2).import_validation(INSERT, seen_in_batch=seen)
        self.assertIsInstance(result, dict)

    @patch("core.import_data_mappers.Soubor.objects")
    def test_seen_in_batch_none_skips_batch_check(self, mock_objects):
        """import_validation() INSERT s seen_in_batch=None nevyvolá chybu ani pro shodné řádky.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=None)
        result = self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=None)
        self.assertIsInstance(result, dict)


class SouborMapperExtensionWhitelistTest(TestCase):
    """Testy pro kontrolu přípony souboru proti whitelistu MIME typů navázaného záznamu — bez DB."""

    def _make_mapper(self, nazev, navazany_objekt):
        """Vytvoří SouborMapper s namockovaným map() vracejícím SouborVazby s daným navázaným objektem."""
        mock_vazba = MagicMock()
        mock_vazba.pk = 1
        mock_vazba.navazany_objekt = navazany_objekt
        mapper = SouborMapper({"nazev": nazev, "vazba": "X-IDENT"})
        mapper.map = MagicMock(return_value={"nazev": nazev, "vazba": mock_vazba})
        return mapper

    def test_disallowed_extension_for_samostatny_nalez_raises_error(self):
        """import_validation() INSERT vyvolá chybu pro textový soubor na samostatném nálezu (jen obrazové formáty)."""
        mapper = self._make_mapper("poznamka.txt", SamostatnyNalez(ident_cely="C-202400001-N00001"))
        with self.assertRaises(ImportDataFileExtensionNotAllowedError):
            mapper.import_validation(INSERT)

    @patch("core.import_data_mappers.Soubor.objects")
    def test_allowed_extension_for_samostatny_nalez_passes(self, mock_objects):
        """import_validation() INSERT projde pro obrazový soubor na samostatném nálezu.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        mapper = self._make_mapper("fotka.jpg", SamostatnyNalez(ident_cely="C-202400001-N00002"))
        result = mapper.import_validation(INSERT)
        self.assertIsInstance(result, dict)

    @patch("core.import_data_mappers.Soubor.objects")
    def test_unknown_extension_skips_check(self, mock_objects):
        """import_validation() INSERT nekontroluje příponu, kterou nelze namapovat na MIME typ.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        mapper = self._make_mapper("mracno.xyz", SamostatnyNalez(ident_cely="C-202400001-N00003"))
        result = mapper.import_validation(INSERT)
        self.assertIsInstance(result, dict)

    def test_archive_extension_for_dokument_raises_error(self):
        """import_validation() INSERT vyvolá chybu pro ZIP archiv na běžném dokumentu."""
        mapper = self._make_mapper("archiv.zip", Dokument(ident_cely="C-DL-202400001"))
        with self.assertRaises(ImportDataFileExtensionNotAllowedError):
            mapper.import_validation(INSERT)

    @patch("core.import_data_mappers.Soubor.objects")
    def test_archive_extension_for_model3d_dokument_passes(self, mock_objects):
        """import_validation() INSERT projde pro ZIP archiv na dokumentu 3D modelu.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        mapper = self._make_mapper("model.zip", Dokument(ident_cely="3D-202400001"))
        result = mapper.import_validation(INSERT)
        self.assertIsInstance(result, dict)

    def test_update_with_disallowed_extension_raises_error(self):
        """import_validation() UPDATE vyvolá chybu přípony ještě před delegací na bázovou validaci."""
        mapper = self._make_mapper("poznamka.txt", SamostatnyNalez(ident_cely="C-202400001-N00004"))
        with self.assertRaises(ImportDataFileExtensionNotAllowedError):
            mapper.import_validation(UPDATE)
