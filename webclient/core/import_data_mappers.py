import datetime
import functools
import re
from abc import ABC
from collections.abc import Iterable
from contextvars import ContextVar
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
from xml_generator.models import ModelWithMetadata


@dataclass
class ImportDataValidationResult:
    """
    Datová třída reprezentující výsledek validace jednoho záznamu při importu dat.

    :ivar item_order: Pořadové číslo záznamu v importu.
    :ivar file_name: Název CSV souboru, ze kterého záznam pochází.
    :ivar primary_key_import: Primární klíč záznamu v datovém souboru.
    :ivar primary_key_table: Primární klíč záznamu v databázi.
    :ivar validation_result: Textový popis výsledku validace (úspěch nebo chybová zpráva).
    """

    item_order: int
    file_name: str
    primary_key_import: str = ""
    primary_key_table: str = ""
    validation_result: str = ""

    def to_dict(self) -> dict:
        """
        Serializuje instanci do slovníku vhodného pro uložení jako JSON.

        :return: Slovník s atributy instance.
        """
        return {
            "item_order": self.item_order,
            "file_name": self.file_name,
            "primary_key_import": self.primary_key_import,
            "primary_key_table": self.primary_key_table,
            "validation_result": self.validation_result,
        }


class ImportDataError(Exception):
    """Základní výjimka pro chyby při importu dat."""

    pass


class ImportDataIncorrectStructureError(ImportDataError):
    """
    Výjimka vyvolaná při nesouladu struktury importovaných dat s očekávanou strukturou (chybějící nebo přebývající sloupce).
    """

    def __init__(self, missing_columns, excess_columns):
        """
        Inicializuje instanci třídy.

        :param missing_columns: Parametr ``missing_columns`` se předává do volání ``__init__()``, ``join()``.
        :param excess_columns: Číselná hodnota ``excess_columns`` použitá při výpočtu nebo transformaci.
        """
        message = "{} ".format(_("core_admin.ImportDataIncorrectStructureError.message.part_1"))
        if missing_columns:
            message += "{}: {} ".format(
                _("core_admin.ImportDataIncorrectStructureError.message.missing_columns"),
                ", ".join(missing_columns),
            )
        if excess_columns:
            message += "{}: {} ".format(
                _("core_admin.ImportDataIncorrectStructureError.message.excess_columns"),
                ", ".join(excess_columns),
            )
        super().__init__(message)


class ImportDataIncorrectStructureContentObjectError(ImportDataError):
    """
    Výjimka vyvolaná při nesouladu struktury obsahu importovaných dat s očekávanou strukturou (neplatná kombinace sloupců).
    """

    def __init__(self, columns, *expected_colummns_options):
        """
        Inicializuje instanci třídy.

        :param columns: Parametr ``columns`` se předává do volání ``__init__()``, ``join()``.
        :param expected_colummns_options: Parametr ``expected_colummns_options`` se předává do volání ``__init__()``, ``join()``.
        """
        super().__init__(
            "{} {}: {} {}: {} ".format(
                _("core_admin.ImportDataIncorrectStructureContentObjectError.message.part_1"),
                _("core_admin.ImportDataIncorrectStructureContentObjectError.message.columns"),
                ", ".join(columns),
                _("core_admin.ImportDataIncorrectStructureContentObjectError.message.expected_columns_options"),
                "; ".join([str(op) for op in expected_colummns_options]),
            )
        )


class ImportDataMissingReferencedValueError(ImportDataError):
    """
    Výjimka vyvolaná při chybějící hodnotě referencovaného záznamu — buď v databázi, nebo v importovaných datech.
    """

    def __init__(self, missing_value_id, missing_model_name=None, missing_field_name=None):
        """
        Inicializuje instanci třídy.

        :param missing_value_id: Identifikátor objektu ``missing_value``.
        :param missing_model_name: Název modelu, ve kterém lookup selhal.
        :param missing_field_name: Název pole, ve kterém lookup selhal.
        """
        self.missing_value_id = missing_value_id
        self.missing_model_name = missing_model_name
        self.missing_field_name = missing_field_name
        message = "{} {} {} ".format(
            _("core_admin.ImportDataMissingReferencedValueError.message.part_1"),
            str(missing_value_id),
            _("core_admin.ImportDataMissingReferencedValueError.message.part_2"),
        )
        if missing_model_name:
            message += "{} {} ".format(
                str(missing_model_name),
                _("core_admin.ImportDataMissingReferencedValueError.message.part_3"),
            )
        if missing_field_name:
            message += "{} {}".format(
                _("core_admin.ImportDataMissingReferencedValueError.message.part_4"),
                str(missing_field_name),
            )
        super().__init__(message)


class ImportDataIntegrityError(ImportDataError):
    """
    Výjimka vyvolaná ve dvou případech:

    při insertu — pokud záznam se stejným primárním klíčem již v databázi existuje,
    při updatu — pokud záznam se zadaným primárním klíčem v databázi neexistuje.
    """

    def __init__(self, record_id, model_name, performed_action):
        """
        Inicializuje instanci třídy.

        :param record_id: Identifikátor objektu ``record``.
        :param model_name: Název modelu používaný pro cílení operace.
        :param performed_action: Parametr ``performed_action`` předává se do volání ``__init__()``, ``format()``.
        """
        self.record_id = record_id
        self.model_name = model_name
        self.performed_action = performed_action
        super().__init__(
            "{} {} {} {} {} ({})".format(
                _("core_admin.ImportDataIntegrityError.message.part_1"),
                record_id,
                _("core_admin.ImportDataIntegrityError.message.part_2"),
                model_name,
                _("core_admin.ImportDataIntegrityError.message.part_3"),
                performed_action,
            )
        )


class ImportDataLimitChoicesError(ImportDataError):
    """Výjimka vyvolaná při hodnotě cizího klíče, která nesplňuje omezení limit_choices_to."""

    def __init__(self, record_id, limit_choices_to: dict, field_verbose_name):
        """
        Inicializuje instanci třídy.

        :param record_id: Identifikátor objektu ``record``.
        :param limit_choices_to: Omezení ``limit_choices_to``, které nalezený záznam nesplňuje.
        :param field_verbose_name: Čitelný název cílového modelového pole.
        """
        self.record_id = record_id
        self.limit_choices_to = limit_choices_to
        self.field_verbose_name = field_verbose_name
        super().__init__(
            "{} {} {} {}".format(
                _("core_admin.ImportDataLimitChoicesError.message.part_1"),
                record_id,
                _("core_admin.ImportDataLimitChoicesError.message.part_2"),
                field_verbose_name,
            )
        )


class ImportDataMissingHeslarValueError(ImportDataError):
    """
    Výjimka vyvolaná, pokud hodnota není platnou položkou hesláře určeného omezením ``nazev_heslare``.
    """

    def __init__(self, field_name, heslar_name, value):
        """
        Inicializuje instanci třídy.

        :param field_name: Název pole, ve kterém lookup selhal.
        :param heslar_name: Název hesláře (hodnota ``nazev_heslare``), do kterého hodnota nepatří.
        :param value: Hodnota, která nebyla v hesláři nalezena.
        """
        self.field_name = field_name
        self.heslar_name = heslar_name
        self.value = value
        super().__init__(
            "{} {} {} {} {} {}".format(
                _("core_admin.ImportDataMissingHeslarValueError.message.part_1"),
                str(value),
                _("core_admin.ImportDataMissingHeslarValueError.message.part_2"),
                str(field_name),
                _("core_admin.ImportDataMissingHeslarValueError.message.part_3"),
                str(heslar_name),
            )
        )


class ImportDataUnsupportedFileError(ImportDataError):
    """Výjimka vyvolaná při výskytu nepodporovaného názvu souboru v importovaném archivu."""

    def __init__(self, file_name):
        """
        Inicializuje instanci třídy.

        :param file_name: Parametr ``file_name`` se předává do volání ``__init__()``, ``format()``.
        """
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
        """
        Inicializuje instanci třídy.

        :param file_names: Parametr ``file_names`` se předává do volání ``__init__()``, ``format()``.
        """
        self.file_names = file_names
        super().__init__(
            "{} {} {}".format(
                _("core_admin.ImportDataUnsupportedFilesError.message.part_1"),
                ", ".join(file_names),
                _("core_admin.ImportDataUnsupportedFilesError.message.part_2"),
            )
        )


class ImportDataIncorrectPrimaryKeyFormatError(ImportDataError):
    """Výjimka vyvolaná při nesouladu hodnoty primárního klíče s očekávaným formátem."""

    def __init__(self, primary_key_value):
        """
        Inicializuje instanci třídy.

        :param primary_key_value: Textový název nebo klíč ``primary_key_value`` používaný v rámci operace.
        """
        self.primary_key_value = primary_key_value
        super().__init__(
            "{} {}".format(
                _("core_admin.ImportDataIncorrectPrimaryKeyFormatError.message"),
                primary_key_value,
            )
        )


class ImportDataActiveUserCannotBeDeleted(ImportDataError):
    """
    Výjimka vyvolaná při snaze o smazání aktivního uživatele
    """

    def __init__(self, primary_key_value):
        """
        Inicializuje výjimku pro pokus o smazání právě aktivního uživatele.

        :param primary_key_value: Hodnota ``ident_cely`` uživatele, který nesmí být smazán.
        """
        self.primary_key_value = primary_key_value
        super().__init__(
            "{} {}".format(
                _("core_admin.ImportDataActiveUserCannotBeDeleted.message"),
                primary_key_value,
            )
        )


class ImportDataEmptyError(ImportDataError):
    """
    Výjimka vyvolaná při pokusu o import ZIP archivu bez platných záznamů.

    Vyvolá se po dokončení validační smyčky, pokud žádný CSV soubor neobsahuje žádný
    záznam k importu.
    """

    def __init__(self):
        """Inicializuje výjimku pro prázdný import."""
        super().__init__(_("core.admin.import_data.error.empty_import"))


class ImportDataMissingFileError(ImportDataError):
    """
    Výjimka vyvolaná při pokusu o import bez přiloženého souboru.

    Vyvolá se v případě, kdy formulář neobsahuje žádný nahraný soubor.
    """

    def __init__(self):
        """Inicializuje výjimku pro chybějící soubor."""
        super().__init__(_("core.admin.import_data.error.missing_file"))


class BaseImportField:
    """
    Základní třída pro importní pole. Neprovádí žádnou validaci ani zpracování hodnoty.

    Používá se především pro textová pole.
    """

    def __init__(self):
        """Inicializuje instanci třídy."""
        self._value = None
        self.field_verbose_name = None

    def set_import_context(self, model_class, field_name):
        """
        Nastaví kontext cílového modelového pole pro chybové zprávy importu.

        :param model_class: Modelová třída, do které se importuje.
        :param field_name: Název cílového pole modelu.
        """
        self.field_verbose_name = None
        try:
            self.field_verbose_name = str(model_class._meta.get_field(field_name).verbose_name)
        except FieldDoesNotExist:
            self.field_verbose_name = field_name

    @property
    def value(self):
        """
        Provádí operaci value.

        :return: Vrací atribut objektu.
        """
        return self._value

    @value.setter
    def value(self, value):
        """
        Provádí operaci value.

        :param value: Parametr ``value`` předává se do volání ``str()``, ``_process_value()``, pracuje se s atributy ``setter``, ovlivňuje větvení podmínek.
        """
        if str(value).lower() == "nan":
            value = None
        self._value = self._process_value(value)

    @property
    def is_null(self):
        """
        Určí, zda null.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return self._value is None or str(self._value).lower() == "nan"

    @property
    def instance_value(self):
        """
        Provádí operaci instance value.

        :return: Vrací atribut objektu.
        """
        return self._value

    @property
    def serialized_value(self):
        """
        Provádí operaci serialized value.

        :return: Vrací atribut objektu.
        """
        return self._value

    def _process_value(self, value):
        """
               Provádí operaci process value.

               :param value: Parametr ``value`` vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.
        """
        return value


class FileNameImportField(BaseImportField):
    """Importní pole pro název souboru bez adresářových oddělovačů a skrytého prefixu."""

    forbidden_separators = ("/", "\\")

    def _process_value(self, value) -> str | None:
        """
        Ověří a normalizuje název souboru pro import.

        Hodnotu typu ``bytes`` dekóduje jako UTF-8, ostatní ne-řetězcové typy převede na ``str``.
        Odmítne názvy obsahující adresářové oddělovače (``/``, ``\\``) nebo začínající tečkou,
        protože takové hodnoty by mohly vést k průchodu adresáři nebo skrytým souborům.

        :param value: Název souboru k ověření; může být ``str``, ``bytes`` nebo jiný typ.
        :return: Ověřený název souboru jako řetězec, nebo ``None`` pokud je vstup ``None``.
        :raises ImportDataError: Vyvolá se, pokud název obsahuje ``/`` nebo ``\\``, nebo začíná tečkou.
        """
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        elif not isinstance(value, str):
            value = str(value)
        if any(separator in value for separator in self.forbidden_separators) or value.startswith("."):
            raise ImportDataError(f"Invalid file name value: {value}")
        return value


class IntegerImportField(BaseImportField):
    """Importní pole pro hodnoty datového typu integer."""

    pattern = re.compile(r"\d+")

    def _process_value(self, value) -> int | None:
        """
               Provádí operaci process value.

               :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``str()``, pracuje se s atributy ``decode``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.

            :raises ImportDataError: Vyvolá se při splnění podmínky ``value``.
        """

        if not value:
            return None
        if isinstance(value, int) or isinstance(value, float):
            value = str(value)
        elif isinstance(value, bytes):
            value = value.decode("utf-8")
        match = self.pattern.search(value)
        if match:
            return int(match.group())
        raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_integer_value')}: {value}")


class PositiveIntegerImportField(BaseImportField):
    """
    Importní pole pro kladné celočíselné hodnoty. Záporná čísla způsobí vyvolání ImportDataError.
    """

    def _process_value(self, value) -> int | None:
        """
               Provádí operaci process value.

               :param value: Parametr ``value`` předává se do volání ``_process_value()``, ``ImportDataError()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.

            :raises ImportDataError: Vyvolá se při splnění podmínky ``value is not None and value < 0``.
        """
        value = super()._process_value(value)
        if value is not None and value < 0:
            raise ImportDataError(f"{_('core_admin.ImportDataError.message.invalid_positive_integer_value')}: {value}")
        return value


class DecimalImportField(BaseImportField):
    """Importní pole pro desetinná čísla (float)."""

    pattern = re.compile(r"^-?\d+\.?\d*$")

    def _process_value(self, value) -> float | None:
        """
               Provádí operaci process value.

               :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``str()``, pracuje se s atributy ``decode``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.

            :raises ImportDataError: Vyvolá se při splnění podmínky ``value``.
        """
        if not value:
            return None
        if isinstance(value, Decimal) or isinstance(value, float):
            value = str(value)
        elif isinstance(value, bytes):
            value = value.decode("utf-8")
        match = self.pattern.fullmatch(value)
        if match:
            return float(match.group())
        raise ImportDataError(f"{_('core_admin.DecimalImportField.message.invalid_decimal_value')}: {value}")


class BooleanImportField(BaseImportField):
    """Importní pole pro hodnoty datového typu boolean."""

    def _process_value(self, value) -> bool | None:
        """
               Provádí operaci process value.

                Převede řetězec na bool. Pokud hodnota není "true"/"1" ani "false"/"0", vyvolá ImportDataError.

               :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``ImportDataError()``, pracuje se s atributy ``lower``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.

            :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.
        """

        if isinstance(value, bool):
            return value
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        normalized_value = str(value).strip().lower()
        if normalized_value in ("true", "1", "-1"):
            return True
        if normalized_value in ("false", "0"):
            return False
        raise ImportDataError(_("core_admin.BooleanImportField.message.invalid_boolean_value") + ": " + str(value))


class DateImportField(BaseImportField):
    """Importní pole pro hodnoty datového typu date."""

    pattern_iso = re.compile(r"(\d{4}-\d{1,2}-\d{1,2})(?:[ T]\d{1,2}:\d{1,2}(?::\d{1,2})?)?")
    pattern_dotted_year_first = re.compile(r"(\d{4}\.\d{1,2}\.\d{1,2})(?: \d{1,2}:\d{1,2}(?::\d{1,2})?)?")
    pattern_localized = re.compile(r"(\d{1,2}\. ?\d{1,2}\. ?\d{4})(?: \d{1,2}:\d{1,2}(?::\d{1,2})?)?")

    @property
    def value(self):
        """
        Provádí operaci value.

        :return: Vrací hodnotu podle větve zpracování.
        """
        return self._value.isoformat() if self._value else None

    @value.setter
    def value(self, value):
        """
        Provádí operaci value.

        :param value: Parametr ``value`` předává se do volání ``_process_value()``, pracuje se s atributy ``setter``.
        """
        self._value = self._process_value(value)

    @property
    def serialized_value(self):
        """
        Provádí operaci serialized value.

        :return: Vrací hodnotu podle větve zpracování.
        """
        return self._value.strftime("%Y-%m-%d") if self._value else None

    def _process_value(self, value) -> datetime.date | None:
        """
        Převede vstupní hodnotu na ``date``.

        Podporované formáty jsou ``YYYY-MM-DD``, ``YYYY.MM.DD`` a ``DD.MM.YYYY``.
        Případná časová složka vstupu (např. ``"2026-05-31 13:45:59"``) se ignoruje
        a zpracuje se pouze část s datem.

        :param value: Vstupní hodnota.
        :return: Hodnota ``date`` nebo ``None`` pro prázdnou hodnotu.
        :raises ImportDataError: Vyvolá se, pokud hodnota neodpovídá podporovanému formátu.
        """
        if not value or str(value).lower() == "nan":
            return None
        if isinstance(value, str):
            try:
                if match := self.pattern_iso.match(value):
                    return datetime.datetime.strptime(match.group(1), "%Y-%m-%d").date()
                if match := self.pattern_dotted_year_first.match(value):
                    return datetime.datetime.strptime(match.group(1), "%Y.%m.%d").date()
                if match := self.pattern_localized.match(value):
                    return datetime.datetime.strptime(match.group(1).replace(" ", ""), "%d.%m.%Y").date()
            except ValueError:
                raise ImportDataError(_("core_admin.ImportDataError.message.invalid_date_value") + ": " + str(value))
        if isinstance(value, datetime.date):
            return value
        raise ImportDataError(_("core_admin.ImportDataError.message.invalid_date_value") + ": " + str(value))


class DateTimeImportField(BaseImportField):
    """
    Importní pole pro hodnoty datového typu datetime.

    Podporované formáty vstupu:

    .. list-table::
       :header-rows: 1
       :widths: 30 35 35

       * - Formát
         - Příklad
         - Výstup
       * - ``YYYY-MM-DD HH:MM:SS``
         - ``2026-05-31 13:45:59``
         - ``2026-05-31 13:45:59``
       * - ``YYYY.MM.DD HH:MM:SS``
         - ``2026.05.31 13:45:59``
         - ``2026-05-31 13:45:59``
       * - ``DD.MM.YYYY HH:MM:SS``
         - ``31.05.2026 13:45:59``
         - ``2026-05-31 13:45:59``
    """

    patterns = (
        (re.compile(r"(\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}).*"), "%Y-%m-%d %H:%M:%S"),
        (re.compile(r"(\d{4}\.\d{1,2}\.\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}).*"), "%Y.%m.%d %H:%M:%S"),
        (re.compile(r"(\d{1,2}\.\d{1,2}\.\d{4} \d{1,2}:\d{1,2}:\d{1,2}).*"), "%d.%m.%Y %H:%M:%S"),
    )

    @property
    def value(self):
        """
        Provádí operaci value.

        :return: Vrací hodnotu podle větve zpracování.
        """
        return self._value.strftime("%Y-%m-%d %H:%M:%S") if self._value else None

    @value.setter
    def value(self, value):
        """
        Provádí operaci value.

        :param value: Parametr ``value`` předává se do volání ``_process_value()``, pracuje se s atributy ``setter``.
        """
        self._value = self._process_value(value)

    @property
    def serialized_value(self):
        """
        Provádí operaci serialized value.

        :return: Vrací hodnotu podle větve zpracování.
        """
        return self._value.strftime("%Y-%m-%d %H:%M:%S") if self._value else None

    def _process_value(self, value) -> datetime.datetime | None:
        """
        Převede vstupní hodnotu na ``datetime`` v lokální časové zóně.

        :param value: Vstupní hodnota.
        :return: Hodnota ``datetime`` s časovou zónou, nebo ``None`` pro prázdnou hodnotu.
        :raises ImportDataError: Vyvolá se, pokud hodnota neodpovídá žádnému podporovanému formátu.
        """
        if not value or str(value).lower() == "nan":
            return None
        if isinstance(value, str):
            try:
                for pattern, datetime_format in self.patterns:
                    if match := pattern.match(value):
                        parsed_value = datetime.datetime.strptime(match.group(1), datetime_format)
                        return timezone.make_aware(parsed_value)
            except ValueError:
                raise ImportDataError(
                    _("core_admin.ImportDataError.message.invalid_date_time_value") + ": " + str(value)
                )
        if isinstance(value, datetime.datetime):
            return value
        raise ImportDataError(_("core_admin.ImportDataError.message.invalid_date_time_value") + ": " + str(value))


class DateRangeImportField(BaseImportField):
    """Importní pole pro hodnoty datového typu date range."""

    pattern = re.compile(r"\[\d{4}-\d{1,2}-\d{1,2}, ?\d{4}-\d{1,2}-\d{1,2}\)")

    @property
    def serialized_value(self):
        """
        Provádí operaci serialized value.

        :return: Vrací hodnotu podle větve zpracování.
        """
        return f"[{self.value.lower.strftime('%Y-%m-%d')},{self.value.upper.strftime('%Y-%m-%d')})"

    def _process_value(self, value) -> DateRange | None:
        """
               Provádí operaci process value.

               Převede řetězec na DateRange ve formátu "[YYYY-MM-DD, YYYY-MM-DD)".
               Pokud hodnota neodpovídá očekávanému formátu, vyvolá ImportDataError.

               :param value: Parametr ``value`` předává se do volání ``str()``, ``isinstance()``, pracuje se s atributy ``strip``, ovlivňuje větvení podmínek.
        :return: Výstup funkce odpovídající implementované logice.

            :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.
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
    """Importní pole pro hodnoty odkazující na instanci jiného modelu (cizí klíč)."""

    _records_context = ContextVar("lookup_import_field_records", default=None)
    _lookup_cache_context = ContextVar("lookup_import_field_cache", default=None)

    def __init__(
        self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", limit_choices_to: dict | None = None
    ):
        """
        Inicializuje instanci třídy.

        :param lookup_model_classes: Parametr ``lookup_model_classes`` předává se do volání ``isinstance()``, ovlivňuje větvení podmínek.
        :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.
        :param limit_choices_to: Parametr ``limit_choices_to`` ovlivňuje větvení podmínek.

            :raises ValueError: Vyvolá se s textem ``core_admin.LookupImportField.message.limit_choices_to_unsupported_model``.
        """
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
            raise ValueError(_("core_admin.LookupImportField.message.limit_choices_to_unsupported_model"))
        self.limit_choices_to = limit_choices_to

    @classmethod
    def clear_cache(cls):
        """
        Vyčistí cache vyhledaných FK záznamů v aktuálním kontextu.

        :return: Funkce nevrací žádnou hodnotu.
        """
        cls._lookup_cache_context.set({})

    @classmethod
    def clear_records(cls):
        """
        Vyčistí seznam importovaných záznamů v aktuálním kontextu.

        :return: Funkce nevrací žádnou hodnotu.
        """
        cls._records_context.set([])

    @classmethod
    def set_records(cls, records):
        """
        Nastaví seznam dosud připravených importovaných záznamů pro aktuální kontext.

        :param records: Seznam záznamů dostupný pro FK lookup při validaci importu.
        :return: Funkce nevrací žádnou hodnotu.
        """
        cls._records_context.set(records)

    @classmethod
    def get_records(cls):
        """
        Vrátí seznam importovaných záznamů dostupný v aktuálním kontextu.

        :return: Seznam záznamů nebo prázdný seznam, pokud ještě nebyl nastaven.
        """
        records = cls._records_context.get()
        if records is None:
            records = []
            cls._records_context.set(records)
        return records

    @classmethod
    def get_lookup_cache(cls):
        """
        Vrátí cache vyhledaných FK záznamů pro aktuální kontext.

        :return: Slovník s cache lookup výsledků.
        """
        lookup_cache = cls._lookup_cache_context.get()
        if lookup_cache is None:
            lookup_cache = {}
            cls._lookup_cache_context.set(lookup_cache)
        return lookup_cache

    @property
    def instance_value(self):
        """
        Provádí operaci instance value.

        :return: Vrací atribut objektu.
        """
        return self._instance_value

    @staticmethod
    def _get_record_lookup_value(record, lookup_field_name):
        """
        Vrátí hodnotu atributu z importovaného záznamu i pro lookup cesty s oddělovačem ``__``.

        :param record: Parametr ``record`` předává se do volání ``getattr()``.
        :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.

        :return: Vrací hodnotu atributu nebo ``None``, pokud cestu nelze vyhodnotit.
        """
        value = record
        for attribute in lookup_field_name.split("__"):
            if value is None:
                return None
            value = getattr(value, attribute, None)
        return value

    @staticmethod
    def _get_cache_key(model_class, lookup_field_name, value):
        """
        Sestaví klíč pro sdílenou cache vyhledaných instancí.

        :param model_class: Třída modelu použitá pro lookup.
        :param lookup_field_name: Název lookup pole.
        :param value: Vyhledávaná hodnota.
        :return: N-tice použitelná jako klíč cache.
        """
        return model_class, lookup_field_name, value

    def _check_limit_choices_to(self, record):
        """
        Ověří limit choices to.

        :param record: Parametr ``record`` předává se do volání ``all()``, ``getattr()``, ovlivňuje větvení podmínek.
        :return: Vrací výsledek ověření nebo validačního pravidla.

            :raises ImportDataLimitChoicesError: Vyvolá se při splnění podmínky ``not all((getattr(record, k).pk == v for k, v in self.limit_choices_to.items()))``.
        """
        if self.limit_choices_to:
            if not all(getattr(record, k).pk == v for k, v in self.limit_choices_to.items()):
                raise ImportDataLimitChoicesError(record, self.limit_choices_to, self.field_verbose_name)

    def _process_value(self, value):
        """
               Provádí operaci process value.

               Ověří existenci hodnoty v databázi nebo v importovaných záznamech a vrátí odpovídající záznam.
               Pokud referencovaný záznam neexistuje a lookup je omezen přes ``nazev_heslare``,
               vyvolá ImportDataMissingHeslarValueError; jinak ImportDataMissingReferencedValueError.

               :param value: Parametr ``value`` předává se do volání ``str()``, ``len()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.

            :raises ImportDataMissingHeslarValueError: Vyvolá se, pokud hodnota neodpovídá hesláři určenému omezením ``nazev_heslare``.
            :raises ImportDataMissingReferencedValueError: Vyvolá se v ostatních případech, kdy referencovaný záznam nebyl nalezen.
        """

        self._instance_value = None
        if str(value).lower() == "nan" or value is None or len(str(value)) == 0:
            return None
        lookup_cache = self.get_lookup_cache()
        records = self.get_records()
        for current_class in self.lookup_model_class_list:
            cache_key = self._get_cache_key(current_class, self.lookup_field_name, value)
            record = lookup_cache.get(cache_key)
            if record:
                self._check_limit_choices_to(record)
                self._instance_value = record
                return value
            record = current_class.objects.filter(**{self.lookup_field_name: value}).first()
            if record:
                lookup_cache[cache_key] = record
                self._check_limit_choices_to(record)
                self._instance_value = record
                return value
            filtered_records = [
                record
                for record in records
                if isinstance(record, current_class)
                and self._get_record_lookup_value(record, self.lookup_field_name) == value
            ]
            if len(filtered_records) == 1:
                lookup_cache[cache_key] = filtered_records[0]
                self._check_limit_choices_to(filtered_records[0])
                self._instance_value = filtered_records[0]
                return value
        if self.limit_choices_to and "nazev_heslare" in self.limit_choices_to:
            raise ImportDataMissingHeslarValueError(
                self.lookup_field_name,
                self.limit_choices_to["nazev_heslare"],
                value,
            )
        raise ImportDataMissingReferencedValueError(
            value,
            ", ".join([current_class.__name__ for current_class in self.lookup_model_class_list]),
            self.lookup_field_name,
        )


class RuianLookupImportField(LookupImportField):
    """
    Rozšíření LookupImportField pro import dat z RUIAN. Odstraní prefix "ruian-" a převede hodnotu na integer.
    """

    @LookupImportField.value.setter
    def value(self, value):
        """
        Provádí operaci value.

        :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``match()``, ovlivňuje větvení podmínek.
        """
        if isinstance(value, str):
            match = re.match(r"ruian-(\d+)", value)
            value = int(match.group(1))
        LookupImportField.value.fset(self, value)


class VazbaLookupImportField(LookupImportField):
    """Importní pole pro referencované modely přes vazbu (relaci). Relace je 1:1 místo 1:N."""

    def __init__(self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", read_field_name: str = None):
        """
        Inicializuje instanci třídy.

        :param lookup_model_classes: Parametr ``lookup_model_classes`` předává se do volání ``__init__()``.
        :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.
        :param read_field_name: Textový název nebo klíč ``read_field_name`` používaný v rámci operace.
        """
        super().__init__(lookup_model_classes, lookup_field_name)
        self.read_field_name = read_field_name

    def _process_value(self, value):
        """
               Provádí operaci process value.

               :param value: Parametr ``value`` předává se do volání ``get_record_from_ident()``, ``get()``, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.

            :raises ImportDataMissingReferencedValueError: Vyvolá se v konkrétních chybových větvích této funkce.
        """
        if value is None:
            return None
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
                    dokument_cast = DokumentCast.objects.get(ident_cely=value)
                    self._instance_value = (
                        getattr(dokument_cast, self.read_field_name)
                        if self.read_field_name and hasattr(dokument_cast, self.read_field_name)
                        else dokument_cast
                    )
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
        raise ImportDataMissingReferencedValueError(value, missing_field_name=self.lookup_field_name)


class GeomImportField(BaseImportField):
    """Importní pole pro geometrické hodnoty."""

    def __init__(self, srid):
        """
        Inicializuje instanci třídy.

        :param srid: Parametr ``srid`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        super().__init__()
        self.srid = srid

    @property
    def serialized_value(self):
        """
        Provádí operaci serialized value.

        :return: Vrací výsledek volání ``getattr()``.
        """
        return getattr(self._value, "wkt", None)

    def _process_value(self, value) -> GEOSGeometry | None:
        """
               Provádí operaci process value.

               Převede řetězec na objekt GEOSGeometry. Pokud převod selže, vyvolá ImportDataError.

               :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``GEOSGeometry()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.

            :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.
        """
        if not value:
            return None
        if isinstance(value, str):
            value = GEOSGeometry(value, srid=self.srid)
        if isinstance(value, GEOSGeometry):
            if value.srid != self.srid:
                raise ImportDataError(
                    f"{_('core_admin.GeomImportField.message.srid_mismatch')}: {value.srid} != {self.srid}"
                )
            return value
        raise ImportDataError(f"{_('core_admin.GeomImportField.message.invalid_date_value')}: {value}")


class GenericForeignKeyImportField(LookupImportField):
    """Importní pole pro generický cizí klíč."""

    def __init__(
        self, lookup_model_classes=None, lookup_field_name: str = "ident_cely", serialized_attribute: str = None
    ):
        """
        Inicializuje instanci třídy.

        :param lookup_model_classes: Parametr ``lookup_model_classes`` předává se do volání ``__init__()``.
        :param lookup_field_name: Textový název nebo klíč ``lookup_field_name`` používaný v rámci operace.
        :param serialized_attribute: Parametr ``serialized_attribute`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        super().__init__(lookup_model_classes, lookup_field_name)
        self.serialized_attribute = serialized_attribute

    @property
    def serialized_value(self):
        """
        Provádí operaci serialized value.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``getattr()``, atribut objektu.
        """
        if self.serialized_attribute:
            return getattr(self._instance_value, self.serialized_attribute)
        else:
            return self._value

    def _process_value(self, value: str | int):
        """
        Vyhledá objekt generického cizího klíče v databázi a vrátí původní identifikátor.

        Model instanci ukládá do ``self._instance_value`` — stejný kontrakt jako ``LookupImportField``.
        Původní identifikátor (string nebo int) se vrací jako návratová hodnota, čímž je zachován
        LSP kontrakt s rodičovskou třídou.

        :param value: Identifikátor záznamu — string ve formátu ``"<prefix>-<číslo>"`` nebo číslo.
        :return: Původní identifikátor po případné konverzi na int.
        :raises ImportDataMissingReferencedValueError: Vyvolá se, pokud hodnota není nalezena v žádném z modelů.
        """
        if isinstance(value, str) and (match := re.match(r"(?:\w+-)?(\d+)", value)):
            value = int(match.group(1))

        for current_class in self.lookup_model_class_list:
            try:
                self._instance_value = current_class.objects.get(**{self.lookup_field_name: value})
                return value
            except current_class.DoesNotExist:
                continue
        raise ImportDataMissingReferencedValueError(
            value,
            ", ".join([current_class.__name__ for current_class in self.lookup_model_class_list]),
            self.lookup_field_name,
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

    _registry: dict[str, type["ImportModelMapper"]] = {}

    @classmethod
    def register(cls, file_key: str):
        """Dekorátor pro registraci třídy mapperu pod daným klíčem souboru.

        :param file_key: Klíč (název souboru bez přípony), pod kterým se mapper registruje.
        :return: Vrací dekorátor přijímající třídu mapperu.
        """

        def decorator(mapper_cls: type["ImportModelMapper"]) -> type["ImportModelMapper"]:
            cls._registry[file_key] = mapper_cls
            return mapper_cls

        return decorator

    def __init__(self, value_dict):
        """
        Inicializuje instanci třídy.

        :param value_dict: Kolekce nebo datová struktura `value_dict` zpracovávaná touto funkcí.
        """
        self.value_dict = value_dict
        if self.require_primary_key_value is None:
            self.require_primary_key_value = isinstance(self.primary_key, tuple)

    @classmethod
    def get_import_data_mapper_dict(cls):
        """
        Vrátí slovník mapující názvy importních souborů na příslušné třídy mapperů.

        :return: Vrací slovník registrovaných mapperů.
        """

        return cls._registry

    @classmethod
    def get_import_data_mapper(cls, file_name):
        """
        Vrátí třídu mapperu odpovídající zadanému názvu souboru (bez přípony).

        :param file_name: Parametr ``file_name`` se předává do volání ``get()``, pracuje se s atributy ``split``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``get()``.
        """

        return cls.get_import_data_mapper_dict().get(file_name.split(".")[0])

    @classmethod
    def get_file_name_for_mapper(cls, mapper_class):
        """
        Vrátí název souboru odpovídající zadané třídě mapperu.

        :param mapper_class: Třída mapperu, podle které se vyhledá odpovídající název souboru.
        """

        return [k for k, v in cls.get_import_data_mapper_dict().items() if v == mapper_class][0]

    @classmethod
    def get_mapping(cls, include_primary_key=False) -> dict:
        """
        Vrátí slovník mapování polí pomocí metody map_field.

        :param include_primary_key: Parametr ``include_primary_key`` ovlivňuje větvení podmínek.
        :return: Vrací výsledek operace.
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

    @classmethod
    def load_record_from_db(cls, record):
        """
        Načte aktuální podobu záznamu z databáze podle jeho primárního klíče.

        :param record: Instance modelu, jejíž aktuální stav má být z databáze znovu načten.
        :return: Nalezený záznam z databáze, jinak ``None`` při chybě nebo nepodporovaném primárním klíči.
        """
        if isinstance(cls.primary_key, str):
            try:
                return cls.model_class.objects.get(pk=record.pk)
            except Exception:
                return None

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        """
        Vrátí slovník s názvem (názvy) a hodnotou (hodnotami) primárního klíče pro filtrování.

        :return: Vrací hodnotu typu ``dict | None``; podle větve může jít o: None, slovník, hodnotu podle větve zpracování.
        """

        def value_dict_name(value):
            """
            Provádí operaci value dict name.

            :param value: Parametr ``value`` pracuje se s atributy ``split``, vstupuje do návratové hodnoty.

                :return: Vrací hodnotu podle větve zpracování.
            """
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
        """
               Zpracuje primary key.

               :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``match()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :return: Výstup funkce odpovídající implementované logice.

            :raises ImportDataIncorrectPrimaryKeyFormatError: Vyvolá se při splnění podmínky ``match``.
        """
        if isinstance(value, str) and cls.primary_key_prefix:
            match = re.match(f"{cls.primary_key_prefix}-(.*)", value)
            if match:
                return int(match.group(1))
            else:
                raise ImportDataIncorrectPrimaryKeyFormatError(value)
        return value

    @staticmethod
    def _parse_primary_key_custom_prefix(value, prefix):
        """
               Zpracuje primary key custom prefix.

               :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``int()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
               :param prefix: Číselná hodnota ``prefix`` použitá při výpočtu nebo transformaci.
        :return: Výstup funkce odpovídající implementované logice.
        """
        if isinstance(value, str) and prefix:
            return int(re.match(f"{prefix}-(.*)", value).group(1))
        return value

    @classmethod
    def map_field(cls, field_name):
        """
        Namapuje pole modelu na odpovídající instanci BaseImportField nebo její podtřídy.

        :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``BaseImportField()``, výsledek volání ``IntegerImportField()``, výsledek volání ``PositiveIntegerImportField()``.
            :raises ImportDataError: Vyvolá se v konkrétních chybových větvích této funkce.
        """
        return cls._import_field_for_model_field(cls.model_class, field_name)

    @classmethod
    def _import_field_for_model_field(cls, model_class, field_name):
        """
        Vrátí instanci importního pole odpovídající typu pole ``field_name`` v ``model_class``.

        :param model_class: Modelová třída, na které se pole hledá.
        :param field_name: Název pole modelu.
        :return: Instance ``BaseImportField`` nebo její podtřídy, případně ``None`` pro ``ForeignKey``.
        :raises ImportDataError: Pokud typ pole není podporován.
        """
        model_field = model_class._meta.get_field(field_name)
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
        """
        Určí, zda field required.

        :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.
        :return: Vrací výsledek ověření nebo validačního pravidla.
        """
        try:
            model_field = cls.model_class._meta.get_field(field_name)
            return not model_field.null
        except FieldDoesNotExist:
            return False

    def create_records(self, performed_action) -> list:
        """
        Vytvoří instanci záznamu nebo více instancí modelů připravených k uložení do databáze.

        :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``ImportDataError()``, ovlivňuje větvení podmínek.
        :return: Nově vytvořená hodnota připravená touto funkcí.

            :raises ImportDataError: Vyvolá se při splnění podmínky ``performed_action not in (ImportDataAdminForm.PERFORMED_ACTION_INSERT, ImportDataAdminForm.PERFORMED_ACTION_UPDATE, ImportDataAdminForm.PERFO``.
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

    def import_validation(self, performed_action, *args, **kwargs) -> dict | None:
        """
        Provede validaci na základě primárního klíče. Při insertu záznam nesmí existovat,

        při updatu musí existovat. Vrátí slovník s primárními klíči, nebo vyvolá ImportDataIntegrityError.

        :param performed_action: Parametr ``performed_action`` předává se do volání ``ImportDataIntegrityError()``, ovlivňuje větvení podmínek.
        :param args: Dodatečné poziční argumenty zachované kvůli jednotné signatuře, metoda je nepoužívá.
        :param kwargs: Dodatečné pojmenované argumenty zachované kvůli jednotné signatuře, metoda je nepoužívá.
        :return: Vrací výsledek operace.

            :raises ImportDataIntegrityError: Vyvolá se při splnění podmínky ``performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT and self.model_class.objects.filter(**self._get_filter_kwargs_primary_key())``; nebo při splnění podmínky ``performed_action in (ImportDataAdminForm.PERFORMED_ACTION_UPDATE, ImportDataAdminForm.PERFORMED_ACTION_DELETE) and (not self.model_class.obj``.
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
        """
        Ověří column structure.

        :param performed_action: Parametr ``performed_action`` ovlivňuje větvení podmínek.
        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``set()``, ``get_mapping()``.
        :return: Vrací výsledek ověření nebo validačního pravidla.

            :raises ImportDataIncorrectStructureError: Vyvolá se při splnění podmínky ``missing_columns or excess_columns``.
        """
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

        :param performed_action: Parametr ``performed_action`` předává se do volání ``_check_column_structure()``.
        :param instance_values: Parametr ``instance_values`` ovlivňuje větvení podmínek.
        :param serialize: Parametr ``serialize`` slouží jako vstup pro logiku funkce ``map``.
        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``_check_column_structure()``, ``get_mapping()``.
        :return: Vrací výsledek operace.
        """

        self._check_column_structure(performed_action, include_primary_key)

        mapping_dict = {}
        for field_name, field_instance in self.get_mapping(include_primary_key).items():
            if field_name in self.value_dict:
                field_value = self.value_dict[field_name]
                field_instance.set_import_context(self.model_class, self.map_column_name_to_field_name(field_name))
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
        """
        Ověří required fields.

        :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``check_required_fields``.

            :raises ImportDataError: Vyvolá se při splnění podmínky ``required and (value is None or str(value).lower().strip() in ('nan', '') or pd.isna(value))``.
        """
        for key, value in self.value_dict.items():
            required = self.is_field_required(key)
            if required and (value is None or str(value).lower().strip() in ("nan", "") or pd.isna(value)):
                raise ImportDataError(f"{_('core_admin.ImportDataError.message.missing_required_field')}: {key}")

    def map_column_name_to_field_name(self, column_name):
        """
        Provádí operaci map column name to field name.

        Převede název sloupce z importního souboru na název pole Django modelu.
        Používá se, pokud se název pole liší od názvu databázového sloupce.

        :param column_name: Textový název nebo klíč ``column_name`` používaný v rámci operace.

            :return: Vrací výsledek volání ``get()``.
        """

        return self.column_to_field_mapping.get(column_name, column_name)

    @classmethod
    def create_relations(cls, instance):
        """
        Vytvoří vazební záznamy pro Historie, Komponenty a Soubory, pokud ještě neexistují.

        :param instance: Parametr ``instance`` předává se do volání ``getattr()``, pracuje se s atributy ``historie``, ``soubory``, ovlivňuje větvení podmínek.
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
    def record_postprocessing(cls, record, performed_action, fedora_transaction):
        """
        Provádí operaci record postprocessing.

        :param record: Parametr ``record`` vstupuje do návratové hodnoty.
        :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``record_postprocessing``.
        :param fedora_transaction: Parametr ``fedora_transaction`` slouží jako vstup pro logiku funkce ``record_postprocessing``.

            :return: Vrací proměnná ``record``.
        """
        return record

    @classmethod
    def fedora_update_targets(cls, record) -> set:
        """
        Vrátí cíle pro následnou aktualizaci ve Fedoře odvozené z navázaných záznamů.

        :param record: Záznam, po jehož změně se mají vyhledat dotčené objekty s ``ident_cely``.
        :return: Množina dvojic ``(třída, primární_klíč)`` pro záznamy, které mají být ve Fedoře aktualizovány.
        """
        return {
            (item.__class__, item.pk)
            for item in cls._get_updated_ident_cely_record_list(record)
            if item and getattr(item, "ident_cely", None)
        }

    @staticmethod
    def _get_updated_ident_cely_record_list(record) -> list:
        """
        Vrátí výchozí seznam záznamů, jejichž ``ident_cely`` se má po změně přegenerovat.

        :param record: Záznam zpracovávaný importem.
        :return: Seznam obsahující přímo ``record`` pro modely s metadaty, jinak prázdný seznam.
        """
        if isinstance(record, ModelWithMetadata):
            return [record]
        else:
            return []

    @staticmethod
    def get_record_history(record):
        """
        Určí výchozí cíl pro zápis historie importované změny.

        :param record: Záznam, pro který se má najít objekt určený pro historii.
        :return: ``None``, pokud mapper nemá definovaný konkrétní cílový objekt historie.
        """
        return None


class GeometryTransformMixin:
    """
    Mixin pro mappery s geometrickými poli. Při insertu zajišťuje konverzi mezi souřadnicovými systémy:

    WGS84 (SRID 4326) → S-JTSK (SRID 5514) a naopak.
    """

    def transform_geometries(self, mapping_dict, performed_action):
        """
        Transformuje geometries. v aplikaci.

        :param mapping_dict: Parametr ``mapping_dict`` předává se do volání ``transform_geom_to_sjtsk()``, ``transform_geom_to_wgs84()``, pracuje se s atributy ``get``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param performed_action: Parametr ``performed_action`` ovlivňuje větvení podmínek.

            :return: Vrací proměnná ``mapping_dict``.
        """
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
    lookup_fields_mapping: dict = {}

    @classmethod
    def _field_to_model(cls):
        """
        Sestaví mapování ``field_name -> model_class`` na základě ``cls.fields``, ``cls.foreign_key_fields``
        a ``cls.classes``. Slouží k tomu, aby typově korektní importní pole bylo zvoleno i tehdy,
        když jeden mapper pokrývá více modelů.
        """
        alias_to_model = {entry[0]: entry[1] for entry in cls.classes}
        mapping = {}
        for model_alias, field_name in tuple(cls.fields) + tuple(cls.foreign_key_fields):
            if model_alias in alias_to_model:
                mapping[field_name] = alias_to_model[model_alias]
        return mapping

    @classmethod
    def map_field(cls, field_name):
        """
        Najde správný model pro ``field_name`` napříč všemi modely mapperu a vrátí
        odpovídající importní pole. Pole z ``lookup_fields_mapping`` má přednost.

        :param field_name: Název sloupce importovaného souboru.
        :return: Instance ``BaseImportField`` nebo její podtřídy.
        """
        if field_name in cls.lookup_fields_mapping:
            return cls.lookup_fields_mapping[field_name]
        model_class = cls._field_to_model().get(field_name)
        if model_class is None:
            return BaseImportField()
        model_field_name = cls.column_to_field_mapping.get(field_name, field_name)
        try:
            import_field = cls._import_field_for_model_field(model_class, model_field_name)
        except FieldDoesNotExist:
            return BaseImportField()
        if import_field is None:
            return BaseImportField()
        return import_field

    def import_validation(self, performed_action, *args, **kwargs):
        """
        Ověří existenci více-modelového záznamu podle ``ident_cely`` hlavního archeologického záznamu.

        :param performed_action: Typ prováděné operace importu.
        :param args: Další poziční argumenty předané nadřazené implementaci.
        :param kwargs: Další klíčové argumenty předané nadřazené implementaci.
        :return: Slovník filtračních podmínek pro dohledání cílového záznamu.
        :raises ImportDataIntegrityError: Vyvolá se, pokud záznam při insertu již existuje nebo při updatu či mazání chybí.
        """
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
        """
        Vrací filter kwargs primary key.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        return {"ident_cely": self.value_dict.get("ident_cely")}

    def create_records(self, performed_action) -> list:
        """
        Vytvoří records. v aplikaci.

        :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ovlivňuje větvení podmínek.
        :return: Nově vytvořená hodnota připravená touto funkcí.
        """
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
                if field_name in mapping_dict:
                    setattr(instance_class_0, field_name, field_value)
            for field_name, field_value in mapping_dict_class_1.items():
                if field_name in mapping_dict:
                    setattr(instance_class_1, field_name, field_value)
            return [instance_class_0, instance_class_1]
        return []

    @classmethod
    def is_field_required(cls, field_name) -> bool:
        """
        Určí, zda field required.

        :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.
        :return: Vrací výsledek ověření nebo validačního pravidla.
        """
        for mapper_class_tuple in cls.classes:
            mapper_class = mapper_class_tuple[1]
            try:
                model_field = mapper_class._meta.get_field(field_name)
                return not model_field.null and not model_field.has_default()
            except FieldDoesNotExist:
                continue
        return False


@ImportModelMapper.register("heslar")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["nazev_heslare"] = LookupImportField(HeslarNazev, "nazev")
        return field_mapping


@ImportModelMapper.register("heslar_datace")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["obdobi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBDOBI})
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record) -> list:
        """
        Vrátí heslářové období navázané na importovanou dataci.

        :param record: Záznam ``HeslarDatace`` po importu.
        :return: Seznam s objektem ``obdobi``, jehož identifikátor se má případně aktualizovat.
        """
        return [record.obdobi]


@ImportModelMapper.register("heslar_dokument_typ_material_rada")
class HeslarDokumentTypMaterialRadaMapper(ImportModelMapper):
    """Mapovač pro model HeslarDokumentTypMaterialRada."""

    model_class = HeslarDokumentTypMaterialRada
    primary_key = "id"
    primary_key_prefix = "hdtm"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
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

    @staticmethod
    def _get_updated_ident_cely_record_list(record: HeslarDokumentTypMaterialRada) -> list:
        """
        Vrátí dokumentovou řadu navázanou na importovanou kombinaci typu a materiálu.

        :param record: Záznam ``HeslarDokumentTypMaterialRada`` po importu.
        :return: Seznam s navázanou hodnotou ``dokument_rada``.
        """
        return [record.dokument_rada]


@ImportModelMapper.register("heslar_hierarchie")
class HeslarHierarchieMapper(ImportModelMapper):
    """Mapovač pro model HeslarHierarchie."""

    fields = ("typ",)
    model_class = HeslarHierarchie
    primary_key = "id"
    primary_key_prefix = "hier"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["heslo_nadrazene"] = LookupImportField(Heslar)
        field_mapping["heslo_podrazene"] = LookupImportField(Heslar)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: HeslarHierarchie) -> list:
        """
        Vrátí oba heslářové uzly propojené importovanou hierarchií.

        :param record: Záznam ``HeslarHierarchie`` po importu.
        :return: Seznam nadřazeného a podřazeného hesla.
        """
        return [record.heslo_nadrazene, record.heslo_podrazene]


@ImportModelMapper.register("heslar_odkazy")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["heslo"] = LookupImportField(Heslar)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: HeslarOdkaz) -> list:
        """
        Vrátí heslo navázané na importovaný externí odkaz hesláře.

        :param record: Záznam ``HeslarOdkaz`` po importu.
        :return: Seznam s heslem, jehož metadata mohou být změnou odkazu dotčena.
        """
        return [record.heslo]


@ImportModelMapper.register("organizace")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
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

    @staticmethod
    def _get_updated_ident_cely_record_list(record: Organizace) -> list:
        """
        Vrátí přímo importovanou organizaci jako cíl pro následné aktualizace.

        :param record: Záznam ``Organizace`` po importu.
        :return: Jednoprvkový seznam obsahující importovanou organizaci.
        """
        return [record]


@ImportModelMapper.register("osoby")
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


@ImportModelMapper.register("projekty")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
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
        """
               Provádí operaci map.

               :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``transform_geometries()``, vstupuje do návratové hodnoty.
               :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
               :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
               :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        return self.transform_geometries(mapping_dict, performed_action)

    @staticmethod
    def get_record_history(record: Projekt):
        """
        Vrátí projekt jako cíl pro zápis historie.

        :param record: Importovaný záznam ``Projekt``.
        :return: Přímo předaný projekt.
        """
        return record


@ImportModelMapper.register("projekty_katastry")
class ProjektKatastrMapper(ImportModelMapper):
    """Mapovač pro model ProjektKatastr."""

    model_class = ProjektKatastr
    primary_key = ("projekt", "katastr")
    allow_update = False
    primary_key_filter_field = ("projekt__ident_cely", "katastr__kod")
    primary_key_prefix = (None, "ruian")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["projekt"] = LookupImportField(Projekt)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: ProjektKatastr) -> list:
        """
        Vrátí projekt navázaný na importovanou vazbu ke katastru.

        :param record: Záznam ``ProjektKatastr`` po importu.
        :return: Seznam s projektem, jehož identifikátor je potřeba zohlednit.
        """
        return [record.projekt]

    @staticmethod
    def get_record_history(record: ProjektKatastr):
        """
        Vrátí projekt související s importovanou vazbou na katastr.

        :param record: Záznam ``ProjektKatastr`` po importu.
        :return: Projekt, do jehož historie má být změna propsána.
        """
        return record.projekt


@ImportModelMapper.register("projekty_oznamovatele")
class ProjektOznamovatelMapper(ImportModelMapper):
    """Mapovač pro model Oznamovatel."""

    fields = ("oznamovatel", "odpovedna_osoba", "adresa", "telefon", "email", "poznamka")
    model_class = Oznamovatel
    primary_key = "projekt"
    primary_key_filter_field = "projekt__ident_cely"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["projekt"] = LookupImportField(Projekt)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: Oznamovatel) -> list:
        """
        Vrátí projekt, k němuž patří importovaný oznamovatel.

        :param record: Záznam ``Oznamovatel`` po importu.
        :return: Seznam s navázaným projektem.
        """
        return [record.projekt]

    @staticmethod
    def get_record_history(record: Oznamovatel):
        """
        Vrátí projekt jako cíl pro historii změn oznamovatele.

        :param record: Záznam ``Oznamovatel`` po importu.
        :return: Projekt, k němuž se oznamovatel vztahuje.
        """
        return record.projekt


@ImportModelMapper.register("samostatne_nalezy")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
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
        """
               Provádí operaci map.

               :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``transform_geometries()``, vstupuje do návratové hodnoty.
               :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
               :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
               :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        return self.transform_geometries(mapping_dict, performed_action)

    @staticmethod
    def _get_updated_ident_cely_record_list(record: SamostatnyNalez) -> list:
        """
        Vrátí samostatný nález a jeho projekt pro návaznou aktualizaci identifikátorů.

        :param record: Záznam ``SamostatnyNalez`` po importu.
        :return: Seznam obsahující nález a případně jeho projekt.
        """
        return [record, record.projekt]

    @staticmethod
    def get_record_history(record: SamostatnyNalez):
        """
        Vrátí samostatný nález jako cíl pro historii změn.

        :param record: Záznam ``SamostatnyNalez`` po importu.
        :return: Přímo předaný nález.
        """
        return record


@ImportModelMapper.register("az_akce")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping = field_mapping | cls.lookup_fields_mapping
        return field_mapping

    @staticmethod
    def _is_import_null(value) -> bool:
        """
        Určí, zda importovaná hodnota reprezentuje prázdnou hodnotu.

        :param value: Hodnota z importovaného řádku.
        :return: ``True``, pokud hodnota odpovídá prázdné hodnotě.
        """
        return value is None or pd.isna(value) or str(value).strip().lower() in ("", "nan", "none", "null")

    def import_validation(self, performed_action, *args, **kwargs):
        """
        Ověří existenci archeologického záznamu a konzistenci typu akce s projektem.

        :param performed_action: Typ prováděné operace importu.
        :param args: Další poziční argumenty předané nadřazené implementaci.
        :param kwargs: Další klíčové argumenty předané nadřazené implementaci.
        :return: Slovník filtračních podmínek pro dohledání cílového záznamu.
        :raises ImportDataError: Vyvolá se, pokud ``typ`` a ``projekt`` porušují ``akce_typ_check``.
        """
        typ = self.value_dict.get("typ")
        projekt_is_null = self._is_import_null(self.value_dict.get("projekt"))
        if typ == Akce.TYP_AKCE_SAMOSTATNA and not projekt_is_null:
            raise ImportDataError(_("core_admin.ImportDataError.message.akce_typ_check.typ_n_requires_empty_projekt"))
        if typ == Akce.TYP_AKCE_PROJEKTOVA and projekt_is_null:
            raise ImportDataError(_("core_admin.ImportDataError.message.akce_typ_check.typ_r_requires_filled_projekt"))
        if not self._is_import_null(typ) and typ not in (Akce.TYP_AKCE_SAMOSTATNA, Akce.TYP_AKCE_PROJEKTOVA):
            raise ImportDataError(f"{_('core_admin.ImportDataError.message.akce_typ_check.invalid_typ')}: {typ}")
        return super().import_validation(performed_action, *args, **kwargs)

    @classmethod
    def record_postprocessing(cls, record, performed_action, fedora_transaction):
        """
        Provádí operaci record postprocessing.

        :param record: Parametr ``record`` předává se do volání ``isinstance()``, ``record_postprocessing()``, pracuje se s atributy ``typ_zaznamu``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param performed_action: Parametr ``performed_action`` předává se do volání ``record_postprocessing()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``record_postprocessing()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``record_postprocessing()``.
        """
        if isinstance(record, ArcheologickyZaznam) and performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
            record.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
        return super().record_postprocessing(record, performed_action, fedora_transaction)

    @staticmethod
    def _get_updated_ident_cely_record_list(record: Akce | ArcheologickyZaznam) -> list:
        """
        Vrátí archeologický záznam a projekt dotčené akce podle typu importovaného objektu.

        :param record: Záznam ``Akce`` nebo ``ArcheologickyZaznam`` po importu.
        :return: Seznam souvisejícího archeologického záznamu a projektu.
        """
        if isinstance(record, ArcheologickyZaznam):
            return [record, record.akce.projekt]
        elif isinstance(record, Akce):
            return [record.archeologicky_zaznam, record.projekt]

    @staticmethod
    def get_record_history(record: Akce | ArcheologickyZaznam):
        """
        Vrátí archeologický záznam, do jehož historie se změna akce zapisuje.

        :param record: Záznam ``Akce`` nebo ``ArcheologickyZaznam`` po importu.
        :return: Archeologický záznam odpovídající importované akci.
        """
        if isinstance(record, ArcheologickyZaznam):
            return record
        elif isinstance(record, Akce):
            return record.archeologicky_zaznam


@ImportModelMapper.register("az_lokality")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping = field_mapping | cls.lookup_fields_mapping
        return field_mapping

    @staticmethod
    def get_record_history(record: ArcheologickyZaznam | Lokalita):
        """
        Vrátí archeologický záznam navázaný na lokalitu.

        :param record: Záznam ``Lokalita`` nebo přímo ``ArcheologickyZaznam`` po importu.
        :return: Archeologický záznam, ke kterému se historie váže.
        """
        if isinstance(record, Lokalita):
            return record.archeologicky_zaznam
        else:
            return record


@ImportModelMapper.register("az_akce_vedouci")
class AkceVedouciMapper(ImportModelMapper):
    """Mapovač pro model AkceVedouci."""

    model_class = AkceVedouci
    primary_key = "id"
    primary_key_prefix = "vedo"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["akce"] = LookupImportField(Akce, "archeologicky_zaznam__ident_cely")
        field_mapping["vedouci"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        return field_mapping

    @staticmethod
    def get_record_history(record: AkceVedouci):
        """
        Vrátí archeologický záznam akce, k níž je vedoucí navázán.

        :param record: Záznam ``AkceVedouci`` po importu.
        :return: Archeologický záznam nadřazené akce.
        """
        return record.akce.archeologicky_zaznam

    @staticmethod
    def _get_updated_ident_cely_record_list(record: AkceVedouci) -> list:
        """
        Vrátí archeologický záznam dotčený změnou vedoucího akce.

        :param record: Záznam ``AkceVedouci`` po importu.
        :return: Seznam s archeologickým záznamem navázané akce.
        """
        return [record.akce.archeologicky_zaznam]


@ImportModelMapper.register("az_katastry")
class ArcheologickyZaznamKatastrMapper(ImportModelMapper):
    """Mapovač pro model ArcheologickyZaznamKatastr."""

    model_class = ArcheologickyZaznamKatastr
    primary_key = ("archeologicky_zaznam", "katastr")
    allow_update = False
    primary_key_filter_field = ("archeologicky_zaznam__ident_cely", "katastr__kod")
    primary_key_prefix = (None, "ruian")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: ArcheologickyZaznamKatastr) -> list:
        """
        Vrátí archeologický záznam propojený s importovanou vazbou na katastr.

        :param record: Záznam ``ArcheologickyZaznamKatastr`` po importu.
        :return: Seznam s navázaným archeologickým záznamem.
        """
        return [record.archeologicky_zaznam]

    @staticmethod
    def get_record_history(record: ArcheologickyZaznamKatastr):
        """
        Vrátí archeologický záznam jako cíl pro historii vazby na katastr.

        :param record: Záznam ``ArcheologickyZaznamKatastr`` po importu.
        :return: Navázaný archeologický záznam.
        """
        return record.archeologicky_zaznam


@ImportModelMapper.register("az_pian")
class PianMapper(ImportModelMapper, GeometryTransformMixin):
    """Mapovač pro model Pian."""

    fields = ("ident_cely", "stav", "geom_system", "geom", "geom_sjtsk")
    model_class = Pian
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PIAN_TYP})
        field_mapping["presnost"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PIAN_PRESNOST})
        field_mapping["zm10"] = LookupImportField(Kladyzm, "cislo")
        field_mapping["zm50"] = LookupImportField(Kladyzm, "cislo")
        return field_mapping

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """
               Provádí operaci map.

               :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``transform_geometries()``, vstupuje do návratové hodnoty.
               :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
               :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
               :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        return self.transform_geometries(mapping_dict, performed_action)

    @staticmethod
    def get_record_history(record: Pian):
        """
        Vrátí přímo importovaný PIAN jako cíl pro historii.

        :param record: Záznam ``Pian`` po importu.
        :return: Přímo předaný záznam ``Pian``.
        """
        return record


@ImportModelMapper.register("az_dokumentacni_jednotky")
class DokumentacniJednotkaMapper(ImportModelMapper):
    """Mapovač pro model DokumentacniJednotka."""

    fields = ("ident_cely", "negativni_jednotka", "nazev")
    model_class = DokumentacniJednotka
    require_primary_key_value = True
    komponenty_vazba = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["pian"] = LookupImportField(Pian)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DJ_TYP})
        return field_mapping

    @classmethod
    def record_postprocessing(cls, record, performed_action, fedora_transaction):
        """
        Provádí operaci record postprocessing.

        :param record: Parametr ``record`` předává se do volání ``vytvor_pian()``, pracuje se s atributy ``archeologicky_zaznam``, ``pian``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
        :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``record_postprocessing``.
        :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``vytvor_pian()``.

            :return: Vrací proměnná ``record``.
        """
        record: DokumentacniJednotka
        if pian := record.archeologicky_zaznam.hlavni_katastr.pian:
            record.pian = pian
        else:
            record.pian = vytvor_pian(record.archeologicky_zaznam.hlavni_katastr, fedora_transaction)
        return record

    @staticmethod
    def _get_updated_ident_cely_record_list(record: DokumentacniJednotka) -> list:
        """
        Vrátí archeologický záznam navázaný na dokumentační jednotku.

        :param record: Záznam ``DokumentacniJednotka`` po importu.
        :return: Seznam s nadřazeným archeologickým záznamem.
        """
        return [record.archeologicky_zaznam]

    @staticmethod
    def get_record_history(record: DokumentacniJednotka):
        """
        Vrátí archeologický záznam jako cíl pro historii dokumentační jednotky.

        :param record: Záznam ``DokumentacniJednotka`` po importu.
        :return: Archeologický záznam navázaný na dokumentační jednotku.
        """
        return record.archeologicky_zaznam


@ImportModelMapper.register("az_adb")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokumentacni_jednotka"] = LookupImportField(DokumentacniJednotka)
        field_mapping["typ_sondy"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_ADB_TYP})
        field_mapping["podnet"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_ADB_PODNET})
        field_mapping["autor_popisu"] = LookupImportField(Osoba)
        field_mapping["autor_revize"] = LookupImportField(Osoba)
        field_mapping["sm5"] = LookupImportField(Kladysm5, "mapno")
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: Adb) -> list:
        """
        Vrátí ADB záznam a jeho nadřazený archeologický záznam pro aktualizaci identifikátorů.

        :param record: Záznam ``Adb`` po importu.
        :return: Seznam obsahující ADB záznam a archeologický záznam dokumentační jednotky.
        """
        return [record, record.dokumentacni_jednotka.archeologicky_zaznam]

    @staticmethod
    def get_record_history(record: Adb):
        """
        Vrátí archeologický záznam nadřazený importovanému ADB záznamu.

        :param record: Záznam ``Adb`` po importu.
        :return: Archeologický záznam propojený přes dokumentační jednotku.
        """
        return record.dokumentacni_jednotka.archeologicky_zaznam


@ImportModelMapper.register("az_adb_vyskove_body")
class AdbVyskovyBod(ImportModelMapper):
    """Mapovač pro model VyskovyBod."""

    fields = ("ident_cely", "geom")
    model_class = VyskovyBod
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["adb"] = LookupImportField(Adb)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_VYSKOVY_BOD_TYP})
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: VyskovyBod) -> list:
        """
        Vrátí výškový bod nepřímo přes ADB záznam a jeho archeologický kontext.

        :param record: Záznam ``VyskovyBod`` po importu.
        :return: Seznam s ADB záznamem a nadřazeným archeologickým záznamem.
        """
        return [record.adb, record.adb.dokumentacni_jednotka.archeologicky_zaznam]

    @staticmethod
    def get_record_history(record: VyskovyBod):
        """
        Vrátí archeologický záznam navázaný na importovaný výškový bod.

        :param record: Záznam ``VyskovyBod`` po importu.
        :return: Archeologický záznam dostupný přes navázaný ADB záznam.
        """
        return record.adb.dokumentacni_jednotka.archeologicky_zaznam


@ImportModelMapper.register("dokumenty_lety")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["letiste_start"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LETISTE})
        field_mapping["letiste_cil"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LETISTE})
        field_mapping["pozorovatel"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        field_mapping["pocasi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_POCASI})
        field_mapping["dohlednost"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOHLEDNOST})
        return field_mapping


@ImportModelMapper.register("dokumenty")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = {}
        for __, item in cls.fields:
            field_mapping[item] = cls.map_field(item)
        field_mapping = field_mapping | cls.lookup_fields_mapping
        return field_mapping

    def create_records(self, performed_action) -> list:
        """
        Vytvoří instanci Dokument a DokumentExtraData s vazbou na Dokument.

        :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ovlivňuje větvení podmínek.
        :return: Nově vytvořená hodnota připravená touto funkcí.
        """

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
            for field_name, field_value in mapping_dict_dokument.items():
                setattr(dokument, field_name, field_value)
            if dokument_extra_data_query.exists():
                dokument_extra_data = dokument_extra_data_query.first()
            elif any(value is not None for value in mapping_dict_dokument_extra_data.values()):
                # Nový DokumentExtraData zakládáme jen pokud import skutečně nese nějaká data,
                # která do něj patří. Bez této kontroly by se ukládal záznam se samými NULL
                # hodnotami a narazil na NOT NULL constraint (např. geom_system).
                dokument_extra_data = DokumentExtraData(dokument=dokument)
            else:
                return [dokument]
            for field_name, field_value in mapping_dict_dokument_extra_data.items():
                setattr(dokument_extra_data, field_name, field_value)
            return [dokument_extra_data, dokument]
        return []

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """
               Provádí operaci map.

               :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``, ``transform_geometries()``, vstupuje do návratové hodnoty.
               :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
               :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
               :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        return self.transform_geometries(mapping_dict, performed_action)

    @staticmethod
    def get_record_history(record: Dokument | DokumentExtraData):
        """
        Vrátí dokument, do jehož historie se má změna propsat.

        :param record: Záznam ``Dokument`` nebo ``DokumentExtraData`` po importu.
        :return: Přímo dokument nebo dokument navázaný přes extra data.
        """
        if isinstance(record, Dokument):
            return record
        else:
            return record.dokument


@ImportModelMapper.register("dokumenty_autori")
class DokumentAutorMapper(ImportModelMapper):
    """Mapovač pro model DokumentAutor."""

    fields = ("poradi",)
    model_class = DokumentAutor
    primary_key = ("dokument", "autor")
    allow_update = False
    primary_key_filter_field = ("dokument__ident_cely", "autor__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["autor"] = LookupImportField(Osoba)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: DokumentAutor) -> list:
        """
        Vrátí dokument dotčený změnou pořadí nebo vazby autora.

        :param record: Záznam ``DokumentAutor`` po importu.
        :return: Seznam s navázaným dokumentem.
        """
        return [record.dokument]

    @staticmethod
    def get_record_history(record: DokumentAutor):
        """
        Vrátí dokument jako cíl pro historii vazby autora.

        :param record: Záznam ``DokumentAutor`` po importu.
        :return: Navázaný dokument.
        """
        return record.dokument


@ImportModelMapper.register("dokumenty_jazyky")
class DokumentJazykMapper(ImportModelMapper):
    """Mapovač pro model DokumentJazyk."""

    model_class = DokumentJazyk
    primary_key = ("dokument", "jazyk")
    allow_update = False
    primary_key_filter_field = ("dokument__ident_cely", "jazyk__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["jazyk"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_JAZYK})
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: DokumentJazyk) -> list:
        """
        Vrátí dokument dotčený změnou jazykové vazby.

        :param record: Záznam ``DokumentJazyk`` po importu.
        :return: Seznam s navázaným dokumentem.
        """
        return [record.dokument]

    @staticmethod
    def get_record_history(record: DokumentJazyk):
        """
        Vrátí dokument jako cíl pro historii jazykové vazby.

        :param record: Záznam ``DokumentJazyk`` po importu.
        :return: Navázaný dokument.
        """
        return record.dokument


@ImportModelMapper.register("dokumenty_osoby")
class DokumentOsobaMapper(ImportModelMapper):
    """Mapovač pro model DokumentOsoba."""

    model_class = DokumentOsoba
    primary_key = ("dokument", "osoba")
    allow_update = False
    primary_key_filter_field = ("dokument__ident_cely", "osoba__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["osoba"] = LookupImportField(Osoba)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: DokumentOsoba) -> list:
        """
        Vrátí dokument dotčený změnou osobní vazby.

        :param record: Záznam ``DokumentOsoba`` po importu.
        :return: Seznam s navázaným dokumentem.
        """
        return [record.dokument]

    @staticmethod
    def get_record_history(record: DokumentOsoba):
        """
        Vrátí dokument jako cíl pro historii osobní vazby.

        :param record: Záznam ``DokumentOsoba`` po importu.
        :return: Navázaný dokument.
        """
        return record.dokument


@ImportModelMapper.register("dokumenty_posudky")
class DokumentPosudekMapper(ImportModelMapper):
    """Mapovač pro model DokumentPosudek."""

    model_class = DokumentPosudek
    primary_key = ("dokument", "posudek")
    allow_update = False
    primary_key_filter_field = ("dokument__ident_cely", "posudek__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["posudek"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_POSUDEK_TYP})
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: DokumentPosudek) -> list:
        """
        Vrátí dokument dotčený změnou vazby na posudek.

        :param record: Záznam ``DokumentPosudek`` po importu.
        :return: Seznam s navázaným dokumentem.
        """
        return [record.dokument]

    @staticmethod
    def get_record_history(record: DokumentPosudek):
        """
        Vrátí dokument jako cíl pro historii vazby na posudek.

        :param record: Záznam ``DokumentPosudek`` po importu.
        :return: Navázaný dokument.
        """
        return record.dokument


@ImportModelMapper.register("dokumenty_tvary")
class TvarMapper(ImportModelMapper):
    """Mapovač pro model Tvar."""

    fields = ("poznamka",)
    model_class = Tvar
    primary_key = "id"
    primary_key_prefix = "tvar"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["tvar"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_LETFOTO_TVAR})
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: Tvar) -> list:
        """
        Vrátí dokument dotčený změnou tvaru leteckého snímku.

        :param record: Záznam ``Tvar`` po importu.
        :return: Seznam s dokumentem, ke kterému tvar patří.
        """
        return [record.dokument]

    @staticmethod
    def get_record_history(record: Tvar):
        """
        Vrátí dokument jako cíl pro historii tvaru.

        :param record: Záznam ``Tvar`` po importu.
        :return: Navázaný dokument.
        """
        return record.dokument


@ImportModelMapper.register("dokumenty_casti")
class DokumentCastMapper(ImportModelMapper):
    """Mapovač pro model DokumentCast."""

    fields = ("ident_cely", "poznamka")
    model_class = DokumentCast
    require_primary_key_value = True
    komponenty_vazba = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument"] = LookupImportField(Dokument)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["projekt"] = LookupImportField(Projekt)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: DokumentCast) -> list:
        """
        Vrátí všechny hlavní entity navázané na importovanou část dokumentu.

        :param record: Záznam ``DokumentCast`` po importu.
        :return: Seznam dokumentu, archeologického záznamu a projektu, pokud jsou navázány.
        """
        return [record.dokument, record.archeologicky_zaznam, record.projekt]

    @staticmethod
    def get_record_history(record: DokumentCast):
        """
        Vrátí dokument jako cíl pro historii části dokumentu.

        :param record: Záznam ``DokumentCast`` po importu.
        :return: Nadřazený dokument.
        """
        return record.dokument


@ImportModelMapper.register("dokumenty_neident_akce")
class NeidentAkceMapper(ImportModelMapper):
    """Mapovač pro model NeidentAkce."""

    fields = ("rok_zahajeni", "rok_ukonceni", "lokalizace", "popis", "poznamka", "pian")
    model_class = NeidentAkce
    primary_key = "dokument_cast"
    primary_key_filter_field = "dokument_cast__ident_cely"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["dokument_cast"] = LookupImportField(DokumentCast)
        field_mapping["katastr"] = RuianLookupImportField(RuianKatastr, "kod")
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: NeidentAkce) -> list:
        """
        Vrátí dokument navázaný na neidentifikovanou akci přes část dokumentu.

        :param record: Záznam ``NeidentAkce`` po importu.
        :return: Seznam s nadřazeným dokumentem.
        """
        return [record.dokument_cast.dokument]

    @staticmethod
    def get_record_history(record: NeidentAkce):
        """
        Vrátí dokument jako cíl pro historii neidentifikované akce.

        :param record: Záznam ``NeidentAkce`` po importu.
        :return: Dokument navázaný přes část dokumentu.
        """
        return record.dokument_cast.dokument


@ImportModelMapper.register("dokumenty_neident_akce_vedouci")
class NeidentAkceVedouciMapper(ImportModelMapper):
    """Mapovač pro model NeidentAkceVedouci."""

    model_class = NeidentAkceVedouci
    primary_key = ("neident_akce", "vedouci")
    allow_update = False
    primary_key_filter_field = ("neident_akce__dokument_cast__ident_cely", "vedouci__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["neident_akce"] = LookupImportField(NeidentAkce, "dokument_cast__ident_cely")
        field_mapping["vedouci"] = LookupImportField(Osoba)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: NeidentAkceVedouci) -> list:
        """
        Vrátí dokument dotčený změnou vedoucího neidentifikované akce.

        :param record: Záznam ``NeidentAkceVedouci`` po importu.
        :return: Seznam s dokumentem navázaným přes neidentifikovanou akci.
        """
        return [record.neident_akce.dokument_cast.dokument]

    @staticmethod
    def get_record_history(record: NeidentAkceVedouci):
        """
        Vrátí dokument jako cíl pro historii vedoucího neidentifikované akce.

        :param record: Záznam ``NeidentAkceVedouci`` po importu.
        :return: Dokument navázaný přes neidentifikovanou akci.
        """
        return record.neident_akce.dokument_cast.dokument


@ImportModelMapper.register("komponenty")
class KomponentaMapper(ImportModelMapper):
    """Mapovač pro model Komponenta."""

    fields = ("ident_cely", "jistota", "presna_datace", "poznamka")
    column_to_field_mapping = {"vazba": "komponenta_vazby"}
    model_class = Komponenta
    require_primary_key_value = True

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vazba"] = VazbaLookupImportField(
            (DokumentacniJednotka, DokumentCast), read_field_name="komponenty"
        )
        field_mapping["obdobi"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBDOBI})
        field_mapping["areal"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_AREAL})
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: Komponenta) -> list:
        """
        Vrátí záznamy dotčené změnou komponenty podle typu navázaného objektu.

        :param record: Záznam ``Komponenta`` po importu.
        :return: Seznam archeologických záznamů nebo dokumentů odvozených z vazby komponenty.
        """
        record_list = []
        navazany_objekt = record.komponenta_vazby.navazany_objekt
        if isinstance(navazany_objekt, DokumentCast):
            if navazany_objekt.archeologicky_zaznam:
                record_list.append(navazany_objekt.archeologicky_zaznam)
            elif navazany_objekt.dokument:
                record_list.append(navazany_objekt.dokument)
        elif isinstance(navazany_objekt, DokumentacniJednotka):
            record_list.append(navazany_objekt.archeologicky_zaznam)
        return record_list

    @staticmethod
    def get_record_history(record: Komponenta):
        """
        Vrátí objekt, do jehož historie se má změna komponenty propsat.

        :param record: Záznam ``Komponenta`` po importu.
        :return: Archeologický záznam nebo dokument odvozený z vazby komponenty.
        """
        navazany_objekt = record.komponenta_vazby.navazany_objekt
        if isinstance(navazany_objekt, DokumentCast):
            if navazany_objekt.archeologicky_zaznam:
                return navazany_objekt.archeologicky_zaznam
            elif navazany_objekt.dokument:
                return navazany_objekt.dokument
        elif isinstance(navazany_objekt, DokumentacniJednotka):
            return navazany_objekt.archeologicky_zaznam


@ImportModelMapper.register("komponenty_aktivity")
class KomponentaAktivitaMapper(ImportModelMapper):
    """Mapovač pro model KomponentaAktivita."""

    model_class = KomponentaAktivita
    primary_key = ("komponenta", "aktivita")
    allow_update = False
    primary_key_filter_field = ("komponenta__ident_cely", "aktivita__ident_cely")

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["aktivita"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_AKTIVITA})
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: KomponentaAktivita) -> list:
        """
        Vrátí stejné cílové záznamy jako navázaná komponenta.

        :param record: Záznam ``KomponentaAktivita`` po importu.
        :return: Seznam záznamů odvozený z mapperu komponenty.
        """
        komponenta = record.komponenta
        return KomponentaMapper._get_updated_ident_cely_record_list(komponenta)

    @staticmethod
    def get_record_history(record: KomponentaAktivita):
        """
        Vrátí objekt historie stejný jako u navázané komponenty.

        :param record: Záznam ``KomponentaAktivita`` po importu.
        :return: Cílový objekt historie odvozený z komponenty.
        """
        komponenta = record.komponenta
        return KomponentaMapper.get_record_history(komponenta)


class NalezMapper(ImportModelMapper):
    """Základní mapper pro nálezy."""

    fields = ("pocet", "poznamka")
    primary_key = "id"

    @staticmethod
    def _get_updated_ident_cely_record_list(record: NalezObjekt | NalezPredmet) -> list:
        """
        Vrátí cílové záznamy odvozené z komponenty, ke které nález patří.

        :param record: Záznam ``NalezObjekt`` nebo ``NalezPredmet`` po importu.
        :return: Seznam záznamů získaný z mapperu komponenty.
        """
        komponenta = record.komponenta
        return KomponentaMapper._get_updated_ident_cely_record_list(komponenta)

    @staticmethod
    def get_record_history(record: NalezObjekt | NalezPredmet):
        """
        Vrátí objekt historie odvozený z komponenty navázané na nález.

        :param record: Záznam ``NalezObjekt`` nebo ``NalezPredmet`` po importu.
        :return: Cílový objekt historie získaný z mapperu komponenty.
        """
        komponenta = record.komponenta
        return KomponentaMapper.get_record_history(komponenta)


@ImportModelMapper.register("komponenty_nalezy_objekty")
class NalezObjektMapper(NalezMapper):
    """Mapovač pro model NalezObjekt."""

    model_class = NalezObjekt
    primary_key_prefix = "nalo"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["druh"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_DRUH})
        field_mapping["specifikace"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_SPECIFIKACE}
        )
        return field_mapping


@ImportModelMapper.register("komponenty_nalezy_predmety")
class NalezPredmetMapper(NalezMapper):
    """Mapovač pro model NalezPredmet."""

    model_class = NalezPredmet
    primary_key_prefix = "nalp"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["komponenta"] = LookupImportField(Komponenta)
        field_mapping["druh"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_PREDMET_DRUH})
        field_mapping["specifikace"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_PREDMET_SPECIFIKACE}
        )
        return field_mapping


@ImportModelMapper.register("externi_zdroje")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["typ"] = LookupImportField(Heslar, limit_choices_to={"nazev_heslare": HESLAR_EXTERNI_ZDROJ_TYP})
        field_mapping["typ_dokumentu"] = LookupImportField(
            Heslar, limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP}
        )
        return field_mapping

    @staticmethod
    def get_record_history(record: ExterniZdroj):
        """
        Vrátí přímo importovaný externí zdroj jako cíl pro historii.

        :param record: Záznam ``ExterniZdroj`` po importu.
        :return: Přímo předaný externí zdroj.
        """
        return record


@ImportModelMapper.register("externi_zdroje_autori")
class ExterniZdrojAutorMapper(ImportModelMapper):
    """Mapovač pro model ExterniZdrojAutor."""

    fields = ("poradi",)
    primary_key = ("externi_zdroj", "autor")
    allow_update = False
    primary_key_filter_field = ("externi_zdroj__ident_cely", "autor__ident_cely")
    model_class = ExterniZdrojAutor

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        field_mapping["autor"] = LookupImportField(Osoba)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: ExterniZdrojAutor) -> list:
        """
        Vrátí externí zdroj dotčený změnou pořadí nebo vazby autora.

        :param record: Záznam ``ExterniZdrojAutor`` po importu.
        :return: Seznam s navázaným externím zdrojem.
        """
        return [record.externi_zdroj]

    @staticmethod
    def get_record_history(record: ExterniZdrojAutor):
        """
        Vrátí externí zdroj jako cíl pro historii vazby autora.

        :param record: Záznam ``ExterniZdrojAutor`` po importu.
        :return: Navázaný externí zdroj.
        """
        return record.externi_zdroj


@ImportModelMapper.register("externi_zdroje_editori")
class ExterniZdrojEditorMapper(ImportModelMapper):
    """Mapovač pro model ExterniZdrojEditor."""

    fields = ("poradi",)
    primary_key = ("externi_zdroj", "editor")
    allow_update = False
    primary_key_filter_field = ("externi_zdroj__ident_cely", "editor__ident_cely")
    model_class = ExterniZdrojEditor

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        field_mapping["editor"] = LookupImportField(Osoba)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: ExterniZdrojEditor) -> list:
        """
        Vrátí externí zdroj dotčený změnou pořadí nebo vazby editora.

        :param record: Záznam ``ExterniZdrojEditor`` po importu.
        :return: Seznam s navázaným externím zdrojem.
        """
        return [record.externi_zdroj]

    @staticmethod
    def get_record_history(record: ExterniZdrojEditor):
        """
        Vrátí externí zdroj jako cíl pro historii vazby editora.

        :param record: Záznam ``ExterniZdrojEditor`` po importu.
        :return: Navázaný externí zdroj.
        """
        return record.externi_zdroj


@ImportModelMapper.register("externi_odkazy")
class ExterniOdkazMapper(ImportModelMapper):
    """Mapovač pro model ExterniOdkaz."""

    fields = ("paginace",)
    model_class = ExterniOdkaz
    primary_key = "id"
    primary_key_prefix = "exto"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["archeologicky_zaznam"] = LookupImportField(ArcheologickyZaznam)
        field_mapping["externi_zdroj"] = LookupImportField(ExterniZdroj)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: ExterniOdkaz) -> list:
        """
        Vrátí externí zdroj a archeologický záznam propojené importovaným odkazem.

        :param record: Záznam ``ExterniOdkaz`` po importu.
        :return: Seznam navázaného externího zdroje a archeologického záznamu.
        """
        return [record.externi_zdroj, record.archeologicky_zaznam]

    @staticmethod
    def get_record_history(record: ExterniOdkaz):
        """
        Vrátí externí zdroj jako cíl pro historii externího odkazu.

        :param record: Záznam ``ExterniOdkaz`` po importu.
        :return: Navázaný externí zdroj.
        """
        return record.externi_zdroj


@ImportModelMapper.register("uzivatele")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["osoba"] = LookupImportField(Osoba)
        field_mapping["organizace"] = LookupImportField(Organizace)
        return field_mapping

    @staticmethod
    def get_record_history(record: User):
        """
        Vrátí uživatele jako cíl pro historii změn.

        :param record: Záznam ``User`` po importu.
        :return: Přímo předaný uživatel.
        """
        return record

    def import_validation(self, performed_action, user_id) -> dict | None:
        """
        Zabrání smazání aktivního uživatele a jinak deleguje běžnou validaci mapperu.

        :param performed_action: Typ prováděné operace importu.
        :param user_id: Primární klíč aktuálně přihlášeného uživatele.
        :return: Filtrační podmínky primárního klíče nebo ``None`` podle standardní validace mapperu.
        :raises ImportDataActiveUserCannotBeDeleted: Vyvolá se při pokusu smazat právě aktivního uživatele.
        """
        if (
            performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE
            and User.objects.get(pk=user_id).ident_cely == self.value_dict["ident_cely"]
        ):
            raise ImportDataActiveUserCannotBeDeleted(self.value_dict["ident_cely"])
        return super().import_validation(performed_action)


@ImportModelMapper.register("uzivatele_notifikace_projekty")
class UzivatelNotifikaceProjektMapper(ImportModelMapper):
    """Mapovač pro model Pes (notifikace uživatele vázané na projekt či územní jednotku RUIAN)."""

    model_class = Pes
    primary_key = ("uzivatel", "ruian")
    allow_update = False
    primary_key_prefix = (None, "ruian")
    column_to_field_mapping = {"uzivatel": "user"}

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(False)
        field_mapping["uzivatel"] = LookupImportField(User, "ident_cely")
        field_mapping["ruian"] = GenericForeignKeyImportField([RuianKatastr, RuianOkres, RuianKraj], "kod", "kod")
        return field_mapping

    @functools.cached_property
    def _ruian_content_object(self) -> RuianKatastr | RuianOkres | RuianKraj:
        """
        Vrátí objekt RUIAN odpovídající hodnotě v importovaném záznamu.

        Výsledek je cachován per-instance — DB dotaz proběhne nejvýše jednou za řádek CSV,
        i když je ``_ruian_content_object`` voláno z více metod (``_get_filter_kwargs_primary_key``,
        ``map``, ``create_records``).

        :return: Instance modelu ``RuianKatastr``, ``RuianOkres`` nebo ``RuianKraj``.
        :raises ImportDataMissingReferencedValueError: Vyvolá se, pokud hodnota není nalezena v žádném z modelů.
        """
        field = GenericForeignKeyImportField([RuianKatastr, RuianOkres, RuianKraj], "kod", "kod")
        field.value = self.value_dict.get("ruian", self.value_dict.get("object_id"))
        return field._instance_value

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        """
        Vrací filter kwargs primary key.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        content_object = self._ruian_content_object
        return {
            "user__ident_cely": self.value_dict["uzivatel"],
            "content_type": ContentType.objects.get_for_model(content_object),
            "object_id": content_object.pk,
        }

    @classmethod
    def map_field(cls, field_name):
        """
        Provádí operaci map field.

        :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.

            :return: Vrací výsledek volání ``map_field()``.
        """
        if field_name == "uzivatel":
            field_name = "user"
        return super().map_field(field_name)

    def create_records(self, performed_action) -> list:
        """
        Vytvoří záznamy v aplikaci.

        :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``.
        :return: Nově vytvořená hodnota připravená touto funkcí.
        """
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            return [self.model_class.objects.get(**self._get_filter_kwargs_primary_key())]
        mapping_dict = self.map(performed_action, True)
        mapping_dict = {self.map_column_name_to_field_name(field): value for field, value in mapping_dict.items()}
        app_label, model = mapping_dict["content_type"].split(".")
        content_object = self._ruian_content_object
        return [
            Pes(
                user=mapping_dict["user"],
                content_type=ContentType.objects.get(app_label=app_label, model=model),
                content_object=content_object,
            )
        ]

    def _check_column_structure(self, performed_action, include_primary_key=False):
        """
        Ověří column structure.

        :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``_check_column_structure``.
        :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``_check_column_structure``.
        :return: Vrací výsledek ověření nebo validačního pravidla.

            :raises ImportDataIncorrectStructureContentObjectError: Vyvolá se při splnění podmínky ``mapping_column_set != expected_column_set_import and mapping_column_set != expected_column_set_job``.
        """
        mapping_column_set = set(self.value_dict.keys())
        expected_column_set_import = {"uzivatel", "ruian"}
        expected_column_set_job = {"uzivatel", "content_type", "object_id"}
        if mapping_column_set != expected_column_set_import and mapping_column_set != expected_column_set_job:
            raise ImportDataIncorrectStructureContentObjectError(
                mapping_column_set, expected_column_set_import, expected_column_set_job
            )

    def map(self, performed_action, instance_values=False, serialize=False, include_primary_key=False) -> dict:
        """
               Provádí operaci map.

               :param performed_action: Parametr ``performed_action`` předává se do volání ``map()``.
               :param instance_values: Parametr ``instance_values`` předává se do volání ``map()``.
               :param serialize: Parametr ``serialize`` předává se do volání ``map()``.
               :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``map()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        mapping_dict = super().map(performed_action, instance_values, serialize, include_primary_key)
        content_object = self._ruian_content_object
        content_type: ContentType = ContentType.objects.get_for_model(content_object)
        return {
            "uzivatel": mapping_dict["uzivatel"],
            "content_type": f"{content_type.app_label}.{content_type.model}",
            "object_id": content_object.kod,
        }

    @staticmethod
    def _get_updated_ident_cely_record_list(record: Pes) -> list:
        """
        Vrátí uživatele dotčeného změnou projektové notifikace.

        :param record: Záznam ``Pes`` po importu.
        :return: Seznam s uživatelem navázaným na notifikaci.
        """
        return [record.user]

    @staticmethod
    def get_record_history(record: Pes):
        """
        Vrátí uživatele jako cíl pro historii projektové notifikace.

        :param record: Záznam ``Pes`` po importu.
        :return: Uživatel navázaný na notifikaci.
        """
        return record.user


@ImportModelMapper.register("uzivatele_spoluprace")
class UzivatelSpolupraceMapper(ImportModelMapper):
    """Mapovač pro model UzivatelSpoluprace."""

    fields = ("stav",)
    model_class = UzivatelSpoluprace
    primary_key = "id"
    primary_key_prefix = "spol"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vedouci"] = LookupImportField(User)
        field_mapping["spolupracovnik"] = LookupImportField(User)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: UzivatelSpoluprace) -> list:
        """
        Vrátí oba uživatele zapojené do spolupráce.

        :param record: Záznam ``UzivatelSpoluprace`` po importu.
        :return: Seznam vedoucího a spolupracovníka.
        """
        return [record.vedouci, record.spolupracovnik]

    @staticmethod
    def get_record_history(record: UzivatelSpoluprace):
        """
        Vrátí vedoucího uživatele jako cíl pro historii spolupráce.

        :param record: Záznam ``UzivatelSpoluprace`` po importu.
        :return: Vedoucí uživatel navázaný na spolupráci.
        """
        return record.vedouci


@ImportModelMapper.register("uzivatele_opravneni")
class UzivatelOpravneniMapper(ImportModelMapper):
    """Mapovač pro přiřazení skupinových oprávnění uživateli (model User)."""

    model_class = User
    primary_key = ("uzivatel", "skupina")
    allow_update = False
    supported_actions = (
        ImportDataAdminForm.PERFORMED_ACTION_INSERT,
        ImportDataAdminForm.PERFORMED_ACTION_DELETE,
    )
    column_to_field_mapping = {"uzivatel": "ident_cely"}

    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = {"uzivatel": LookupImportField(User), "skupina": LookupImportField(Group, "name")}
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        """
        Vrací filter kwargs primary key.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        return {"ident_cely": self.value_dict["uzivatel"]}

    def create_records(self, performed_action):
        """
        Vytvoří records. v aplikaci.

        :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``create_records``.

            :return: Vrací seznam.
        """
        if performed_action not in self.supported_actions:
            raise ImportDataError(
                f"{_('core_admin.ImportDataError.message.invalid_performed_action')}: {performed_action}"
            )
        return [User.objects.get(ident_cely=self.value_dict["uzivatel"])]

    def import_validation(self, performed_action, *args, **kwargs):
        """
        Ověří, že import oprávnění provede skutečnou změnu.

        :param performed_action: Požadovaná importní akce.
        :param args: Nepoužité poziční argumenty zachované kvůli sjednocenému rozhraní mapperů.
        :param kwargs: Nepoužité pojmenované argumenty zachované kvůli sjednocenému rozhraní mapperů.
        :return: Slovník s podmínkou pro dohledání cílového uživatele.
        """
        if performed_action not in self.supported_actions:
            raise ImportDataError(
                f"{_('core_admin.ImportDataError.message.invalid_performed_action')}: {performed_action}"
            )
        user = User.objects.get(ident_cely=self.value_dict["uzivatel"])
        group = Group.objects.get(name=self.value_dict["skupina"])
        relation_exists = user.groups.filter(pk=group.pk).exists()
        record_id = {"uzivatel": self.value_dict["uzivatel"], "skupina": self.value_dict["skupina"]}
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT and relation_exists:
            raise ImportDataIntegrityError(record_id, "User.groups", performed_action)
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE and not relation_exists:
            raise ImportDataIntegrityError(record_id, "User.groups", performed_action)
        return self._get_filter_kwargs_primary_key()

    @staticmethod
    def get_record_history(record: User):
        """
        Vrátí uživatele jako cíl pro historii změn oprávnění.

        :param record: Záznam ``User`` po importu.
        :return: Přímo předaný uživatel.
        """
        return record

    @staticmethod
    def _get_updated_ident_cely_record_list(record: User) -> list:
        """
        Vrátí uživatele dotčeného změnou skupinového oprávnění.

        :param record: Záznam ``User`` po importu.
        :return: Jednoprvkový seznam s uživatelem.
        """
        return [record]


@ImportModelMapper.register("soubory")
class SouborMapper(ImportModelMapper):
    """Mapovač pro model Soubor."""

    fields = ("nazev",)
    model_class = Soubor
    primary_key = "id"
    primary_key_prefix = "soub"

    @classmethod
    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["nazev"] = FileNameImportField()
        field_mapping["vazba"] = VazbaLookupImportField(read_field_name="soubory")
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: Soubor) -> list:
        """
        Vrátí objekt navázaný na importovaný soubor.

        :param record: Záznam ``Soubor`` po importu.
        :return: Seznam s objektem dostupným přes vazbu souboru.
        """
        return [record.vazba.navazany_objekt]

    @staticmethod
    def get_record_history(record: Soubor):
        """
        Vrátí přímo soubor jako cíl pro historii změn.

        :param record: Záznam ``Soubor`` po importu.
        :return: Přímo předaný soubor.
        """
        return record

    @staticmethod
    def get_related_history_targets(record: Soubor) -> list:
        """
        Vrátí záznamy, kterým má import binárního souboru zapsat historii.

        Soubory dokumentů jsou v historii hlavních záznamů vedené přes navázané
        archeologické záznamy, zatímco soubory projektu a samostatného nálezu se
        zapisují přímo na navázaný objekt.

        :param record: Importovaný záznam ``Soubor``.
        :return: Seznam záznamů s historií dotčenou importem souboru.
        """
        related_record = record.vazba.navazany_objekt if record.vazba_id else None
        if isinstance(related_record, Dokument):
            targets = []
            seen = set()
            for cast in related_record.casti.select_related("archeologicky_zaznam").all():
                archeologicky_zaznam = cast.archeologicky_zaznam
                if archeologicky_zaznam and archeologicky_zaznam.pk not in seen:
                    targets.append(archeologicky_zaznam)
                    seen.add(archeologicky_zaznam.pk)
            return targets
        if isinstance(related_record, ModelWithMetadata):
            return [related_record]
        return []


@ImportModelMapper.register("uzivatele_notifikace")
class UzivatelNotifikaceMapper(ImportModelMapper):
    """Mapovač pro přiřazení typů notifikací uživateli (model User)."""

    model_class = User
    primary_key = ("uzivatel", "notifikace")
    allow_update = False
    supported_actions = (
        ImportDataAdminForm.PERFORMED_ACTION_INSERT,
        ImportDataAdminForm.PERFORMED_ACTION_DELETE,
    )
    column_to_field_mapping = {"uzivatel": "ident_cely"}

    def get_mapping(cls, include_primary_key=False):
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` slouží jako vstup pro logiku funkce ``get_mapping``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = {"uzivatel": LookupImportField(User), "notifikace": LookupImportField(UserNotificationType)}
        return field_mapping

    def _get_filter_kwargs_primary_key(self) -> dict | None:
        """
        Vrací filter kwargs primary key.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        return {"ident_cely": self.value_dict["uzivatel"]}

    def create_records(self, performed_action):
        """
        Vytvoří records. v aplikaci.

        :param performed_action: Parametr ``performed_action`` slouží jako vstup pro logiku funkce ``create_records``.

            :return: Vrací seznam.
        """
        if performed_action not in self.supported_actions:
            raise ImportDataError(
                f"{_('core_admin.ImportDataError.message.invalid_performed_action')}: {performed_action}"
            )
        return [User.objects.get(ident_cely=self.value_dict["uzivatel"])]

    def import_validation(self, performed_action, *args, **kwargs):
        """
        Ověří, že import notifikace provede skutečnou změnu.

        :param performed_action: Požadovaná importní akce.
        :param args: Nepoužité poziční argumenty zachované kvůli sjednocenému rozhraní mapperů.
        :param kwargs: Nepoužité pojmenované argumenty zachované kvůli sjednocenému rozhraní mapperů.
        :return: Slovník s podmínkou pro dohledání cílového uživatele.
        """
        if performed_action not in self.supported_actions:
            raise ImportDataError(
                f"{_('core_admin.ImportDataError.message.invalid_performed_action')}: {performed_action}"
            )
        user = User.objects.get(ident_cely=self.value_dict["uzivatel"])
        notification_type = UserNotificationType.objects.get(ident_cely=self.value_dict["notifikace"])
        relation_exists = user.notification_types.filter(pk=notification_type.pk).exists()
        record_id = {"uzivatel": self.value_dict["uzivatel"], "notifikace": self.value_dict["notifikace"]}
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT and relation_exists:
            raise ImportDataIntegrityError(record_id, "User.notification_types", performed_action)
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE and not relation_exists:
            raise ImportDataIntegrityError(record_id, "User.notification_types", performed_action)
        return self._get_filter_kwargs_primary_key()

    @staticmethod
    def get_record_history(record: User):
        """
        Vrátí uživatele jako cíl pro historii notifikačních preferencí.

        :param record: Záznam ``User`` po importu.
        :return: Přímo předaný uživatel.
        """
        return record

    @staticmethod
    def _get_updated_ident_cely_record_list(record: User) -> list:
        """
        Vrátí uživatele dotčeného změnou typu notifikace.

        :param record: Záznam ``User`` po importu.
        :return: Jednoprvkový seznam s uživatelem.
        """
        return [record]


@ImportModelMapper.register("historie")
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
        """
        Vrací mapping. v aplikaci.

        :param include_primary_key: Parametr ``include_primary_key`` předává se do volání ``get_mapping()``.

            :return: Vrací proměnná ``field_mapping``.
        """
        field_mapping = super().get_mapping(include_primary_key)
        field_mapping["vazba"] = VazbaLookupImportField(read_field_name="historie")
        field_mapping["uzivatel"] = LookupImportField(User)
        return field_mapping

    @staticmethod
    def _get_updated_ident_cely_record_list(record: Historie) -> list:
        """
        Vrátí objekty dotčené importovaným historickým záznamem podle typu vazby.

        :param record: Záznam ``Historie`` po importu.
        :return: Seznam objektů navázaných přes ``vazba``, jejichž identifikátory je třeba aktualizovat.
        """
        navazany_objekt = record.vazba.navazany_objekt
        if isinstance(navazany_objekt, ModelWithMetadata) or isinstance(navazany_objekt, User):
            return [navazany_objekt]
        elif isinstance(navazany_objekt, UzivatelSpoluprace):
            return [navazany_objekt.spolupracovnik, navazany_objekt.vedouci]
        elif isinstance(navazany_objekt, Soubor):
            return [navazany_objekt]
