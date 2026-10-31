"""Ověření bezeztrátového přepisu JPEG metadat a odmítnutí vadných hlaviček."""

import io
import unittest

from core.models import Soubor
from PIL import Image


class JpegMetadataTests(unittest.TestCase):
    """Přepis APP1 nesmí změnit jiné segmenty ani komprimované skeny."""

    def test_other_app_segments_and_scans_are_preserved(self):
        """XMP, ICC a komentář se zachovají doslova i při změně EXIF."""
        old_exif = Image.Exif()
        old_exif[271] = "Old camera"
        stream = io.BytesIO()
        Image.new("RGB", (32, 24)).save(stream, format="JPEG", exif=old_exif)
        original = stream.getvalue()
        extras = b""
        for marker, payload in (
            (b"\xff\xe1", b"http://ns.adobe.com/xap/1.0/\x00xmp"),
            (b"\xff\xe2", b"ICC_PROFILE\x00\x01\x01profile"),
            (b"\xff\xfe", b"comment"),
        ):
            extras += marker + (len(payload) + 2).to_bytes(2, "big") + payload
        original = original[:2] + extras + original[2:]
        new_exif = Image.Exif()
        new_exif[271] = "New camera"
        result = Soubor.replace_exif(original, new_exif.tobytes())
        self.assertIn(extras, result)
        self.assertEqual(result.split(b"\xff\xda", 1)[1], original.split(b"\xff\xda", 1)[1])
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.size, (32, 24))
            self.assertEqual(image.getexif()[271], "New camera")

    def test_incomplete_or_invalid_headers_are_rejected(self):
        """Neúplná délka, segment mimo soubor a chybějící sken nesmí vytvořit JPEG."""
        for content in (
            b"invalid",
            b"\xff\xd8",
            b"\xff\xd8\xff",
            b"\xff\xd8\xff\xe1\x00",
            b"\xff\xd8\xff\xe1\x00\x10Exif",
            b"\xff\xd8\xff\xe1\x00\x01",
            b"\xff\xd8\xff\xd9",
            b"\xff\xd8data",
        ):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    Soubor.replace_exif(content, Image.Exif().tobytes())

    def test_oversized_exif_is_rejected(self):
        """EXIF přesahující 16bitovou délku APP1 se nesmí zapsat jako vadná hlavička."""
        with self.assertRaises(ValueError):
            Soubor.replace_exif(b"\xff\xd8\xff\xda", b"Exif\x00\x00" + b"x" * 65535)
