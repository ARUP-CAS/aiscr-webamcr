import datetime
import io
import logging
import os
import re
import time
import zipfile
from enum import Enum
from typing import Optional, Union

import magic
import piexif
import py7zr
import rarfile
from core.constants import ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_BADATEL_ID
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.forms import ValidationError
from django.http import FileResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla_dynamicka import (
    PRISTUPNOST_ANONYM_ID,
    PRISTUPNOST_ARCHEOLOG_ID,
    PRISTUPNOST_ARCHIVAR_ID,
    PRISTUPNOST_BADATEL_ID,
)
from historie.models import Historie, HistorieVazby
from nalez.models import NalezObjekt, NalezPredmet
from notifikace_projekty.models import Pes
from PIL import Image
from uzivatel.models import User
from xml_generator.models import ModelWithMetadata

from .connectors import ClamdConnectionError, ClamdNetworkSocket, ClamdResponseError
from .constants import (
    DOKUMENT_RELATION_TYPE,
    NAHRANI_SBR,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SOUBOR_RELATION_TYPE,
)
from .repository_connector import RepositoryBinaryFile

logger = logging.getLogger(__name__)


class AntivirusCheckResult(Enum):
    # Antivirus vrátil odpověď, že soubor je v pořádku
    """Implementuje komponentu ``AntivirusCheckResult`` v rámci aplikace."""
    PASSES = 0
    # Antivirus nalezl v souboru virus
    VIRUS_FOUND = 1
    # Kontrola antivirem selhala kvůli chybě
    CHECK_FAILED = 2
    # Kontrola antivirem byla přeskočena, protože není nakonfigurován žádný antivirus
    SKIPPED = 3


def get_upload_to(instance, filename):
    """
    Určí cestu pro uložení souboru.

    :param instance: Instance souboru.
    :param filename: Název souboru.
    :return: Cesta pro uložení souboru.
    """
    instance: Soubor
    vazba: SouborVazby = instance.vazba
    if vazba.typ_vazby == PROJEKT_RELATION_TYPE:
        regex_oznameni = re.compile(r"\w*oznameni_?(?:X-)?[A-Z][-_]\w*\.pdf")
        regex_log_dokumentace = re.compile(r"\w*log_dokumentace[\w\-]*\.\w{2,4}")
        if regex_oznameni.fullmatch(instance.nazev) or regex_log_dokumentace.fullmatch(instance.nazev):
            folder = "AG/"
        else:
            folder = "PD/"
    elif vazba.typ_vazby == SAMOSTATNY_NALEZ_RELATION_TYPE:
        folder = "FN/"
    elif vazba.typ_vazby == DOKUMENT_RELATION_TYPE:
        folder = "SD/"
    else:
        folder = ""
    base_path = f"soubory/{folder}{datetime.datetime.now().strftime('%Y/%m/%d')}"
    return os.path.join(base_path, instance.nazev)


class SouborVazby(ExportModelOperationsMixin("soubor_vazby"), models.Model):
    """
    Model pro relační tabulku mezi souborem a záznamem.

    Obsahuje typ vazby podle typu záznamu.
    """

    CHOICES = (
        (PROJEKT_RELATION_TYPE, _("historie.models.historieVazby.projekt")),
        (DOKUMENT_RELATION_TYPE, _("historie.models.historieVazby.dokument")),
        (SAMOSTATNY_NALEZ_RELATION_TYPE, _("historie.models.historieVazby.nalez")),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)
    suppress_signal = False

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "soubor_vazby"

    @property
    def navazany_objekt(self) -> Optional[ModelWithMetadata]:
        """
        Vrátí navázaný objekt podle typu vazby.

        :return: Navázaný objekt (Projekt, Dokument nebo SamostatnyNalez).
        """
        if self.typ_vazby == PROJEKT_RELATION_TYPE:
            return self.projekt_souboru
        if self.typ_vazby == DOKUMENT_RELATION_TYPE:
            if hasattr(self, "dokument_souboru") and self.dokument_souboru is not None:
                return self.dokument_souboru
        if self.typ_vazby == SAMOSTATNY_NALEZ_RELATION_TYPE:
            return self.samostatny_nalez_souboru


class Soubor(ExportModelOperationsMixin("soubor"), models.Model):
    """Model pro soubor. Obsahuje jeho základné data, vazbu na historii a souborovů vazbu."""

    rozsah = models.IntegerField(blank=True, null=True)
    nazev = models.TextField()
    mimetype = models.TextField(db_index=True)
    vazba = models.ForeignKey(SouborVazby, on_delete=models.CASCADE, db_column="vazba", related_name="soubory")
    historie = models.OneToOneField(
        HistorieVazby,
        on_delete=models.SET_NULL,
        db_column="historie",
        related_name="soubor_historie",
        null=True,
    )
    path = models.CharField(max_length=500, null=True)
    size_mb = models.DecimalField(decimal_places=10, max_digits=150)
    sha_512 = models.CharField(max_length=128, null=True, blank=True, db_index=True)

    @property
    def url(self):
        """
        Vrátí URL pro přístup k souboru.

        :return: URL souboru nebo prázdný řetězec.
        """
        if self.path and settings.FEDORA_SERVER_NAME.lower() in self.path.lower():
            return f"{settings.DIGIARCHIV_SERVER_URL}id/{self.path.split('record/')[1]}"
        return ""

    @property
    def repository_uuid(self):
        """
        Vrátí UUID souboru v repozitáři.

        :return: Vrací vybranou hodnotu z kolekce.
        """
        if self.path and settings.FEDORA_SERVER_NAME.lower() in self.path.lower():
            return self.path.split("/")[-1]

    def calculate_sha_512(self):
        """
        Vrátí SHA-512 hash souboru uloženého v Fedora repozitáři.

        :return: Haš souboru ze skladiště nebo prázdný řetězec, pokud soubor neexistuje.
        """
        repository_content = self.get_repository_content()
        if repository_content is not None:
            return repository_content.sha_512
        return ""

    def delete(self, using=None, keep_parents=False):
        """
        Odstraní záznam objektu.

        :param using: Alias databázového spojení použitý při operaci.
        :param keep_parents: Parametr ``keep_parents`` se předává do volání ``delete()``.
        """
        if self.historie is None:
            self.create_soubor_vazby()
        super().delete(using, keep_parents)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "soubor"
        indexes = [
            models.Index(
                fields=[
                    "mimetype",
                ],
                name="mimetype_idx",
                opclasses=["text_ops"],
            ),
        ]
        ordering = [
            "nazev",
        ]

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(Soubor, self).__init__(*args, **kwargs)
        self.suppress_signal = False
        self.active_transaction = None
        self.close_active_transaction_when_finished = False
        self.binary_data = None

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací atribut objektu.
        """
        return self.nazev

    def create_soubor_vazby(self):
        """Metoda pro vytvoření vazby na historii."""
        logger.debug("core.models.Soubor.create_soubor_vazby.start")
        hv = HistorieVazby(typ_vazby=SOUBOR_RELATION_TYPE)
        hv.save()
        self.historie = hv
        self.save()
        logger.debug("core.models.soubor.create_soubor_vazby.finished", extra={"historie": hv})

    @property
    def vytvoreno(self):
        """
        Vrátí záznam historie s typem zmény "Nahrání SBR" (prvního nahrání souboru).

        :return: Záznam historie nebo ``None``, pokud soubor nevlastní historii.
        """
        if self.historie is not None:
            return self.historie.historie_set.filter(typ_zmeny=NAHRANI_SBR).order_by("datum_zmeny").first()
        else:
            self.create_soubor_vazby()
            logger.warning("core.models.soubor.vytvoreno.error", extra={"pk": self.pk})
            return None

    def get_repository_content(
        self, ident_cely_old=None, thumb_small=False, thumb_large=False, timestamp=None
    ) -> Optional[RepositoryBinaryFile]:
        """
        Vrací repository content.

        :param ident_cely_old: Identifikátor ``ident_cely_old`` používaný pro dohledání cílového záznamu.
        :param thumb_small: Parametr ``thumb_small`` se předává do volání ``get_binary_file()``.
        :param thumb_large: Parametr ``thumb_large`` se předává do volání ``get_binary_file()``.
        :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        from .repository_connector import FedoraRepositoryConnector

        record = self.vazba.navazany_objekt
        if record is not None and self.repository_uuid is not None:
            logger.debug(
                "core.models.Soubor.get_repository_content",
                extra={"ident_cely": record.ident_cely, "uuid": self.repository_uuid},
            )
            conector = FedoraRepositoryConnector(record, skip_container_check=False)
            rep_bin_file = conector.get_binary_file(
                self.repository_uuid, ident_cely_old, thumb_small, thumb_large, timestamp
            )
            return rep_bin_file
        logger.debug(
            "core.models.Soubor.get_repository_content.not_found",
            extra={"ident_cely": record, "uuid": self.repository_uuid, "pk": self.pk},
        )
        return None

    def zaznamenej_nahrani(self, user, file_name=None):
        """
        Metoda pro zapsáni vytvoření souboru do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param file_name: Parametr ``file_name`` se předává do volání ``Historie()``.
        """
        self.create_soubor_vazby()
        hist = Historie(
            typ_zmeny=NAHRANI_SBR,
            uzivatel=user,
            poznamka=file_name if file_name else self.nazev,
            vazba=self.historie,
        ).save()
        logger.debug("core.models.soubor.zaznamenej_nahrani.finished", extra={"historie": hist})

    def zaznamenej_nahrani_nove_verze(self, user, nazev=None):
        """
        Metoda pro zapsáni nahrání nové verze souboru do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param nazev: Parametr ``nazev`` se předává do volání ``Historie()``, ovlivňuje větvení podmínek.
        """
        if self.historie is None:
            self.create_soubor_vazby()
        if not nazev:
            nazev = self.nazev
        hist = Historie(
            typ_zmeny=NAHRANI_SBR,
            uzivatel=user,
            poznamka=nazev,
            vazba=self.historie,
        ).save()
        logger.debug("core.models.soubor.zaznamenej_nahrani_nove_verze.finished", extra={"historie": hist})

    @classmethod
    def get_file_extension_by_mime(cls, file):
        """
        Vrací file extension by mime.

        :param file: Soubor nebo cesta k souboru používaná při operaci.

            :return: Vrací výsledek volání ``get()``.
        """
        mime_type = cls.get_mime_types(file)
        return {
            "image/jpeg": ("jpeg", "jpg", "jpe", "jfif", "jfif-tbnl", "jif", "pjpg"),
            "image/png": ("png",),
            "image/tiff": ("tiff", "tif"),
            "image/heic": ("heic", "heif"),
            "image/heif": ("heic", "heif"),
            "image/svg+xml": ("svg", "svgz"),
            "image/bmp": ("bmp",),
            "image/gif": ("gif",),
            "text/plain": ("txt", "text"),
            "application/pdf": ("pdf",),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ("xlsx",),
            "text/csv": ("csv",),
            "application/zip": ("zip",),
            "application/zip-compressed": ("zip",),
            "application/x-zip-compressed": ("zip",),
            "application/vnd.rar": ("rar",),
            "application/x-rar-compressed": ("rar",),
            "application/x-rar": ("rar",),
            "application/x-7z-compressed": ("7z",),
            "application/vnd.ms-excel": ("xls", "xla", "xlb", "xlc", "xlm", "xlt", "xlw"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ("docx",),
            "application/msword": ("doc", "dot", "wiz"),
            "application/rtf": ("rtf",),
            "text/rtf": ("rtf",),
            "application/vnd.oasis.opendocument.text": ("odt",),
            "application/vnd.oasis.opendocument.spreadsheet": ("ods",),
        }.get(mime_type, [])

    @staticmethod
    def _detect_mime(file) -> str:
        """
        Detekuje MIME typ souboru pomocí ``libmagic`` s workaroundem pro regresi v ``libmagic >= 5.46``,
        kde běžný ZIP s obsahem je vrácen jako ``application/octet-stream``.

        :param file: File-like objekt s podporou ``seek`` a ``read``.
        :return: Detekovaný MIME typ.
        """
        file.seek(0)
        mime_type = magic.from_buffer(file.read(), mime=True)
        file.seek(0)
        if mime_type == "application/octet-stream":
            head = file.read(4)
            file.seek(0)
            if head.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")) and zipfile.is_zipfile(file):
                mime_type = "application/zip"
            file.seek(0)
        return mime_type

    @classmethod
    def get_thumb_icon(cls, file):
        """
        Vrací thumb icon.

        :param file: Soubor nebo cesta k souboru používaná při operaci.

            :return: Vrací n-tici.
        """
        mime_type = cls._detect_mime(file)
        logger.debug("core.models.Soubor.get_thumb_icon.start", extra={"mime_type": mime_type})
        icon_filename = {
            "image/heic": "heic.png",
            "image/heif": "heic.png",
            "text/plain": "txt.png",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx.png",
            "text/csv": "csv.png",
            "application/zip": "zip.png",
            "application/zip-compressed": "zip.png",
            "application/x-zip-compressed": "zip.png",
            "application/vnd.rar": "rar.png",
            "application/x-rar-compressed": "rar.png",
            "application/x-rar": "rar.png",
            "application/x-7z-compressed": "7z.png",
            "application/vnd.ms-excel": "xls.png",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx.png",
            "application/msword": "doc.png",
            "application/rtf": "rtf.png",
            "text/rtf": "rtf.png",
            "application/vnd.oasis.opendocument.text": "odt.png",
            "application/vnd.oasis.opendocument.spreadsheet": "ods.png",
            "application/pdf": "pdf.png",
            "image/bmp": "bmp.png",
            "image/gif": "gif.png",
            "image/jpeg": "jpg.png",
            "image/png": "png.png",
            "image/svg+xml": "svg.png",
            "image/tiff": "tif.png",
        }.get(mime_type, "file.png")

        file_path = os.path.join(settings.STATICFILES_DIRS[0], "icons", icon_filename)
        file_bytes = io.BytesIO()
        with open(file_path, "rb") as file:
            file_bytes.write(file.read())
        file_bytes.seek(0)
        logger.debug("core.models.Soubor.get_thumb_icon.end", extra={"mime_type": mime_type, "file": icon_filename})
        if icon_filename == "file.png":
            logger.warning("core.models.Soubor.get_thumb_icon.no_icon", extra={"mime_type": mime_type})
            return None, mime_type
        return file_bytes, mime_type

    @classmethod
    def get_mime_types(cls, file, check_archive=False) -> Union[set, bool, str]:
        """
        Vrací mime types.

        :param file: Soubor nebo cesta k souboru používaná při operaci.
        :param check_archive: Parametr ``check_archive`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        mime_type = cls._detect_mime(file)
        logger.debug(
            "core.models.Soubor.get_mime_type.mime_type", extra={"mime_type": mime_type, "option": check_archive}
        )
        if check_archive:
            mime_types = set()
            mime_types.add(mime_type)
            if mime_type == "application/zip":
                try:
                    with zipfile.ZipFile(file, "r") as zip_ref:
                        zip_ref.testzip()
                except Exception as err:
                    logger.info("core.models.Soubor.get_mime_type.cannot_unpack_zipfile", extra={"error": err})
                    if "encrypted" in str(err):
                        return "encrypted"
                    return False
            elif mime_type == "application/x-7z-compressed":
                file_input = io.BytesIO(file.read())
                try:
                    with py7zr.SevenZipFile(file_input, mode="r") as archive:
                        if archive.needs_password():
                            return "encrypted"
                        result = archive.test()
                        if result is False:
                            return False
                except Exception as err:
                    logger.info("core.models.Soubor.get_mime_type.cannot_unpack_7zfile", extra={"error": err})
                    return False
                finally:
                    file_input.close()
            elif mime_type in ("application/x-rar-compressed", "application/x-rar"):
                file_input = io.BytesIO(file.read())
                try:
                    with rarfile.RarFile(file_input) as archive:
                        archive.testrar()
                except Exception as err:
                    if "requires password" in str(err):
                        return "encrypted"
                    logger.info(
                        "core.models.Soubor.get_mime_type.cannot_unpack_rarfile",
                        extra={"mime_type": mime_type, "error": err},
                    )
                    return False
                finally:
                    file_input.close()
            file.seek(0)
            if "application/octet-stream" in mime_types:
                mime_types.remove("application/octet-stream")
            logger.debug("core.models.Soubor.get_mime_type.end", extra={"mime_type": mime_types})
            if len(mime_types) == 1:
                return list(mime_types)[0]
            else:
                return mime_types
        else:
            logger.debug("core.models.Soubor.get_mime_type.end", extra={"mime_type": mime_type})
            return mime_type

    @classmethod
    def remove_gps_data(cls, bytes_io: io.BytesIO) -> io.BytesIO:
        """
        Odstraní GPS metadata z fotografie uložené v paměti.

        Funkce načte EXIF data z obrázku, odstraní GPS informace a pokusí se
        znovu uložit EXIF. Pokud narazí na nevalidní nebo nekompatibilní EXIF
        tagy (např. UserComment, MakerNote apod.), automaticky je odstraní,
        aby bylo možné obrázek úspěšně uložit.

        V případě jakékoli chyby vrací původní vstupní soubor beze změny.

        :param bytes_io: Obsah souboru připravený ke kontrole antivirem.
        :return: Vrací výsledek operace odstranění.
        """
        try:
            img = Image.open(bytes_io)
            exif_data = img.info.get("exif")
            if exif_data:
                exif_dict = piexif.load(exif_data)
            else:
                bytes_io.seek(0)
                return bytes_io
        except Exception as err:
            logger.error("core.models.Soubor.remove_gps_data.cannot_open_file", extra={"error": err})
            bytes_io.seek(0)
            return bytes_io
        # Odstranění GPS dat, pokud existují
        if "GPS" in exif_dict and exif_dict["GPS"] != {}:
            del exif_dict["GPS"]
        else:
            logger.debug("core.models.Soubor.remove_gps_data.no_GPS_data")
            bytes_io.seek(0)
            return bytes_io
        if 41729 in exif_dict["Exif"] and isinstance(exif_dict["Exif"][41729], int):
            exif_dict["Exif"][41729] = str(exif_dict["Exif"][41729]).encode("utf-8")
        MAX_FIX_ATTEMPTS = 10
        for attempt in range(MAX_FIX_ATTEMPTS):
            try:
                new_exif_bytes = piexif.dump(exif_dict)
                break
            except ValueError as err:
                msg = str(err)
                # hledáme "37890 in Exif IFD"
                match = re.search(r"(\d+)\s+in\s+(\w+)\s+IFD", msg)
                if not match:
                    logger.error(
                        "core.models.Soubor.remove_gps_data.unhandled_exif_error",
                        extra={"error": msg},
                    )
                    bytes_io.seek(0)
                    return bytes_io
                tag = int(match.group(1))
                ifd = match.group(2)
                logger.info(
                    "core.models.Soubor.remove_gps_data.removing_broken_exif_tag",
                    extra={"tag": tag, "ifd": ifd},
                )
                # odstranění problémového tagu
                exif_dict.get(ifd, {}).pop(tag, None)
        else:
            # nepodařilo se opravit ani po několika pokusech
            logger.error("core.models.Soubor.remove_gps_data.exif_cleanup_failed")
            bytes_io.seek(0)
            return bytes_io
        try:
            output_io = io.BytesIO()
            img.save(output_io, format=img.format, exif=new_exif_bytes)
            output_io.seek(0)
            logger.debug("core.models.Soubor.remove_gps_data.GPS_data_removed")
            return output_io
        except Exception as err:
            logger.error("core.models.Soubor.remove_gps_data.cannot_save_file", extra={"error": err})
            bytes_io.seek(0)
            return bytes_io

    # Povolené MIME typy podle typu uploadu — odpovídá whitelistu v `static/js/dz.js`.
    PAS_ACCEPTED_MIMES = frozenset(
        {
            "image/tiff",
            "image/jpeg",
            "image/png",
            "image/heic",
            "image/heif",
        }
    )

    DOKUMENT_ACCEPTED_MIMES = frozenset(
        {
            "application/pdf",
            "image/tiff",
            "image/jpeg",
            "image/png",
            "image/svg+xml",
            "text/plain",
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        }
    )

    MODEL3D_ACCEPTED_MIMES = frozenset(
        {
            "application/pdf",
            "image/tiff",
            "image/jpeg",
            "image/png",
            "image/svg+xml",
            "application/zip",
            "application/zip-compressed",
            "application/x-zip-compressed",
            "application/vnd.rar",
            "application/x-rar",
            "application/x-rar-compressed",
            "application/x-compressed",
            "application/x-7z-compressed",
        }
    )

    PROJEKT_ACCEPTED_MIMES = frozenset(
        {
            "application/pdf",
            "image/tiff",
            "image/jpeg",
            "image/png",
            "image/svg+xml",
            "image/heic",
            "image/heif",
            "image/bmp",
            "image/gif",
            "application/zip",
            "application/zip-compressed",
            "application/x-zip-compressed",
            "application/vnd.rar",
            "application/x-rar",
            "application/x-rar-compressed",
            "application/x-compressed",
            "application/x-7z-compressed",
            "application/msword",  # doc
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
            "application/vnd.ms-excel",  # xls
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
            "text/plain",
            "text/csv",
            "application/rtf",
            "text/rtf",
            "application/vnd.oasis.opendocument.text",  # odt
            "application/vnd.oasis.opendocument.spreadsheet",  # ods
        }
    )

    @classmethod
    def check_mime_for_url(cls, file, source_url=""):
        """
        Ověří, zda detekovaný MIME typ souboru spadá do whitelistu pro danou upload URL.

        Whitelisty per větev musí odpovídat seznamům v ``static/js/dz.js``.

        :param file: Soubor nebo cesta k souboru používaná při operaci.
        :param source_url: URL uploadu — určuje, který whitelist se použije
            (``pas``, ``dokument``, ``model3d`` nebo výchozí ``projekt``).
        :return: ``True``/``False`` podle výsledku kontroly, případně řetězec
            ``"encrypted"`` u zaheslovaných archivů.
        """
        mime = cls.get_mime_types(file, check_archive=True)
        logger.debug("core.models.Soubor.check_mime_for_url.mime_types", extra={"mime_type": mime})
        if mime == "encrypted":
            return mime
        if mime is False:
            return False
        if isinstance(mime, str):
            mime = {mime}
        if "soubor/nahrat/pas/" in source_url or "/api/pas/nalez/" in source_url:
            allowed = cls.PAS_ACCEPTED_MIMES
        elif "soubor/nahrat/dokument/" in source_url:
            allowed = cls.DOKUMENT_ACCEPTED_MIMES
        elif "soubor/nahrat/model3d/" in source_url:
            allowed = cls.MODEL3D_ACCEPTED_MIMES
        else:
            allowed = cls.PROJEKT_ACCEPTED_MIMES
        unaccepted = mime - allowed
        if unaccepted:
            logger.debug(
                "core.models.Soubor.check_mime_for_url.unaccepted_types",
                extra={"mime_type": list(unaccepted), "source_url": source_url},
            )
            return False
        return True

    @classmethod
    def check_antivirus(cls, bytes_io: io.BytesIO):
        """
        Zkontroluje soubor na přítomnost virů pomocí ClamAV.

        :param bytes_io: Obsah souboru připravený ke kontrole antivirem.
        :return: Výsledek antivirové kontroly (`PASSES`, `VIRUS_FOUND`, `CHECK_FAILED` nebo `SKIPPED`).
        """
        if settings.CLAMD_HOST and settings.CLAMD_PORT:
            try:
                clamd = ClamdNetworkSocket()
                bytes_io.seek(0)
                start_time = time.time()
                result = clamd.instream(bytes_io)
                duration_ms = (time.time() - start_time) * 1000
                filename, (status, reason) = next(iter(result.items()))
                if status == "OK":
                    logger.debug(
                        "core.models.Soubor.check_antivirus.passes",
                        extra={"response": status, "duration_ms": duration_ms},
                    )
                    return AntivirusCheckResult.PASSES
                elif status == "ERROR":
                    logger.debug(
                        "core.models.Soubor.check_antivirus.error",
                        extra={"response": status, "duration_ms": duration_ms},
                    )
                    return AntivirusCheckResult.CHECK_FAILED
                else:
                    logger.debug(
                        "core.models.Soubor.check_antivirus.virus_found",
                        extra={"response": status, "reason": reason, "duration_ms": duration_ms},
                    )
                    return AntivirusCheckResult.VIRUS_FOUND
            except ClamdConnectionError as err:
                logger.error("core.models.Soubor.check_antivirus.connection_error", extra={"error": str(err)})
                return AntivirusCheckResult.CHECK_FAILED
            except ClamdResponseError as err:
                logger.error("core.models.Soubor.check_antivirus.response_error", extra={"error": str(err)})
                return AntivirusCheckResult.CHECK_FAILED
        return AntivirusCheckResult.SKIPPED

    def _create_file_response(self, rep_bin_file: RepositoryBinaryFile) -> FileResponse:
        """
        Vytvoří file response.

        :param rep_bin_file: Parametr ``rep_bin_file`` pracuje se s atributy ``content``.
        :return: Nově vytvořená hodnota připravená touto funkcí.
        """
        content = rep_bin_file.content
        response = FileResponse(content, filename=self.nazev)
        content.seek(0)
        response["Content-Length"] = content.getbuffer().nbytes
        content.seek(0)
        response["Content-Disposition"] = f"attachment; filename={self.nazev}"
        return response

    @cached_property
    def large_thumbnail(self) -> FileResponse | None:
        """
        Vrátí větší náhled obrázku.

        :return: FileResponse s náhledem nebo None.
        """
        rep_bin_file: RepositoryBinaryFile = self.get_repository_content(thumb_large=True)
        if self.repository_uuid is not None and rep_bin_file:
            response = self._create_file_response(rep_bin_file)
            response["Content-Type"] = "image/png"
            response["Content-Disposition"] = f"attachment; filename={self.nazev}.png"
            return response
        return None

    @cached_property
    def small_thumbnail(self) -> FileResponse | None:
        """
        Vrátí menší náhled obrázku.

        :return: FileResponse s náhledem nebo None.
        """
        rep_bin_file: RepositoryBinaryFile = self.get_repository_content(thumb_small=True)
        if self.repository_uuid is not None and rep_bin_file:
            response = self._create_file_response(rep_bin_file)
            response["Content-Type"] = "image/png"
            response["Content-Disposition"] = f'inline; filename="{self.nazev}.png"'
            response["Cache-Control"] = "private, max-age=43200"
            return response
        return None

    @cached_property
    def content_file_response(self) -> FileResponse | None:
        """
        Vrátí soubor jako HTTP response.

        :return: FileResponse se souborem nebo None.
        """
        rep_bin_file: RepositoryBinaryFile = self.get_repository_content()
        if self.repository_uuid is not None and rep_bin_file and rep_bin_file.size_mb > 0:
            return self._create_file_response(rep_bin_file)
        return None

    def getMock(self):
        """
        Vrátí mock reprezentaci souboru.

        :return: Slovník s daty souboru.
        """
        return {"name": self.nazev, "size": float(self.size_mb * 1000000), "type": self.mimetype, "id": self.pk}

    def get_historicke_verze(self):
        """
        Metoda k získání údajů o historických verzích ve Fedoře pro tabulku historie

        :return: Vrací proměnná ``results``.
        """
        from core.repository_connector import FedoraRepositoryConnector
        from core.utils import get_timezone

        timezone = get_timezone()
        record = self.vazba.navazany_objekt
        results = []
        if record is not None and self.repository_uuid is not None:
            logger.debug(
                "core.models.Soubor.get_repository_content",
                extra={"ident_cely": record.ident_cely, "uuid": self.repository_uuid},
            )
            connector = FedoraRepositoryConnector(record)
            history_list = connector.get_historie_file(self.repository_uuid)
            for history_item in history_list:
                local_dt = history_item["datetime"].astimezone(timezone)
                url = reverse(
                    "core:stahnout_data_historicka",
                    kwargs={
                        "model_name": self.__class__.__name__,
                        "ident_cely": self.pk,
                        "timestamp": history_item["timestamp"],
                    },
                )
                results.append(
                    {
                        "datum": local_dt,
                        "url": url,
                        "uzivatel": history_item["creator"],
                    }
                )
        return results

    def get_soubor_historicky(self, timestamp) -> FileResponse | None:
        """
        Metoda k získání vlastního souboru dané verze z Fedory

        :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.
        :return: Vrací výsledek operace.
        """
        rep_bin_file: RepositoryBinaryFile = self.get_repository_content(timestamp=timestamp)
        if self.repository_uuid is not None and rep_bin_file and rep_bin_file.size_mb > 0:
            return self._create_file_response(rep_bin_file)
        return None


class ProjektSekvence(models.Model):
    """Model pro tabulku se sekvencemi projektu."""

    region = models.CharField(max_length=1)
    rok = models.IntegerField()
    sekvence = models.IntegerField()

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "projekt_sekvence"
        constraints = [
            models.UniqueConstraint(fields=["region", "rok"], name="unique_sekvence_projekt"),
        ]


class OdstavkaSystemu(ExportModelOperationsMixin("odstavka_systemu"), models.Model):
    """Model pro tabulku s odstávkami systému."""

    info_od = models.DateField(_("core.model.OdstavkaSystemu.infoOd.label"))
    datum_odstavky = models.DateField(_("core.model.OdstavkaSystemu.datumOdstavky.label"))
    cas_odstavky = models.TimeField(_("core.model.OdstavkaSystemu.casOdstavky.label"))
    status = models.BooleanField(_("core.model.OdstavkaSystemu.status.label"), default=True)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "odstavky_systemu"
        verbose_name = _("core.model.OdstavkaSystemu.modelTitle.label")
        verbose_name_plural = _("core.model.OdstavkaSystemu.modelTitles.label")

    def clean(self):
        """
        Metoda clean, kde se navíc kontrolu, jestli už není jedna odstávka uložena.

        :raises ValidationError: Vyvolá se při splnění podmínky ``odstavky.first().pk != self.pk``.
        """
        odstavky = OdstavkaSystemu.objects.filter(status=True)
        if odstavky.count() > 0 and self.status:
            if odstavky.first().pk != self.pk:
                raise ValidationError(_("core.model.OdstavkaSystemu.jenJednaAktivniOdstavkaPovolena.text"))
        super(OdstavkaSystemu, self).clean()

    def __str__(self) -> str:
        """
               Vrací textovou reprezentaci objektu.

        :return: Textová reprezentace odstávky systému.
        """
        return "{}: {} {}".format(_("core.model.OdstavkaSystemu.text"), self.datum_odstavky, self.cas_odstavky)


class Permissions(models.Model):
    """Implementuje komponentu ``Permissions`` v rámci aplikace."""

    class ownershipChoices(models.TextChoices):
        """Implementuje komponentu ``ownershipChoices`` v rámci aplikace."""

        my = "my", _("core.models.permissions.ownershipChoices.my")
        our = "our", _("core.models.permissions.ownershipChoices.our")

    class actionChoices(models.TextChoices):
        """Implementuje komponentu ``actionChoices`` v rámci aplikace."""

        adb_smazat = "adb_smazat", _("core.models.permissions.actionChoices.adb_smazat")
        vb_smazat = "vb_smazat", _("core.models.permissions.actionChoices.vb_smazat")
        adb_zapsat = "adb_zapsat", _("core.models.permissions.actionChoices.adb_zapsat")
        archz_adb_zapsat = "archz_adb_zapsat", _("core.models.permissions.actionChoices.archz_adb_zapsat")
        archz_komponenta_zapsat = "archz_komponenta_zapsat", _(
            "core.models.permissions.actionChoices.archz_komponenta_zapsat"
        )
        archz_pian_zapsat = "archz_pian_zapsat", _("core.models.permissions.actionChoices.archz_pian_zapsat")
        archz_vratit = "archz_vratit", _("core.models.permissions.actionChoices.archz_vratit")
        archz_odeslat = "archz_odeslat", _("core.models.permissions.actionChoices.archz_odeslat")
        archz_archivovat = "archz_archivovat", _("core.models.permissions.actionChoices.archz_archivovat")
        archz_pian_edit = "archz_pian_edit", _("core.models.permissions.actionChoices.archz_pian_edit")
        archz_vedouci_smazat = "archz_vedouci_smazat", _("core.models.permissions.actionChoices.archz_vedouci_smazat")
        archz_edit = "archz_edit", _("core.models.permissions.actionChoices.archz_edit")
        archz_smazat = "archz_smazat", _("core.models.permissions.actionChoices.archz_smazat")
        archz_zmenit_proj = "archz_zmenit_proj", _("core.models.permissions.actionChoices.archz_zmenit_proj")
        archz_zmenit_sam = "archz_zmenit_sam", _("core.models.permissions.actionChoices.archz_zmenit_sam")
        archz_odpojit_dokument = "archz_odpojit_dokument", _(
            "core.models.permissions.actionChoices.archz_odpojit_dokument"
        )
        archz_pripojit_dok = "archz_pripojit_dok", _("core.models.permissions.actionChoices.archz_pripojit_dok")
        archz_pripojit_proj = "archz_pripojit_proj", _("core.models.permissions.actionChoices.archz_pripojit_proj")
        archz_pripojit_dok_proj = "archz_pripojit_dok_proj", _(
            "core.models.permissions.actionChoices.archz_pripojit_dok_proj"
        )
        archz_dj_zapsat = "archz_dj_zapsat", _("core.models.permissions.actionChoices.archz_dj_zapsat")
        archz_pripojit_do_proj = "archz_pripojit_do_proj", _(
            "core.models.permissions.actionChoices.archz_pripojit_do_proj"
        )
        dj_smazat = "dj_smazat", _("core.models.permissions.actionChoices.dj_smazat")
        dj_zmenit_katastr = "dj_zmenit_katastr", _("core.models.permissions.actionChoices.dj_zmenit_katastr")
        dok_pripojit_archz = "dok_pripojit_archz", _("core.models.permissions.actionChoices.dok_pripojit_archz")
        dok_pripojit_proj = "dok_pripojit_proj", _("core.models.permissions.actionChoices.dok_pripojit_proj")
        dok_cast_odpojit = "dok_cast_odpojit", _("core.models.permissions.actionChoices.dok_cast_odpojit")
        dok_cast_edit = "dok_cast_edit", _("core.models.permissions.actionChoices.dok_cast_edit")
        dok_cast_smazat = "dok_cast_smazat", _("core.models.permissions.actionChoices.dok_cast_smazat")
        dok_cast_zapsat = "dok_cast_zapsat", _("core.models.permissions.actionChoices.dok_cast_zapsat")
        dok_komponenta_zapsat = "dok_komponenta_zapsat", _(
            "core.models.permissions.actionChoices.dok_komponenta_zapsat"
        )
        dok_edit = "dok_edit", _("core.models.permissions.actionChoices.dok_edit")
        dok_smazat = "dok_smazat", _("core.models.permissions.actionChoices.dok_smazat")
        dok_archivovat = "dok_archivovat", _("core.models.permissions.actionChoices.dok_archivovat")
        dok_odeslat = "dok_odeslat", _("core.models.permissions.actionChoices.dok_odeslat")
        dok_vratit = "dok_vratit", _("core.models.permissions.actionChoices.dok_vratit")
        dok_tvary_edit = "dok_tvary_edit", _("core.models.permissions.actionChoices.dok_tvary_edit")
        dok_tvary_smazat = "dok_tvary_smazat", _("core.models.permissions.actionChoices.dok_tvary_smazat")
        dok_zapsat_do_archz = "dok_zapsat_do_archz", _("core.models.permissions.actionChoices.dok_zapsat_do_archz")
        dok_zapsat_do_projekt = "dok_zapsat_do_projekt", _(
            "core.models.permissions.actionChoices.dok_zapsat_do_projekt"
        )
        model_edit = "model_edit", _("core.models.permissions.actionChoices.model_edit")
        neident_akce_edit = "neident_akce_edit", _("core.models.permissions.actionChoices.neident_akce_edit")
        neident_akce_smazat = "neident_akce_smazat", _("core.models.permissions.actionChoices.neident_akce_smazat")
        ez_edit = "ez_edit", _("core.models.permissions.actionChoices.ez_edit")
        ez_odeslat = "ez_odeslat", _("core.models.permissions.actionChoices.ez_odeslat")
        ez_potvrdit = "ez_potvrdit", _("core.models.permissions.actionChoices.ez_potvrdit")
        ez_vratit = "ez_vratit", _("core.models.permissions.actionChoices.ez_vratit")
        ez_smazat = "ez_smazat", _("core.models.permissions.actionChoices.ez_smazat")
        eo_edit_ez = "eo_edit_ez", _("core.models.permissions.actionChoices.eo_edit_ez")
        eo_edit_akce = "eo_edit_akce", _("core.models.permissions.actionChoices.eo_edit_akce")
        eo_odpojit_ez = "eo_odpojit_ez", _("core.models.permissions.actionChoices.eo_odpojit_ez")
        eo_odpojit_akce = "eo_odpojit_akce", _("core.models.permissions.actionChoices.eo_odpojit_akce")
        eo_pripojit_akce = "eo_pripojit_akce", _("core.models.permissions.actionChoices.eo_pripojit_akce")
        eo_pripojit_ez = "eo_pripojit_ez", _("core.models.permissions.actionChoices.eo_pripojit_ez")
        lokalita_komponenta_zapsat = "lokalita_komponenta_zapsat", _(
            "core.models.permissions.actionChoices.lokalita_komponenta_zapsat"
        )
        lokalita_pian_edit = "lokalita_pian_edit", _("core.models.permissions.actionChoices.lokalita_pian_edit")
        lokalita_pian_zapsat = "lokalita_pian_zapsat", _("core.models.permissions.actionChoices.lokalita_pian_zapsat")
        lokalita_dj_zapsat = "lokalita_dj_zapsat", _("core.models.permissions.actionChoices.lokalita_dj_zapsat")
        lokalita_edit = "lokalita_edit", _("core.models.permissions.actionChoices.lokalita_edit")
        komponenta_detail_akce = "komponenta_detail_akce", _(
            "core.models.permissions.actionChoices.komponenta_detail_akce"
        )
        komponenta_detail_dok = "komponenta_detail_dok", _(
            "core.models.permissions.actionChoices.komponenta_detail_dok"
        )
        komponenta_smazat_akce = "komponenta_smazat_akce", _(
            "core.models.permissions.actionChoices.komponenta_smazat_akce"
        )
        komponenta_smazat_dok = "komponenta_smazat_dok", _(
            "core.models.permissions.actionChoices.komponenta_smazat_dok"
        )
        komponenta_zapsat_akce = "komponenta_zapsat_akce", _(
            "core.models.permissions.actionChoices.komponenta_zapsat_akce"
        )
        komponenta_zapsat_dok = "komponenta_zapsat_dok", _(
            "core.models.permissions.actionChoices.komponenta_zapsat_dok"
        )
        nalez_smazat_dokument = "nalez_smazat_dokument", _(
            "core.models.permissions.actionChoices.nalez_smazat_dokument"
        )
        nalez_smazat_akce = "nalez_smazat_akce", _("core.models.permissions.actionChoices.nalez_smazat_akce")
        nalez_edit_dokument = "nalez_edit_dokument", _("core.models.permissions.actionChoices.nalez_edit_dokument")
        nalez_edit_akce = "nalez_edit_akce", _("core.models.permissions.actionChoices.nalez_edit_akce")
        notifikace_projekty = "notifikace_projekty", _("core.models.permissions.actionChoices.notifikace_projekty")
        pas_edit = "pas_edit", _("core.models.permissions.actionChoices.pas_edit")
        pas_archivovat = "pas_archivovat", _("core.models.permissions.actionChoices.pas_archivovat")
        pas_odeslat = "pas_odeslat", _("core.models.permissions.actionChoices.pas_odeslat")
        pas_potvrdit = "pas_potvrdit", _("core.models.permissions.actionChoices.pas_potvrdit")
        pas_vratit = "pas_vratit", _("core.models.permissions.actionChoices.pas_vratit")
        pas_smazat = "pas_smazat", _("core.models.permissions.actionChoices.pas_smazat")
        pas_ulozeni_edit = "pas_ulozeni_edit", _("core.models.permissions.actionChoices.pas_ulozeni_edit")
        pas_zapsat_do_projektu = "pas_zapsat_do_projektu", _(
            "core.models.permissions.actionChoices.pas_zapsat_do_projektu"
        )
        mapa_pas = "mapa_pas", _("core.models.permissions.actionChoices.mapa_pas")
        mapa_pian = "mapa_pian", _("core.models.permissions.actionChoices.mapa_pian")
        pian_potvrdit = "pian_potvrdit", _("core.models.permissions.actionChoices.pian_potvrdit")
        pian_odpojit = "pian_odpojit", _("core.models.permissions.actionChoices.pian_odpojit")
        pian_zapsat = "pian_zapsat", _("core.models.permissions.actionChoices.pian_zapsat")
        projekt_archivovat = "projekt_archivovat", _("core.models.permissions.actionChoices.projekt_archivovat")
        projekt_dok_odpojit = "projekt_dok_odpojit", _("core.models.permissions.actionChoices.projekt_dok_odpojit")
        projekt_dok_pripojit = "projekt_dok_pripojit", _("core.models.permissions.actionChoices.projekt_dok_pripojit")
        projekt_edit = "projekt_edit", _("core.models.permissions.actionChoices.projekt_edit")
        projekt_generovat_exp_list = "projekt_generovat_exp_list", _(
            "core.models.permissions.actionChoices.projekt_generovat_exp_list"
        )
        projekt_generovat_oznameni = "projekt_generovat_oznameni", _(
            "core.models.permissions.actionChoices.projekt_generovat_oznameni"
        )
        projekt_oznamovatel_zapsat = "projekt_oznamovatel_zapsat", _(
            "core.models.permissions.actionChoices.projekt_oznamovatel_zapsat"
        )
        projekt_oznamovatel_edit = "projekt_oznamovatel_edit", _(
            "core.models.permissions.actionChoices.projekt_oznamovatel_edit"
        )
        projekt_zadost_udaje_oznamovatel = "projekt_zadost_udaje_oznamovatel", _(
            "core.models.permissions.actionChoices.projekt_zadost_udaje_oznamovatel"
        )
        projekt_smazat = "projekt_smazat", _("core.models.permissions.actionChoices.projekt_smazat")
        projekt_navrh_ke_zruseni = "projekt_navrh_ke_zruseni", _(
            "core.models.permissions.actionChoices.projekt_navrh_ke_zruseni"
        )
        projekt_prihlasit = "projekt_prihlasit", _("core.models.permissions.actionChoices.projekt_prihlasit")
        projekt_schvalit = "projekt_schvalit", _("core.models.permissions.actionChoices.projekt_schvalit")
        projekt_ukoncit_v_terenu = "projekt_ukoncit_v_terenu", _(
            "core.models.permissions.actionChoices.projekt_ukoncit_v_terenu"
        )
        projekt_upravit_datum_oznameni = (
            "projekt_upravit_datum_oznameni",
            _("core.models.permissions.actionChoices.projekt_upravit_datum_oznameni"),
        )
        projekt_zadost_odhlaseni_projektu = "projekt_zadost_odhlaseni_projektu", _(
            "core.models.permissions.actionChoices.projekt_zadost_odhlaseni_projektu"
        )
        projekt_zadost_zruseni_projektu = "projekt_zadost_zruseni_projektu", _(
            "core.models.permissions.actionChoices.projekt_zadost_zruseni_projektu"
        )
        projekt_uzavrit = "projekt_uzavrit", _("core.models.permissions.actionChoices.projekt_uzavrit")
        projekt_vratit_navrh_zruseni = "projekt_vratit_navrh_zruseni", _(
            "core.models.permissions.actionChoices.projekt_vratit_navrh_zruseni"
        )
        projekt_vratit = "projekt_vratit", _("core.models.permissions.actionChoices.projekt_vratit")
        projekt_zahajit_v_terenu = "projekt_zahajit_v_terenu", _(
            "core.models.permissions.actionChoices.projekt_zahajit_v_terenu"
        )
        projekt_zrusit = "projekt_zrusit", _("core.models.permissions.actionChoices.projekt_zrusit")
        projekt_autocomplete_archz = "projekt_autocomplete_archz", _(
            "core.models.permissions.actionChoices.projekt_autocomplete_archz"
        )
        projekt_autocomplete_dokument = "projekt_autocomplete_dokument", _(
            "core.models.permissions.actionChoices.projekt_autocomplete_dokument"
        )
        projekt_pas_zobrazit = "projekt_pas_zobrazit", _("core.models.permissions.actionChoices.projekt_pas_zobrazit")
        soubor_nahrat_dokument = "soubor_nahrat_dokument", _(
            "core.models.permissions.actionChoices.soubor_nahrat_dokument"
        )
        soubor_nahrat_model3d = "soubor_nahrat_model3d", _(
            "core.models.permissions.actionChoices.soubor_nahrat_model3d"
        )
        soubor_nahrat_pas = "soubor_nahrat_pas", _("core.models.permissions.actionChoices.soubor_nahrat_pas")
        soubor_nahrat_projekt = "soubor_nahrat_projekt", _(
            "core.models.permissions.actionChoices.soubor_nahrat_projekt"
        )
        soubor_smazat_projekt = "soubor_smazat_projekt", _(
            "core.models.permissions.actionChoices.soubor_smazat_projekt"
        )
        soubor_smazat_dokument = "soubor_smazat_dokument", _(
            "core.models.permissions.actionChoices.soubor_smazat_dokument"
        )
        soubor_smazat_model3d = "soubor_smazat_model3d", _(
            "core.models.permissions.actionChoices.soubor_smazat_model3d"
        )
        soubor_nahradit_model3d = "soubor_nahradit_model3d", _(
            "core.models.permissions.actionChoices.soubor_nahradit_model3d"
        )
        soubor_smazat_pas = "soubor_smazat_pas", _("core.models.permissions.actionChoices.soubor_smazat_pas")
        soubor_stahnout_projekt = "soubor_stahnout_projekt", _(
            "core.models.permissions.actionChoices.soubor_stahnout_projekt"
        )
        soubor_stahnout_dokument = "soubor_stahnout_dokument", _(
            "core.models.permissions.actionChoices.soubor_stahnout_dokument"
        )
        soubor_stahnout_model3d = "soubor_stahnout_model3d", _(
            "core.models.permissions.actionChoices.soubor_stahnout_model3d"
        )
        soubor_stahnout_pas = "soubor_stahnout_pas", _("core.models.permissions.actionChoices.soubor_stahnout_pas")
        soubor_nahradit_dokument = "soubor_nahradit_dokument", _(
            "core.models.permissions.actionChoices.soubor_nahradit_dokument"
        )
        soubor_nahradit_pas = "soubor_nahradit_pas", _("core.models.permissions.actionChoices.soubor_nahradit_pas")
        soubor_nahled_projekt = "soubor_nahled_projekt", _(
            "core.models.permissions.actionChoices.soubor_nahled_projekt"
        )
        soubor_nahled_dokument = "soubor_nahled_dokument", _(
            "core.models.permissions.actionChoices.soubor_nahled_dokument"
        )
        soubor_nahled_model3d = "soubor_nahled_model3d", _(
            "core.models.permissions.actionChoices.soubor_nahled_model3d"
        )
        soubor_nahled_pas = "soubor_nahled_pas", _("core.models.permissions.actionChoices.soubor_nahled_pas")
        spoluprace_zadost = "spoluprace_zadost", _("core.models.permissions.actionChoices.spoluprace_zadost")
        spoluprace_aktivovat = "spoluprace_aktivovat", _("core.models.permissions.actionChoices.spoluprace_aktivovat")
        spoluprace_deaktivovat = "spoluprace_deaktivovat", _(
            "core.models.permissions.actionChoices.spoluprace_deaktivovat"
        )
        spoluprace_smazat = "spoluprace_smazat", _("core.models.permissions.actionChoices.spoluprace_smazat")
        spoluprace_edit_projekty = "spoluprace_edit_projekty", _(
            "core.models.permissions.actionChoices.spoluprace_edit_projekty"
        )
        pian_import_new = "pian_import_new", "core.models.permissions.actionChoices.pian_import_new"
        pian_import_change = "pian_import_change", "core.models.permissions.actionChoices.pian_import_change"
        akce_dj_zakladni = "akce_dj_zakladni", "core.models.permissions.actionChoices.akce_dj_zakladni"
        akce_pripojit_pian_mapa = (
            "akce_pripojit_pian_mapa",
            "core.models.permissions.actionChoices.akce_pripojit_pian_mapa",
        )
        akce_pripojit_pian_id = "akce_pripojit_pian_id", "core.models.permissions.actionChoices.akce_pripojit_pian_id"
        lokalita_dj_zakladni = "lokalita_dj_zakladni", "core.models.permissions.actionChoices.lokalita_dj_zakladni"
        lokalita_pripojit_pian_mapa = (
            "lokalita_pripojit_pian_mapa",
            "core.models.permissions.actionChoices.lokalita_pripojit_pian_mapa",
        )
        lokalita_pripojit_pian_id = (
            "lokalita_pripojit_pian_id",
            "core.models.permissions.actionChoices.lokalita_pripojit_pian_id",
        )
        dokumenty_tabulka_projekt = "dokumenty_tabulka_projekt", _(
            "core.models.permissions.actionChoices.dokumenty_tabulka_projekt"
        )
        dokumenty_tabulka_arch_z = "dokumenty_tabulka_arch_z", _(
            "core.models.permissions.actionChoices.dokumenty_tabulka_arch_z"
        )
        vypis_dokument = "vypis_dokument", _("core.models.permissions.actionChoices.vypis_dokument")
        vypis_projekt = "vypis_projekt", _("core.models.permissions.actionChoices.vypis_projekt")
        vypis_akce = "vypis_akce", _("core.models.permissions.actionChoices.vypis_akce")
        vypis_lokalita = "vypis_lokalita", _("core.models.permissions.actionChoices.vypis_lokalita")
        vypis_pas = "vypis_pas", _("core.models.permissions.actionChoices.vypis_pas")
        vypis_model3d = "vypis_model3d", _("core.models.permissions.actionChoices.vypis_model3d")
        vypis_ez = "vypis_ez", _("core.models.permissions.actionChoices.vypis_ez")
        historie_fedora = "historie_fedora", _("core.models.permissions.actionChoices.historie_fedora")

    pristupnost_to_groups = {
        PRISTUPNOST_ANONYM_ID: 0,
        PRISTUPNOST_BADATEL_ID: ROLE_BADATEL_ID,
        PRISTUPNOST_ARCHEOLOG_ID: ROLE_ARCHEOLOG_ID,
        PRISTUPNOST_ARCHIVAR_ID: ROLE_ARCHIVAR_ID,
    }

    permission_to_override = [actionChoices.soubor_nahled_dokument, actionChoices.soubor_stahnout_dokument]

    address_in_app = models.CharField(max_length=150, verbose_name=_("core.models.permissions.addressInApp"))
    main_role = models.ForeignKey(
        Group,
        models.DO_NOTHING,
        db_column="role",
        related_name="role_opravneni",
        verbose_name=_("core.models.permissions.mainRole"),
    )
    base = models.BooleanField(default=True, verbose_name=_("core.models.permissions.base"))
    status = models.CharField(
        max_length=10,
        verbose_name=_("core.models.permissions.status"),
        null=True,
        blank=True,
    )
    ownership = models.CharField(
        max_length=10,
        verbose_name=_("core.models.permissions.ownership"),
        null=True,
        blank=True,
        choices=ownershipChoices.choices,
    )
    accessibility = models.CharField(
        max_length=10,
        verbose_name=_("core.models.permissions.accessibility"),
        null=True,
        blank=True,
        choices=ownershipChoices.choices,
    )
    action = models.CharField(
        max_length=50,
        verbose_name=_("core.models.permissions.action"),
        null=True,
        blank=True,
        choices=actionChoices.choices,
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        verbose_name = _("core.model.permissions.modelTitle.label")
        verbose_name_plural = _("core.model.permissions.modelTitles.label")

    def check_concrete_permission(self, user, ident=None, typ=None, skip_status=False):
        """
        Ověří, zda má uživatel konkrétní oprávnění na daný záznam a typ.

        :param user: Uživatel, pro kterého se kontroluje oprávnění.
        :param ident: Identifikátor archeologického záznamu (např. C-XX-YYYYNNNNN).
        :param typ: Typ objektu, pro který se kontroluje oprávnění (např. projekt, lokalita).
        :param skip_status: Pokud ``True``, přeskočí stavovou podmínku oprávnění a vyhodnotí pouze
            základ, vlastnictví a přístupnost.
        :return: ``True`` pokud má uživatel oprávnění, ``False`` jinak.
        """
        self.typ = typ
        self.object = None
        self.logged_in_user = user
        self.permission_object = None
        self.ident = ident
        perm_check = True
        if not self.check_base():
            logger.debug("core.model.Permissions.check_concrete_permission.base_false")
            return False
        if self.ident is not None:
            if skip_status:
                perm_check = status_check = True
            else:
                perm_check = status_check = self.check_status()
            if perm_check and not self.check_ownership(self.ownership):
                logger.debug("core.model.Permissions.check_concrete_permission.ownership_false")
                perm_check = False
            if perm_check and not self.check_accessibility():
                logger.debug("core.model.Permissions.check_concrete_permission.accessibility_false")
                perm_check = False
            if not perm_check and status_check and self.check_permission_skip():
                logger.debug("core.model.Permissions.check_concrete_permission.skip_True")
                perm_check = True
            if not perm_check and self.action in self.permission_to_override:
                perm_check = self.permission_override()
        logger.debug(
            "core.model.Permissions.check_concrete_permission.Permission_check_outcome", extra={"value": perm_check}
        )
        return perm_check

    def check_base(self):
        """
        Ověří base. v aplikaci.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if self.base:
            return True
        else:
            return False

    def check_status(self):
        """
        Ověří status. v aplikaci.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if self.status:
            if not self.permission_object:
                self.get_permission_object()
                if self.permission_object == "error":
                    return True
            subed_status = re.sub("[a-zA-Z]", "", self.status)
            if ">" in self.status:
                if not int(self.permission_object.stav) > int(subed_status[1]):
                    return False
            elif "<" in subed_status:
                if not int(self.permission_object.stav) < int(subed_status[1]):
                    return False
            elif "-" in subed_status:
                if not (
                    int(self.permission_object.stav) >= int(subed_status[0])
                    and int(self.permission_object.stav) <= int(subed_status[-1])
                ):
                    return False
            else:
                if not int(self.permission_object.stav) == int(subed_status):
                    logger.debug(
                        "core.model.Permissions.check_status.status_nok",
                        extra={"stav": self.permission_object.stav, "value": subed_status},
                    )
                    return False
        return True

    def check_ownership(self, ownership):
        """
        Ověří ownership. v aplikaci.

        :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if ownership:
            if not self.permission_object:
                self.get_permission_object()
            if self.permission_object == "error":
                return True
            if (
                self.permission_object.get_create_user()
                and self.logged_in_user in self.permission_object.get_create_user()
            ):
                return True
            if ownership == self.ownershipChoices.our:
                if self.logged_in_user.organizace in self.permission_object.get_create_org():
                    return True
            return False
        return True

    def check_accessibility(self):
        """
        Ověří accessibility. v aplikaci.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if self.accessibility:
            if not self.check_ownership(self.accessibility):
                permission_object_pristupnost = self.permission_object.pristupnost.pk
                try:
                    if not self.logged_in_user.hlavni_role.pk >= self.pristupnost_to_groups.get(
                        permission_object_pristupnost
                    ):
                        return False
                except Exception as e:
                    logger.debug("core.model.Permissions.check_accessibility.error", extra={"error": e})
                    return False
        return True

    def check_permission_skip(self):
        """
        Ověří permission skip.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if not self.permission_object:
            self.get_permission_object()
            if self.permission_object == "error":
                return True
        perm_skips = list(PermissionsSkip.objects.filter(user=self.logged_in_user).values_list("ident_list", flat=True))
        if len(perm_skips) > 0:
            try:
                id = self.permission_object.ident_cely
            except Exception as e:
                logger.debug("core.model.Permissions.check_permission_skip.error", extra={"error": e})
                try:
                    id = self.permission_object.id
                except Exception as e:
                    logger.debug(
                        "core.model.Permissions.check_permission_skip.permission_object_error", extra={"error": e}
                    )
                    id = None
            finally:
                if id in perm_skips[0].split(","):
                    return True
        return False

    def get_permission_object(self):
        """Vrací permission object."""
        from core.ident_cely import get_record_from_ident
        from pas.models import UzivatelSpoluprace

        if "spoluprace/" in self.address_in_app:
            self.permission_object = UzivatelSpoluprace.objects.get(id=self.ident)
        elif "nalez/smazat" in self.address_in_app:
            if self.typ == "objekt":
                self.permission_object = NalezObjekt.objects.get(id=self.ident).get_permission_object()
            elif self.typ == "predmet":
                self.permission_object = NalezPredmet.objects.get(id=self.ident).get_permission_object()
            else:
                self.object = get_record_from_ident(self.ident)
                self.permission_object = self.object.get_permission_object()
        elif "notifikace-projekty/smazat" in self.address_in_app:
            self.permission_object = Pes.objects.get(id=self.ident)
        elif "pian/stav/potvrdit" in self.address_in_app:
            self.object = get_record_from_ident(self.ident)
            self.permission_object = self.object.pian
        else:
            try:
                self.object = get_record_from_ident(self.ident)
                self.permission_object = self.object.get_permission_object()
            except Exception as e:
                logger.warning(
                    "core.models.Permission.get_permission_object.object_error",
                    extra={"error": e, "ident_cely": self.ident},
                )
                self.permission_object = "error"

    def permission_override(self):
        """
        Metoda pro uplatneni specifickych obejiti opravneni podle nazvu akce.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if self.action in [self.actionChoices.soubor_nahled_dokument, self.actionChoices.soubor_stahnout_dokument]:
            if (
                self.logged_in_user.organizace.cteni_dokumentu
                and self.logged_in_user.hlavni_role.pk == ROLE_ARCHEOLOG_ID
            ):
                return True
            else:
                return False


def check_permissions(action, user, ident=None, skip_status=False):
    """
    Ověří permissions. v aplikaci.

    :param action: Identifikátor akce, která se má provést.
    :param user: Parametr ``user`` se předává do volání ``filter()``, ``append()``, pracuje se s atributy ``hlavni_role``.
    :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
    :param skip_status: Pokud ``True``, přeskočí stavovou podmínku při vyhodnocení konkrétního oprávnění.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
    """
    permission_set = Permissions.objects.filter(
        main_role=user.hlavni_role,
        action=action,
    )

    logger.debug("core.model.check_permissions.checking_action_permission", extra={"value": permission_set})
    if permission_set.count() > 0:
        tested = []
        for concrete_permission in permission_set:
            tested.append(concrete_permission.check_concrete_permission(user, ident, skip_status=skip_status))
        if not any(tested):
            return False
    return True


class PermissionsSkip(models.Model):
    """Implementuje komponentu ``PermissionsSkip`` v rámci aplikace."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ident_list = models.TextField()

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        verbose_name = _("core.model.permissionsSkip.modelTitle.label")
        verbose_name_plural = _("core.model.permissionsSkip.modelTitles.label")
