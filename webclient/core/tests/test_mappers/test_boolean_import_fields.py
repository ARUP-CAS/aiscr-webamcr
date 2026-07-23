from core.constants import DOKUMENT_CAST_RELATION_TYPE
from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    BooleanImportField,
    DokumentacniJednotkaMapper,
    ImportDataError,
    KomponentaMapper,
    OrganizaceMapper,
    SamostatnyNalezMapper,
    UzivatelMapper,
)
from core.tests.test_mappers.fixtures import create_dokument_fixture
from django.db import models
from django.test import SimpleTestCase, TestCase
from dokument.models import DokumentCast
from komponenta.models import KomponentaVazby

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT

BOOLEAN_MAPPER_CASES = (
    (OrganizaceMapper, ("oao", "zanikla", "cteni_dokumentu")),
    (SamostatnyNalezMapper, ("predano",)),
    (DokumentacniJednotkaMapper, ("negativni_jednotka",)),
    (KomponentaMapper, ("jistota",)),
    (UzivatelMapper, ("is_active", "is_staff", "is_superuser")),
)

BOOLEAN_VALUE_CASES = (
    ("0", False),
    (0, False),
    ("1", True),
    (1, True),
    # Access exports checked Yes/No fields as -1.
    ("-1", True),
    (-1, True),
)

INVALID_BOOLEAN_VALUES = ("", None, "2", 2, "yes", "no")


def _boolean_fields_for_mapper(mapper_class):
    """Vrátí BooleanField sloupce přímo z metadat modelu mapperu."""
    boolean_fields = []
    for field_name in mapper_class.fields:
        model_field_name = mapper_class.column_to_field_mapping.get(field_name, field_name)
        if model_field_name not in mapper_class.model_class._meta._forward_fields_map:
            continue
        model_field = mapper_class.model_class._meta.get_field(model_field_name)
        if isinstance(model_field, models.BooleanField):
            boolean_fields.append(field_name)
    return tuple(boolean_fields)


def _row_for_mapper(mapper_class, boolean_field, raw_value, extra_values=None):
    """Sestaví kompletní minimální řádek pro map() a create_records()."""
    row = {field_name: None for field_name in mapper_class.get_mapping(include_primary_key=True)}
    row.update(extra_values or {})
    if isinstance(mapper_class.primary_key, str):
        row[mapper_class.primary_key] = f"{mapper_class.__name__}-BOOL-001"
    else:
        for primary_key in mapper_class.primary_key:
            row[primary_key] = f"{mapper_class.__name__}-{primary_key}-BOOL-001"
    for field_name in _boolean_fields_for_mapper(mapper_class):
        row[field_name] = "0"
    row[boolean_field] = raw_value
    return row


class BooleanImportFieldsTest(TestCase):
    """Testy importního mapování BooleanField hodnot."""

    def setUp(self):
        """Vytvoří minimální vazbu potřebnou pro KomponentaMapper."""
        dokument = create_dokument_fixture("C-TX-000000001")
        komponenta_vazby = KomponentaVazby.objects.create(typ_vazby=DOKUMENT_CAST_RELATION_TYPE)
        self.dokument_cast = DokumentCast(
            ident_cely=f"{dokument.ident_cely}-D001",
            dokument=dokument,
            komponenty=komponenta_vazby,
        )
        self.dokument_cast.suppress_signal = True
        self.dokument_cast.save()

    def _extra_values_for_mapper(self, mapper_class):
        if mapper_class == KomponentaMapper:
            return {"vazba": self.dokument_cast.ident_cely}
        return {}

    def test_boolean_mapper_cases_cover_all_mapper_boolean_fields(self):
        """Seznam testovaných polí odpovídá BooleanField polím registrovaných mapperů."""
        for mapper_class, expected_fields in BOOLEAN_MAPPER_CASES:
            with self.subTest(mapper=mapper_class.__name__):
                self.assertEqual(_boolean_fields_for_mapper(mapper_class), expected_fields)

    def test_boolean_values_map_to_expected_bool(self):
        """map() akceptuje textové i číselné 0/1/-1 hodnoty pro všechna BooleanField pole."""
        for mapper_class, boolean_fields in BOOLEAN_MAPPER_CASES:
            for boolean_field in boolean_fields:
                for raw_value, expected_value in BOOLEAN_VALUE_CASES:
                    with self.subTest(
                        mapper=mapper_class.__name__,
                        field=boolean_field,
                        raw_value=raw_value,
                    ):
                        mapper = mapper_class(
                            _row_for_mapper(
                                mapper_class,
                                boolean_field,
                                raw_value,
                                self._extra_values_for_mapper(mapper_class),
                            )
                        )
                        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
                        self.assertIn(boolean_field, result)
                        self.assertIs(result[boolean_field], expected_value)

    def test_boolean_values_create_records_with_expected_bool(self):
        """create_records() nastaví správnou bool hodnotu na vytvářené instanci."""
        for mapper_class, boolean_fields in BOOLEAN_MAPPER_CASES:
            for boolean_field in boolean_fields:
                model_field_name = mapper_class.column_to_field_mapping.get(boolean_field, boolean_field)
                for raw_value, expected_value in BOOLEAN_VALUE_CASES:
                    with self.subTest(
                        mapper=mapper_class.__name__,
                        field=boolean_field,
                        raw_value=raw_value,
                    ):
                        mapper = mapper_class(
                            _row_for_mapper(
                                mapper_class,
                                boolean_field,
                                raw_value,
                                self._extra_values_for_mapper(mapper_class),
                            )
                        )
                        records = mapper.create_records(INSERT)
                        self.assertEqual(len(records), 1)
                        record = records[0]
                        self.assertIsInstance(record, mapper_class.model_class)
                        self.assertIs(getattr(record, model_field_name), expected_value)

    def test_invalid_boolean_values_raise_error(self):
        """map() odmítá nepodporované boolean hodnoty pro všechna BooleanField pole."""
        for mapper_class, boolean_fields in BOOLEAN_MAPPER_CASES:
            for boolean_field in boolean_fields:
                for raw_value in INVALID_BOOLEAN_VALUES:
                    with self.subTest(
                        mapper=mapper_class.__name__,
                        field=boolean_field,
                        raw_value=raw_value,
                    ):
                        mapper = mapper_class(
                            _row_for_mapper(
                                mapper_class,
                                boolean_field,
                                raw_value,
                                self._extra_values_for_mapper(mapper_class),
                            )
                        )
                        with self.assertRaises(ImportDataError):
                            mapper.map(INSERT, serialize=True, include_primary_key=True)


class BooleanImportFieldPandasCoercionTest(SimpleTestCase):
    """Testy BooleanImportField pro hodnoty vzniklé pandas koercí bez dtype=str."""

    def test_float_1_0_parsed_as_true(self):
        """'1.0' (pandas koerce True v nullable sloupci) se přijme jako True."""
        field = BooleanImportField()
        field.value = "1.0"
        self.assertIs(field.value, True)

    def test_float_0_0_parsed_as_false(self):
        """'0.0' (pandas koerce False v nullable sloupci) se přijme jako False."""
        field = BooleanImportField()
        field.value = "0.0"
        self.assertIs(field.value, False)

    def test_native_float_1_0_parsed_as_true(self):
        """Nativní float 1.0 se přijme jako True."""
        field = BooleanImportField()
        field.value = 1.0
        self.assertIs(field.value, True)

    def test_native_float_0_0_parsed_as_false(self):
        """Nativní float 0.0 se přijme jako False."""
        field = BooleanImportField()
        field.value = 0.0
        self.assertIs(field.value, False)
