import datetime
import re
from abc import ABC
from collections.abc import Iterable

from adb.models import Adb, VyskovyBod
from arch_z.models import Akce, AkceVedouci, ArcheologickyZaznam, ArcheologickyZaznamKatastr, ExterniOdkaz
from core.constants import DOKUMENT_RELATION_TYPE
from core.forms import ImportDataAdminForm
from core.ident_cely import get_record_from_ident
from core.models import Soubor, SouborVazby
from dj.models import DokumentacniJednotka
from django.contrib.gis.db import models as pgmodels
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.postgres.fields import DateRangeField
from django.db import models
from django.db.backends.postgresql.psycopg_any import DateRange
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
from heslar.models import (
    Heslar,
    HeslarDatace,
    HeslarDokumentTypMaterialRada,
    HeslarHierarchie,
    HeslarNazev,
    HeslarOdkaz,
    RuianKatastr,
)
from historie.models import Historie, HistorieVazby
from komponenta.models import Komponenta, KomponentaAktivita
from lokalita.models import Lokalita
from nalez.models import NalezObjekt, NalezPredmet
from neidentakce.models import NeidentAkce, NeidentAkceVedouci
from notifikace_projekty.models import Pes
from pas.models import SamostatnyNalez, UzivatelSpoluprace
from pian.models import Kladyzm, Pian
from projekt.models import Projekt, ProjektKatastr
from uzivatel.models import Organizace, Osoba, User


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
        if isinstance(value, int):
            value = str(value)
        elif isinstance(value, bytes):
            value = value.decode("utf-8")
        value = self.pattern.search(value).group()
        if value:
            return int(value) if value is not None else None
        else:
            raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_integer_value')}: {value}")


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
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
        raise ImportDataError(f"{_('core_admin.BooleanImportField.message.invalid_boolean_value')}: {value}")


class DateImportField(BaseImportField):
    """
    Class for import fields that should contain date values.
    """

    pattern_iso = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")
    pattern_localized = re.compile(r"\d{1,2}\. ?\d{1,2}\. ?\d{4}")

    def value(self):
        return self._value.isoformat() if self._value else None

    def _process_value(self, value) -> datetime.date | None:
        """
        Tries to convert a string value to date. If the string value is not in the format "YYYY-MM-DD" or "DD.MM.YYYY",
        then the exception ImportDataError is raised.
        """

        if not value:
            return None
        if isinstance(value, str):
            if self.pattern_iso.match(value):
                return datetime.datetime.strptime(value, "%Y-%m-%d").date()
            if self.pattern_localized.match(value):
                return datetime.datetime.strptime(value.replace(" ", ""), "%d.%m.%Y").date()
        elif isinstance(value, datetime.date):
            return value
        raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_date_value')}: {value}")


class DateRangeImportField(BaseImportField):
    """
    Class for import fields that should contain date values.
    """

    pattern = re.compile(r"\[\d{4}-\d{1,2}-\d{1,2},\d{4}-\d{1,2}-\d{1,2}\)")

    @property
    def serialized_value(self):
        return f"[{self.value.lower.strftime('%Y-%m-%d')},{self.value.upper.strftime('%Y-%m-%d')})"

    def _process_value(self, value) -> DateRange | None:
        """
        Tries to convert a string value to date. If the string value is not in the format "YYYY-MM-DD" or "DD.MM.YYYY",
        then the exception ImportDataError is raised.
        """

        if not value:
            return None
        if isinstance(value, str):
            if self.pattern.fullmatch(value):
                start, end = value.strip("[)").split(",")
                start = datetime.datetime.strptime(start, "%Y-%m-%d").date()
                end = datetime.datetime.strptime(end, "%Y-%m-%d").date()
                return DateRange(start, end)
        raise ImportDataError(f"{_('core_admin.DateRangeImportField.message.invalid_date_range_value')}: {value}")


class LookupImportField(BaseImportField):
    """
    Class for import fields that should contain a reference to another model instance.
    """

    records = []

    def __init__(self, lookup_model_classes=None, lookup_field_name: str = "ident_cely"):
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

    @property
    def instance_value(self):
        return self._instance_value

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
                self._instance_value = saved_records_query.first()
                return value
            filtered_records = [
                record
                for record in self.records
                if isinstance(record, current_class) and getattr(record, self.lookup_field_name, None) == value
            ]
            if len(filtered_records) == 1:
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


class KomponentaLookupImportField(LookupImportField):
    """
    Class for import field with referenced models for Komponenta.
    """

    def __init__(self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", read_field_name: str = None):
        super().__init__(lookup_model_classes, lookup_field_name)
        self.read_field_name = read_field_name

    def _process_value(self, value):
        record = get_record_from_ident(value)
        if isinstance(record, Dokument):
            self._instance_value = DokumentCast.objects.get(ident_cely=value)
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


class GeomImportField(BaseImportField):
    """
    Class for import fields that should contain boolean values.
    """

    def __init__(self, srid):
        super().__init__()
        self.srid = srid

    @property
    def serialized_value(self):
        return getattr(self._value, "wkt", None)

    def _process_value(self, value) -> GEOSGeometry | None:
        """
        Tries to convert string value to bool. If the string value is not "true" or "false", then the exception
        ImportDataError is raised.
        """
        if not value:
            return None
        if isinstance(value, str):
            value = GEOSGeometry(value, srid=self.srid)
        if isinstance(value, GEOSGeometry):
            return value
        raise ImportDataError(f"{_('core_admin.GeomImportField.message.invalid_date_value')}: {value}")


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
            "projekt_oznamovatele": ProjektOznamovatelMapper,
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
    def get_mapping(cls):
        """
        Map imported values using the map_field method.
        """

        field_mapping = {}
        for item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        """
        Returns a dict with primary key field name(s) and field value(s).
        """

        if isinstance(self.primary_key, str):
            primary_key_filter_field = self.primary_key_filter_field or self.primary_key
            return {primary_key_filter_field: self.value_dict[self.primary_key]}
        elif isinstance(self.primary_key, Iterable):
            if self.primary_key_filter_field:
                primary_key_zipped = zip(self.primary_key, self.primary_key_filter_field)
                return {
                    primary_key_filter_field: self.value_dict[primary_key]
                    for primary_key, primary_key_filter_field in primary_key_zipped
                }
            else:
                return {key: self.value_dict[key] for key in self.primary_key}

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
        if isinstance(model_field, models.DateField):
            return BaseImportField()
        if isinstance(model_field, models.BooleanField):
            return BooleanImportField()
        if isinstance(model_field, pgmodels.PointField):
            return GeomImportField(model_field.srid)
        if isinstance(model_field, DateRangeField):
            return DateRangeImportField()
        raise ImportDataError(f"_('core.admin.ImportModelMapper.map_field.error'): {field_name}")

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
                if field_name != self.primary_key:
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

        if self.primary_key:
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

    def map(self, performed_action, instance_values=False, serialize=False) -> dict:
        """
        Checks if the file columns structure is valid as the first step. If not, the ImportDataIncorrectStructureError
        exception is raised. Then it creates a dict with field names as keys and values are instances of
        BaseImportField class or one of its child classes with values loaded from the import file.
        """

        mapping_dict = {}
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            mapping_column_set = set(self.value_dict.keys())
            value_dict_column_set = set(self.get_mapping().keys())
            if mapping_column_set != value_dict_column_set:
                excess_columns = mapping_column_set - value_dict_column_set
                missing_columns = value_dict_column_set - mapping_column_set
                raise ImportDataIncorrectStructureError(missing_columns, excess_columns)
        for field_name, field_instance in self.get_mapping().items():
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


class MultipleClassImportModelMapper(ImportModelMapper):
    foreign_key_fields = tuple()

    def import_validation(self, performed_action):
        if (
            performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT
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

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["nazev_heslare"] = LookupImportField(HeslarNazev, "nazev")
        return field_mapping


class HeslarDataceMapper(ImportModelMapper):
    fields = (
        "obdobi",
        "rok_od_min",
        "rok_od_max",
        "rok_do_min",
        "rok_do_max",
        "poznamka",
    )
    model_class = HeslarDatace

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["obdobi"] = LookupImportField(Heslar)
        return field_mapping


class HeslarDokumentTypMaterialRadaMapper(ImportModelMapper):
    fields = ("id",)
    model_class = HeslarDokumentTypMaterialRada
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["dokument_typ"] = LookupImportField(Heslar)
        field_mapping["dokument_material"] = LookupImportField(Heslar)
        field_mapping["dokument_rada"] = LookupImportField(Heslar)
        return field_mapping


class HeslarHierarchieMapper(ImportModelMapper):
    fields = ("typ",)
    model_class = HeslarHierarchie
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["heslo_nadrazene"] = LookupImportField(Heslar)
        field_mapping["heslo_podrazene"] = LookupImportField(Heslar)
        return field_mapping


class HeslarOdkazMapper(ImportModelMapper):
    fields = (
        "id",
        "zdroj",
        "nazev_kodu" "kod",
        "uri",
        "skos_mapping_relation",
    )
    model_class = HeslarOdkaz
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
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
    )
    model_class = Organizace

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["soucast"] = LookupImportField(Organizace)
        field_mapping["typ_organizace"] = LookupImportField(Heslar)
        field_mapping["zverejneni_pristupnost"] = LookupImportField(Heslar)
        return field_mapping


class OsobaMapper(ImportModelMapper):
    fields = ("ident_cely", "vypis_cely", "vypis", "jmeno", "prijmeni", "rodne_prijmeni", "rok_narozeni", "rok_umrti")
    model_class = Osoba


class ProjektMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "stav",
        "lokalizace",
        "parcelni_cislo",
        "geom",
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

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["typ_projektu"] = LookupImportField(Heslar)
        field_mapping["hlavni_katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        field_mapping["vedouci_projektu"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        field_mapping["kulturni_pamatka"] = LookupImportField(Heslar)
        return field_mapping


class ProjektKatastrMapper(ImportModelMapper):
    fields = ("projekt", "katastr")
    model_class = ProjektKatastr

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["projekt"] = LookupImportField(Projekt)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping


class ProjektOznamovatelMapper(ImportModelMapper):
    fields = ("projekt", "oznamovatel", "odpovedna_osoba", "adresa", "telefon", "email", "poznamka")
    model_class = ProjektKatastr

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["ident_cely"] = LookupImportField(Projekt)
        return field_mapping


class SamostatnyNalezMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "stav",
        "evidencni_cislo",
        "lokalizace",
        "geom_system",
        "geom_updated_at",
        "geom_sjtsk_updated_at",
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

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["projekt"] = LookupImportField(Projekt)
        field_mapping["pristupnost"] = LookupImportField(Heslar)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        field_mapping["okolnosti"] = LookupImportField(Heslar)
        field_mapping["nalezce"] = LookupImportField(Osoba)
        field_mapping["predano_organizace"] = LookupImportField(Organizace)
        field_mapping["obdobi"] = LookupImportField(Heslar)
        field_mapping["druh_nalezu"] = LookupImportField(Heslar)
        field_mapping["specifikace"] = LookupImportField(Heslar)
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
        ("archeologicky_zaznam", "projekt"),
        ("archeologicky_zaznam", "pristupnost"),
        ("archeologicky_zaznam", "hlavni_katastr"),
        ("akce", "hlavni_vedouci"),
        ("akce", "organizace"),
        ("akce", "specifikace_data"),
        ("akce", "hlavni_typ"),
        ("akce", "vedlejsi_typ"),
    )
    model_class = ArcheologickyZaznam

    @classmethod
    def get_mapping(cls):
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping["projekt"] = LookupImportField(Projekt)
        field_mapping["pristupnost"] = LookupImportField(Heslar)
        field_mapping["hlavni_katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        field_mapping["hlavni_vedouci"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        field_mapping["specifikace_data"] = LookupImportField(Heslar)
        field_mapping["hlavni_typ"] = LookupImportField(Heslar)
        field_mapping["vedlejsi_typ"] = LookupImportField(Heslar)
        return field_mapping

    def _get_filter_kwargs_primary_key(self):
        return {"ident_cely": self.value_dict["ident_cely"]}

    @classmethod
    def map_field(cls, field_name):
        mapping_dict = {
            "je_nz": BooleanImportField(),
            "odlozena_nz": BooleanImportField(),
            "projekt": LookupImportField(Projekt),
            "pristupnost": LookupImportField(Heslar),
            "hlavni_katastr": RuianLookupImportField(RuianKatastr, "kod"),
            "hlavni_vedouci": LookupImportField(Osoba),
            "organizace": LookupImportField(Organizace),
            "specifikace_data": LookupImportField(Heslar),
            "hlavni_typ": LookupImportField(Heslar),
            "vedlejsi_typ": LookupImportField(Heslar),
        }
        return mapping_dict.get(field_name, BaseImportField())

    def create_records(self, performed_action) -> list:
        """
        Creates ArcheologickyZaznam instance and Akce instance with relationship set to the ArcheologickyZaznam.
        """

        arch_z_fields = [
            item for model, item in self.fields + self.foreign_key_fields if model == "archeologicky_zaznam"
        ]
        akce_fields = [item for model, item in self.fields + self.foreign_key_fields if model == "akce"]
        mapping_dict = self.map(performed_action, True)
        mapping_dict_arch_z = {field: mapping_dict[field] for field in arch_z_fields}
        mapping_dict_akce = {field: mapping_dict[field] for field in akce_fields}
        mapping_dict_arch_z = {
            self.map_column_name_to_field_name(field): value for field, value in mapping_dict_arch_z.items()
        }
        mapping_dict_akce = {
            self.map_column_name_to_field_name(field): value for field, value in mapping_dict_akce.items()
        }
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            arch_z = ArcheologickyZaznam(**mapping_dict_arch_z)
            akce = Akce(**mapping_dict_akce)
            akce.archeologicky_zaznam = arch_z
            return [arch_z, akce]
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE:
            arch_z = ArcheologickyZaznam.objects.get(ident_cely=mapping_dict["ident_cely"])
            akce = Akce.objects.get(archeologicky_zaznam=arch_z)
            for field_name, field_value in mapping_dict_arch_z.items():
                setattr(arch_z, field_name, field_value)
            for field_name, field_value in mapping_dict_akce.items():
                setattr(akce, field_name, field_value)
            return [arch_z, akce]
        return []


class LokalitaMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "stav",
        "pristupnost",
        "hlavni_katastr",
        "nazev",
        "uzivatelske_oznaceni",
        "typ_lokality",
        "druh",
        "zachovalost",
        "jistota",
        "popis",
        "poznamka",
    )
    model_class = Lokalita


class AkceVedouciMapper(ImportModelMapper):
    fields = ("id", "akce", "vedouci", "organizace")
    model_class = AkceVedouci
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["akce"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["vedouci"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        return field_mapping


class ArcheologickyZaznamKatastrMapper(ImportModelMapper):
    fields = ("archeologicky_zaznam", "katastr")
    model_class = ArcheologickyZaznamKatastr
    primary_key = ("archeologicky_zaznam", "katastr")

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping


class PianMapper(ImportModelMapper):
    fields = ("ident_cely", "stav", "geom_system", "geom", "geom_sjtsk")
    model_class = Pian

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["typ"] = LookupImportField(Projekt)
        field_mapping["presnost"] = LookupImportField(Projekt)
        field_mapping["zm10"] = LookupImportField(Kladyzm, "gid")
        field_mapping["zm50"] = LookupImportField(Kladyzm, "gid")
        return field_mapping


class DokumentacniJednotkaMapper(ImportModelMapper):
    fields = ("ident_cely", "negativni_jednotka", "nazev")
    model_class = DokumentacniJednotka

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["pian"] = LookupImportField(Pian)
        field_mapping["typ"] = LookupImportField(Heslar)
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

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["dokumentacni_jednotka"] = LookupImportField(DokumentacniJednotka)
        field_mapping["typ_sondy"] = LookupImportField(Heslar)
        field_mapping["podnet"] = LookupImportField(Heslar)
        field_mapping["autor_popisu"] = LookupImportField(Osoba)
        field_mapping["autor_popisu"] = LookupImportField(Osoba)
        field_mapping["sm5"] = LookupImportField(Kladyzm, "gid")
        return field_mapping


class AdbVyskovyBod(ImportModelMapper):
    fields = ("ident_cely", "geom")
    model_class = VyskovyBod

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["adb"] = LookupImportField(Adb)
        field_mapping["typ"] = LookupImportField(Heslar)
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
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["letiste_start"] = LookupImportField(Heslar)
        field_mapping["letiste_cil"] = LookupImportField(Heslar)
        field_mapping["pozorovatel"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        field_mapping["pocasi"] = LookupImportField(Heslar)
        field_mapping["dohlednost"] = LookupImportField(Heslar)
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
    model_class = Dokument
    historie_typ_vazby = DOKUMENT_RELATION_TYPE
    soubory_typ_vazby = DOKUMENT_RELATION_TYPE

    @classmethod
    def get_mapping(cls):
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping["let"] = LookupImportField(Let)
        field_mapping["typ_dokumentu"] = LookupImportField(Heslar)
        field_mapping["material_originalu"] = LookupImportField(Heslar)
        field_mapping["rada"] = LookupImportField(Heslar)
        field_mapping["organizace"] = LookupImportField(Organizace)
        field_mapping["pristupnost"] = LookupImportField(Heslar)
        field_mapping["ulozeni_originalu"] = LookupImportField(Heslar)
        field_mapping["licence"] = LookupImportField(Heslar)
        field_mapping["format"] = LookupImportField(Heslar)
        field_mapping["zachovalost"] = LookupImportField(Heslar)
        field_mapping["nahrada"] = LookupImportField(Heslar)
        field_mapping["udalost_typ"] = LookupImportField(Heslar)
        field_mapping["zeme"] = LookupImportField(Heslar)
        return field_mapping

    def _get_filter_kwargs_primary_key(self):
        return {"ident_cely": self.value_dict["ident_cely"]}

    @classmethod
    def map_field(cls, field_name):
        mapping_dict = {
            "let": LookupImportField(Let),
            "typ_dokumentu": LookupImportField(Heslar),
            "material_originalu": LookupImportField(Heslar),
            "rada": LookupImportField(Heslar),
            "organizace": LookupImportField(Organizace),
            "rok_vzniku": IntegerImportField(),
            "pristupnost": LookupImportField(Heslar),
            "ulozeni_originalu": LookupImportField(Heslar),
            "stav": IntegerImportField(),
            "datum_zverejneni": DateImportField(),
            "licence": LookupImportField(Heslar),
            "format": LookupImportField(Heslar),
            "datum_vzniku": DateImportField(),
            "zachovalost": LookupImportField(Heslar),
            "nahrada": LookupImportField(Heslar),
            "pocet_variant_originalu": IntegerImportField(),
            "udalost_typ": LookupImportField(Heslar),
            "zeme": LookupImportField(Heslar),
            "rok_od": IntegerImportField(),
            "rok_do": IntegerImportField(),
            "duveryhodnost": IntegerImportField(),
            "geom": IntegerImportField(),
            "geom_sjtsk": IntegerImportField(),
        }
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


class DokumentAutorMapper(MultipleClassImportModelMapper):
    fields = ("poradi",)
    model_class = DokumentAutor
    primary_key = ("dokument", "autor")

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["autor"] = LookupImportField(Osoba)
        return field_mapping


class DokumentJazykMapper(ImportModelMapper):
    fields = tuple()
    model_class = DokumentJazyk
    primary_key = ("dokument", "jazyk")

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["jazyk"] = LookupImportField(Heslar)
        return field_mapping


class DokumentOsobaMapper(ImportModelMapper):
    fields = tuple()
    model_class = DokumentOsoba
    primary_key = ("dokument", "osoba")

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["osoba"] = LookupImportField(Osoba)
        return field_mapping


class DokumentPosudekMapper(ImportModelMapper):
    fields = tuple()
    model_class = DokumentPosudek
    primary_key = ("dokument", "posudek")

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["posudek"] = LookupImportField(Heslar)
        return field_mapping


class TvarMapper(ImportModelMapper):
    fields = ("id", "poznamka")
    model_class = Tvar
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["tvar"] = LookupImportField(Heslar)
        return field_mapping


class DokumentCastMapper(ImportModelMapper):
    fields = ("ident_cely", "poznamka")
    model_class = DokumentCast
    primary_key = "ident_cely"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["projekt"] = LookupImportField(Projekt)
        return field_mapping


class NeidentAkceMapper(ImportModelMapper):
    fields = ("rok_zahajeni", "rok_ukonceni", "lokalizace", "popis", "poznamka", "pian")
    model_class = NeidentAkce
    primary_key = "ident_cely"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["dokument_cast"] = LookupImportField(DokumentCast)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping


class NeidentAkceVedouciMapper(ImportModelMapper):
    fields = tuple()
    model_class = NeidentAkceVedouci
    primary_key = ("neident_akce", "vedouci")

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["neident_akce"] = LookupImportField(DokumentCast)
        field_mapping["vedouci"] = LookupImportField(Osoba)
        return field_mapping


class KomponentaMapper(ImportModelMapper):
    fields = ("ident_cely", "jistota", "presna_datace", "poznamka")
    model_class = Komponenta
    primary_key = "ident_cely"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["vazba"] = KomponentaLookupImportField(
            [DokumentacniJednotka, DokumentCast], read_field_name="komponenty"
        )
        field_mapping["obdobi"] = LookupImportField(Heslar)
        field_mapping["areal"] = LookupImportField(Heslar)
        return field_mapping


class KomponentaAktivitaMapper(ImportModelMapper):
    fields = ()
    model_class = KomponentaAktivita
    primary_key = ("komponenta", "aktivita")

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["aktivita"] = LookupImportField(Heslar)
        return field_mapping


class NalezMapper(ImportModelMapper):
    fields = ("id", "pocet", "poznamka")
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["druh"] = LookupImportField(Heslar)
        field_mapping["specifikace"] = LookupImportField(Heslar)
        return field_mapping


class NalezObjektMapper(NalezMapper):
    model_class = NalezObjekt


class NalezPredmetMapper(NalezMapper):
    model_class = NalezPredmet


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
    primary_key = "ident_cely"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["typ"] = LookupImportField(Heslar)
        field_mapping["typ_dokumentu"] = LookupImportField(Heslar)
        return field_mapping


class ExterniZdrojOsobaMapper(ImportModelMapper):
    fields = ("poradi",)
    primary_key = ("externi_zdroj", "autor")
    primary_key_filter_field = ("externi_zdroj__ident_cely", "autor__ident_cely")

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        field_mapping["autor"] = LookupImportField(Osoba)
        return field_mapping


class ExterniZdrojAutorMapper(ExterniZdrojOsobaMapper):
    model_class = ExterniZdrojAutor


class ExterniZdrojEditorMapper(ExterniZdrojOsobaMapper):
    model_class = ExterniZdrojEditor


class ExterniOdkazMapper(ImportModelMapper):
    fields = ("id", "organizace")
    model_class = ExterniOdkaz
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
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

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["osoba"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        return field_mapping


class UzivatelNotifikaceProjektMapper(ImportModelMapper):
    fields = tuple()
    model_class = Pes

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["uzivatel"] = LookupImportField(User)
        return field_mapping


class UzivatelSpolupraceMapper(ImportModelMapper):
    fields = ("id", "stav")
    model_class = UzivatelSpoluprace
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["vedouci"] = LookupImportField(User)
        field_mapping["spolupracovnik"] = LookupImportField(User)
        return field_mapping


class UzivatelOpravneniMapper:
    pass


class UzivatelNotifikaceMapper:
    pass


class SouborMapper(ImportModelMapper):
    fields = (
        "id",
        "path",
        "nazev",
        "mimetype",
        "rozsah",
        "size_mb",
        "sha_512",
    )
    models_class = Soubor
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        return field_mapping


class HistorieMapper(ImportModelMapper):
    fields = (
        "id",
        "datum_zmeny",
        "typ_zmeny",
        "poznamka",
    )
    model_class = Historie
    primary_key = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["vazba"] = KomponentaLookupImportField(read_field_name="historie")
        field_mapping["uzivatel"] = LookupImportField(User)
        return field_mapping
