import datetime
import re
from abc import ABC
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

import pandas as pd
from adb.models import Adb, Kladysm5, VyskovyBod
from arch_z.models import Akce, AkceVedouci, ArcheologickyZaznam, ArcheologickyZaznamKatastr, ExterniOdkaz
from core.constants import DOKUMENT_RELATION_TYPE
from core.coordTransform import transform_geom_to_sjtsk, transform_geom_to_wgs84
from core.forms import ImportDataAdminForm
from core.ident_cely import get_record_from_ident
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
    HESLAR_JAZYK,
    HESLAR_JISTOTA_URCENI,
    HESLAR_LETFOTO_TVAR,
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
from pian.models import Kladyzm, Pian, vytvor_pian
from projekt.models import Projekt, ProjektKatastr
from uzivatel.models import Organizace, Osoba, User, UserNotificationType


@dataclass
class ImportDataValidationResult:
    """
    Datová třída, která reprezentuje výsledek validace jednoho záznamu při importu dat.

    Attributes:
        item_order: Pořadové číslo záznamu v importu.
        file_name: Název CSV souboru, ze kterého záznam pochází.
        primary_key_import: Primární klíč záznamu v datovém souboru.
        primary_key_table: Primární klíč záznamu v databázi.
        validation_result: Textový popis výsledku validace (úspěch nebo chybová zpráva).
    """

    item_order: int
    file_name: str
    primary_key_import: str = ""
    primary_key_table: str = ""
    validation_result: str = ""


class ImportDataError(Exception):
    """Základní výjimka pro chyby při importu dat."""

    pass


class ImportDataIncorrectStructureError(ImportDataError):
    """
    Výjimka vyvolaná při nesouladu struktury importovaných dat s očekávanou strukturou (chybějící nebo přebývající sloupce).
    """

    def __init__(self, missing_columns, excess_columns):
        """Inicializuje instanci třídy.

        :param missing_columns: Vstupní hodnota ``missing_columns`` pro danou operaci.
        :param excess_columns: Vstupní hodnota ``excess_columns`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        super().__init__(
            _("core_admin.ImportDataIncorrectStructureError.message.part_1")
            + " "
            + (
                _("core_admin.ImportDataIncorrectStructureError.message.missing_columns")
                + ": "
                + ", ".join(missing_columns)
                + " "
                if missing_columns
                else ""
            )
            + (
                _("core_admin.ImportDataIncorrectStructureError.message.excess_columns")
                + ": "
                + ", ".join(excess_columns)
                + " "
                if excess_columns
                else ""
            )
        )


class ImportDataIncorrectStructureContentObjectError(ImportDataError):
    """
    Výjimka vyvolaná při nesouladu struktury obsahu importovaných dat s očekávanou strukturou (neplatná kombinace sloupců).
    """

    def __init__(self, columns, *expected_colummns_options):
        """Inicializuje instanci třídy.

        :param columns: Vstupní hodnota ``columns`` pro danou operaci.
        :param expected_colummns_options: Dodatečné poziční argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super().__init__(
            f'{_("core_admin.ImportDataIncorrectStructureContentObjectError.message.part_1")} '
            + (
                f'{_("core_admin.ImportDataIncorrectStructureContentObjectError.message.columns")}: {", ".join(columns)} '
            )
            + (
                f'{_("core_admin.ImportDataIncorrectStructureContentObjectError.message.expected_columns_options")}: {"; ".join([str(op) for op in expected_colummns_options])} '
            )
        )


class ImportDataMissingReferencedValueError(ImportDataError):
    """
    Výjimka vyvolaná při chybějící hodnotě referencovaného záznamu — buď v databázi, nebo v importovaných datech.
    """

    def __init__(self, missing_value_id, missing_model_name=None):
        """Inicializuje instanci třídy.

        :param missing_value_id: Identifikátor objektu ``missing_value``.
        :param missing_model_name: Vstupní hodnota ``missing_model_name`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
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
    Výjimka vyvolaná ve dvou případech:
    při insertu — pokud záznam se stejným primárním klíčem již v databázi existuje,
    při updatu — pokud záznam se zadaným primárním klíčem v databázi neexistuje.
    """

    def __init__(self, record_id, model_name, performed_action):
        """Inicializuje instanci třídy.

        :param record_id: Identifikátor objektu ``record``.
        :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.
        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        self.record_id = record_id
        self.model_name = model_name
        self.performed_action = performed_action
        super().__init__(
            "{} {} {} {} {} ({} {})".format(
                _("core_admin.ImportDataIntegrityError.message.part_1"),
                record_id,
                _("core_admin.ImportDataIntegrityError.message.part_2"),
                model_name,
                _("core_admin.ImportDataIntegrityError.message.part_3"),
                _("core_admin.ImportDataIntegrityError.message.part_4"),
                performed_action,
            )
        )


class ImportDataLimitChoicesError(ImportDataError):
    """Výjimka vyvolaná při hodnotě cizího klíče, která nesplňuje omezení limit_choices_to."""

    def __init__(self, record_id, limit_choices_to: dict):
        """Inicializuje instanci třídy.

        :param record_id: Identifikátor objektu ``record``.
        :param limit_choices_to: Vstupní hodnota ``limit_choices_to`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        self.record_id = record_id
        self.limit_choices_to = limit_choices_to
        super().__init__(
            "{} {} {} {} {}".format(
                _("core_admin.ImportDataLimitChoicesError.message.part_1"),
                record_id,
                _("core_admin.ImportDataLimitChoicesError.message.part_2"),
                ",".join(["{}: {}".format(k, v) for k, v in limit_choices_to.items()]),
                _("core_admin.ImportDataLimitChoicesError.message.part_3"),
            )
        )


class ImportDataHeslarPresnostLimitChoicesError(ImportDataError):
    """Výjimka vyvolaná při neplatné hodnotě přesnosti v hesláři u importovaného záznamu."""

    def __init__(self, record_id):
        """Inicializuje instanci třídy.

        :param record_id: Identifikátor objektu ``record``.
        :return: Funkce nevrací hodnotu (``None``)."""
        self.record_id = record_id
        super().__init__(
            f'{_("core_admin.ImportDataLimitChoicesError.message.part_1")} '
            + f'{record_id} {_("core_admin.ImportDataLimitChoicesError.message.part_2")} '
        )


class ImportDataUnsupportedFileError(ImportDataError):
    """
    Výjimka vyvolaná při výskytu nepodporovaného názvu souboru v importovaném archivu.
    """

    def __init__(self, file_name):
        """Inicializuje instanci třídy.

        :param file_name: Vstupní hodnota ``file_name`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        self.file_name = file_name
        super().__init__(
            "{} {} {}".format(
                _("core_admin.ImportDataUnsupportedFileError.message.part_1"),
                file_name,
                _("core_admin.ImportDataUnsupportedFileError.message.part_2"),
            )
        )


class ImportDataUnsupportedFilesError(ImportDataError):
    """
    Výjimka vyvolaná při výskytu jednoho nebo více nepodporovaných názvů souborů v importovaném archivu.
    """

    def __init__(self, file_names):
        """Inicializuje instanci třídy.

        :param file_names: Vstupní hodnota ``file_names`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        self.file_names = file_names
        super().__init__(
            "{} {} {}".format(
                _("core_admin.ImportDataUnsupportedFilesError.message.part_1"),
                ", ".join(file_names),
                _("core_admin.ImportDataUnsupportedFilesError.message.part_2"),
            )
        )


class ImportDataIncorrectPrimaryKeyFormatError(ImportDataError):
    """
    Výjimka vyvolaná při nesouladu hodnoty primárního klíče s očekávaným formátem.
    """

    def __init__(self, primary_key_value):
        """Inicializuje instanci třídy.

        :param primary_key_value: Vstupní hodnota ``primary_key_value`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        self.primary_key_value = primary_key_value
        super().__init__(
            "{} {}".format(
                _("core_admin.ImportDataIncorrectPrimaryKeyFormatError.message"),
                primary_key_value,
            )
        )


class BaseImportField:
    """
    Základní třída pro importní pole. Neprovádí žádnou validaci ani zpracování hodnoty.
    Používá se především pro textová pole.
    """

    def __init__(self):
        """Inicializuje instanci třídy.

        :return: Funkce nevrací hodnotu (``None``)."""
        self._value = None

    @property
    def value(self):
        """Provádí operaci value.

        :return: Vrací výsledek provedené operace."""
        return self._value

    @value.setter
    def value(self, value):
        """Provádí operaci value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if str(value).lower() == "nan":
            value = None
        self._value = self._process_value(value)

    @property
    def is_null(self):
        """Určí, zda null.

        :return: Vrací výsledek ověření nebo validačního pravidla."""
        return self._value is None or str(self._value).lower() == "nan"

    @property
    def instance_value(self):
        """Provádí operaci instance value.

        :return: Vrací výsledek provedené operace."""
        return self._value

    @property
    def serialized_value(self):
        """Provádí operaci serialized value.

        :return: Vrací výsledek provedené operace."""
        return self._value

    def _process_value(self, value):
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        return value


class IntegerImportField(BaseImportField):
    """
    Importní pole pro hodnoty datového typu integer.
    """

    pattern = re.compile(r"\d+")

    def _process_value(self, value) -> int | None:
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""

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
    """Importní pole pro kladné celočíselné hodnoty. Záporná čísla způsobí vyvolání ImportDataError."""

    def _process_value(self, value) -> int | None:
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        value = super()._process_value(value)
        if value is not None and value < 0:
            raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_positive_integer_value')}: {value}")
        return value


class DecimalImportField(BaseImportField):
    """Importní pole pro desetinná čísla (float)."""

    pattern = re.compile(r"\d+\.\d*")

    def _process_value(self, value) -> float | None:
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
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
    Importní pole pro hodnoty datového typu boolean.
    """

    def _process_value(self, value) -> bool | None:
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""

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
    Importní pole pro hodnoty datového typu date.
    """

    pattern_iso = re.compile(r"(\d{4}-\d{1,2}-\d{1,2})(?: 0{1,2}:0{1,2}:0{1,2})?")
    pattern_localized = re.compile(r"\d{1,2}\. ?\d{1,2}\. ?\d{4}")

    @property
    def value(self):
        """Provádí operaci value.

        :return: Vrací výsledek provedené operace."""
        return self._value.isoformat() if self._value else None

    @value.setter
    def value(self, value):
        """Provádí operaci value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        self._value = self._process_value(value)

    @property
    def serialized_value(self):
        """Provádí operaci serialized value.

        :return: Vrací výsledek provedené operace."""
        return self._value.strftime("%Y-%m-%d") if self._value else None

    def _process_value(self, value) -> datetime.date | None:
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""

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
    Importní pole pro hodnoty datového typu datetime.
    Podporovaný formát: "YYYY-MM-DD HH:MM:SS".
    """

    pattern_iso = re.compile(r"(\d{4}-\d{1,2}-\d{1,2}.?\d{1,2}:\d{1,2}:\d{1,2}).*")

    @property
    def value(self):
        """Provádí operaci value.

        :return: Vrací výsledek provedené operace."""
        return self._value.strftime("%Y-%m-%d %H:%M:%S") if self._value else None

    @value.setter
    def value(self, value):
        """Provádí operaci value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        self._value = self._process_value(value)

    @property
    def serialized_value(self):
        """Provádí operaci serialized value.

        :return: Vrací výsledek provedené operace."""
        return self._value.strftime("%Y-%m-%d %H:%M:%S") if self._value else None

    def _process_value(self, value) -> datetime.datetime | None:
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
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
    Importní pole pro hodnoty datového typu date range.
    """

    pattern = re.compile(r"\[\d{4}-\d{1,2}-\d{1,2}, ?\d{4}-\d{1,2}-\d{1,2}\)")

    @property
    def serialized_value(self):
        """Provádí operaci serialized value.

        :return: Vrací výsledek provedené operace."""
        return f"[{self.value.lower.strftime('%Y-%m-%d')},{self.value.upper.strftime('%Y-%m-%d')})"

    def _process_value(self, value) -> DateRange | None:
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""

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
    Importní pole pro hodnoty odkazující na instanci jiného modelu (cizí klíč).
    """

    records = []

    def __init__(
        self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", limit_choices_to: dict | None = None
    ):
        """Inicializuje instanci třídy.

        :param lookup_model_classes: Vstupní hodnota ``lookup_model_classes`` pro danou operaci.
        :param lookup_field_name: Vstupní hodnota ``lookup_field_name`` pro danou operaci.
        :param limit_choices_to: Vstupní hodnota ``limit_choices_to`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
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
        """Provádí operaci instance value.

        :return: Vrací výsledek provedené operace."""
        return self._instance_value

    def _check_limit_choices_to(self, record):
        """Ověří limit choices to.

        :param record: Vstupní hodnota ``record`` pro danou operaci.
        :return: Vrací výsledek ověření nebo validačního pravidla."""
        if self.limit_choices_to:
            if not all(getattr(record, k).pk == v for k, v in self.limit_choices_to.items()):
                raise ImportDataLimitChoicesError(record, self.limit_choices_to)

    def _process_value(self, value):
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""

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
    Rozšíření LookupImportField pro import dat z RUIAN. Odstraní prefix "ruian-" a převede hodnotu na integer.
    """

    @LookupImportField.value.setter
    def value(self, value):
        """Provádí operaci value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if isinstance(value, str):
            match = re.match(r"ruian-(\d+)", value)
            value = int(match.group(1))
        LookupImportField.value.fset(self, value)


class VazbaLookupImportField(LookupImportField):
    """
    Importní pole pro referencované modely přes vazbu (relaci). Relace je 1:1 místo 1:N.
    """

    def __init__(self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", read_field_name: str = None):
        """Inicializuje instanci třídy.

        :param lookup_model_classes: Vstupní hodnota ``lookup_model_classes`` pro danou operaci.
        :param lookup_field_name: Vstupní hodnota ``lookup_field_name`` pro danou operaci.
        :param read_field_name: Vstupní hodnota ``read_field_name`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        super().__init__(lookup_model_classes, lookup_field_name)
        self.read_field_name = read_field_name

    def _process_value(self, value):
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        try:
            record = get_record_from_ident(value)
        except Exception:
            record = None
        if record and self.lookup_model_class_list:
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


class GeomImportField(BaseImportField):
    """
    Importní pole pro geometrické hodnoty.
    """

    def __init__(self, srid):
        """Inicializuje instanci třídy.

        :param srid: Vstupní hodnota ``srid`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        super().__init__()
        self.srid = srid

    @property
    def serialized_value(self):
        """Provádí operaci serialized value.

        :return: Vrací výsledek provedené operace."""
        return getattr(self._value, "wkt", None)

    def _process_value(self, value) -> GEOSGeometry | None:
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if not value:
            return None
        if isinstance(value, str):
            value = GEOSGeometry(value, srid=self.srid)
        if isinstance(value, GEOSGeometry):
            return value
        raise ImportDataError(f"{_('core_admin.GeomImportField.message.invalid_date_value')}: {value}")


class GenericForeignKeyImportField(LookupImportField):
    """
    Importní pole pro generický cizí klíč.
    """

    def __init__(
        self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", serialized_attribute: str = None
    ):
        """Inicializuje instanci třídy.

        :param lookup_model_classes: Vstupní hodnota ``lookup_model_classes`` pro danou operaci.
        :param lookup_field_name: Vstupní hodnota ``lookup_field_name`` pro danou operaci.
        :param serialized_attribute: Vstupní hodnota ``serialized_attribute`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        super().__init__(lookup_model_classes, lookup_field_name)
        self.serialized_attribute = serialized_attribute

    @property
    def serialized_value(self):
        """Provádí operaci serialized value.

        :return: Vrací výsledek provedené operace."""
        if self.serialized_attribute:
            return getattr(self._value, self.serialized_attribute)
        else:
            return self._value.pk

    def _process_value(self, value: str | int):
        """Provádí operaci process value.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
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
    Základní třída pro hromadný import dat. Načítá data z importovaného souboru,
    předzpracovává hodnoty podle cílového pole a vytváří záznamy.
    """

    fields = tuple()
    column_to_field_mapping = {}
    model_class = None
    primary_key = "ident_cely"
    primary_key_filter_field = None
    historie_typ_vazby = None
    soubory_typ_vazby = None
    komponenty_vazba = False
    require_primary_key_value = None
    primary_key_prefix = None
    allow_update = True

    def __init__(self, value_dict):
        """Inicializuje instanci třídy.

        :param value_dict: Vstupní hodnota ``value_dict`` pro danou operaci.
        :return: Funkce nevrací hodnotu (``None``)."""
        self.value_dict = value_dict
        if self.require_primary_key_value is None:
            self.require_primary_key_value = isinstance(self.primary_key, tuple)

    @classmethod
    def get_import_data_mapper_dict(cls):
        """
        Vrátí slovník mapující názvy importních souborů na příslušné třídy mapperů.
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
            "az_akce": ArcheologickyZaznamAkceMapper,
            "az_lokality": LokalitaMapper,
            "az_akce_vedouci": AkceVedouciMapper,
            "az_katastry": ArcheologickyZaznamKatastrMapper,
            "az_pian": PianMapper,
            "az_dokumentacni_jednotky": DokumentacniJednotkaMapper,
            "az_adb": AdbMapper,
            "az_adb_vyskove_body": AdbVyskovyBod,
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
        Vrátí třídu mapperu odpovídající zadanému názvu souboru (bez přípony).
        """

        return cls.get_import_data_mapper_dict().get(file_name.split(".")[0])

    @classmethod
    def get_mapping(cls, include_primary_key=False) -> dict:
        """
        Vrátí slovník mapování polí pomocí metody map_field.
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
        Vrátí slovník s názvem (názvy) a hodnotou (hodnotami) primárního klíče pro filtrování.
        """

        def value_dict_name(value):
            """Provádí operaci value dict name.

            :param value: Vstupní hodnota ``value`` pro danou operaci.
            :return: Vrací výsledek provedené operace."""
            return value.split("__")[0] if "__" in value else value

        if (
            not self.require_primary_key_value
            and isinstance(self.primary_key, str)
            and self.primary_key not in self.value_dict
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
        """Zpracuje primary key.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if isinstance(value, str) and cls.primary_key_prefix:
            match = re.match(f"{cls.primary_key_prefix}-(.*)", value)
            if match:
                return int(match.group(1))
            else:
                raise ImportDataIncorrectPrimaryKeyFormatError(value)
        return value

    @staticmethod
    def _parse_primary_key_custom_prefix(value, prefix):
        """Zpracuje primary key custom prefix.

        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :param prefix: Vstupní hodnota ``prefix`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if isinstance(value, str) and prefix:
            return int(re.match(f"{prefix}-(.*)", value).group(1))
        return value

    @classmethod
    def map_field(cls, field_name):
        """
        Namapuje pole modelu na odpovídající instanci BaseImportField nebo její podtřídy.
        """

        model_field = cls.model_class._meta.get_field(field_name)
        if (
            isinstance(model_field, models.TextField)
            or isinstance(model_field, models.CharField)
            or isinstance(model_field, models.URLField)
        ):
            return BaseImportField()
        if isinstance(model_field, models.IntegerField):
            return IntegerImportField()
        if isinstance(model_field, models.PositiveIntegerField):
            return PositiveIntegerImportField()
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
        """Určí, zda field required.

        :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
        :return: Vrací výsledek ověření nebo validačního pravidla."""
        try:
            model_field = cls.model_class._meta.get_field(field_name)
            return not model_field.null
        except FieldDoesNotExist:
            return False

    def create_records(self, performed_action) -> list:
        """Vytvoří records.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace."""

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
        Provede validaci na základě primárního klíče. Při insertu záznam nesmí existovat,
        při updatu musí existovat. Vrátí slovník s primárními klíči, nebo vyvolá ImportDataIntegrityError.
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

    def _check_column_structure(self, performed_action, include_primary_key=False):
        """Ověří column structure.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací výsledek ověření nebo validačního pravidla."""
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

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """
        Nejprve ověří strukturu sloupců souboru — při nesouladu vyvolá ImportDataIncorrectStructureError.
        Poté vrátí slovník s názvy polí jako klíči a instancemi BaseImportField s načtenými hodnotami jako hodnotami.
        """

        self._check_column_structure(performed_action, include_primary_key)

        mapping_dict = {}
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
        """Ověří required fields.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací výsledek ověření nebo validačního pravidla."""
        for key, value in self.value_dict.items():
            required = self.is_field_required(key)
            if required and (value is None or str(value).lower().strip() in ("nan", "") or pd.isna(value)):
                raise ImportDataError(f"{_('core_admin.ImportDataError.message.missing_required_field')}: {key}")

    def map_column_name_to_field_name(self, column_name):
        """Provádí operaci map column name to field name.

        :param column_name: Vstupní hodnota ``column_name`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""

        return self.column_to_field_mapping.get(column_name, column_name)

    @classmethod
    def create_relations(cls, instance):
        """Vytvoří relations.

        :param instance: Vstupní hodnota ``instance`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace."""

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
    def record_postprocessing(cls, record, performed_action, fedora_transaction):
        """Provádí operaci record postprocessing.

        :param record: Vstupní hodnota ``record`` pro danou operaci.
        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        return record


class GeometryTransformMixin:
    """
    Mixin pro mappery s geometrickými poli. Při insertu zajišťuje konverzi mezi souřadnicovými systémy:
    WGS84 (SRID 4326) → S-JTSK (SRID 5514) a naopak.
    """

    def transform_geometries(self, mapping_dict, performed_action):
        """Transformuje geometries.

        :param mapping_dict: Vstupní hodnota ``mapping_dict`` pro danou operaci.
        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            if mapping_dict.get("geom_system") == 4326 and mapping_dict.get("geom"):
                mapping_dict["geom_sjtsk"] = transform_geom_to_sjtsk(mapping_dict["geom"])
            elif mapping_dict.get("geom_system") == 5514 and mapping_dict.get("geom_sjtsk"):
                mapping_dict["geom"] = transform_geom_to_wgs84(mapping_dict["geom_sjtsk"])
        return mapping_dict


class MultipleClassImportModelMapper(ImportModelMapper):
    """Základní třída pro mappery importující data do více modelů najednou."""

    foreign_key_fields = tuple()
    classes = tuple()

    def import_validation(self, performed_action):
        """Načte validation.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
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
        """Vrací filter kwargs primary key.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return {"ident_cely": self.value_dict.get("ident_cely")}

    def create_records(self, performed_action) -> list:
        """Vytvoří records.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace."""
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
        """Určí, zda field required.

        :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
        :return: Vrací výsledek ověření nebo validačního pravidla."""
        for mapper_class_tuple in cls.classes:
            mapper_class = mapper_class_tuple[1]
            try:
                model_field = mapper_class._meta.get_field(field_name)
                return not model_field.null and not model_field.has_default()
            except FieldDoesNotExist:
                continue
        return False


class HeslarMapper(ImportModelMapper):
    """Mapovač pro model Heslar."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["nazev_heslare"] = LookupImportField(HeslarNazev, "nazev")
        return field_mapping


class HeslarDataceMapper(ImportModelMapper):
    """Mapovač pro model HeslarDatace."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["obdobi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBDOBI})
        return field_mapping


class HeslarDokumentTypMaterialRadaMapper(ImportModelMapper):
    """Mapovač pro model HeslarDokumentTypMaterialRada."""

    model_class = HeslarDokumentTypMaterialRada
    primary_key = "id"
    primary_key_prefix = "hdtm"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
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
    """Mapovač pro model HeslarHierarchie."""

    fields = ("typ",)
    model_class = HeslarHierarchie
    primary_key = "id"
    primary_key_prefix = "hier"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["heslo_nadrazene"] = LookupImportField(Heslar)
        field_mapping["heslo_podrazene"] = LookupImportField(Heslar)
        return field_mapping


class HeslarOdkazMapper(ImportModelMapper):
    """Mapovač pro model HeslarOdkaz."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["heslo"] = LookupImportField(Heslar)
        return field_mapping


class OrganizaceMapper(ImportModelMapper):
    """Mapovač pro model Organizace."""

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
        "web",
    )
    model_class = Organizace
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["soucast"] = LookupImportField(Organizace)
        field_mapping["typ_organizace"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_ORGANIZACE_TYP}
        )
        field_mapping["zverejneni_pristupnost"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST}
        )
        field_mapping["licence"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LICENCE})
        return field_mapping


class OsobaMapper(ImportModelMapper):
    """Mapovač pro model Osoba."""

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


class ProjektMapper(ImportModelMapper, GeometryTransformMixin):
    """Mapovač pro model Projekt."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
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

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """Provádí operaci map.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
        :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        return self.transform_geometries(mapping_dict, performed_action)


class ProjektKatastrMapper(ImportModelMapper):
    """Mapovač pro model ProjektKatastr."""

    model_class = ProjektKatastr
    primary_key = ("projekt", "katastr")
    allow_update = False
    primary_key_filter_field = ("projekt__ident_cely", "katastr__kod")
    primary_key_prefix = (None, "ruian")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["projekt"] = LookupImportField(Projekt)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping


class ProjektOznamovatelMapper(ImportModelMapper):
    """Mapovač pro model Oznamovatel."""

    fields = ("oznamovatel", "odpovedna_osoba", "adresa", "telefon", "email", "poznamka")
    model_class = Oznamovatel
    primary_key = "projekt"
    primary_key_filter_field = "projekt__ident_cely"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["projekt"] = LookupImportField(Projekt)
        return field_mapping


class SamostatnyNalezMapper(ImportModelMapper, GeometryTransformMixin):
    """Mapovač pro model SamostatnyNalez."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
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

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """Provádí operaci map.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
        :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        return self.transform_geometries(mapping_dict, performed_action)


class ArcheologickyZaznamAkceMapper(MultipleClassImportModelMapper):
    """Mapovač pro modely ArcheologickyZaznam a Akce."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping = field_mapping | cls.lookup_fields_mapping
        return field_mapping

    @classmethod
    def map_field(cls, field_name):
        """Provádí operaci map field.

        :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        mapping_dict = {
            "hlavni_katastr": RuianLookupImportField(RuianKatastr, "kod"),
        }
        mapping_dict = mapping_dict | cls.lookup_fields_mapping
        return mapping_dict.get(field_name, BaseImportField())

    @classmethod
    def record_postprocessing(cls, record, performed_action, fedora_transaction):
        """Provádí operaci record postprocessing.

        :param record: Vstupní hodnota ``record`` pro danou operaci.
        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if isinstance(record, ArcheologickyZaznam) and performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            record.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
        return super().record_postprocessing(record, performed_action, fedora_transaction)


class LokalitaMapper(MultipleClassImportModelMapper):
    """Mapovač pro modely ArcheologickyZaznam a Lokalita."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping = field_mapping | cls.lookup_fields_mapping
        return field_mapping

    @classmethod
    def map_field(cls, field_name):
        """Provádí operaci map field.

        :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        mapping_dict = {
            "hlavni_katastr": RuianLookupImportField(RuianKatastr, "kod"),
        }
        mapping_dict = mapping_dict | cls.lookup_fields_mapping
        return mapping_dict.get(field_name, BaseImportField())


class AkceVedouciMapper(ImportModelMapper):
    """Mapovač pro model AkceVedouci."""

    model_class = AkceVedouci
    primary_key = "id"
    primary_key_prefix = "vedo"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["akce"] = LookupImportField(Akce, "archeologicky_zaznam__ident_cely")
        field_mapping["vedouci"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        return field_mapping


class ArcheologickyZaznamKatastrMapper(ImportModelMapper):
    """Mapovač pro model ArcheologickyZaznamKatastr."""

    model_class = ArcheologickyZaznamKatastr
    primary_key = ("archeologicky_zaznam", "katastr")
    allow_update = False
    primary_key_filter_field = ("archeologicky_zaznam__ident_cely", "katastr__kod")
    primary_key_prefix = (None, "ruian")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping


class PianMapper(ImportModelMapper, GeometryTransformMixin):
    """Mapovač pro model Pian."""

    fields = ("ident_cely", "stav", "geom_system", "geom", "geom_sjtsk")
    model_class = Pian
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PIAN_TYP})
        field_mapping["presnost"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PIAN_PRESNOST})
        field_mapping["zm10"] = LookupImportField(Kladyzm, "cislo")
        field_mapping["zm50"] = LookupImportField(Kladyzm, "cislo")
        return field_mapping

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """Provádí operaci map.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
        :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        return self.transform_geometries(mapping_dict, performed_action)


class DokumentacniJednotkaMapper(ImportModelMapper):
    """Mapovač pro model DokumentacniJednotka."""

    fields = ("ident_cely", "negativni_jednotka", "nazev")
    model_class = DokumentacniJednotka
    require_primary_key_value = True
    komponenty_vazba = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["pian"] = LookupImportField(Pian)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DJ_TYP})
        return field_mapping

    @classmethod
    def record_postprocessing(cls, record, performed_action, fedora_transaction):
        """Provádí operaci record postprocessing.

        :param record: Vstupní hodnota ``record`` pro danou operaci.
        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        record: DokumentacniJednotka
        if pian := record.archeologicky_zaznam.hlavni_katastr.pian:
            record.pian = pian
        else:
            record.pian = vytvor_pian(record.archeologicky_zaznam.hlavni_katastr, fedora_transaction)
        return record


class AdbMapper(ImportModelMapper):
    """Mapovač pro model Adb."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokumentacni_jednotka"] = LookupImportField(DokumentacniJednotka)
        field_mapping["typ_sondy"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_ADB_TYP})
        field_mapping["podnet"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_ADB_PODNET})
        field_mapping["autor_popisu"] = LookupImportField(Osoba)
        field_mapping["autor_revize"] = LookupImportField(Osoba)
        field_mapping["sm5"] = LookupImportField(Kladysm5, "mapno")
        return field_mapping


class AdbVyskovyBod(ImportModelMapper):
    """Mapovač pro model VyskovyBod."""

    fields = ("ident_cely", "geom")
    model_class = VyskovyBod
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["adb"] = LookupImportField(Adb)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_VYSKOVY_BOD_TYP})
        return field_mapping


class DokumentLetMapper(ImportModelMapper):
    """Mapovač pro model Let."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["letiste_start"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LETISTE})
        field_mapping["letiste_cil"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LETISTE})
        field_mapping["pozorovatel"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        field_mapping["pocasi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_POCASI})
        field_mapping["dohlednost"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOHLEDNOST})
        return field_mapping


class DokumentMapper(MultipleClassImportModelMapper, GeometryTransformMixin):
    """Mapovač pro modely Dokument a DokumentExtraData."""

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
    classes = (
        ("dokument", Dokument),
        ("dokument_extra_data", DokumentExtraData, "dokument"),
    )
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping = field_mapping | cls.lookup_fields_mapping
        return field_mapping

    @classmethod
    def map_field(cls, field_name):
        """Provádí operaci map field.

        :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        mapping_dict = cls.lookup_fields_mapping
        return mapping_dict.get(field_name, BaseImportField())

    def create_records(self, performed_action) -> list:
        """Vytvoří records.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace."""

        fields_dokument = [item for model, item in self.fields + self.foreign_key_fields if model == "dokument"]
        fields_dokument_extra_data = [
            item for model, item in self.fields + self.foreign_key_fields if model == "dokument_extra_data"
        ]
        mapping_dict = self.map(performed_action, True)
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            dokument = Dokument.objects.get(ident_cely=mapping_dict["ident_cely"])
            dokument_extra_data_query = DokumentExtraData.objects.filter(dokument=dokument)
            if dokument_extra_data_query.exists():
                return [dokument_extra_data_query.first(), dokument]
            else:
                return [dokument]
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
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE:
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
            return [dokument_extra_data, dokument]
        return []

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """Provádí operaci map.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
        :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        return self.transform_geometries(mapping_dict, performed_action)


class DokumentAutorMapper(ImportModelMapper):
    """Mapovač pro model DokumentAutor."""

    fields = ("poradi",)
    model_class = DokumentAutor
    primary_key = ("dokument", "autor")
    allow_update = False
    primary_key_filter_field = ("dokument__ident_cely", "autor__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["autor"] = LookupImportField(Osoba)
        return field_mapping


class DokumentJazykMapper(ImportModelMapper):
    """Mapovač pro model DokumentJazyk."""

    model_class = DokumentJazyk
    primary_key = ("dokument", "jazyk")
    allow_update = False
    primary_key_filter_field = ("dokument__ident_cely", "jazyk__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["jazyk"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_JAZYK})
        return field_mapping


class DokumentOsobaMapper(ImportModelMapper):
    """Mapovač pro model DokumentOsoba."""

    model_class = DokumentOsoba
    primary_key = ("dokument", "osoba")
    allow_update = False
    primary_key_filter_field = ("dokument__ident_cely", "osoba__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["osoba"] = LookupImportField(Osoba)
        return field_mapping


class DokumentPosudekMapper(ImportModelMapper):
    """Mapovač pro model DokumentPosudek."""

    model_class = DokumentPosudek
    primary_key = ("dokument", "posudek")
    allow_update = False
    primary_key_filter_field = ("dokument__ident_cely", "posudek__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["posudek"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_POSUDEK_TYP})
        return field_mapping


class TvarMapper(ImportModelMapper):
    """Mapovač pro model Tvar."""

    fields = ("poznamka",)
    model_class = Tvar
    primary_key = "id"
    primary_key_prefix = "tvar"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["tvar"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LETFOTO_TVAR})
        return field_mapping


class DokumentCastMapper(ImportModelMapper):
    """Mapovač pro model DokumentCast."""

    fields = ("ident_cely", "poznamka")
    model_class = DokumentCast
    require_primary_key_value = True
    komponenty_vazba = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["projekt"] = LookupImportField(Projekt)
        return field_mapping


class NeidentAkceMapper(ImportModelMapper):
    """Mapovač pro model NeidentAkce."""

    fields = ("rok_zahajeni", "rok_ukonceni", "lokalizace", "popis", "poznamka", "pian")
    model_class = NeidentAkce
    primary_key = "dokument_cast"
    primary_key_filter_field = "dokument_cast__ident_cely"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument_cast"] = LookupImportField(DokumentCast)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping


class NeidentAkceVedouciMapper(ImportModelMapper):
    """Mapovač pro model NeidentAkceVedouci."""

    model_class = NeidentAkceVedouci
    primary_key = ("neident_akce", "vedouci")
    allow_update = False
    primary_key_filter_field = ("neident_akce__dokument_cast__ident_cely", "vedouci__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["neident_akce"] = LookupImportField(DokumentCast)
        field_mapping["vedouci"] = LookupImportField(Osoba)
        return field_mapping


class KomponentaMapper(ImportModelMapper):
    """Mapovač pro model Komponenta."""

    fields = ("ident_cely", "jistota", "presna_datace", "poznamka")
    model_class = Komponenta
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vazba"] = VazbaLookupImportField(
            (DokumentacniJednotka, DokumentCast), read_field_name="komponenty"
        )
        field_mapping["obdobi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBDOBI})
        field_mapping["areal"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_AREAL})
        return field_mapping


class KomponentaAktivitaMapper(ImportModelMapper):
    """Mapovač pro model KomponentaAktivita."""

    model_class = KomponentaAktivita
    primary_key = ("komponenta", "aktivita")
    allow_update = False
    primary_key_filter_field = ("komponenta__ident_cely", "aktivita__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["aktivita"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_AKTIVITA})
        return field_mapping


class NalezMapper(ImportModelMapper):
    """Základní mapper pro nálezy."""

    fields = ("pocet", "poznamka")
    primary_key = "id"


class NalezObjektMapper(NalezMapper):
    """Mapovač pro model NalezObjekt."""

    model_class = NalezObjekt
    primary_key_prefix = "nalo"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["druh"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_DRUH})
        field_mapping["specifikace"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_SPECIFIKACE}
        )
        return field_mapping


class NalezPredmetMapper(NalezMapper):
    """Mapovač pro model NalezPredmet."""

    model_class = NalezPredmet
    primary_key_prefix = "nalp"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["druh"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PREDMET_DRUH})
        field_mapping["specifikace"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PREDMET_SPECIFIKACE}
        )
        return field_mapping


class ExterniZdrojMapper(ImportModelMapper):
    """Mapovač pro model ExterniZdroj."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_EXTERNI_ZDROJ_TYP})
        field_mapping["typ_dokumentu"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP}
        )
        return field_mapping


class ExterniZdrojAutorMapper(ImportModelMapper):
    """Mapovač pro model ExterniZdrojAutor."""

    fields = ("poradi",)
    primary_key = ("externi_zdroj", "autor")
    allow_update = False
    primary_key_filter_field = ("externi_zdroj__ident_cely", "autor__ident_cely")
    model_class = ExterniZdrojAutor

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        field_mapping["autor"] = LookupImportField(Osoba)
        return field_mapping


class ExterniZdrojEditorMapper(ImportModelMapper):
    """Mapovač pro model ExterniZdrojEditor."""

    fields = ("poradi",)
    primary_key = ("externi_zdroj", "editor")
    allow_update = False
    primary_key_filter_field = ("externi_zdroj__ident_cely", "editor__ident_cely")
    model_class = ExterniZdrojEditor

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        field_mapping["editor"] = LookupImportField(Osoba)
        return field_mapping


class ExterniOdkazMapper(ImportModelMapper):
    """Mapovač pro model ExterniOdkaz."""

    fields = ("paginace",)
    model_class = ExterniOdkaz
    primary_key = "id"
    primary_key_prefix = "exto"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        return field_mapping


class UzivatelMapper(ImportModelMapper):
    """Mapovač pro model User."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["osoba"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        return field_mapping


class UzivatelNotifikaceProjektMapper(ImportModelMapper):
    """Mapovač pro model Pes (notifikace uživatele vázané na projekt či územní jednotku RUIAN)."""

    model_class = Pes
    primary_key = ("uzivatel", "ruian")
    allow_update = False
    primary_key_prefix = (None, "ruian")
    column_to_field_mapping = {"uzivatel": "user"}

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(False)
        field_mapping["uzivatel"] = LookupImportField(User, "ident_cely")
        field_mapping["ruian"] = GenericForeignKeyImportField([RuianKatastr, RuianOkres, RuianKraj], "kod", "kod")
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        """Vrací filter kwargs primary key.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        primary_key_import_field: GenericForeignKeyImportField = self.get_mapping()["ruian"]
        content_object = primary_key_import_field._process_value(self.value_dict["ruian"])
        return {
            "user__ident_cely": self.value_dict["uzivatel"],
            "content_type": ContentType.objects.get_for_model(content_object),
            "object_id": content_object.pk,
        }

    @classmethod
    def map_field(cls, field_name):
        """Provádí operaci map field.

        :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if field_name == "uzivatel":
            field_name = "user"
        return super().map_field(field_name)

    def create_records(self, performed_action) -> list:
        """Vytvoří records.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace."""
        mapping_dict = self.map(performed_action, True)
        mapping_dict = {self.map_column_name_to_field_name(field): value for field, value in mapping_dict.items()}
        app_label, model = mapping_dict["content_type"].split(".")
        primary_key_import_field: GenericForeignKeyImportField = self.get_mapping()["ruian"]
        content_object = primary_key_import_field._process_value(
            self.value_dict.get("ruian", self.value_dict.get("object_id"))
        )
        return [
            Pes(
                user=mapping_dict["user"],
                content_type=ContentType.objects.get(app_label=app_label, model=model),
                content_object=content_object,
            )
        ]

    def _check_column_structure(self, performed_action, include_primary_key=False):
        """Ověří column structure.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací výsledek ověření nebo validačního pravidla."""
        mapping_column_set = set(self.value_dict.keys())
        expected_column_set_import = {"uzivatel", "ruian"}
        expected_column_set_job = {"uzivatel", "content_type", "object_id"}
        if mapping_column_set != expected_column_set_import and mapping_column_set != expected_column_set_job:
            raise ImportDataIncorrectStructureContentObjectError(
                mapping_column_set, expected_column_set_import, expected_column_set_job
            )

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """Provádí operaci map.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :param instance_values: Vstupní hodnota ``instance_values`` pro danou operaci.
        :param serialize: Vstupní hodnota ``serialize`` pro danou operaci.
        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        primary_key_import_field: GenericForeignKeyImportField = self.get_mapping()["ruian"]
        content_object = primary_key_import_field._process_value(
            self.value_dict.get("ruian", self.value_dict.get("object_id"))
        )
        content_type: ContentType = ContentType.objects.get_for_model(content_object)
        return {
            "uzivatel": mapping_dict["uzivatel"],
            "content_type": f"{content_type.app_label}.{content_type.model}",
            "object_id": content_object.kod,
        }


class UzivatelSpolupraceMapper(ImportModelMapper):
    """Mapovač pro model UzivatelSpoluprace."""

    fields = ("stav",)
    model_class = UzivatelSpoluprace
    primary_key = "id"
    primary_key_prefix = "spol"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vedouci"] = LookupImportField(User)
        field_mapping["spolupracovnik"] = LookupImportField(User)
        return field_mapping


class UzivatelOpravneniMapper(ImportModelMapper):
    """Mapovač pro přiřazení skupinových oprávnění uživateli (model User)."""

    model_class = User
    primary_key = ("uzivatel", "skupina")
    allow_update = False
    column_to_field_mapping = {"uzivatel": "ident_cely"}

    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = {"uzivatel": LookupImportField(User), "skupina": LookupImportField(Group, "name")}
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        """Vrací filter kwargs primary key.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return {"ident_cely": self.value_dict["uzivatel"]}

    def create_records(self, performed_action):
        """Vytvoří records.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace."""
        return [User.objects.get(ident_cely=self.value_dict["uzivatel"])]

    def import_validation(self, performed_action):
        """Načte validation.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        return self._get_filter_kwargs_primary_key()


class SouborMapper(ImportModelMapper):
    """Mapovač pro model Soubor."""

    fields = ("nazev",)
    model_class = Soubor
    primary_key = "id"
    primary_key_prefix = "soub"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vazba"] = VazbaLookupImportField(read_field_name="soubory")
        return field_mapping


class UzivatelNotifikaceMapper(ImportModelMapper):
    """Mapovač pro přiřazení typů notifikací uživateli (model User)."""

    model_class = User
    primary_key = ("uzivatel", "notifikace")
    allow_update = False
    column_to_field_mapping = {"uzivatel": "ident_cely"}

    def get_mapping(cls, include_primary_key=False):
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = {"uzivatel": LookupImportField(User), "notifikace": LookupImportField(UserNotificationType)}
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        """Vrací filter kwargs primary key.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return {"ident_cely": self.value_dict["uzivatel"]}

    def create_records(self, performed_action):
        """Vytvoří records.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace."""
        return [User.objects.get(ident_cely=self.value_dict["uzivatel"])]

    def import_validation(self, performed_action):
        """Načte validation.

        :param performed_action: Vstupní hodnota ``performed_action`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        return self._get_filter_kwargs_primary_key()


class HistorieMapper(ImportModelMapper):
    """Mapovač pro model Historie."""

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
        """Vrací mapping.

        :param include_primary_key: Vstupní hodnota ``include_primary_key`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vazba"] = VazbaLookupImportField(read_field_name="historie")
        field_mapping["uzivatel"] = LookupImportField(User)
        return field_mapping
