"""Regrese odstranění GPS z JPEG nad limitem pixelů Pillow (issue #4229)."""

import io
from unittest import mock

import piexif
from core.models import Soubor
from django.test import SimpleTestCase
from PIL import Image, JpegImagePlugin


class LargeJpegGpsTests(SimpleTestCase):
    """Čištění JPEG nesmí dekódovat pixely ani změnit rozlišení fotografie."""

    @staticmethod
    def _photo(gps=True):
        """Vytvoří JPEG s GPS a nesouvisejícími EXIF údaji.

        :param gps: Zda do fotografie vložit GPS souřadnice.
        :return: Stream fotografie na začátku.
        """
        metadata = {"0th": {piexif.ImageIFD.Make: b"Test camera", piexif.ImageIFD.Orientation: 6}}
        if gps:
            metadata["GPS"] = {1: b"N", 2: ((50, 1), (5, 1), (0, 1))}
        content = io.BytesIO()
        Image.effect_noise((96, 64), 50).convert("RGB").save(
            content, format="JPEG", exif=piexif.dump(metadata), quality=93
        )
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
        metadata = piexif.load(result.getvalue())
        self.assertFalse(metadata["GPS"])
        self.assertEqual(metadata["0th"][piexif.ImageIFD.Make], b"Test camera")
        self.assertEqual(metadata["0th"][piexif.ImageIFD.Orientation], 6)
        # SOS a následující komprimovaná data musí zůstat doslova stejná.
        self.assertEqual(result.getvalue().split(b"\xff\xda", 1)[1], original.split(b"\xff\xda", 1)[1])
        with Image.open(result) as image:
            self.assertEqual(image.size, (96, 64))

    def test_regular_jpeg_also_preserves_compressed_image_data(self):
        """Běžný JPEG se při odstranění GPS také nesmí ztrátově rekomprimovat."""
        content = self._photo()
        original = content.getvalue()
        result = Soubor.remove_gps_data(content)
        self.assertFalse(piexif.load(result.getvalue())["GPS"])
        self.assertEqual(result.getvalue().split(b"\xff\xda", 1)[1], original.split(b"\xff\xda", 1)[1])

    def test_large_jpeg_without_gps_is_unchanged(self):
        """JPEG bez GPS se vrací beze změny i nad limitem pixelů."""
        content = self._photo(gps=False)
        original = content.getvalue()
        with mock.patch.object(Image, "MAX_IMAGE_PIXELS", 100):
            self.assertIs(Soubor.remove_gps_data(content), content)
        self.assertEqual(content.tell(), 0)
        self.assertEqual(content.getvalue(), original)
