"""
Testy generování náhledů v ``FedoraRepositoryConnector.__generate_thumb`` (issue #4229).

Fotografie s vysokým počtem pixelů dřív tiše dostaly místo náhledu ikonu typu (``jpg.png``):
``Image.open`` nad výchozím limitem Pillow vyvolal ``DecompressionBombError``, výjimka se
zalogovala jen na úrovni ``info`` a zpracování pokračovalo ikonou. Limit Pillow se v testech
snižuje přes ``Image.MAX_IMAGE_PIXELS``, aby nebylo nutné vyrábět obrázek nad 179 MP.

Ikony mají 512x512 px, zdrojové obrázky 900x600 px - podle poměru stran náhledu se proto
pozná, zda vznikl z obrázku, nebo z ikony. Snížený limit leží mezi oběma počty pixelů, aby
selhal zdrojový obrázek, ale ne ikona, ze které se dělá náhradní náhled.
"""

import io
from unittest import mock

from core import repository_connector
from core.repository_connector import THUMB_MAX_PX, FedoraRepositoryConnector, ThumbFailureReason
from django.test import SimpleTestCase
from PIL import Image

_generate_thumb = FedoraRepositoryConnector._FedoraRepositoryConnector__generate_thumb

#: Limit Pillow, nad jehož dvojnásobkem ``Image.open`` vyvolá ``DecompressionBombError``:
#: 300 000 px, tedy nad ikonou (262 144 px) a pod zdrojovým obrázkem (540 000 px).
_NIZKY_LIMIT_PILLOW = 150_000


def _rozmer_nahledu(rozmer: tuple) -> tuple:
    """
    Spočítá rozměr malého náhledu týmž ``Image.thumbnail``, jaký používá aplikace.

    :param rozmer: Rozměr předlohy ``(sirka, vyska)``.
    :return: Rozměr náhledu ``(sirka, vyska)``.
    """
    obrazek = Image.new("RGB", rozmer)
    obrazek.thumbnail((THUMB_MAX_PX, THUMB_MAX_PX))
    return obrazek.size


#: Rozměr malého náhledu zdrojového obrázku 900x600.
_NAHLED_Z_OBRAZKU = _rozmer_nahledu((900, 600))
#: Rozměr malého náhledu vyrobeného ze čtvercové ikony 512x512.
_NAHLED_Z_IKONY = _rozmer_nahledu((512, 512))


def _obrazek(fmt: str, orientace: int = None) -> io.BytesIO:
    """
    Vyrobí obrázek 900x600 px v daném formátu.

    :param fmt: Formát pro ``PIL.Image.save`` (``JPEG``, ``PNG``).
    :param orientace: Hodnota EXIF tagu Orientation (0x0112); ``None`` tag nevloží.
    :return: Pozicovaný stream s daty obrázku.
    """
    exif = Image.Exif()
    if orientace is not None:
        exif[0x0112] = orientace
    buf = io.BytesIO()
    Image.new("RGB", (900, 600), (200, 100, 50)).save(buf, format=fmt, exif=exif)
    buf.seek(0)
    return buf


def _rozmer(nahled: io.BytesIO) -> tuple:
    """
    Vrátí rozměr vygenerovaného náhledu.

    :param nahled: PNG náhled vrácený z ``__generate_thumb``.
    :return: Dvojice ``(sirka, vyska)``.
    """
    return Image.open(nahled).size


class GenerateThumbVelkyObrazekTest(SimpleTestCase):
    """Náhled obrázku nad limitem pixelů vznikne z obrázku, nebo je selhání v logu rozpoznatelné."""

    def test_jpeg_nad_limitem_pillow_dostane_skutecny_nahled(self):
        """JPEG nad výchozím limitem Pillow se dekóduje zmenšeně a náhled vznikne z obrázku, ne z ikony."""
        with mock.patch.object(Image, "MAX_IMAGE_PIXELS", _NIZKY_LIMIT_PILLOW):
            with self.assertNoLogs("core.repository_connector", level="WARNING"):
                nahled = _generate_thumb("foto.jpg", _obrazek("JPEG"), large=False)
        self.assertEqual(_rozmer(nahled), _NAHLED_Z_OBRAZKU)

    def test_exif_orientace_se_uplatni_i_po_zmenseni(self):
        """Otočení podle EXIF se provede i po přesunu ``exif_transpose`` za ``thumbnail``."""
        nahled = _generate_thumb("foto.jpg", _obrazek("JPEG", orientace=6), large=False)
        self.assertEqual(_rozmer(nahled), tuple(reversed(_NAHLED_Z_OBRAZKU)))

    def test_jpeg_nad_stropem_nahledu_skonci_ikonou_s_duvodem(self):
        """JPEG nad ``THUMB_JPEG_MAX_PIXELS`` dostane ikonu a selhání je v logu s důvodem ``pixel_limit``."""
        with mock.patch.object(Image, "MAX_IMAGE_PIXELS", _NIZKY_LIMIT_PILLOW), mock.patch.object(
            repository_connector, "THUMB_JPEG_MAX_PIXELS", 2 * _NIZKY_LIMIT_PILLOW
        ):
            with self.assertLogs("core.repository_connector", level="WARNING") as logy:
                nahled = _generate_thumb("foto.jpg", _obrazek("JPEG"), large=False)
        self.assertEqual(_rozmer(nahled), _NAHLED_Z_IKONY)
        self.assertEqual(logy.records[0].reason, ThumbFailureReason.PIXEL_LIMIT.value)
        self.assertEqual(logy.records[0].mime_type, "image/jpeg")

    def test_png_nad_limitem_pillow_skonci_ikonou_s_duvodem(self):
        """Jiný formát než JPEG se dekóduje celý, proto pro něj zůstává výchozí limit Pillow."""
        with mock.patch.object(Image, "MAX_IMAGE_PIXELS", _NIZKY_LIMIT_PILLOW):
            with self.assertLogs("core.repository_connector", level="WARNING") as logy:
                nahled = _generate_thumb("foto.png", _obrazek("PNG"), large=False)
        self.assertEqual(_rozmer(nahled), _NAHLED_Z_IKONY)
        self.assertEqual(logy.records[0].reason, ThumbFailureReason.PIXEL_LIMIT.value)

    def test_vycerpani_pameti_se_v_logu_odlisi(self):
        """``MemoryError`` při otevření obrázku se zaloguje s důvodem ``out_of_memory``."""
        puvodni = repository_connector._open_image_for_thumb
        volani = iter([MemoryError()])

        def _otevri(image):
            chyba = next(volani, None)
            if chyba is not None:
                raise chyba
            return puvodni(image)

        with mock.patch.object(repository_connector, "_open_image_for_thumb", side_effect=_otevri):
            with self.assertLogs("core.repository_connector", level="WARNING") as logy:
                nahled = _generate_thumb("foto.jpg", _obrazek("JPEG"), large=False)
        self.assertEqual(_rozmer(nahled), _NAHLED_Z_IKONY)
        self.assertEqual(logy.records[0].reason, ThumbFailureReason.OUT_OF_MEMORY.value)

    def test_other_error_is_logged_separately(self):
        """Jiná chyba dekodéru nesmí být zaměněna za paměť ani limit pixelů."""
        original = repository_connector._open_image_for_thumb
        calls = iter([OSError("invalid image")])

        def open_image(image):
            error = next(calls, None)
            if error is not None:
                raise error
            return original(image)

        with mock.patch.object(repository_connector, "_open_image_for_thumb", side_effect=open_image):
            with self.assertLogs("core.repository_connector", level="WARNING") as logs:
                thumbnail = _generate_thumb("photo.jpg", _obrazek("JPEG"), large=False)
        self.assertEqual(_rozmer(thumbnail), _NAHLED_Z_IKONY)
        self.assertEqual(logs.records[0].reason, "error")
