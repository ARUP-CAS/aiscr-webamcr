"""Regrese GPS v HEIF, včetně vedlejších obrázků a chybného EXIF."""

import io
import unittest
from unittest.mock import patch

import piexif
import pillow_heif
from core.models import Soubor
from PIL import Image


class HeifGpsTests(unittest.TestCase):
    """Kontroluje skutečné kódování i dekódování HEIF bez databáze a Fedory."""

    def _photo(self, gps_frames):
        """Vytvoří kontejner s GPS jen ve vybraných obrázcích."""
        images = pillow_heif.HeifFile()
        for gps in gps_frames:
            image = Image.new("RGB", (32, 32), "red")
            image.info["exif"] = piexif.dump(
                {
                    "0th": {piexif.ImageIFD.Make: b"Test camera"},
                    "GPS": {1: b"N", 2: ((50, 1), (5, 1), (0, 1))} if gps else {},
                }
            )
            images.add_from_pillow(image)
        content = io.BytesIO()
        images.save(content)
        content.seek(0)
        return content

    def test_all_frames_are_cleaned(self):
        """GPS zmizí i z vedlejších obrázků, ostatní EXIF a počet obrázků zůstanou."""
        for frames in ((True,), (True, True), (False, True)):
            with self.subTest(frames=frames):
                content = self._photo(frames)
                original = pillow_heif.open_heif(content)
                self.assertTrue(any(piexif.load(image.info["exif"])["GPS"] for image in original))
                content.seek(0)
                result = Soubor.remove_heif_gps_data(content)
                self.assertEqual(result.tell(), 0)
                stored = pillow_heif.open_heif(result)
                self.assertEqual(len(stored), len(frames))
                for image in stored:
                    exif = piexif.load(image.info["exif"])
                    self.assertFalse(exif["GPS"])
                    self.assertEqual(exif["0th"][piexif.ImageIFD.Make], b"Test camera")

    def test_clean_file_is_unchanged(self):
        """Soubor bez GPS nevyžaduje opětovné kódování."""
        content = self._photo((False,))
        original = content.getvalue()
        self.assertIs(Soubor.remove_heif_gps_data(content), content)
        self.assertEqual(content.getvalue(), original)
        self.assertEqual(content.tell(), 0)

    def test_encoder_failure_does_not_return_original(self):
        """Selhání kodéru zastaví zpracování místo předání originálu s GPS."""
        content = self._photo((True,))
        with patch.object(pillow_heif.HeifFile, "save", side_effect=RuntimeError("encoder unavailable")):
            with self.assertRaises(RuntimeError):
                Soubor.remove_heif_gps_data(content)

    def test_detection_resets_stream(self):
        """Detekce HEIF i jiného formátu ponechá stream připravený ke čtení."""
        for content, expected in ((self._photo((True,)), True), (io.BytesIO(b"not heif"), False)):
            content.seek(3)
            self.assertEqual(Soubor.is_heif(content), expected)
            self.assertEqual(content.tell(), 0)
