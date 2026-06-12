"""
Testy detekce MIME typu pro :class:`core.models.Soubor`.

Pokrývají všechny formáty z mapy :meth:`Soubor.get_file_extension_by_mime`,
včetně formátů, u kterých došlo k regresi v ``libmagic >= 5.46``
(ZIP archivy s běžným obsahem, změna MIME pro RTF).
"""

import io
import os
import zipfile

import py7zr
from core.models import Soubor
from django.test import SimpleTestCase
from PIL import Image

RESOURCES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "projekt",
    "tests",
    "resources",
)


def _pillow_image(fmt: str) -> io.BytesIO:
    """
    Vygeneruje minimální obrázek pomocí Pillow a vrátí jej jako ``BytesIO``.

    :param fmt: Formát obrázku ve tvaru přijímaném ``PIL.Image.save`` (např. ``PNG``).
    :return: Pozicovaný stream s daty obrázku.
    """
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buf, format=fmt)
    buf.seek(0)
    return buf


def _zip_with(entries: dict, compression: int = zipfile.ZIP_DEFLATED) -> io.BytesIO:
    """
    Vytvoří v paměti ZIP archiv s danými soubory.

    :param entries: Mapování ``{nazev_souboru: obsah}`` (obsah jako ``str`` nebo ``bytes``).
    :param compression: Použitá komprese (např. ``ZIP_STORED`` pro nekomprimovaný obsah).
    :return: Pozicovaný stream s daty archivu.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression) as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    buf.seek(0)
    return buf


def _opendocument(mimetype: str, extra_entries: dict = None) -> io.BytesIO:
    """
    Sestaví minimální OpenDocument archiv.

    Specifikace ODF vyžaduje, aby ``mimetype`` byl **prvním** záznamem a **STORED**
    (bez komprese) — jinak jej ``libmagic`` neoznačí jako ODT/ODS.

    :param mimetype: Hodnota MIME typu zapsaná do souboru ``mimetype``.
    :param extra_entries: Další soubory přidávané do archivu (volitelně).
    :return: Pozicovaný stream s archivem.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(zipfile.ZipInfo("mimetype"), mimetype, compress_type=zipfile.ZIP_STORED)
        for name, content in (extra_entries or {}).items():
            zf.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)
    buf.seek(0)
    return buf


def _seven_zip_archive() -> io.BytesIO:
    """
    Vytvoří v paměti minimální platný 7z archiv pomocí ``py7zr``.

    Použito v testech ``check_mime_for_url``, které volají archive validation
    (``check_archive=True``) a vyžadují, aby šel archiv úspěšně otevřít.

    :return: Pozicovaný stream s archivem.
    """
    buf = io.BytesIO()
    with py7zr.SevenZipFile(buf, mode="w") as archive:
        archive.writestr(b"hello", "a.txt")
    buf.seek(0)
    return buf


def _fixture(name: str) -> io.BytesIO:
    """
    Načte fixtures z ``projekt/tests/resources/`` do ``BytesIO``.

    :param name: Název souboru ve složce resources.
    :return: Pozicovaný stream s obsahem souboru.
    """
    with open(os.path.join(RESOURCES_DIR, name), "rb") as fh:
        return io.BytesIO(fh.read())


class MimeDetectionTests(SimpleTestCase):
    """Ověřuje, že :meth:`Soubor.get_mime_types` vrátí očekávaný MIME typ pro každý formát."""

    def _assert_mime(self, label: str, file_obj: io.BytesIO, accepted: tuple):
        """
        Pomocná aserce: detekovaný MIME musí být v množině ``accepted``.

        :param label: Popisek formátu pro chybovou hlášku.
        :param file_obj: Vstupní stream se soubory.
        :param accepted: N-tice přijatelných MIME řetězců (vč. historických synonym).
        """
        with self.subTest(format=label):
            detected = Soubor.get_mime_types(file_obj)
            self.assertIn(
                detected,
                accepted,
                msg=f"{label}: očekáván jeden z {accepted}, detekováno {detected!r}",
            )

    def _assert_extension(self, label: str, file_obj: io.BytesIO, expected_ext: str):
        """
        Pomocná aserce: ``get_file_extension_by_mime`` musí obsahovat očekávanou příponu.

        :param label: Popisek formátu.
        :param file_obj: Vstupní stream.
        :param expected_ext: Přípona, která musí být ve výstupní n-tici.
        """
        with self.subTest(format=label):
            extensions = Soubor.get_file_extension_by_mime(file_obj)
            self.assertIn(
                expected_ext,
                extensions,
                msg=f"{label}: očekávána přípona {expected_ext!r} mezi {extensions}",
            )

    # === Rastr ===

    def test_png(self):
        """Ověří detekci PNG obrázku."""
        self._assert_mime("png", _pillow_image("PNG"), ("image/png",))
        self._assert_extension("png", _pillow_image("PNG"), "png")

    def test_jpeg(self):
        """Ověří detekci JPEG obrázku."""
        self._assert_mime("jpeg", _pillow_image("JPEG"), ("image/jpeg",))
        self._assert_extension("jpeg", _pillow_image("JPEG"), "jpg")

    def test_gif(self):
        """Ověří detekci GIF obrázku."""
        self._assert_mime("gif", _pillow_image("GIF"), ("image/gif",))
        self._assert_extension("gif", _pillow_image("GIF"), "gif")

    def test_bmp(self):
        """Ověří detekci BMP obrázku."""
        self._assert_mime("bmp", _pillow_image("BMP"), ("image/bmp",))
        self._assert_extension("bmp", _pillow_image("BMP"), "bmp")

    def test_tiff(self):
        """Ověří detekci TIFF obrázku."""
        self._assert_mime("tiff", _pillow_image("TIFF"), ("image/tiff",))
        self._assert_extension("tiff", _pillow_image("TIFF"), "tif")

    def test_svg(self):
        """Ověří detekci SVG obrázku."""
        svg = io.BytesIO(
            b'<?xml version="1.0"?>'
            b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
            b'<rect width="10" height="10" fill="red"/></svg>'
        )
        self._assert_mime("svg", svg, ("image/svg+xml", "image/svg"))
        svg.seek(0)
        self._assert_extension("svg", svg, "svg")

    # === Dokumenty ===

    def test_pdf(self):
        """Ověří detekci PDF dokumentu."""
        self._assert_mime("pdf", _fixture("test.pdf"), ("application/pdf",))
        self._assert_extension("pdf", _fixture("test.pdf"), "pdf")

    def test_doc(self):
        """Ověří detekci DOC (MS Word, formát OLE/CFB)."""
        self._assert_mime("doc", _fixture("test.doc"), ("application/msword",))
        self._assert_extension("doc", _fixture("test.doc"), "doc")

    def test_docx(self):
        """Ověří detekci DOCX (MS Word, formát OOXML)."""
        self._assert_mime(
            "docx",
            _fixture("test.docx"),
            ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",),
        )
        self._assert_extension("docx", _fixture("test.docx"), "docx")

    def test_xlsx(self):
        """Ověří detekci XLSX (MS Excel, formát OOXML)."""
        # Minimální XLSX = ZIP obsahující xl/workbook.xml a [Content_Types].xml
        data = _zip_with(
            {
                "[Content_Types].xml": (
                    '<?xml version="1.0"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>'
                ),
                "xl/workbook.xml": '<?xml version="1.0"?><workbook/>',
            }
        )
        self._assert_mime(
            "xlsx",
            data,
            ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",),
        )
        data.seek(0)
        self._assert_extension("xlsx", data, "xlsx")

    def test_odt(self):
        """Ověří detekci ODT (OpenDocument Text)."""
        data = _opendocument(
            "application/vnd.oasis.opendocument.text",
            {"content.xml": '<?xml version="1.0"?><document/>'},
        )
        self._assert_mime("odt", data, ("application/vnd.oasis.opendocument.text",))
        data.seek(0)
        self._assert_extension("odt", data, "odt")

    def test_ods(self):
        """Ověří detekci ODS (OpenDocument Spreadsheet)."""
        data = _opendocument(
            "application/vnd.oasis.opendocument.spreadsheet",
            {"content.xml": '<?xml version="1.0"?><document/>'},
        )
        self._assert_mime("ods", data, ("application/vnd.oasis.opendocument.spreadsheet",))
        data.seek(0)
        self._assert_extension("ods", data, "ods")

    def test_rtf(self):
        """Ověří detekci RTF dokumentu."""
        # libmagic vrací v různých verzích buď ``application/rtf`` nebo ``text/rtf``.
        rtf = io.BytesIO(b"{\\rtf1\\ansi\\deff0 Hello, world!}")
        self._assert_mime("rtf", rtf, ("application/rtf", "text/rtf"))
        rtf.seek(0)
        self._assert_extension("rtf", rtf, "rtf")

    # === Text ===

    def test_plain_text(self):
        """Ověří detekci prostého textu."""
        self._assert_mime("txt", io.BytesIO(b"hello world\n"), ("text/plain",))
        self._assert_extension("txt", io.BytesIO(b"hello world\n"), "txt")

    def test_csv(self):
        """Ověří detekci CSV souboru."""
        # libmagic potřebuje více řádků, aby rozpoznal CSV.
        csv = io.BytesIO(b"a,b,c\n1,2,3\n4,5,6\n7,8,9\n")
        self._assert_mime("csv", csv, ("text/csv",))
        csv.seek(0)
        self._assert_extension("csv", csv, "csv")

    # === Archivy ===

    def test_zip(self):
        """Ověří detekci běžného ZIP archivu (regresní test pro libmagic 5.46)."""
        # Regrese v libmagic 5.46: běžný ZIP s obsahem vrací ``application/octet-stream``.
        # Cíl: detekce musí fungovat i pro běžný archiv (vyžaduje fallback v get_mime_types).
        data = _zip_with({"a.txt": "hello", "b.txt": "world"})
        self._assert_mime(
            "zip",
            data,
            ("application/zip", "application/x-zip-compressed", "application/zip-compressed"),
        )
        data.seek(0)
        self._assert_extension("zip", data, "zip")

    def test_seven_zip(self):
        """Ověří detekci 7z archivu."""
        data = io.BytesIO(b"7z\xbc\xaf\x27\x1c\x00\x04" + b"\x00" * 64)
        self._assert_mime("7z", data, ("application/x-7z-compressed",))
        data.seek(0)
        self._assert_extension("7z", data, "7z")

    def test_rar(self):
        """Ověří detekci RAR archivu."""
        # RAR4 signatura.
        data = io.BytesIO(b"Rar!\x1a\x07\x00" + b"\x00" * 64)
        self._assert_mime(
            "rar",
            data,
            ("application/vnd.rar", "application/x-rar-compressed", "application/x-rar"),
        )
        data.seek(0)
        self._assert_extension("rar", data, "rar")


class ThumbIconTests(SimpleTestCase):
    """
    Ověřuje, že :meth:`Soubor.get_thumb_icon` vrací ne-None ikonu pro všechny formáty
    z whitelistů — regresní test pro libmagic 5.46, kdy ZIP/RTF detekce vrátila MIME,
    který v mapě ikon chyběl, a volající :func:`__generate_thumb_from_icon` pak padal
    na ``Image.open(None)``.
    """

    def _assert_has_icon(self, label: str, file_obj: io.BytesIO):
        """Pomocná aserce: ``get_thumb_icon`` musí vrátit nenulový stream s ikonou."""
        with self.subTest(format=label):
            file_obj.seek(0)
            thumb, mime = Soubor.get_thumb_icon(file_obj)
            self.assertIsNotNone(
                thumb,
                msg=f"{label}: chybí ikona pro detekovaný MIME {mime!r}",
            )

    def test_zip_has_icon(self):
        """ZIP s běžným obsahem (regrese libmagic 5.46) musí mít ikonu."""
        self._assert_has_icon("zip", _zip_with({"a.txt": "hello", "b.txt": "world"}))

    def test_rtf_has_icon(self):
        """RTF musí mít ikonu (libmagic 5.46 vrací ``text/rtf``)."""
        self._assert_has_icon("rtf", io.BytesIO(b"{\\rtf1\\ansi\\deff0 Hello, world!}"))

    def test_doc_has_icon(self):
        """DOC musí mít ikonu."""
        self._assert_has_icon("doc", _fixture("test.doc"))

    def test_docx_has_icon(self):
        """DOCX musí mít ikonu."""
        self._assert_has_icon("docx", _fixture("test.docx"))

    def test_pdf_has_icon(self):
        """PDF musí mít ikonu."""
        self._assert_has_icon("pdf", _fixture("test.pdf"))

    def test_jpeg_has_icon(self):
        """JPEG musí mít ikonu."""
        self._assert_has_icon("jpeg", _pillow_image("JPEG"))


class CheckMimeForUrlTests(SimpleTestCase):
    """
    Ověřuje, že :meth:`Soubor.check_mime_for_url` aplikuje správný whitelist MIME typů
    pro každou ze čtyř upload větví (``pas``, ``dokument``, ``model3d``, ``projekt``/výchozí).

    Whitelisty musí odpovídat seznamům přijímaných typů v ``static/js/dz.js``.
    """

    PAS_URL = "/soubor/nahrat/pas/123/"
    PAS_API_URL = "/api/pas/nalez/M-202400001-N00001/upload-foto"
    DOKUMENT_URL = "/soubor/nahrat/dokument/123/"
    MODEL3D_URL = "/soubor/nahrat/model3d/123/"
    PROJEKT_URL = "/soubor/nahrat/projekt/123/"

    def _check(self, url: str, file_obj: io.BytesIO) -> bool:
        """Pomocný wrapper, který před voláním resetuje pozici streamu."""
        file_obj.seek(0)
        return Soubor.check_mime_for_url(file_obj, source_url=url)

    # === PAS — povoleno: TIFF, JPEG, PNG, HEIC, HEIF ===

    def test_pas_accepts_jpeg(self):
        """JPEG je povolen v PAS uploadu."""
        self.assertTrue(self._check(self.PAS_URL, _pillow_image("JPEG")))

    def test_pas_accepts_png(self):
        """PNG je povolen v PAS uploadu."""
        self.assertTrue(self._check(self.PAS_URL, _pillow_image("PNG")))

    def test_pas_accepts_tiff(self):
        """TIFF je povolen v PAS uploadu."""
        self.assertTrue(self._check(self.PAS_URL, _pillow_image("TIFF")))

    def test_pas_rejects_pdf(self):
        """PDF v PAS uploadu nesmí projít."""
        self.assertFalse(self._check(self.PAS_URL, _fixture("test.pdf")))

    def test_pas_rejects_doc(self):
        """DOC v PAS uploadu nesmí projít."""
        self.assertFalse(self._check(self.PAS_URL, _fixture("test.doc")))

    def test_pas_rejects_bmp(self):
        """BMP v PAS uploadu nesmí projít (dříve propouštěl image/* fallback)."""
        self.assertFalse(self._check(self.PAS_URL, _pillow_image("BMP")))

    def test_pas_api_rejects_bmp(self):
        """Nová PAS API URL musí používat stejný MIME whitelist jako PAS upload."""
        self.assertFalse(self._check(self.PAS_API_URL, _pillow_image("BMP")))

    # === Dokument — povoleno: PDF, TIFF, JPEG, PNG, SVG, TXT, XLSX, CSV ===

    def test_dokument_accepts_pdf(self):
        """PDF je povolen v dokumentovém uploadu."""
        self.assertTrue(self._check(self.DOKUMENT_URL, _fixture("test.pdf")))

    def test_dokument_accepts_jpeg(self):
        """JPEG je povolen v dokumentovém uploadu."""
        self.assertTrue(self._check(self.DOKUMENT_URL, _pillow_image("JPEG")))

    def test_dokument_accepts_xlsx(self):
        """XLSX je povolen v dokumentovém uploadu."""
        xlsx = _zip_with(
            {
                "[Content_Types].xml": (
                    '<?xml version="1.0"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>'
                ),
                "xl/workbook.xml": '<?xml version="1.0"?><workbook/>',
            }
        )
        self.assertTrue(self._check(self.DOKUMENT_URL, xlsx))

    def test_dokument_accepts_csv(self):
        """CSV je povolen v dokumentovém uploadu."""
        csv = io.BytesIO(b"a,b,c\n1,2,3\n4,5,6\n7,8,9\n")
        self.assertTrue(self._check(self.DOKUMENT_URL, csv))

    def test_dokument_rejects_doc(self):
        """DOC v dokumentovém uploadu nesmí projít — Office formáty patří do projektu."""
        self.assertFalse(self._check(self.DOKUMENT_URL, _fixture("test.doc")))

    def test_dokument_rejects_zip(self):
        """ZIP v dokumentovém uploadu nesmí projít."""
        zip_data = _zip_with({"a.txt": "hello"})
        self.assertFalse(self._check(self.DOKUMENT_URL, zip_data))

    def test_dokument_rejects_bmp(self):
        """BMP v dokumentovém uploadu nesmí projít."""
        self.assertFalse(self._check(self.DOKUMENT_URL, _pillow_image("BMP")))

    # === Model3D — povoleno: PDF, TIFF, JPEG, PNG, SVG, ZIP, RAR, 7z ===

    def test_model3d_accepts_pdf(self):
        """PDF je povolen v model3D uploadu."""
        self.assertTrue(self._check(self.MODEL3D_URL, _fixture("test.pdf")))

    def test_model3d_accepts_zip(self):
        """ZIP je povolen v model3D uploadu (regresní test pro libmagic 5.46)."""
        zip_data = _zip_with({"model.obj": "v 0 0 0\n", "texture.png": b"\x89PNG\r\n\x1a\n"})
        self.assertTrue(self._check(self.MODEL3D_URL, zip_data))

    def test_model3d_accepts_7z(self):
        """7z je povolen v model3D uploadu."""
        self.assertTrue(self._check(self.MODEL3D_URL, _seven_zip_archive()))

    def test_model3d_rejects_doc(self):
        """DOC v model3D uploadu nesmí projít."""
        self.assertFalse(self._check(self.MODEL3D_URL, _fixture("test.doc")))

    def test_model3d_rejects_txt(self):
        """TXT v model3D uploadu nesmí projít."""
        self.assertFalse(self._check(self.MODEL3D_URL, io.BytesIO(b"hello world\n")))

    # === Projekt (else) — povoleno vše ostatní z whitelistu ===

    def test_projekt_accepts_doc(self):
        """DOC je povolen v projektovém uploadu (regresní test bug 1 — chybějící čárka)."""
        self.assertTrue(self._check(self.PROJEKT_URL, _fixture("test.doc")))

    def test_projekt_accepts_docx(self):
        """DOCX je povolen v projektovém uploadu."""
        self.assertTrue(self._check(self.PROJEKT_URL, _fixture("test.docx")))

    def test_projekt_accepts_zip(self):
        """ZIP je povolen v projektovém uploadu (regresní test pro libmagic 5.46)."""
        zip_data = _zip_with({"a.txt": "hello", "b.txt": "world"})
        self.assertTrue(self._check(self.PROJEKT_URL, zip_data))

    def test_projekt_accepts_rtf(self):
        """RTF je povolen v projektovém uploadu."""
        rtf = io.BytesIO(b"{\\rtf1\\ansi\\deff0 Hello, world!}")
        self.assertTrue(self._check(self.PROJEKT_URL, rtf))

    def test_projekt_accepts_csv(self):
        """CSV je povolen v projektovém uploadu (regresní test bug 1 — chybějící čárka)."""
        csv = io.BytesIO(b"a,b,c\n1,2,3\n4,5,6\n7,8,9\n")
        self.assertTrue(self._check(self.PROJEKT_URL, csv))

    def test_projekt_accepts_bmp(self):
        """BMP je povolen v projektovém uploadu."""
        self.assertTrue(self._check(self.PROJEKT_URL, _pillow_image("BMP")))

    def test_projekt_accepts_gif(self):
        """GIF je povolen v projektovém uploadu."""
        self.assertTrue(self._check(self.PROJEKT_URL, _pillow_image("GIF")))

    def test_projekt_accepts_odt(self):
        """ODT je povolen v projektovém uploadu."""
        odt = _opendocument(
            "application/vnd.oasis.opendocument.text",
            {"content.xml": '<?xml version="1.0"?><document/>'},
        )
        self.assertTrue(self._check(self.PROJEKT_URL, odt))

    def test_projekt_accepts_ods(self):
        """ODS je povolen v projektovém uploadu."""
        ods = _opendocument(
            "application/vnd.oasis.opendocument.spreadsheet",
            {"content.xml": '<?xml version="1.0"?><document/>'},
        )
        self.assertTrue(self._check(self.PROJEKT_URL, ods))

    def test_projekt_rejects_webp(self):
        """WebP obrázek v projektu nesmí projít — není v whitelistu."""
        self.assertFalse(self._check(self.PROJEKT_URL, _pillow_image("WEBP")))
