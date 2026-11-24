"""Skutečné velké fotografie pro kontrolu GPS bez snížení limitu Pillow (#4229)."""

import io
from unittest import mock

from core.exceptions import GpsDataRemovalError, GpsImageMemoryError, GpsImagePixelLimitError
from core.models import EXIF_GPS_IFD_TAG, Soubor
from django.test import SimpleTestCase
from PIL import Image, JpegImagePlugin, PngImagePlugin, TiffImagePlugin


class HighResolutionGpsTests(SimpleTestCase):
    """Ověřuje odstranění GPS z reálně zakódovaných fotografií o 16 a 180 MP.

    Jednobarevné šedotónové předlohy omezují paměť a velikost testovacích dat,
    jejich rozměry i zakódované obrazové řádky však odpovídají skutečné fotografii.
    Soubory se vytvářejí postupně v paměti a neukládají se do repozitáře.
    """

    def _check_cleanup(self, fmt, size, opener):
        """Vytvoří celý obrázek, odstraní GPS a nezávisle zkontroluje jeho metadata.

        :param fmt: Výstupní formát JPEG, PNG nebo TIFF.
        :param size: Skutečné rozměry předlohy v pixelech.
        :param opener: Dekodér formátu pro kontrolu hlaviček bez globálního limitu Pillow.
        """
        metadata = Image.Exif()
        metadata[271] = "Test camera"
        metadata[EXIF_GPS_IFD_TAG] = {1: "N", 2: (50.0, 5.0, 0.0)}
        content = io.BytesIO()
        with Image.new("L", size, 127) as image:
            image.save(content, format=fmt, exif=metadata.tobytes())
        content.seek(0)
        # Pouze kontrola metadat používá přímý dekodér. Produkční kód ani limit se nemockují.
        with opener(io.BytesIO(content.getvalue())) as original:
            self.assertEqual(original.size, size)
            self.assertTrue(original.getexif().get_ifd(EXIF_GPS_IFD_TAG))

        result = Soubor.remove_gps_data(content)

        self.assertEqual(result.tell(), 0)
        with opener(result) as cleaned:
            self.assertEqual(cleaned.size, size)
            self.assertFalse(cleaned.getexif().get_ifd(EXIF_GPS_IFD_TAG))
            self.assertEqual(cleaned.getexif()[271], "Test camera")

    def test_large_jpeg(self):
        """JPEG o 16 MP se předá bez GPS a se zachovanými rozměry."""
        self._check_cleanup("JPEG", (4096, 4096), JpegImagePlugin.JpegImageFile)

    def test_huge_jpeg(self):
        """JPEG o 180 MP překračuje výchozí chybový limit Pillow a musí přijít o GPS."""
        self._check_cleanup("JPEG", (15000, 12000), JpegImagePlugin.JpegImageFile)

    def test_large_png(self):
        """PNG o 16 MP se předá bez GPS a se zachovanými rozměry."""
        self._check_cleanup("PNG", (4096, 4096), PngImagePlugin.PngImageFile)

    def test_huge_png(self):
        """PNG o 180 MP se nesmí předat s původními GPS souřadnicemi."""
        self._check_cleanup("PNG", (15000, 12000), PngImagePlugin.PngImageFile)

    def test_large_tiff(self):
        """TIFF o 16 MP se předá bez GPS a se zachovanými rozměry."""
        self._check_cleanup("TIFF", (4096, 4096), TiffImagePlugin.TiffImageFile)

    def test_huge_tiff(self):
        """TIFF o 180 MP se nesmí předat s původními GPS souřadnicemi."""
        self._check_cleanup("TIFF", (15000, 12000), TiffImagePlugin.TiffImageFile)

    def test_unreadable_image_is_rejected(self):
        """Chyba čtení nesmí předat původní soubor k archivaci."""
        with self.assertRaises(GpsDataRemovalError):
            Soubor.remove_gps_data(io.BytesIO(b"invalid image"))

    def test_decode_limit_rejects_image_without_changing_pillow_limit(self):
        """Překročení lokálního stropu odmítne obrázek a nezmění globální nastavení."""
        content = io.BytesIO()
        with Image.new("L", (32, 32)) as image:
            image.save(content, format="PNG")
        pillow_limit = Image.MAX_IMAGE_PIXELS
        with mock.patch.object(Soubor, "GPS_MAX_DECODE_PIXELS", 100):
            with self.assertRaises(GpsDataRemovalError) as raised:
                Soubor.remove_gps_data(content)
        self.assertIsInstance(raised.exception.__cause__, GpsImagePixelLimitError)
        self.assertEqual(Image.MAX_IMAGE_PIXELS, pillow_limit)

    def test_remaining_gps_in_encoded_output_is_rejected(self):
        """Kontrola výstupu nesmí přijmout kodér, který vrátí původní GPS."""
        content = io.BytesIO()
        metadata = Image.Exif()
        metadata[EXIF_GPS_IFD_TAG] = {1: "N", 2: (50.0, 5.0, 0.0)}
        with Image.new("L", (32, 32)) as image:
            image.save(content, format="PNG", exif=metadata)
        original = content.getvalue()
        with mock.patch.object(Image.Image, "save", side_effect=lambda output, **kwargs: output.write(original)):
            with self.assertRaises(GpsDataRemovalError):
                Soubor.remove_gps_data(content)

    def test_encoder_failure_is_rejected(self):
        """Selhání zápisu PNG nesmí vrátit soubor s GPS."""
        content = io.BytesIO()
        metadata = Image.Exif()
        metadata[EXIF_GPS_IFD_TAG] = {1: "N", 2: (50.0, 5.0, 0.0)}
        with Image.new("L", (32, 32)) as image:
            image.save(content, format="PNG", exif=metadata)
        content.seek(0)
        with mock.patch.object(Image.Image, "save", side_effect=OSError("encoder failed")):
            with self.assertRaises(GpsDataRemovalError):
                Soubor.remove_gps_data(content)

    def test_cleanup_failures_keep_their_log_category(self):
        """Limit pixelů, nedostatek paměti a jiné chyby mají rozlišitelnou příčinu."""
        for error, reason in (
            (Image.DecompressionBombError("pixels"), "pixel_limit"),
            (MemoryError(), "out_of_memory"),
            (OSError("unreadable"), "error"),
        ):
            with self.subTest(reason=reason):
                with mock.patch.object(Soubor, "_open_image_for_gps", side_effect=error):
                    with self.assertLogs("core.models", level="ERROR") as logs:
                        with self.assertRaises(GpsDataRemovalError) as raised:
                            Soubor.remove_gps_data(io.BytesIO(b"invalid"))
                self.assertEqual(getattr(logs.records[0], "reason", None), reason)
                self.assertEqual(getattr(raised.exception, "reason", None), reason)
                self.assertIs(raised.exception.__cause__, error)
                if reason == "out_of_memory":
                    self.assertIsInstance(raised.exception, GpsImageMemoryError)
                elif reason == "pixel_limit":
                    self.assertIsInstance(raised.exception, GpsImagePixelLimitError)
