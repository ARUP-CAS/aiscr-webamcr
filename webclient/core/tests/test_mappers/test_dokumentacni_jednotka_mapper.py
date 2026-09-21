from unittest.mock import MagicMock, patch

from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DokumentacniJednotkaMapper,
    ImportDataIncorrectStructureError,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "C-AZ-999999999-D01",
    "negativni_jednotka": "false",
    "nazev": "Test DJ",
    "archeologicky_zaznam": "C-AZ-999999999",
    "pian": "PIAN-C-000001",
    "typ": "HES-DJTYP-001",
}


class DokumentacniJednotkaMapperInvalidStructureTest(TestCase):
    """Testy pro DokumentacniJednotkaMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = DokumentacniJednotkaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = DokumentacniJednotkaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_archeologicky_zaznam_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci archeologicky_zaznam."""
        row = VALID_ROW.copy()
        del row["archeologicky_zaznam"]
        mapper = DokumentacniJednotkaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_typ_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci typ."""
        row = VALID_ROW.copy()
        del row["typ"]
        mapper = DokumentacniJednotkaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = DokumentacniJednotkaMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_unknown_column_in_update_raises_error(self):
        """_check_column_structure() UPDATE vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = DokumentacniJednotkaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper._check_column_structure(UPDATE, include_primary_key=True)


class DokumentacniJednotkaMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro DokumentacniJednotkaMapper.check_required_fields — bez DB."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        from core.import_data_mappers import ImportDataError

        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = DokumentacniJednotkaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_archeologicky_zaznam_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je archeologicky_zaznam None."""
        from core.import_data_mappers import ImportDataError

        row = VALID_ROW.copy()
        row["archeologicky_zaznam"] = None
        mapper = DokumentacniJednotkaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_typ_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je typ None (not null FK)."""
        from core.import_data_mappers import ImportDataError

        row = VALID_ROW.copy()
        row["typ"] = None
        mapper = DokumentacniJednotkaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_nazev_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je nazev None (nullable pole)."""
        row = VALID_ROW.copy()
        row["nazev"] = None
        mapper = DokumentacniJednotkaMapper(row)
        mapper.check_required_fields(INSERT)

    def test_pian_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je pian None (nullable FK)."""
        row = VALID_ROW.copy()
        row["pian"] = None
        mapper = DokumentacniJednotkaMapper(row)
        mapper.check_required_fields(INSERT)


class DokumentacniJednotkaMapperRecordPostprocessingTest(TestCase):
    """Testy pro DokumentacniJednotkaMapper.record_postprocessing — guard TYP_DJ_KATASTR."""

    def _make_record(self, typ_id, existing_katastr_pian=None):
        """Sestaví mock DokumentacniJednotka se zadaným typem a pianem katastru."""
        record = MagicMock()
        record.typ.id = typ_id
        record.archeologicky_zaznam.hlavni_katastr.pian = existing_katastr_pian
        return record

    def test_katastr_typ_with_existing_pian_sets_pian(self):
        """Pro TYP_DJ_KATASTR s existujícím pianem katastru se record.pian nastaví na tento pian."""
        from heslar.hesla_dynamicka import TYP_DJ_KATASTR

        existing_pian = MagicMock()
        record = self._make_record(TYP_DJ_KATASTR, existing_katastr_pian=existing_pian)

        DokumentacniJednotkaMapper.record_postprocessing(record, INSERT, MagicMock())

        self.assertIs(record.pian, existing_pian)

    def test_katastr_typ_without_pian_creates_pian(self):
        """Pro TYP_DJ_KATASTR bez pianu katastru se volá vytvor_pian a výsledek se přiřadí."""
        from heslar.hesla_dynamicka import TYP_DJ_KATASTR

        record = self._make_record(TYP_DJ_KATASTR, existing_katastr_pian=None)
        new_pian = MagicMock()

        with patch("core.import_data_mappers.vytvor_pian", return_value=new_pian) as mock_vytvor:
            DokumentacniJednotkaMapper.record_postprocessing(record, INSERT, MagicMock())

        mock_vytvor.assert_called_once()
        self.assertIs(record.pian, new_pian)

    def test_non_katastr_typ_does_not_set_pian(self):
        """Pro jiný typ DJ než TYP_DJ_KATASTR se record.pian nesmí přepsat."""
        from heslar.hesla_dynamicka import TYP_DJ_KATASTR

        non_katastr_id = TYP_DJ_KATASTR + 1
        record = self._make_record(non_katastr_id)
        original_pian = record.pian

        with patch("core.import_data_mappers.vytvor_pian") as mock_vytvor:
            DokumentacniJednotkaMapper.record_postprocessing(record, INSERT, MagicMock())

        mock_vytvor.assert_not_called()
        self.assertIs(record.pian, original_pian)

    def test_non_katastr_typ_on_update_does_not_set_pian(self):
        """Pro jiný typ DJ při UPDATE se record.pian rovněž nesmí přepsat."""
        from heslar.hesla_dynamicka import TYP_DJ_KATASTR

        non_katastr_id = TYP_DJ_KATASTR + 1
        record = self._make_record(non_katastr_id)
        original_pian = record.pian

        with patch("core.import_data_mappers.vytvor_pian") as mock_vytvor:
            DokumentacniJednotkaMapper.record_postprocessing(record, UPDATE, MagicMock())

        mock_vytvor.assert_not_called()
        self.assertIs(record.pian, original_pian)
