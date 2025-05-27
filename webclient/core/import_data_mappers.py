from abc import ABC

from django.db import models
from django.utils.translation import gettext_lazy as _
from heslar.models import Heslar, HeslarDatace, HeslarNazev


class ImportDataError(Exception):
    pass


class ImportDataMissingReferencedValueError(ImportDataError):
    def __init__(self, missing_value_id, missing_model_name):
        self.missing_value_id = missing_value_id
        self.missing_model_name = missing_model_name
        super().__init__(
            f'{_("core_admin.ImportDataMissingReferencedValueError.message.part_1")} '
            + f'{missing_value_id} {_("core_admin.ImportDataMissingReferencedValueError.message.part_2")} '
            + f'{missing_model_name} {_("core_admin.ImportDataMissingReferencedValueError.message.part_2")} '
        )


class BaseImportField:
    def __init__(self):
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = self._process_value(value)

    def _process_value(self, value):
        return value


class IntegerImportField(BaseImportField):
    def _process_value(self, value):
        return int(value) if value is not None else None


class LookupImportField(BaseImportField):
    records = []

    def __init__(self, lookup_model_class, lookup_field_name: str):
        super().__init__()
        self.lookup_model_class = lookup_model_class
        self.lookup_field_name = lookup_field_name

    def _process_value(self, value):
        saved_records_query = self.lookup_model_class.objects.filter(**{self.lookup_field_name: value})
        if saved_records_query.exists():
            self._value = saved_records_query.first()
            return
        filtered_records = [
            record
            for record in self.records
            if isinstance(record, self.lookup_model_class) and getattr(record, self.lookup_field_name, None) == value
        ]
        if len(filtered_records) == 1:
            self._value = filtered_records[0]
            return
        raise ImportDataMissingReferencedValueError(value, self.lookup_model_class.__name__)


class ImportModelMapper(ABC):
    fields = tuple()
    model_class = None

    def __init__(self, value_dict):
        self.value_dict = value_dict

    @classmethod
    def get_import_data_mapper_dict(cls):
        return {
            "heslar": HeslarMapper,
            "heslar_datace": HeslarDataceMapper,
        }

    @classmethod
    def get_import_data_mapper(cls, file_name):
        return cls.get_import_data_mapper_dict().get(file_name.split(".")[0])

    @classmethod
    def get_mapping(cls):
        field_mapping = {}
        for item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        return field_mapping

    @classmethod
    def map_field(cls, field_name):
        model_field = cls.model_class._meta.get_field(field_name)
        if isinstance(model_field, models.TextField) or isinstance(model_field, models.CharField):
            return BaseImportField()
        if isinstance(model_field, models.IntegerField):
            return IntegerImportField()

    def map(self):
        mapping_dict = {}
        for field_name, field_instance in self.get_mapping().items():
            field_value = self.value_dict[field_name]
            field_instance.value = field_value
            mapping_dict[field_name] = field_instance.value
        return self.model_class(**mapping_dict)


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

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["nazev_heslare"] = LookupImportField(HeslarNazev, "nazev")
        return field_mapping

    model_class = Heslar


class HeslarDataceMapper(ImportModelMapper):
    fields = (
        "obdobi",
        "rok_od_min",
        "rok_od_max",
        "rok_do_min",
        "rok_do_max",
        "poznamka",
    )

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["obdobi"] = LookupImportField(Heslar, "ident_cely")
        return field_mapping

    model_class = HeslarDatace
