import re
from abc import ABC

from arch_z.models import AkceVedouci, ArcheologickyZaznam
from django.db import models
from django.utils.translation import gettext_lazy as _
from heslar.models import (
    Heslar,
    HeslarDatace,
    HeslarDokumentTypMaterialRada,
    HeslarHierarchie,
    HeslarNazev,
    HeslarOdkaz,
    RuianKatastr,
)
from lokalita.models import Lokalita
from pas.models import SamostatnyNalez
from projekt.models import Projekt, ProjektKatastr
from uzivatel.models import Organizace, Osoba


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


class ImportDataIntegrityError(ImportDataError):
    def __init__(self, record_id, model_name):
        self.record_id = record_id
        self.model_name = model_name
        super().__init__(
            f'{_("core_admin.ImportDataIntegrityError.message.part_1")} '
            + f'{record_id} {_("core_admin.ImportDataIntegrityError.message.part_2")} '
            + f'{model_name} {_("core_admin.ImportDataIntegrityError.message.part_2")} '
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

    @property
    def instance_value(self):
        return self._value

    def _process_value(self, value):
        return value


class IntegerImportField(BaseImportField):
    pattern = re.compile(r"\d+")

    def _process_value(self, value):
        if isinstance(value, int):
            value = str(value)
        elif isinstance(value, bytes):
            value = value.decode("utf-8")
        value = self.pattern.search(value).group()
        if value:
            return int(value) if value is not None else None
        else:
            raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_integer_value')}: {value}")


class LookupImportField(BaseImportField):
    records = []

    def __init__(self, lookup_model_class, lookup_field_name: str = "ident_cely"):
        super().__init__()
        self.lookup_model_class = lookup_model_class
        self.lookup_field_name = lookup_field_name
        self._instance_value = None

    @property
    def instance_value(self):
        return self._instance_value

    def _process_value(self, value):
        saved_records_query = self.lookup_model_class.objects.filter(**{self.lookup_field_name: value})
        if saved_records_query.exists():
            self._instance_value = saved_records_query.first()
            return value
        filtered_records = [
            record
            for record in self.records
            if isinstance(record, self.lookup_model_class) and getattr(record, self.lookup_field_name, None) == value
        ]
        if len(filtered_records) == 1:
            return value
        raise ImportDataMissingReferencedValueError(value, self.lookup_model_class.__name__)


class ImportModelMapper(ABC):
    fields = tuple()
    model_class = None
    private_key_field = "ident_cely"

    def __init__(self, value_dict):
        self.value_dict = value_dict

    @classmethod
    def get_import_data_mapper_dict(cls):
        return {
            "heslar": HeslarMapper,
            "heslar_datace": HeslarDataceMapper,
            "heslar_dokument_typ_material_rada": HeslarDokumentTypMaterialRadaMapper,
            "heslar_hierarchie": HeslarHierarchieMapper,
            "heslar_odkaz": HeslarOdkazMapper,
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

    def create_record(self):
        mapping_dict = self.map(True)
        return self.model_class(**mapping_dict)

    def import_validation(self, error_when_exists=True):
        if self.private_key_field:
            mapping_dict = self.map()
            if error_when_exists and self.model_class.objects.filter(pk=mapping_dict[self.private_key_field]).exists():
                raise ImportDataIntegrityError(mapping_dict[self.private_key_field], self.model_class.__name__)
            elif (
                not error_when_exists
                and not self.model_class.objects.filter(pk=mapping_dict[self.private_key_field]).exists()
            ):
                raise ImportDataIntegrityError(mapping_dict[self.private_key_field], self.model_class.__name__)

    def map(self, instance_values=False):
        mapping_dict = {}
        for field_name, field_instance in self.get_mapping().items():
            field_value = self.value_dict[field_name]
            field_instance.value = field_value
            if instance_values:
                mapping_dict[field_name] = field_instance.instance_value
            else:
                mapping_dict[field_name] = field_instance.value
        return mapping_dict


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
    private_key_field = "id"

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
    private_key_field = "id"

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
    private_key_field = "id"

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
        "typ_projektu",
        "hlavni_katastr",
        "lokalizace",
        "parcelni_cislo",
        "geom",
        "podnet",
        "planovane_zahajeni",
        "vedouci_projektu",
        "organizace",
        "uzivatelske_oznaceni",
        "oznaceni_stavby",
        "kulturni_pamatka",
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
        field_mapping["typ_projektu"] = LookupImportField(Organizace)
        field_mapping["hlavni_katastr"] = LookupImportField(RuianKatastr, "id")
        field_mapping["vedouci_projektu"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        field_mapping["kulturni_pamatka"] = LookupImportField(Organizace)
        return field_mapping


class ProjektKatastrMapper(ImportModelMapper):
    fields = ("projekt", "katastr")
    model_class = ProjektKatastr

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["projekt"] = LookupImportField(Projekt)
        field_mapping["katastr"] = LookupImportField(RuianKatastr, "kod")
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
        field_mapping["katastr"] = LookupImportField(RuianKatastr, "kod")
        field_mapping["okolnosti"] = LookupImportField(Heslar)
        field_mapping["nalezce"] = LookupImportField(Osoba)
        field_mapping["predano_organizace"] = LookupImportField(Organizace)
        field_mapping["obdobi"] = LookupImportField(Heslar)
        field_mapping["druh_nalezu"] = LookupImportField(Heslar)
        field_mapping["specifikace"] = LookupImportField(Heslar)
        return field_mapping


class ArcheologickyZaznamAkceMapper(ImportModelMapper):
    fields = (
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
    )
    model_class = ArcheologickyZaznam


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
    private_key_field = "id"

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["akce"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["vedouci"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        return field_mapping
