import datetime
import re
from abc import ABC
from collections.abc import Iterable
from decimal import Decimal

import pandas as pd
from adb.models import Adb, Kladysm5, VyskovyBod
from arch_z.models import Akce, AkceVedouci, ArcheologickyZaznam, ArcheologickyZaznamKatastr, ExterniOdkaz
from core.constants import DOKUMENT_RELATION_TYPE
from core.coordTransform import transform_geom_to_sjtsk, transform_geom_to_wgs84
from core.forms import ImportDataAdminForm
from core.ident_cely import get_record_from_ident, get_temp_lokalita_ident
from core.models import Soubor, SouborVazby
from dj.models import DokumentacniJednotka
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as pgmodels
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.postgres.fields import DateRangeField
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.backends.postgresql.psycopg_any import DateRange
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from dokument.models import (
    Dokument,
    DokumentAutor,
    DokumentCast,
    DokumentExtraData,
    DokumentJazyk,
    DokumentOsoba,
    DokumentPosudek,
    Let,
    Tvar,
)
from ez.models import ExterniZdroj, ExterniZdrojAutor, ExterniZdrojEditor
from heslar.hesla import (
    HESLAR_ADB_PODNET,
    HESLAR_ADB_TYP,
    HESLAR_AKCE_TYP,
    HESLAR_AKTIVITA,
    HESLAR_AREAL,
    HESLAR_DATUM_SPECIFIKACE,
    HESLAR_DJ_TYP,
    HESLAR_DOHLEDNOST,
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_NAHRADA,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_ULOZENI,
    HESLAR_DOKUMENT_ZACHOVALOST,
    HESLAR_EXTERNI_ZDROJ_TYP,
    HESLAR_JISTOTA_URCENI,
    HESLAR_LETISTE,
    HESLAR_LICENCE,
    HESLAR_LOKALITA_DRUH,
    HESLAR_LOKALITA_TYP,
    HESLAR_NALEZOVE_OKOLNOSTI,
    HESLAR_OBDOBI,
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_ORGANIZACE_TYP,
    HESLAR_PAMATKOVA_OCHRANA,
    HESLAR_PIAN_PRESNOST,
    HESLAR_PIAN_TYP,
    HESLAR_POCASI,
    HESLAR_POSUDEK_TYP,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_PRISTUPNOST,
    HESLAR_PROJEKT_TYP,
    HESLAR_STAV_DOCHOVANI,
    HESLAR_UDALOST_TYP,
    HESLAR_VYSKOVY_BOD_TYP,
    HESLAR_ZEME,
)
from heslar.models import (
    Heslar,
    HeslarDatace,
    HeslarDokumentTypMaterialRada,
    HeslarHierarchie,
    HeslarNazev,
    HeslarOdkaz,
    RuianKatastr,
    RuianKraj,
    RuianOkres,
)
from historie.models import Historie, HistorieVazby
from komponenta.models import Komponenta, KomponentaAktivita, KomponentaVazby
from lokalita.models import Lokalita
from nalez.models import NalezObjekt, NalezPredmet
from neidentakce.models import NeidentAkce, NeidentAkceVedouci
from notifikace_projekty.models import Pes
from oznameni.models import Oznamovatel
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pian.models import Kladyzm, Pian
from projekt.models import Projekt, ProjektKatastr
from uzivatel.models import Organizace, Osoba, User, UserNotificationType


class ImportDataError(Exception):
    pass


class ImportDataIncorrectStructureError(ImportDataError):
    """
    Exception raised when the structure of the imported data does not match the expected structure.
    """

    def __init__(self, missing_columns, excess_columns):
        super().__init__(
            f'{_("core_admin.ImportDataIncorrectStructureError.message.part_1")} '
            + (
                f'{_("core_admin.ImportDataMissingReferencedValueError.message.missing_columns")}: {", ".join(missing_columns)} '
                if missing_columns
                else ""
            )
            + (
                f'{_("core_admin.ImportDataMissingReferencedValueError.message.excess_columns")}: {", ".join(excess_columns)} '
                if excess_columns
                else ""
            )
        )


class ImportDataMissingReferencedValueError(ImportDataError):
    """
    Exception raised when a referenced value is missing in either database or in the imported data.
    """

    def __init__(self, missing_value_id, missing_model_name=None):
        self.missing_value_id = missing_value_id
        self.missing_model_name = missing_model_name
        super().__init__(
            f'{_("core_admin.ImportDataMissingReferencedValueError.message.part_1")} '
            + f'{missing_value_id} {_("core_admin.ImportDataMissingReferencedValueError.message.part_2")} '
            + (
                f'{missing_model_name} {_("core_admin.ImportDataMissingReferencedValueError.message.part_3")} '
                if missing_model_name
                else ""
            )
        )


class ImportDataIntegrityError(ImportDataError):
    """
    Exception raised in two cases.
    During the import action: when a record with the same primary key already exists in the database
    During the update action: when a record with the specified primary key does not exist in the database.
    """

    def __init__(self, record_id, model_name, performed_action):
        self.record_id = record_id
        self.model_name = model_name
        self.performed_action = performed_action
        super().__init__(
            f'{_("core_admin.ImportDataIntegrityError.message.part_1")} '
            + f'{record_id} {_("core_admin.ImportDataIntegrityError.message.part_2")} '
            + f'{model_name} {_("core_admin.ImportDataIntegrityError.message.part_3")} '
            + f'({_("core_admin.ImportDataIntegrityError.message.part_4")} {performed_action})'
        )


class ImportDataLimitChoicesError(ImportDataError):
    def __init__(self, record_id, limit_choices_to: dict):
        self.record_id = record_id
        self.limit_choices_to = limit_choices_to
        super().__init__(
            f'{_("core_admin.ImportDataLimitChoicesError.message.part_1")} '
            + f'{record_id} {_("core_admin.ImportDataLimitChoicesError.message.part_2")} '
            + f'{",".join([f"{k}: {v}" for k,v in limit_choices_to.items()])} {_("core_admin.ImportDataLimitChoicesError.message.part_3")}'
        )


class ImportDataHeslarPresnostLimitChoicesError(ImportDataError):
    def __init__(self, record_id):
        self.record_id = record_id
        super().__init__(
            f'{_("core_admin.ImportDataLimitChoicesError.message.part_1")} '
            + f'{record_id} {_("core_admin.ImportDataLimitChoicesError.message.part_2")} '
        )


class ImportDataUnsupportedFileError(ImportDataError):
    """
    Exception raised when an unsupported file name is included in the imported archive.
    """

    def __init__(self, file_name):
        self.file_name = file_name
        super().__init__(
            f'{_("core_admin.ImportDataUnsupportedFileError.message.part_1")} '
            + f'{file_name} {_("core_admin.ImportDataUnsupportedFileError.message.part_2")} '
        )


class ImportDataUnsupportedMultipleFilesError(ImportDataError):
    """
    Exception raised when an unsupported file name is included in the imported archive.
    """

    def __init__(self, file_name):
        self.file_name = file_name
        super().__init__(
            f'{_("core_admin.ImportDataUnsupportedFileError.message.part_1")} '
            + f'{", ".join(file_name)} {_("core_admin.ImportDataUnsupportedFileError.message.part_2")} '
        )


class BaseImportField:
    """
    Base class for import fields. Does not perform any validation or processing of the value.
    Used mostly for text fields.
    """

    def __init__(self):
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if str(value).lower() == "nan":
            value = None
        self._value = self._process_value(value)

    @property
    def is_null(self):
        return self._value is None or str(self._value).lower() == "nan"

    @property
    def instance_value(self):
        return self._value

    @property
    def serialized_value(self):
        return self._value

    def _process_value(self, value):
        return value


class IntegerImportField(BaseImportField):
    """
    Class for import fields that should contain integer values.
    """

    pattern = re.compile(r"\d+")

    def _process_value(self, value) -> int | None:
        """
        If the value is not a number, then the method raises ImportDataError. Otherwise it converts value to int.
        """

        if not value:
            return None
        if isinstance(value, int) or isinstance(value, float):
            value = str(value)
        elif isinstance(value, bytes):
            value = value.decode("utf-8")
        value = self.pattern.search(value).group()
        if value:
            return int(value) if value is not None else None
        else:
            raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_integer_value')}: {value}")


class PositiveIntegerImportField(BaseImportField):
    def _process_value(self, value) -> int | None:
        value = super()._process_value(value)
        if value is not None and value < 0:
            raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_positive_integer_value')}: {value}")
        return value


class DecimalImportField(BaseImportField):
    pattern = re.compile(r"\d+\.\d*")

    def _process_value(self, value) -> float | None:
        if not value:
            return None
        if isinstance(value, Decimal) or isinstance(value, float):
            value = str(value)
        elif isinstance(value, bytes):
            value = value.decode("utf-8")
        value = self.pattern.search(value).group()
        if value:
            return float(value) if value is not None else None
        else:
            raise ImportDataError(f"{_('core_admin.DecimalImportField.message.invalid_decimal_value')}: {value}")


class BooleanImportField(BaseImportField):
    """
    Class for import fields that should contain boolean values.
    """

    def _process_value(self, value) -> bool | None:
        """
        Tries to convert string value to bool. If the string value is not "true" or "false", then the exception
        ImportDataError is raised.
        """

        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ("true", "1"):
                return True
            elif value.lower() in ("false", "0"):
                return False
        raise ImportDataError(f"{_('core_admin.BooleanImportField.message.invalid_boolean_value')}: {value}")


class DateImportField(BaseImportField):
    """
    Class for import fields that should contain date values.
    """

    pattern_iso = re.compile(r"(\d{4}-\d{1,2}-\d{1,2})(?: 0{1,2}:0{1,2}:0{1,2})?")
    pattern_localized = re.compile(r"\d{1,2}\. ?\d{1,2}\. ?\d{4}")

    @property
    def value(self):
        return self._value.isoformat() if self._value else None

    @value.setter
    def value(self, value):
        self._value = self._process_value(value)

    @property
    def serialized_value(self):
        return self._value.strftime("%Y-%m-%d") if self._value else None

    def _process_value(self, value) -> datetime.date | None:
        """
        Tries to convert a string value to date. If the string value is not in the format "YYYY-MM-DD" or "DD.MM.YYYY",
        then the exception ImportDataError is raised.
        """

        if not value or str(value).lower() == "nan":
            return None
        elif isinstance(value, str):
            if self.pattern_iso.match(value):
                return datetime.datetime.strptime(self.pattern_iso.match(value).group(1), "%Y-%m-%d").date()
            if self.pattern_localized.match(value):
                return datetime.datetime.strptime(value.replace(" ", ""), "%d.%m.%Y").date()
        elif isinstance(value, datetime.date):
            return value
        raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_date_value')}: {value}")


class DateTimeImportField(BaseImportField):
    """
    Class for import fields that should contain date and time values.
    """

    pattern_iso = re.compile(r"(\d{4}-\d{1,2}-\d{1,2}.?\d{1,2}:\d{1,2}:\d{1,2}).*")

    @property
    def value(self):
        return self._value.strftime("%Y-%m-%d %H:%M:%S") if self._value else None

    @value.setter
    def value(self, value):
        self._value = self._process_value(value)

    @property
    def serialized_value(self):
        return self._value.strftime("%Y-%m-%d %H:%M:%S") if self._value else None

    def _process_value(self, value) -> datetime.datetime | None:
        if not value or str(value).lower() == "nan":
            return None
        elif isinstance(value, str):
            if match := self.pattern_iso.match(value):
                value = datetime.datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                return timezone.make_aware(value)
        elif isinstance(value, datetime.datetime):
            return value
        raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_date_time_value')}: {value}")


class DateRangeImportField(BaseImportField):
    """
    Class for import fields that should contain date-range values.
    """

    pattern = re.compile(r"\[\d{4}-\d{1,2}-\d{1,2}, ?\d{4}-\d{1,2}-\d{1,2}\)")

    @property
    def serialized_value(self):
        return f"[{self.value.lower.strftime('%Y-%m-%d')},{self.value.upper.strftime('%Y-%m-%d')})"

    def _process_value(self, value) -> DateRange | None:
        """
        Tries to convert a string value to date. If the string value is not in the format "YYYY-MM-DD" or "DD.MM.YYYY",
        then the exception ImportDataError is raised.
        """

        if not value or str(value).lower() == "nan":
            return None
        if isinstance(value, str):
            if self.pattern.fullmatch(value):
                start, end = value.strip("[)").split(",")
                start = datetime.datetime.strptime(start.strip(), "%Y-%m-%d").date()
                end = datetime.datetime.strptime(end.strip(), "%Y-%m-%d").date()
                return DateRange(start, end)
        raise ImportDataError(f"{_('core_admin.DateRangeImportField.message.invalid_date_range_value')}: {value}")


class LookupImportField(BaseImportField):
    """
    Class for import fields that should contain a reference to another model instance.
    """

    records = []

    def __init__(
        self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", limit_choices_to: dict | None = None
    ):
        super().__init__()
        if not isinstance(lookup_model_classes, Iterable):
            self.lookup_model_class_list = [
                lookup_model_classes,
            ]
        elif lookup_model_classes is None:
            self.lookup_model_class_list = []
        else:
            self.lookup_model_class_list = lookup_model_classes
        self.lookup_field_name = lookup_field_name
        self._instance_value = None
        if limit_choices_to and lookup_model_classes != Heslar:
            raise ValueError("limit_choices_to is only supported for Heslar model")
        self.limit_choices_to = limit_choices_to

    @property
    def instance_value(self):
        return self._instance_value

    def _check_limit_choices_to(self, record):
        if self.limit_choices_to:
            if not all(getattr(record, k).pk == v for k, v in self.limit_choices_to.items()):
                raise ImportDataLimitChoicesError(record, self.limit_choices_to)

    def _process_value(self, value):
        """
        Processes the value by checking if it exists in the database or in the imported records. If yes, it returns
        the record. If the referenced record does not exist, it raises ImportDataMissingReferencedValueError.
        """

        if str(value).lower() == "nan" or value is None or len(str(value)) == 0:
            return None
        for current_class in self.lookup_model_class_list:
            saved_records_query = current_class.objects.filter(**{self.lookup_field_name: value})
            if saved_records_query.exists():
                self._check_limit_choices_to(saved_records_query.first())
                self._instance_value = saved_records_query.first()
                return value
            filtered_records = [
                record
                for record in self.records
                if isinstance(record, current_class) and getattr(record, self.lookup_field_name, None) == value
            ]
            if len(filtered_records) == 1:
                self._check_limit_choices_to(filtered_records[0])
                self._instance_value = filtered_records[0]
                return value
        raise ImportDataMissingReferencedValueError(
            value, ", ".join([current_class.__name__ for current_class in self.lookup_model_class_list])
        )


class RuianLookupImportField(LookupImportField):
    """
    Based on the LookupImportField, this class is used for importing data from RUIAN data. It strips
    the "ruian-" prefix from the value and converts it to an integer.
    """

    @LookupImportField.value.setter
    def value(self, value):
        if isinstance(value, str):
            match = re.match(r"ruian-(\d+)", value)
            value = int(match.group(1))
        LookupImportField.value.fset(self, value)


class VazbaLookupImportField(LookupImportField):
    """
    Class for import field with referenced models for vazba (relation). This relation is 1:1 instead of 1:N
    and these fields manage relation to another model.
    """

    def __init__(self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", read_field_name: str = None):
        super().__init__(lookup_model_classes, lookup_field_name)
        self.read_field_name = read_field_name

    def _process_value(self, value):
        record = get_record_from_ident(value)
        if self.lookup_model_class_list:
            if isinstance(record, Dokument):
                if Dokument in self.lookup_model_class_list:
                    self._instance_value = record
                    return value
                elif DokumentCast in self.lookup_model_class_list:
                    self._instance_value = DokumentCast.objects.get(ident_cely=value)
                    return value
                elif DokumentacniJednotka in self.lookup_model_class_list:
                    self._instance_value = DokumentacniJednotka.objects.get(ident_cely=value)
                    return value
        if record and hasattr(record, self.read_field_name):
            self._instance_value = getattr(record, self.read_field_name)
            return value
        filtered_records = [
            record
            for record in self.records
            if getattr(record, self.lookup_field_name, None) == value and hasattr(record, self.read_field_name)
        ]
        if len(filtered_records) == 1:
            self._instance_value = filtered_records[0].historie
            return value
        raise ImportDataMissingReferencedValueError(value)


class HeslarPresnostLookupImportField(LookupImportField):
    def _check_limit_choices_to(self, record: Pian):
        super()._check_limit_choices_to(record)
        # if record.zkratka >= "4":
        #     raise ImportDataHeslarPresnostLimitChoicesError(record)


class GeomImportField(BaseImportField):
    """
    Class for import fields that should contain geometries.
    """

    def __init__(self, srid):
        super().__init__()
        self.srid = srid

    @property
    def serialized_value(self):
        return getattr(self._value, "wkt", None)

    def _process_value(self, value) -> GEOSGeometry | None:
        """
        Tries to convert string value to geometry.
        """
        if not value:
            return None
        if isinstance(value, str):
            value = GEOSGeometry(value, srid=self.srid)
        if isinstance(value, GEOSGeometry):
            return value
        raise ImportDataError(f"{_('core_admin.GeomImportField.message.invalid_date_value')}: {value}")


class GenericForeignKeyImportField(LookupImportField):
    def __init__(
        self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", serialized_attribute: str = None
    ):
        super().__init__(lookup_model_classes, lookup_field_name)
        self.serialized_attribute = serialized_attribute

    @property
    def serialized_value(self):
        if self.serialized_attribute:
            return getattr(self._value, self.serialized_attribute)
        else:
            return self._value.pk

    def _process_value(self, value):
        if isinstance(value, str) and (match := re.match(r"(?:\w+-)?(\d+)", value)):
            value = int(match.group(1))

        for current_class in self.lookup_model_class_list:
            if current_class.objects.filter(**{self.lookup_field_name: value}).exists():
                return current_class.objects.get(**{self.lookup_field_name: value})
        raise ImportDataMissingReferencedValueError(
            value, ", ".join([current_class.__name__ for current_class in self.lookup_model_class_list])
        )


class ImportModelMapper(ABC):
    """
    Base class for data import. The class loads data from the imported file, preprocesses all values based on the
    target field and creates a record.
    """

    fields = tuple()
    column_to_field_mapping = {}
    model_class = None
    primary_key = "ident_cely"
    primary_key_filter_field = None
    historie_typ_vazby = None
    soubory_typ_vazby = None
    komponenty_vazba = False
    require_primary_key_value = False
    primary_key_prefix = None

    def __init__(self, value_dict):
        self.value_dict = value_dict

    @classmethod
    def get_import_data_mapper_dict(cls):
        """
        Returns a child class based on the import file name.
        """

        return {
            "heslar": HeslarMapper,
            "heslar_datace": HeslarDataceMapper,
            "heslar_dokument_typ_material_rada": HeslarDokumentTypMaterialRadaMapper,
            "heslar_hierarchie": HeslarHierarchieMapper,
            "heslar_odkazy": HeslarOdkazMapper,
            "organizace": OrganizaceMapper,
            "osoby": OsobaMapper,
            "projekty": ProjektMapper,
            "projekty_katastry": ProjektKatastrMapper,
            "projekty_oznamovatele": ProjektOznamovatelMapper,
            "samostatne_nalezy": SamostatnyNalezMapper,
            "AZ_akce": ArcheologickyZaznamAkceMapper,
            "AZ_lokality": LokalitaMapper,
            "AZ_akce_vedouci": AkceVedouciMapper,
            "AZ_katastry": ArcheologickyZaznamKatastrMapper,
            "AZ_pian": PianMapper,
            "AZ_dokumentacni_jednotky": DokumentacniJednotkaMapper,
            "AZ_adb": AdbMapper,
            "AZ_adb_vyskove_body": AdbVyskovyBod,
            "dokumenty_lety": DokumentLetMapper,
            "dokumenty": DokumentMapper,
            "dokumenty_autori": DokumentAutorMapper,
            "dokumenty_jazyky": DokumentJazykMapper,
            "dokumenty_osoby": DokumentOsobaMapper,
            "dokumenty_posudky": DokumentPosudekMapper,
            "dokumenty_tvary": TvarMapper,
            "dokumenty_casti": DokumentCastMapper,
            "dokumenty_neident_akce": NeidentAkceMapper,
            "dokumenty_neident_akce_vedouci": NeidentAkceVedouciMapper,
            "komponenty": KomponentaMapper,
            "komponenty_aktivity": KomponentaAktivitaMapper,
            "komponenty_nalezy_objekty": NalezObjektMapper,
            "komponenty_nalezy_predmety": NalezPredmetMapper,
            "externi_zdroje": ExterniZdrojMapper,
            "externi_zdroje_autori": ExterniZdrojAutorMapper,
            "externi_zdroje_editori": ExterniZdrojEditorMapper,
            "externi_odkazy": ExterniOdkazMapper,
            "uzivatele": UzivatelMapper,
            "uzivatele_notifikace_projekty": UzivatelNotifikaceProjektMapper,
            "uzivatele_spoluprace": UzivatelSpolupraceMapper,
            "uzivatele_opravneni": UzivatelOpravneniMapper,
            "uzivatele_notifikace": UzivatelNotifikaceMapper,
            "soubory": SouborMapper,
            "historie": HistorieMapper,
        }

    @classmethod
    def get_import_data_mapper(cls, file_name):
        """
        Returns a child mapper class based on the file name, omitting the file extension.
        """

        return cls.get_import_data_mapper_dict().get(file_name.split(".")[0])

    @classmethod
    def get_mapping(cls, include_primary_key=False) -> dict:
        """
        Map imported values using the map_field method.
        """

        field_mapping = {}
        for item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        if include_primary_key:
            if isinstance(cls.primary_key, str) and cls.primary_key not in field_mapping:
                field_mapping[cls.primary_key] = cls.map_field(cls.primary_key)
            elif isinstance(cls.primary_key, tuple):
                for primary_key in cls.primary_key:
                    if primary_key not in field_mapping:
                        field_mapping[primary_key] = cls.map_field(primary_key)
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        """
        Returns a dict with primary key field name(s) and field value(s).
        """

        def value_dict_name(value):
            return value.split("__")[0] if "__" in value else value

        if (
            not self.require_primary_key_value
            and self.primary_key == "ident_cely"
            and "ident_cely" not in self.value_dict
        ):
            return None

        if isinstance(self.primary_key, str):
            primary_key_filter_field = self.primary_key_filter_field or self.primary_key
            return {
                primary_key_filter_field: self._parse_primary_key(self.value_dict[value_dict_name(self.primary_key)])
            }
        elif isinstance(self.primary_key, Iterable):
            prefix_list = self.primary_key_prefix or [None] * len(self.primary_key)
            if self.primary_key_filter_field:
                primary_key_zipped = zip(self.primary_key, self.primary_key_filter_field, prefix_list)
                return {
                    primary_key_filter_field: self._parse_primary_key_custom_prefix(
                        self.value_dict[value_dict_name(primary_key)], prefix
                    )
                    for primary_key, primary_key_filter_field, prefix in primary_key_zipped
                }
            else:
                return {
                    key: self._parse_primary_key_custom_prefix(self.value_dict[value_dict_name(key)], prefix)
                    for key, prefix in zip(self.primary_key, prefix_list)
                }

    @classmethod
    def _parse_primary_key(cls, value):
        if isinstance(value, str) and cls.primary_key_prefix:
            return int(re.match(f"{cls.primary_key_prefix}-(.*)", value).group(1))
        return value

    @staticmethod
    def _parse_primary_key_custom_prefix(value, prefix):
        if isinstance(value, str) and prefix:
            return int(re.match(f"{prefix}-(.*)", value).group(1))
        return value

    @classmethod
    def map_field(cls, field_name):
        """
        Maps value to a specific BaseImportField instance or BaseImportField child instance.
        """

        model_field = cls.model_class._meta.get_field(field_name)
        if isinstance(model_field, models.TextField) or isinstance(model_field, models.CharField):
            return BaseImportField()
        if isinstance(model_field, models.IntegerField):
            return IntegerImportField()
        if isinstance(model_field, models.PositiveIntegerField):
            return IntegerImportField()
        if isinstance(model_field, models.DecimalField):
            return DecimalImportField()
        if isinstance(model_field, models.DateTimeField):
            return DateTimeImportField()
        if isinstance(model_field, models.DateField):
            return DateImportField()
        if isinstance(model_field, models.BooleanField):
            return BooleanImportField()
        if isinstance(model_field, pgmodels.PointField):
            return GeomImportField(model_field.srid)
        if isinstance(model_field, pgmodels.GeometryField):
            return GeomImportField(model_field.srid)
        if isinstance(model_field, DateRangeField):
            return DateRangeImportField()
        if isinstance(model_field, models.ForeignKey):
            return None
        raise ImportDataError(f"_('core.admin.ImportModelMapper.map_field.error'): {field_name}")

    @classmethod
    def is_field_required(cls, field_name) -> bool:
        try:
            model_field = cls.model_class._meta.get_field(field_name)
            return not model_field.null
        except FieldDoesNotExist:
            return False

    def create_records(self, performed_action) -> list:
        """
        Create a record instance or multiple model instances that can be saved to database.
        """

        mapping_dict = self.map(performed_action, True)
        if performed_action not in (
            ImportDataAdminForm.PERFORMED_ACTION_INSERT,
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        ):
            raise ImportDataError(
                f"{_('core_admin.ImportDataError.message.invalid_performed_action')}: {performed_action}"
            )
        mapping_dict = {self.map_column_name_to_field_name(field): value for field, value in mapping_dict.items()}
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            return [
                self.model_class(**mapping_dict),
            ]
        if performed_action in (
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        ):
            record = self.model_class.objects.get(**self._get_filter_kwargs_primary_key())
            for field_name, field_value in mapping_dict.items():
                if isinstance(self.primary_key, str) and field_name != self.primary_key:
                    setattr(record, field_name, field_value)
                elif isinstance(self.primary_key, tuple) and field_name not in self.primary_key:
                    setattr(record, field_name, field_value)
            return [
                record,
            ]
        return []

    def import_validation(self, performed_action) -> dict | None:
        """
        Perform the validation based on the primary key. The record should not exist in databased when the insert action
        is performed. It should exist if the update action is performed. If one of the conditions is valid, the method
        returns a dict with mapped primary key field names and values.  Otherwise, the ImportDataIntegrityError
        error is raised.
        """

        if self.primary_key and self._get_filter_kwargs_primary_key():
            if (
                performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT
                and self.model_class.objects.filter(**self._get_filter_kwargs_primary_key()).exists()
            ):
                raise ImportDataIntegrityError(
                    self._get_filter_kwargs_primary_key(), self.model_class.__name__, performed_action
                )
            elif (
                performed_action
                in (ImportDataAdminForm.PERFORMED_ACTION_UPDATE, ImportDataAdminForm.PERFORMED_ACTION_DELETE)
                and not self.model_class.objects.filter(**self._get_filter_kwargs_primary_key()).exists()
            ):
                raise ImportDataIntegrityError(
                    self._get_filter_kwargs_primary_key(), self.model_class.__name__, performed_action
                )
            return self._get_filter_kwargs_primary_key()

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """
        Checks if the file columns structure is valid as the first step. If not, the ImportDataIncorrectStructureError
        exception is raised. Then it creates a dict with field names as keys and values are instances of
        BaseImportField class or one of its child classes with values loaded from the import file.
        """

        mapping_dict = {}
        primary_keys = set((self.primary_key,) if isinstance(self.primary_key, str) else self.primary_key)
        mapping_column_set = set(self.value_dict.keys())
        value_dict_column_set = set(self.get_mapping(include_primary_key).keys()) | primary_keys
        missing_columns = set()
        excess_columns = set()
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            if mapping_column_set != value_dict_column_set:
                excess_columns = mapping_column_set - value_dict_column_set
                missing_columns = (
                    value_dict_column_set
                    - mapping_column_set
                    - (
                        {self.primary_key}
                        if isinstance(self.primary_key, str) and self.require_primary_key_value is False
                        else set()
                    )
                )
        elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE:
            missing_columns = primary_keys - set(self.value_dict.keys())
            excess_columns = mapping_column_set - value_dict_column_set
            if missing_columns or excess_columns:
                raise ImportDataIncorrectStructureError(missing_columns, excess_columns)
        elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            missing_columns = primary_keys - set(self.value_dict.keys())
            excess_columns = mapping_column_set - primary_keys
        if missing_columns or excess_columns:
            raise ImportDataIncorrectStructureError(missing_columns, excess_columns)
        for field_name, field_instance in self.get_mapping(include_primary_key).items():
            if field_name in self.value_dict:
                field_value = self.value_dict[field_name]
                field_instance.value = field_value
                if instance_values:
                    mapping_dict[field_name] = (
                        field_instance.instance_value if not serialize else field_instance.serialized_value
                    )
                else:
                    mapping_dict[field_name] = (
                        field_instance.value if not serialize else field_instance.serialized_value
                    )
        return mapping_dict

    def check_required_fields(self, performed_action):
        for key, value in self.value_dict.items():
            required = self.is_field_required(key)
            if required and (value is None or str(value).lower().strip() in ("nan", "") or pd.isna(value)):
                raise ImportDataError(f"{_('core_admin.ImportDataError.message.missing_required_field')}: {key}")

    def map_column_name_to_field_name(self, column_name):
        """
        Map a column name from the import file to the field name of the Django model. Used when the Django field
        name is different from a database column name.
        """

        return self.column_to_field_mapping.get(column_name, column_name)

    @classmethod
    def create_relations(cls, instance):
        """
        Creates relation fields for Historie and Soubory.
        """

        if cls.historie_typ_vazby and not getattr(instance, "historie", None):
            hv = HistorieVazby(typ_vazby=cls.historie_typ_vazby)
            hv.save()
            instance.historie = hv
        if cls.soubory_typ_vazby and not getattr(instance, "soubory", None):
            sv = SouborVazby(typ_vazby=cls.soubory_typ_vazby)
            sv.save()
            instance.soubory = sv
        if cls.komponenty_vazba is True and not getattr(instance, "komponenty", None):
            kv = KomponentaVazby()
            kv.save()
            instance.komponenty = kv

    @classmethod
    def record_postprocessing(cls, record, performed_action):
        return record


class ImportModelMapperWithGeom(ImportModelMapper):
    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            if mapping_dict.get("geom_system") == 4326 and mapping_dict.get("geom"):
                mapping_dict["geom_sjtsk"] = transform_geom_to_sjtsk(mapping_dict["geom"])
            elif mapping_dict.get("geom_system") == 5514 and mapping_dict.get("geom_sjtsk"):
                mapping_dict["geom"] = transform_geom_to_wgs84(mapping_dict["geom_sjtsk"])
        return mapping_dict


class MultipleClassImportModelMapper(ImportModelMapper):
    foreign_key_fields = tuple()
    classes = tuple()

    def import_validation(self, performed_action):
        if (
            performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT
            and self.value_dict.get("ident_cely")
            and self.model_class.objects.filter(ident_cely=self.value_dict["ident_cely"]).exists()
        ):
            raise ImportDataIntegrityError(
                self._get_filter_kwargs_primary_key(), self.model_class.__name__, performed_action
            )
        elif (
            performed_action
            in (ImportDataAdminForm.PERFORMED_ACTION_UPDATE, ImportDataAdminForm.PERFORMED_ACTION_DELETE)
            and not self.model_class.objects.filter(ident_cely=self.value_dict["ident_cely"]).exists()
        ):
            raise ImportDataIntegrityError(
                self._get_filter_kwargs_primary_key(), self.model_class.__name__, performed_action
            )
        return self._get_filter_kwargs_primary_key()

    def _get_filter_kwargs_primary_key(self):
        return {"ident_cely": self.value_dict.get("ident_cely")}

    def create_records(self, performed_action) -> list:
        class_0_fields = [item for model, item in self.fields + self.foreign_key_fields if model == self.classes[0][0]]
        class_1_fields = [item for model, item in self.fields + self.foreign_key_fields if model == self.classes[1][0]]
        mapping_dict = self.map(performed_action, True)
        mapping_dict_class_0 = {field: mapping_dict.get(field) for field in class_0_fields}
        mapping_dict_class_1 = {field: mapping_dict.get(field) for field in class_1_fields}
        mapping_dict_class_0 = {
            self.map_column_name_to_field_name(field): value for field, value in mapping_dict_class_0.items()
        }
        mapping_dict_class_1 = {
            self.map_column_name_to_field_name(field): value for field, value in mapping_dict_class_1.items()
        }
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            instance_class_0 = self.classes[0][1](**mapping_dict_class_0)
            instance_class_1 = self.classes[1][1](**mapping_dict_class_1)
            setattr(instance_class_1, self.classes[1][2], instance_class_0)
            return [instance_class_0, instance_class_1]
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE:
            instance_class_0 = self.classes[0][1].objects.get(ident_cely=mapping_dict["ident_cely"])
            instance_class_1 = self.classes[1][1].objects.get(archeologicky_zaznam=instance_class_0)
            for field_name, field_value in mapping_dict_class_0.items():
                setattr(instance_class_0, field_name, field_value)
            for field_name, field_value in mapping_dict_class_1.items():
                setattr(instance_class_1, field_name, field_value)
            return [instance_class_0, instance_class_1]
        return []

    @classmethod
    def is_field_required(cls, field_name) -> bool:
        for mapper_class_tuple in cls.classes:
            mapper_class = mapper_class_tuple[1]
            try:
                model_field = mapper_class._meta.get_field(field_name)
                return not model_field.null
            except FieldDoesNotExist:
                continue
        return False


class HeslarMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "heslo",
        "heslo_en",
        "popis",
        "popis_en",
        "zkratka",
        "razeni",
    )
    model_class = Heslar
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["nazev_heslare"] = LookupImportField(HeslarNazev, "nazev")
        return field_mapping


class HeslarDataceMapper(ImportModelMapper):
    fields = (
        "rok_od_min",
        "rok_od_max",
        "rok_do_min",
        "rok_do_max",
        "poznamka",
    )
    model_class = HeslarDatace
    primary_key = "obdobi"
    primary_key_filter_field = "obdobi__ident_cely"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["obdobi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBDOBI})
        return field_mapping


class HeslarDokumentTypMaterialRadaMapper(ImportModelMapper):
    model_class = HeslarDokumentTypMaterialRada
    primary_key = "id"
    primary_key_prefix = "hdtm"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument_typ"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP}
        )
        field_mapping["dokument_material"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_MATERIAL}
        )
        field_mapping["dokument_rada"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_RADA}
        )
        return field_mapping


class HeslarHierarchieMapper(ImportModelMapper):
    fields = ("typ",)
    model_class = HeslarHierarchie
    primary_key = "id"
    primary_key_prefix = "hier"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["heslo_nadrazene"] = LookupImportField(Heslar)
        field_mapping["heslo_podrazene"] = LookupImportField(Heslar)
        return field_mapping


class HeslarOdkazMapper(ImportModelMapper):
    fields = (
        "zdroj",
        "nazev_kodu",
        "kod",
        "uri",
        "scheme_uri",
        "skos_mapping_relation",
    )
    model_class = HeslarOdkaz
    primary_key = "id"
    primary_key_prefix = "hodk"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["heslo"] = LookupImportField(Heslar)
        return field_mapping


class OrganizaceMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "nazev",
        "nazev_en",
        "nazev_zkraceny",
        "nazev_zkraceny_en",
        "oao",
        "mesicu_do_zverejneni",
        "email",
        "telefon",
        "adresa",
        "ico",
        "zanikla",
        "cteni_dokumentu",
        "ror",
    )
    model_class = Organizace
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["soucast"] = LookupImportField(Organizace)
        field_mapping["typ_organizace"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_ORGANIZACE_TYP}
        )
        field_mapping["zverejneni_pristupnost"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST}
        )
        return field_mapping


class OsobaMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "vypis_cely",
        "vypis",
        "jmeno",
        "prijmeni",
        "rodne_prijmeni",
        "rok_narozeni",
        "rok_umrti",
        "orcid",
        "wikidata",
    )
    model_class = Osoba
    require_primary_key_value = True


class ProjektMapper(ImportModelMapperWithGeom):
    fields = (
        "ident_cely",
        "stav",
        "lokalizace",
        "parcelni_cislo",
        "geom",
        "geom_system",
        "geom_sjtsk",
        "podnet",
        "planovane_zahajeni",
        "uzivatelske_oznaceni",
        "oznaceni_stavby",
        "kulturni_pamatka_cislo",
        "kulturni_pamatka_popis",
        "datum_zahajeni",
        "datum_ukonceni",
        "termin_odevzdani_nz",
    )
    model_class = Projekt
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["typ_projektu"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PROJEKT_TYP}
        )
        field_mapping["hlavni_katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        field_mapping["vedouci_projektu"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        field_mapping["kulturni_pamatka"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PAMATKOVA_OCHRANA}
        )
        return field_mapping


class ProjektKatastrMapper(ImportModelMapper):
    model_class = ProjektKatastr
    primary_key = ("projekt", "katastr")
    primary_key_filter_field = ("projekt__ident_cely", "katastr__kod")
    require_primary_key_value = True
    primary_key_prefix = (None, "ruian")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["projekt"] = LookupImportField(Projekt)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping


class ProjektOznamovatelMapper(ImportModelMapper):
    fields = ("oznamovatel", "odpovedna_osoba", "adresa", "telefon", "email", "poznamka")
    model_class = Oznamovatel
    primary_key = "projekt"
    primary_key_filter_field = "projekt__ident_cely"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["projekt"] = LookupImportField(Projekt)
        return field_mapping


class SamostatnyNalezMapper(ImportModelMapperWithGeom):
    fields = (
        "ident_cely",
        "igsn",
        "stav",
        "evidencni_cislo",
        "lokalizace",
        "geom_system",
        "geom",
        "geom_sjtsk",
        "hloubka",
        "datum_nalezu",
        "predano",
        "presna_datace",
        "pocet",
        "poznamka",
    )
    model_class = SamostatnyNalez
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["projekt"] = LookupImportField(Projekt)
        field_mapping["pristupnost"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST})
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        field_mapping["okolnosti"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_NALEZOVE_OKOLNOSTI}
        )
        field_mapping["nalezce"] = LookupImportField(Osoba)
        field_mapping["predano_organizace"] = LookupImportField(Organizace)
        field_mapping["obdobi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBDOBI})
        field_mapping["druh_nalezu"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PREDMET_DRUH}
        )
        field_mapping["specifikace"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PREDMET_SPECIFIKACE}
        )
        return field_mapping


class ArcheologickyZaznamAkceMapper(MultipleClassImportModelMapper):
    fields = (
        ("archeologicky_zaznam", "ident_cely"),
        ("archeologicky_zaznam", "stav"),
        ("akce", "typ"),
        ("akce", "projekt"),
        ("archeologicky_zaznam", "pristupnost"),
        ("archeologicky_zaznam", "hlavni_katastr"),
        ("archeologicky_zaznam", "uzivatelske_oznaceni"),
        ("akce", "lokalizace_okolnosti"),
        ("akce", "je_nz"),
        ("akce", "odlozena_nz"),
        ("akce", "hlavni_vedouci"),
        ("akce", "organizace"),
        ("akce", "specifikace_data"),
        ("akce", "datum_zahajeni"),
        ("akce", "datum_ukonceni"),
        ("akce", "hlavni_typ"),
        ("akce", "vedlejsi_typ"),
        ("akce", "ulozeni_nalezu"),
        ("akce", "ulozeni_dokumentace"),
        ("akce", "souhrn_upresneni"),
    )
    foreign_key_fields = (
        ("akce", "projekt"),
        ("archeologicky_zaznam", "pristupnost"),
        ("archeologicky_zaznam", "hlavni_katastr"),
        ("akce", "hlavni_vedouci"),
        ("akce", "organizace"),
        ("akce", "specifikace_data"),
        ("akce", "hlavni_typ"),
        ("akce", "vedlejsi_typ"),
    )
    lookup_fields_mapping = {
        "projekt": LookupImportField(Projekt),
        "pristupnost": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST}),
        "hlavni_katastr": RuianLookupImportField(RuianKatastr, "kod"),
        "hlavni_vedouci": LookupImportField(Osoba),
        "organizace": LookupImportField(Organizace),
        "specifikace_data": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DATUM_SPECIFIKACE}),
        "hlavni_typ": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_AKCE_TYP}),
        "vedlejsi_typ": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_AKCE_TYP}),
    }
    model_class = ArcheologickyZaznam
    classes = (
        ("archeologicky_zaznam", ArcheologickyZaznam),
        ("akce", Akce, "archeologicky_zaznam"),
    )
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping = field_mapping | cls.lookup_fields_mapping
        return field_mapping

    @classmethod
    def map_field(cls, field_name):
        mapping_dict = {
            "je_nz": BooleanImportField(),
            "odlozena_nz": BooleanImportField(),
            "hlavni_katastr": RuianLookupImportField(RuianKatastr, "kod"),
        }
        mapping_dict = mapping_dict | cls.lookup_fields_mapping
        return mapping_dict.get(field_name, BaseImportField())

    @classmethod
    def record_postprocessing(cls, record, performed_action):
        if isinstance(record, ArcheologickyZaznam) and performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            record.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
        return super().record_postprocessing(record, performed_action)


class LokalitaMapper(MultipleClassImportModelMapper):
    fields = (
        ("archeologicky_zaznam", "ident_cely"),
        ("lokalita", "igsn"),
        ("archeologicky_zaznam", "stav"),
        ("archeologicky_zaznam", "pristupnost"),
        ("archeologicky_zaznam", "hlavni_katastr"),
        ("lokalita", "nazev"),
        ("archeologicky_zaznam", "uzivatelske_oznaceni"),
        ("lokalita", "typ_lokality"),
        ("lokalita", "druh"),
        ("lokalita", "zachovalost"),
        ("lokalita", "jistota"),
        ("lokalita", "popis"),
        ("lokalita", "poznamka"),
    )
    foreign_key_fields = (
        ("archeologicky_zaznam", "pristupnost"),
        ("archeologicky_zaznam", "hlavni_katastr"),
        ("lokalita", "typ_lokality"),
        ("lokalita", "druh"),
        ("lokalita", "zachovalost"),
        ("lokalita", "jistota"),
    )
    lookup_fields_mapping = {
        "pristupnost": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST}),
        "hlavni_katastr": RuianLookupImportField(RuianKatastr, "kod"),
        "typ_lokality": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LOKALITA_TYP}),
        "druh": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LOKALITA_DRUH}),
        "zachovalost": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_STAV_DOCHOVANI}),
        "jistota": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_JISTOTA_URCENI}),
    }
    model_class = ArcheologickyZaznam
    classes = (
        ("archeologicky_zaznam", ArcheologickyZaznam),
        ("lokalita", Lokalita, "archeologicky_zaznam"),
    )
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping = field_mapping | cls.lookup_fields_mapping
        return field_mapping

    @classmethod
    def map_field(cls, field_name):
        mapping_dict = {
            "hlavni_katastr": RuianLookupImportField(RuianKatastr, "kod"),
        }
        mapping_dict = mapping_dict | cls.lookup_fields_mapping
        return mapping_dict.get(field_name, BaseImportField())

    @classmethod
    def record_postprocessing(cls, record, performed_action):
        if isinstance(record, ArcheologickyZaznam):
            if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
                record.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
                if not record.ident_cely:
                    record.ident_cely = get_temp_lokalita_ident(
                        record.lokalita.typ_lokality.zkratka, record.hlavni_katastr.okres.kraj.rada_id
                    )
            return record
        return super().record_postprocessing(record, performed_action)


class AkceVedouciMapper(ImportModelMapper):
    model_class = AkceVedouci
    primary_key = "id"
    primary_key_prefix = "vedo"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["akce"] = LookupImportField(Akce, "archeologicky_zaznam__ident_cely")
        field_mapping["vedouci"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        return field_mapping


class ArcheologickyZaznamKatastrMapper(ImportModelMapper):
    model_class = ArcheologickyZaznamKatastr
    primary_key = ("archeologicky_zaznam", "katastr")
    primary_key_filter_field = ("archeologicky_zaznam__ident_cely", "katastr__kod")
    primary_key_prefix = (None, "ruian")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping


class PianMapper(ImportModelMapperWithGeom):
    fields = ("ident_cely", "stav", "geom_system", "geom", "geom_sjtsk")
    model_class = Pian
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PIAN_TYP})
        field_mapping["presnost"] = HeslarPresnostLookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PIAN_PRESNOST}
        )
        field_mapping["zm10"] = LookupImportField(Kladyzm, "cislo")
        field_mapping["zm50"] = LookupImportField(Kladyzm, "cislo")
        return field_mapping


class DokumentacniJednotkaMapper(ImportModelMapper):
    fields = ("ident_cely", "negativni_jednotka", "nazev")
    model_class = DokumentacniJednotka
    require_primary_key_value = True
    komponenty_vazba = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["pian"] = LookupImportField(Pian)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DJ_TYP})
        return field_mapping


class AdbMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "uzivatelske_oznaceni_sondy",
        "trat",
        "cislo_popisne",
        "parcelni_cislo",
        "stratigraficke_jednotky",
        "rok_popisu",
        "rok_revize",
        "poznamka",
    )
    model_class = Adb
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokumentacni_jednotka"] = LookupImportField(DokumentacniJednotka)
        field_mapping["typ_sondy"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_ADB_TYP})
        field_mapping["podnet"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_ADB_PODNET})
        field_mapping["autor_popisu"] = LookupImportField(Osoba)
        field_mapping["autor_revize"] = LookupImportField(Osoba)
        field_mapping["sm5"] = LookupImportField(Kladysm5, "mapno")
        return field_mapping


class AdbVyskovyBod(ImportModelMapper):
    fields = ("ident_cely", "geom")
    model_class = VyskovyBod

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["adb"] = LookupImportField(Adb)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_VYSKOVY_BOD_TYP})
        return field_mapping


class DokumentLetMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "uzivatelske_oznaceni",
        "datum",
        "hodina_zacatek",
        "hodina_konec",
        "fotoaparat",
        "pilot",
        "typ_letounu",
        "ucel_letu",
    )
    model_class = Let

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["letiste_start"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LETISTE})
        field_mapping["letiste_cil"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LETISTE})
        field_mapping["pozorovatel"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        field_mapping["pocasi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_POCASI})
        field_mapping["dohlednost"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOHLEDNOST})
        return field_mapping


class DokumentMapper(MultipleClassImportModelMapper):
    fields = (
        ("dokument", "ident_cely"),
        ("dokument", "doi"),
        ("dokument", "stav"),
        ("dokument", "rok_vzniku"),
        ("dokument", "datum_zverejneni"),
        ("dokument", "oznaceni_originalu"),
        ("dokument", "popis"),
        ("dokument", "poznamka"),
        ("dokument_extra_data", "cislo_objektu"),
        ("dokument_extra_data", "meritko"),
        ("dokument_extra_data", "vyska"),
        ("dokument_extra_data", "sirka"),
        ("dokument_extra_data", "pocet_variant_originalu"),
        ("dokument_extra_data", "odkaz"),
        ("dokument_extra_data", "datum_vzniku"),
        ("dokument_extra_data", "udalost"),
        ("dokument_extra_data", "region"),
        ("dokument_extra_data", "rok_od"),
        ("dokument_extra_data", "rok_do"),
        ("dokument_extra_data", "duveryhodnost"),
        ("dokument_extra_data", "geom_system"),
        ("dokument_extra_data", "geom"),
        ("dokument_extra_data", "geom_sjtsk"),
    )
    foreign_key_fields = (
        ("dokument", "let"),
        ("dokument", "typ_dokumentu"),
        ("dokument", "material_originalu"),
        ("dokument", "rada"),
        ("dokument", "organizace"),
        ("dokument", "pristupnost"),
        ("dokument", "ulozeni_originalu"),
        ("dokument", "licence"),
        ("dokument_extra_data", "format"),
        ("dokument_extra_data", "zachovalost"),
        ("dokument_extra_data", "nahrada"),
        ("dokument_extra_data", "udalost_typ"),
        ("dokument_extra_data", "zeme"),
    )
    column_to_field_mapping = {"region": "region_extra"}
    lookup_fields_mapping = {
        "let": LookupImportField(Let),
        "typ_dokumentu": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP}),
        "material_originalu": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_MATERIAL}),
        "rada": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_RADA}),
        "organizace": LookupImportField(Organizace),
        "pristupnost": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST}),
        "ulozeni_originalu": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_ULOZENI}),
        "licence": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LICENCE}),
        "format": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_FORMAT}),
        "zachovalost": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_ZACHOVALOST}),
        "nahrada": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_NAHRADA}),
        "udalost_typ": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_UDALOST_TYP}),
        "zeme": LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_ZEME}),
    }
    model_class = Dokument
    historie_typ_vazby = DOKUMENT_RELATION_TYPE
    soubory_typ_vazby = DOKUMENT_RELATION_TYPE
    komponenty_vazba = True
    classes = (
        ("dokument", Dokument),
        ("dokument_extra_data", DokumentExtraData, "dokument"),
    )
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping = field_mapping | cls.lookup_fields_mapping
        return field_mapping

    @classmethod
    def map_field(cls, field_name):
        mapping_dict = {
            "rok_vzniku": IntegerImportField(),
            "stav": IntegerImportField(),
            "datum_zverejneni": DateImportField(),
            "datum_vzniku": DateImportField(),
            "nahrada": LookupImportField(Heslar),
            "pocet_variant_originalu": IntegerImportField(),
            "rok_od": IntegerImportField(),
            "rok_do": IntegerImportField(),
            "duveryhodnost": IntegerImportField(),
            "geom": GeomImportField(4326),
            "geom_sjtsk": GeomImportField(5514),
        }
        mapping_dict = mapping_dict | cls.lookup_fields_mapping
        return mapping_dict.get(field_name, BaseImportField())

    def create_records(self, performed_action) -> list:
        """
        Creates a Dokument instance and DokumentExtraData instance with relation to Dokument instance.
        """

        fields_dokument = [item for model, item in self.fields + self.foreign_key_fields if model == "dokument"]
        fields_dokument_extra_data = [
            item for model, item in self.fields + self.foreign_key_fields if model == "dokument_extra_data"
        ]
        mapping_dict = self.map(performed_action, True)
        mapping_dict_dokument = {field: mapping_dict[field] for field in fields_dokument}
        mapping_dict_dokument_extra_data = {field: mapping_dict[field] for field in fields_dokument_extra_data}
        mapping_dict_dokument = {
            self.map_column_name_to_field_name(field): value for field, value in mapping_dict_dokument.items()
        }
        mapping_dict_dokument_extra_data = {
            self.map_column_name_to_field_name(field): value
            for field, value in mapping_dict_dokument_extra_data.items()
        }
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            dokument = Dokument(**mapping_dict_dokument)
            dokument_extra_data = DokumentExtraData(**mapping_dict_dokument_extra_data)
            dokument_extra_data.dokument = dokument
            return [dokument, dokument_extra_data]
        if performed_action in (
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        ):
            dokument = Dokument.objects.get(ident_cely=mapping_dict["ident_cely"])
            dokument_extra_data_query = DokumentExtraData.objects.filter(dokument=dokument)
            if dokument_extra_data_query.exists():
                dokument_extra_data = dokument_extra_data_query.first()
            else:
                dokument_extra_data = DokumentExtraData(dokument=dokument)
            for field_name, field_value in mapping_dict_dokument.items():
                setattr(dokument, field_name, field_value)
            for field_name, field_value in mapping_dict_dokument_extra_data.items():
                setattr(dokument_extra_data, field_name, field_value)
            return [dokument, dokument_extra_data]
        return []


class DokumentAutorMapper(ImportModelMapper):
    fields = ("poradi",)
    model_class = DokumentAutor
    primary_key = ("dokument", "autor")
    primary_key_filter_field = ("dokument__ident_cely", "autor__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["autor"] = LookupImportField(Osoba)
        return field_mapping


class DokumentJazykMapper(ImportModelMapper):
    model_class = DokumentJazyk
    primary_key = ("dokument", "jazyk")
    primary_key_filter_field = ("dokument__ident_cely", "jazyk__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["jazyk"] = LookupImportField(Heslar)
        return field_mapping


class DokumentOsobaMapper(ImportModelMapper):
    model_class = DokumentOsoba
    primary_key = ("dokument", "osoba")
    primary_key_filter_field = ("dokument__ident_cely", "osoba__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["osoba"] = LookupImportField(Osoba)
        return field_mapping


class DokumentPosudekMapper(ImportModelMapper):
    model_class = DokumentPosudek
    primary_key = ("dokument", "posudek")
    primary_key_filter_field = ("dokument__ident_cely", "posudek__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["posudek"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_POSUDEK_TYP})
        return field_mapping


class TvarMapper(ImportModelMapper):
    fields = ("poznamka",)
    model_class = Tvar
    primary_key = "id"
    primary_key_prefix = "tvar"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["tvar"] = LookupImportField(Heslar)
        return field_mapping


class DokumentCastMapper(ImportModelMapper):
    fields = ("ident_cely", "poznamka")
    model_class = DokumentCast

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["projekt"] = LookupImportField(Projekt)
        return field_mapping


class NeidentAkceMapper(ImportModelMapper):
    fields = ("rok_zahajeni", "rok_ukonceni", "lokalizace", "popis", "poznamka", "pian")
    model_class = NeidentAkce
    primary_key = "dokument_cast"
    primary_key_filter_field = "dokument_cast__ident_cely"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument_cast"] = LookupImportField(DokumentCast)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping


class NeidentAkceVedouciMapper(ImportModelMapper):
    model_class = NeidentAkceVedouci
    primary_key = ("neident_akce", "vedouci")
    primary_key_filter_field = ("neident_akce__dokument_cast__ident_cely", "vedouci__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["neident_akce"] = LookupImportField(DokumentCast)
        field_mapping["vedouci"] = LookupImportField(Osoba)
        return field_mapping


class KomponentaMapper(ImportModelMapper):
    fields = ("ident_cely", "jistota", "presna_datace", "poznamka")
    model_class = Komponenta
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vazba"] = VazbaLookupImportField(
            (DokumentacniJednotka, DokumentCast), read_field_name="komponenty"
        )
        field_mapping["obdobi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBDOBI})
        field_mapping["areal"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_AREAL})
        return field_mapping


class KomponentaAktivitaMapper(ImportModelMapper):
    model_class = KomponentaAktivita
    primary_key = ("komponenta", "aktivita")
    primary_key_filter_field = ("komponenta__ident_cely", "aktivita__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["aktivita"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_AKTIVITA})
        return field_mapping


class NalezMapper(ImportModelMapper):
    fields = ("pocet", "poznamka")
    primary_key = "id"


class NalezObjektMapper(NalezMapper):
    model_class = NalezObjekt
    primary_key_prefix = "nalo"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["druh"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_DRUH})
        field_mapping["specifikace"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_SPECIFIKACE}
        )
        return field_mapping


class NalezPredmetMapper(NalezMapper):
    model_class = NalezPredmet
    primary_key_prefix = "nalp"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["druh"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PREDMET_DRUH})
        field_mapping["specifikace"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PREDMET_SPECIFIKACE}
        )
        return field_mapping


class ExterniZdrojMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "doi",
        "stav",
        "rok_vydani_vzniku",
        "nazev",
        "sbornik_nazev",
        "edice_rada",
        "casopis_denik_nazev",
        "casopis_rocnik",
        "isbn",
        "issn",
        "misto",
        "vydavatel",
        "datum_rd",
        "paginace_titulu",
        "link",
        "organizace",
        "poznamka",
    )
    model_class = ExterniZdroj
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_EXTERNI_ZDROJ_TYP})
        field_mapping["typ_dokumentu"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP}
        )
        return field_mapping


class ExterniZdrojAutorMapper(ImportModelMapper):
    fields = ("poradi",)
    primary_key = ("externi_zdroj", "autor")
    primary_key_filter_field = ("externi_zdroj__ident_cely", "autor__ident_cely")
    model_class = ExterniZdrojAutor

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        field_mapping["autor"] = LookupImportField(Osoba)
        return field_mapping


class ExterniZdrojEditorMapper(ImportModelMapper):
    fields = ("poradi",)
    primary_key = ("externi_zdroj", "editor")
    primary_key_filter_field = ("externi_zdroj__ident_cely", "editor__ident_cely")
    model_class = ExterniZdrojEditor

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        field_mapping["editor"] = LookupImportField(Osoba)
        return field_mapping


class ExterniOdkazMapper(ImportModelMapper):
    fields = ("paginace",)
    model_class = ExterniOdkaz
    primary_key = "id"
    primary_key_prefix = "exto"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        return field_mapping


class UzivatelMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "first_name",
        "last_name",
        "email",
        "telefon",
        "orcid",
        "jazyk",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_login",
    )
    model_class = User
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["osoba"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        return field_mapping


class UzivatelNotifikaceProjektMapper(ImportModelMapper):
    model_class = Pes
    primary_key = ("uzivatel", "ruian")
    primary_key_prefix = (None, "ruian")
    column_to_field_mapping = {"uzivatel": "user"}

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(False)
        field_mapping["uzivatel"] = LookupImportField(User, "ident_cely")
        field_mapping["ruian"] = GenericForeignKeyImportField([RuianKatastr, RuianOkres, RuianKraj], "kod", "kod")
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        primary_key_import_field: GenericForeignKeyImportField = self.get_mapping()["ruian"]
        content_object = primary_key_import_field._process_value(self.value_dict["ruian"])
        return {
            "user__ident_cely": self.value_dict["uzivatel"],
            "content_type": ContentType.objects.get_for_model(content_object),
            "object_id": content_object.pk,
        }

    @classmethod
    def map_field(cls, field_name):
        if field_name == "uzivatel":
            field_name = "user"
        return super().map_field(field_name)


class UzivatelSpolupraceMapper(ImportModelMapper):
    fields = ("stav",)
    model_class = UzivatelSpoluprace
    primary_key = "id"
    primary_key_prefix = "spol"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vedouci"] = LookupImportField(User)
        field_mapping["spolupracovnik"] = LookupImportField(User)
        return field_mapping


class UzivatelOpravneniMapper(ImportModelMapper):
    model_class = User
    primary_key = ("uzivatel", "skupina")
    column_to_field_mapping = {"uzivatel": "ident_cely"}

    def get_mapping(cls, include_primary_key=False):
        field_mapping = {"uzivatel": LookupImportField(User), "skupina": LookupImportField(Group, "name")}
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        return {"ident_cely": self.value_dict["uzivatel"]}

    def create_records(self, performed_action):
        return [User.objects.get(ident_cely=self.value_dict["uzivatel"])]

    def import_validation(self, performed_action):
        return self._get_filter_kwargs_primary_key()


class SouborMapper(ImportModelMapper):
    fields = (
        "path",
        "nazev",
        "mimetype",
        "rozsah",
        "size_mb",
        "sha_512",
    )
    model_class = Soubor
    primary_key = "id"
    primary_key_prefix = "soub"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vazba"] = VazbaLookupImportField(read_field_name="soubory")
        return field_mapping


class UzivatelNotifikaceMapper(ImportModelMapper):
    model_class = User
    primary_key = ("uzivatel", "notifikace")
    column_to_field_mapping = {"uzivatel": "ident_cely"}

    def get_mapping(cls, include_primary_key=False):
        field_mapping = {"uzivatel": LookupImportField(User), "notifikace": LookupImportField(UserNotificationType)}
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        return {"ident_cely": self.value_dict["uzivatel"]}

    def create_records(self, performed_action):
        return [User.objects.get(ident_cely=self.value_dict["uzivatel"])]

    def import_validation(self, performed_action):
        return self._get_filter_kwargs_primary_key()


class HistorieMapper(ImportModelMapper):
    fields = (
        "datum_zmeny",
        "typ_zmeny",
        "poznamka",
    )
    model_class = Historie
    primary_key = "id"
    primary_key_prefix = "hist"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vazba"] = VazbaLookupImportField(read_field_name="historie")
        field_mapping["uzivatel"] = LookupImportField(User)
        return field_mapping
