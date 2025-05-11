from abc import ABC

from heslar.models import Heslar, HeslarNazev


class BaseField:
    def __init__(self):
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class IntegerField(BaseField):
    def set_value(self, value):
        self._value = int(value)


class LookupField(BaseField):
    def __init__(self, lookup_model_class, lookup_field_name: str):
        super().__init__()
        self.lookup_model_class = lookup_model_class
        self.lookup_field_name = lookup_field_name

    @BaseField.value.setter
    def value(self, value):
        self._value = self.lookup_model_class.objects.get(**{self.lookup_field_name: value})


class ImportModelMapper(ABC):
    field_mapping = {}
    model_class = None

    def __init__(self, value_dict):
        self.value_dict = value_dict

    @classmethod
    def get_import_data_mapper(cls, file_name):
        return {
            "heslar": HeslarMapper,
        }.get(file_name.split(".")[0])

    def map(self):
        mapping_dict = {}
        for field_name, field_class in self.field_mapping.items():
            field_value = self.value_dict[field_name]
            field_instance = self.field_mapping[field_name]
            field_instance.value = field_value
            mapping_dict[field_name] = field_instance.value
        return self.model_class(**mapping_dict)


class HeslarMapper(ImportModelMapper):
    field_mapping = {
        "ident_cely": BaseField(),
        "nazev_heslare": LookupField(HeslarNazev, "nazev"),
        "heslo": BaseField(),
        "heslo_en": BaseField(),
        "popis": BaseField(),
        "popis_en": BaseField(),
        "zkratka": BaseField(),
        "razeni": IntegerField(),
    }
    model_class = Heslar
