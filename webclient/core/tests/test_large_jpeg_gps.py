"""Regrese odstranění GPS z JPEG nad limitem pixelů Pillow (issue #4229)."""

import io
import struct
from unittest import mock

from core.models import EXIF_GPS_IFD_TAG, Soubor
from django.test import SimpleTestCase
from PIL import ExifTags, Image, JpegImagePlugin


class LargeJpegGpsTests(SimpleTestCase):
    """Čištění JPEG nesmí dekódovat pixely ani změnit rozlišení fotografie."""

    @staticmethod
    def _photo(gps=True):
        """Vytvoří JPEG s GPS a nesouvisejícími EXIF údaji.

        :param gps: Zda do fotografie vložit GPS souřadnice.
        :return: Stream fotografie na začátku.
        """
        metadata = Image.Exif()
        metadata[271] = "Test camera"
        metadata[274] = 6
        if gps:
            metadata[EXIF_GPS_IFD_TAG] = {1: "N", 2: (50.0, 5.0, 0.0)}
        content = io.BytesIO()
        Image.effect_noise((96, 64), 50).convert("RGB").save(content, format="JPEG", exif=metadata, quality=93)
        content.seek(0)
        return content

    def test_large_jpeg_loses_gps_without_decoding_or_recompressing(self):
        """GPS zmizí i nad limitem; EXIF, rozlišení a komprimovaná obrazová data se zachovají."""
        content = self._photo()
        original = content.getvalue()
        # Limit je nižší než polovina počtu pixelů, takže běžné Image.open selže.
        with (
            mock.patch.object(Image, "MAX_IMAGE_PIXELS", 100),
            mock.patch.object(JpegImagePlugin.JpegImageFile, "load", side_effect=AssertionError("Pixel decoding")),
        ):
            result = Soubor.remove_gps_data(content)
            self.assertEqual(Image.MAX_IMAGE_PIXELS, 100)
        self.assertEqual(result.tell(), 0)
        metadata = JpegImagePlugin.JpegImageFile(result).getexif()
        self.assertNotIn(EXIF_GPS_IFD_TAG, metadata)
        self.assertEqual(metadata[271], "Test camera")
        self.assertEqual(metadata[274], 6)
        # SOS a následující komprimovaná data musí zůstat doslova stejná.
        self.assertEqual(result.getvalue().split(b"\xff\xda", 1)[1], original.split(b"\xff\xda", 1)[1])
        with Image.open(result) as image:
            self.assertEqual(image.size, (96, 64))

    def test_regular_jpeg_also_preserves_compressed_image_data(self):
        """Běžný JPEG se při odstranění GPS také nesmí ztrátově rekomprimovat."""
        content = self._photo()
        original = content.getvalue()
        result = Soubor.remove_gps_data(content)
        self.assertNotIn(EXIF_GPS_IFD_TAG, JpegImagePlugin.JpegImageFile(result).getexif())
        self.assertEqual(result.getvalue().split(b"\xff\xda", 1)[1], original.split(b"\xff\xda", 1)[1])

    def test_large_jpeg_without_gps_is_unchanged(self):
        """JPEG bez GPS se vrací beze změny i nad limitem pixelů."""
        content = self._photo(gps=False)
        original = content.getvalue()
        with mock.patch.object(Image, "MAX_IMAGE_PIXELS", 100):
            self.assertIs(Soubor.remove_gps_data(content), content)
        self.assertEqual(content.tell(), 0)
        self.assertEqual(content.getvalue(), original)

    def test_nonstandard_exif_is_preserved_when_gps_is_removed(self):
        """Nestandardní EXIF ani MakerNote se při odstranění GPS nezahodí."""
        metadata = Image.Exif()
        metadata[EXIF_GPS_IFD_TAG] = {1: "N", 2: (50.0, 5.0, 0.0)}
        metadata[34665] = {37890: b"private", 37500: b"maker-note"}
        content = io.BytesIO()
        Image.new("RGB", (32, 24)).save(content, format="JPEG", exif=metadata)
        result = Soubor.remove_gps_data(content)
        with Image.open(result) as image:
            cleaned = image.getexif()
            self.assertNotIn(EXIF_GPS_IFD_TAG, cleaned)
            self.assertEqual(cleaned.get_ifd(34665)[37890], b"private")
            self.assertEqual(cleaned.get_ifd(34665)[37500], b"maker-note")

    def test_multiple_exif_segments_are_rejected(self):
        """Další EXIF segment nesmí skrýt GPS za prvními metadaty bez GPS."""
        from core.exceptions import GpsDataRemovalError

        original = self._photo(gps=False).getvalue()
        secondary = Image.Exif()
        secondary[EXIF_GPS_IFD_TAG] = {1: "N", 2: (50.0, 5.0, 0.0)}
        payload = secondary.tobytes()
        secondary_segment = b"\xff\xe1" + (len(payload) + 2).to_bytes(2, "big") + payload
        with self.assertRaises(GpsDataRemovalError):
            Soubor.remove_gps_data(io.BytesIO(original[:2] + secondary_segment + original[2:]))

    def test_malformed_gps_directory_is_rejected_during_open(self):
        """Varování při otevření nesmí uložit původní fotografii jako soubor bez GPS."""
        from core.exceptions import GpsDataRemovalError

        metadata = Image.Exif()
        metadata[EXIF_GPS_IFD_TAG] = {1: "N", 2: (50.0, 5.0, 0.0)}
        raw = bytearray(metadata.tobytes())
        endian = ">" if raw[6:8] == b"MM" else "<"
        first = 6 + struct.unpack_from(endian + "I", raw, 10)[0]
        struct.pack_into(endian + "I", raw, first + 6, 100000)
        content = io.BytesIO()
        Image.new("RGB", (16, 16)).save(content, format="JPEG", exif=bytes(raw))
        with self.assertRaises(GpsDataRemovalError):
            Soubor.remove_gps_data(content)

    def test_secondary_directory_and_embedded_thumbnail_are_preserved(self):
        """Čištění GPS zachová popis, orientaci a JPEG uložený v sekundárním EXIF."""
        metadata = Image.Exif()
        metadata[271] = "Camera"
        metadata[EXIF_GPS_IFD_TAG] = {1: "N", 2: (50.0, 5.0, 0.0)}
        raw = bytearray(metadata.tobytes())
        endian = ">" if raw[6:8] == b"MM" else "<"
        first = 6 + struct.unpack_from(endian + "I", raw, 10)[0]
        count = struct.unpack_from(endian + "H", raw, first)[0]
        secondary_offset = len(raw) - 6
        struct.pack_into(endian + "I", raw, first + 2 + count * 12, secondary_offset)
        thumbnail = io.BytesIO()
        Image.new("RGB", (8, 4), "red").save(thumbnail, format="JPEG")
        # Čtyři ručně sestavené IFD1 položky a nulový odkaz na další adresář.
        raw.extend(struct.pack(endian + "H", 4))
        raw.extend(struct.pack(endian + "HHI4s", 270, 2, 4, b"old\0"))
        raw.extend(struct.pack(endian + "HHI", 274, 3, 1) + struct.pack(endian + "H", 3) + b"\0\0")
        raw.extend(struct.pack(endian + "HHII", 513, 4, 1, secondary_offset + 54))
        raw.extend(struct.pack(endian + "HHII", 514, 4, 1, len(thumbnail.getvalue())))
        raw.extend(struct.pack(endian + "I", 0))
        raw.extend(thumbnail.getvalue())
        content = io.BytesIO()
        Image.new("RGB", (32, 24)).save(content, format="JPEG", exif=bytes(raw))
        result = Soubor.remove_gps_data(content)
        with Image.open(result) as image:
            cleaned = image.getexif()
            self.assertNotIn(EXIF_GPS_IFD_TAG, cleaned)
            secondary = cleaned.get_ifd(ExifTags.IFD.IFD1)
            self.assertEqual(secondary[270], "old")
            self.assertEqual(secondary[274], 3)
            cleaned.fp.seek(secondary[513])
            self.assertEqual(cleaned.fp.read(secondary[514]), thumbnail.getvalue())
