import datetime
import re
from abc import ABC
from collections.abc import Iterable

from adb.models import Adb, VyskovyBod
from arch_z.models import AkceVedouci, ArcheologickyZaznam, ArcheologickyZaznamKatastr, ExterniOdkaz
from core.forms import ImportDataAdminForm
from core.ident_cely import get_record_from_ident
from core.models import Soubor
from dj.models import DokumentacniJednotka
from django.db import models
from django.utils.translation import gettext_lazy as _
from dokument.models import (
    Dokument,
    DokumentAutor,
    DokumentCast,
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
from historie.models import Historie
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


class ImportDataMissingReferencedValueError(ImportDataError):
    def __init__(self, missing_value_id, missing_model_name=None):
        self.missing_value_id = missing_value_id
        self.missing_model_name = missing_model_name
        super().__init__(
            f'{_("core_admin.ImportDataMissingReferencedValueError.message.part_1")} '
            + f'{missing_value_id} {_("core_admin.ImportDataMissingReferencedValueError.message.part_2")} '
            + (
                f'{missing_model_name} {_("core_admin.ImportDataMissingReferencedValueError.message.part_2")} '
                if missing_model_name
                else ""
            )
        )


class ImportDataIntegrityError(ImportDataError):
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


class BooleanImportField(BaseImportField):
    def _process_value(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
        raise ImportDataError(f"{_('core_admin.BooleanImportField.message.invalid_boolean_value')}: {value}")


class DateImportField(BaseImportField):
    pattern_iso = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")
    pattern_localized = re.compile(r"\d{1,2}\. ?\d{1,2}\. ?\d{4}")

    def _process_value(self, value):
        if isinstance(value, str):
            if self.pattern_iso.match(value):
                return datetime.datetime.strptime(value, "%Y-%m-%d").date()
            if self.pattern_localized.match(value):
                return datetime.datetime.strptime(value.replace(" ", ""), "%d.%m.%Y").date()
        elif isinstance(value, datetime.date):
            return value
        raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_date_value')}: {value}")


class LookupImportField(BaseImportField):
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


class MultipleLookupImportField(LookupImportField):
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


class ImportModelMapper(ABC):
    fields = tuple()
    model_class = None
    primary_key = "ident_cely"

    def __init__(self, value_dict):
        self.value_dict = value_dict

    @classmethod
    def get_import_data_mapper_dict(cls):
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
        return cls.get_import_data_mapper_dict().get(file_name.split(".")[0])

    @classmethod
    def get_mapping(cls):
        field_mapping = {}
        for item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        return field_mapping

    def _get_filter_kwargs_primary_key(self):
        if isinstance(self.primary_key, str):
            return {self.primary_key: self.value_dict[self.primary_key]}
        elif isinstance(self.primary_key, Iterable):
            return {key: self.value_dict[key] for key in self.primary_key}

    @classmethod
    def map_field(cls, field_name):
        model_field = cls.model_class._meta.get_field(field_name)
        if isinstance(model_field, models.TextField) or isinstance(model_field, models.CharField):
            return BaseImportField()
        if isinstance(model_field, models.IntegerField):
            return IntegerImportField()
        if isinstance(model_field, models.DateField):
            return BaseImportField()
        if isinstance(model_field, models.BooleanField):
            return BooleanImportField()
        raise ImportDataError(f"_('core.admin.ImportModelMapper.map_field.error'): {field_name}")

    def create_records(self, performed_action) -> list:
        mapping_dict = self.map(True)
        if performed_action not in (
            ImportDataAdminForm.PERFORMED_ACTION_INSERT,
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        ):
            raise ImportDataError(
                f"{_('core_admin.ImportDataError.message.invalid_performed_action')}: {performed_action}"
            )
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            return [
                self.model_class(**mapping_dict),
            ]
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE:
            record = self.model_class.objects.get(**self._get_filter_kwargs_primary_key())
            for field_name, field_value in mapping_dict.items():
                if field_name != self.primary_key:
                    setattr(record, field_name, field_value)
            return [
                record,
            ]
        return []

    def import_validation(self, performed_action):
        if self.primary_key:
            mapping_dict = self.map()
            if (
                performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT
                and self.model_class.objects.filter(**self._get_filter_kwargs_primary_key()).exists()
            ):
                raise ImportDataIntegrityError(
                    mapping_dict[self.primary_key], self.model_class.__name__, performed_action
                )
            elif (
                performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE
                and not self.model_class.objects.filter(**self._get_filter_kwargs_primary_key()).exists()
            ):
                raise ImportDataIntegrityError(
                    mapping_dict[self.primary_key], self.model_class.__name__, performed_action
                )

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
        field_mapping["katastr"] = LookupImportField(RuianKatastr, "kod")
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


class DokumentMapper(ImportModelMapper):
    fields = (
        "ident_cely",
        "doi",
        "stav",
        "rok_vzniku",
        "datum_zverejneni",
        "oznaceni_originalu",
        "popis",
        "poznamka",
    )
    fields_extra_data = (
        "cislo_objektu",
        "meritko",
        "vyska",
        "sirka",
        "pocet_variant_originalu",
        "odkaz",
        "datum_vzniku",
        "udalost",
        "region",
        "rok_od",
        "rok_do",
        "duveryhodnost",
        "geom_system",
        "geom",
        "geom_sjtsk",
    )
    model_class = Dokument

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        return field_mapping

    def create_records(self, performed_action) -> list:
        pass


class DokumentAutorMapper(ImportModelMapper):
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
        field_mapping["katastr"] = LookupImportField(RuianKatastr, "kod")
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
        field_mapping["vazba"] = MultipleLookupImportField(
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

    @classmethod
    def get_mapping(cls):
        field_mapping = super().get_mapping()
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        field_mapping["autor"] = LookupImportField(Osoba)
        return field_mapping


class ExterniZdrojAutorMapper(ImportModelMapper):
    model_class = ExterniZdrojAutor


class ExterniZdrojEditorMapper(ImportModelMapper):
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
        field_mapping["vazba"] = MultipleLookupImportField(read_field_name="historie")
        field_mapping["uzivatel"] = LookupImportField(User)
        return field_mapping
