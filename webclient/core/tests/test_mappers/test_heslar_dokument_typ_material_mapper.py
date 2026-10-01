from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    HeslarDokumentTypMaterialMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataIntegrityError,
)
from django.test import TestCase
from heslar.hesla import HESLAR_DOKUMENT_MATERIAL, HESLAR_DOKUMENT_TYP
from heslar.models import Heslar, HeslarDokumentTypMaterial, HeslarNazev

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "dokument_typ": "HES-DOCTYPE-001",
    "dokument_material": "HES-MAT-001",
}


def _create_fixtures():
    """Vytvoří testovací data HeslarNazev a Heslar pro FK pole v HeslarDokumentTypMaterialMapper.

    :return: Dvojici (heslar_typ, heslar_material) — uložené instance Heslar.
    """
    hn_typ = HeslarNazev.objects.get_or_create(pk=HESLAR_DOKUMENT_TYP, defaults={"nazev": "Dokument typ"})[0]
    hn_material = HeslarNazev.objects.get_or_create(
        pk=HESLAR_DOKUMENT_MATERIAL, defaults={"nazev": "Dokument material"}
    )[0]

    heslar_typ = Heslar.objects.get_or_create(
        ident_cely="HES-DOCTYPE-001",
        defaults={"heslo": "Fotodokumentace", "heslo_en": "Photodocumentation", "nazev_heslare": hn_typ},
    )[0]
    heslar_material = Heslar.objects.get_or_create(
        ident_cely="HES-MAT-001",
        defaults={"heslo": "Digitální", "heslo_en": "Digital", "nazev_heslare": hn_material},
    )[0]

    return heslar_typ, heslar_material


class HeslarDokumentTypMaterialMapperInsertValidTest(TestCase):
    """Testy pro HeslarDokumentTypMaterialMapper — platný dataset (INSERT)."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro platný INSERT dataset."""
        self.heslar_typ, self.heslar_material = _create_fixtures()

    def test_map_returns_dict(self):
        """map() vrátí slovník."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_dokument_typ_serialized_as_ident_cely(self):
        """map() vrátí serializovanou hodnotu dokument_typ jako řetězec ident_cely."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["dokument_typ"], "HES-DOCTYPE-001")

    def test_map_dokument_material_serialized_as_ident_cely(self):
        """map() vrátí serializovanou hodnotu dokument_material jako řetězec ident_cely."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["dokument_material"], "HES-MAT-001")

    def test_map_dokument_typ_instance_value(self):
        """map() s instance_values=True vrátí instanci Heslar pro pole dokument_typ."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, instance_values=True, serialize=False, include_primary_key=True)
        self.assertIsInstance(result["dokument_typ"], Heslar)
        self.assertEqual(result["dokument_typ"].ident_cely, "HES-DOCTYPE-001")

    def test_map_includes_all_expected_keys(self):
        """map() vrátí klíče dokument_typ, dokument_material (bez id, require_primary_key_value=False)."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = {"dokument_typ", "dokument_material"}
        self.assertEqual(set(result.keys()), expected_keys)


class HeslarDokumentTypMaterialMapperInvalidStructureTest(TestCase):
    """Testy pro HeslarDokumentTypMaterialMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = HeslarDokumentTypMaterialMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_dokument_typ_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci dokument_typ."""
        row = VALID_ROW.copy()
        del row["dokument_typ"]
        mapper = HeslarDokumentTypMaterialMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_dokument_material_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci dokument_material."""
        row = VALID_ROW.copy()
        del row["dokument_material"]
        mapper = HeslarDokumentTypMaterialMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_value_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = HeslarDokumentTypMaterialMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_id_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím id."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)

    def test_update_excess_column_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při nadbytečném sloupci."""
        row = VALID_ROW.copy()
        row["id"] = "hdtm-1"
        row["extra"] = "hodnota"
        mapper = HeslarDokumentTypMaterialMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class HeslarDokumentTypMaterialMapperCreateRecordsTest(TestCase):
    """Testy pro HeslarDokumentTypMaterialMapper.create_records — akce INSERT."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy create_records INSERT."""
        self.heslar_typ, self.heslar_material = _create_fixtures()

    def test_create_records_returns_list_with_one_instance(self):
        """create_records() vrátí seznam s jednou instancí HeslarDokumentTypMaterial."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertEqual(len(records), 1)
        self.assertIsInstance(records[0], HeslarDokumentTypMaterial)

    def test_create_records_instance_not_saved(self):
        """create_records() vrátí neperzistovanou instanci (bez pk)."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        records = mapper.create_records(INSERT)
        self.assertIsNone(records[0].pk)

    def test_create_records_dokument_typ_resolved(self):
        """create_records() nastaví dokument_typ jako instanci Heslar."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        vazba = mapper.create_records(INSERT)[0]
        self.assertIsInstance(vazba.dokument_typ, Heslar)
        self.assertEqual(vazba.dokument_typ.ident_cely, "HES-DOCTYPE-001")

    def test_create_records_dokument_material_resolved(self):
        """create_records() nastaví dokument_material jako instanci Heslar."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        vazba = mapper.create_records(INSERT)[0]
        self.assertIsInstance(vazba.dokument_material, Heslar)
        self.assertEqual(vazba.dokument_material.ident_cely, "HES-MAT-001")


class HeslarDokumentTypMaterialMapperImportValidationTest(TestCase):
    """Testy pro HeslarDokumentTypMaterialMapper.import_validation."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy import_validation."""
        self.heslar_typ, self.heslar_material = _create_fixtures()
        self.vazba = HeslarDokumentTypMaterial.objects.create(
            dokument_typ=self.heslar_typ,
            dokument_material=self.heslar_material,
        )

    def test_insert_without_id_returns_none(self):
        """import_validation() INSERT bez id vrátí None (require_primary_key_value není True pro string pk bez hodnoty)."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        result = mapper.import_validation(INSERT)
        self.assertIsNone(result)

    def test_update_existing_record_returns_primary_key_dict(self):
        """import_validation() UPDATE vrátí slovník s id pro existující záznam."""
        row = VALID_ROW.copy()
        row["id"] = f"hdtm-{self.vazba.pk}"
        mapper = HeslarDokumentTypMaterialMapper(row)
        result = mapper.import_validation(UPDATE)
        self.assertEqual(result, {"id": self.vazba.pk})

    def test_update_missing_record_raises_integrity_error(self):
        """import_validation() UPDATE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["id"] = "hdtm-999999"
        mapper = HeslarDokumentTypMaterialMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(UPDATE)

    def test_delete_existing_record_returns_primary_key_dict(self):
        """import_validation() DELETE vrátí slovník s id pro existující záznam."""
        row = VALID_ROW.copy()
        row["id"] = f"hdtm-{self.vazba.pk}"
        mapper = HeslarDokumentTypMaterialMapper(row)
        result = mapper.import_validation(DELETE)
        self.assertEqual(result, {"id": self.vazba.pk})

    def test_delete_missing_record_raises_integrity_error(self):
        """import_validation() DELETE vyvolá ImportDataIntegrityError, pokud záznam neexistuje."""
        row = VALID_ROW.copy()
        row["id"] = "hdtm-999999"
        mapper = HeslarDokumentTypMaterialMapper(row)
        with self.assertRaises(ImportDataIntegrityError):
            mapper.import_validation(DELETE)


class HeslarDokumentTypMaterialMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro HeslarDokumentTypMaterialMapper.check_required_fields."""

    def setUp(self):
        """Vytvoří testovací data HeslarNazev a Heslar pro testy check_required_fields."""
        _create_fixtures()

    def test_valid_row_passes(self):
        """check_required_fields() projde bez výjimky pro kompletní platný řádek."""
        mapper = HeslarDokumentTypMaterialMapper(VALID_ROW.copy())
        mapper.check_required_fields(INSERT)

    def test_dokument_typ_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je dokument_typ None (not null FK)."""
        row = VALID_ROW.copy()
        row["dokument_typ"] = None
        mapper = HeslarDokumentTypMaterialMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_dokument_material_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je dokument_material None (not null FK)."""
        row = VALID_ROW.copy()
        row["dokument_material"] = None
        mapper = HeslarDokumentTypMaterialMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
