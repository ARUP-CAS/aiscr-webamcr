"""Regrese odmítnutí fotografií, jejichž GPS nelze bezpečně odstranit."""

import io
import json
import struct
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from api.views import _RECORD_LOCK_PREFIX, PasApiBaseView, SamostatnyNalezFotografieUploadView
from core import image_location
from core.constants import API_REQUEST_LOG_STATUS_FAILURE
from core.exceptions import GpsDataRemovalError
from core.models import Soubor
from core.repository_connector import FedoraTransactionStatus
from core.tests import location_fixtures as fx
from core.views import NewFileUploadView, UpdateExistingFileUploadView
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext as _
from pas.models import SamostatnyNalez
from PIL import ExifTags, Image, TiffTags


class GpsCleanupTests(unittest.TestCase):
    """Ověřuje chyby čištění i skutečný výstup podporovaných formátů."""

    @staticmethod
    def _photo(fmt="JPEG", gps=True):
        """Vytvoří fotografii se souřadnicemi nebo bez nich.

        :param fmt: Formát uložené fotografie.
        :param gps: Zda vložit GPS souřadnice do EXIF.
        :return: Stream fotografie na začátku.
        """
        content = io.BytesIO()
        Image.new("RGB", (32, 32), "red").save(content, format=fmt, exif=fx.exif_bytes(gps=gps))
        content.seek(0)
        return content

    FRAME_VALUES = (10, 128, 250)

    @classmethod
    def _multi_frame_tiff(cls, gps_frames, xmp_frames=None):
        """Ručně sestaví vícesnímkový TIFF s vlastním EXIF a GPS IFD v každém snímku.

        Pillow při zápisu dalších snímků nepřepočítá ukazatele na vnořené IFD, proto
        se testovací soubor skládá přímo podle specifikace TIFF.

        :param gps_frames: Indexy snímků, které dostanou GPS IFD se zeměpisnou šířkou.
        :param xmp_frames: Slovník index snímku → paket XMP uložený v tagu XMLPacket.
        :return: Stream little-endian TIFF na začátku; snímek ``i`` má výrobce ``Cam{i}``
            a jediný šedý pixel s hodnotou ``FRAME_VALUES[i]``.
        """
        data = bytearray(b"II*\x00\x00\x00\x00\x00")
        next_ifd_pointer = 4

        def append(chunk):
            offset = len(data)
            data.extend(chunk)
            if len(data) % 2:
                data.append(0)
            return offset

        def entry(tag, field_type, count, value):
            packed_value = struct.pack("<HH", value, 0) if field_type == TiffTags.SHORT else struct.pack("<I", value)
            return struct.pack("<HHI", tag, field_type, count) + packed_value

        for index, value in enumerate(cls.FRAME_VALUES):
            make = f"Cam{index}".encode() + b"\x00"
            make_offset = append(make)
            pixel_offset = append(bytes([value]))
            entries = [
                entry(ExifTags.Base.ImageWidth, TiffTags.SHORT, 1, 1),
                entry(ExifTags.Base.ImageLength, TiffTags.SHORT, 1, 1),
                entry(ExifTags.Base.BitsPerSample, TiffTags.SHORT, 1, 8),
                entry(ExifTags.Base.Compression, TiffTags.SHORT, 1, 1),
                entry(ExifTags.Base.PhotometricInterpretation, TiffTags.SHORT, 1, 1),
                entry(ExifTags.Base.Make, TiffTags.ASCII, len(make), make_offset),
                entry(ExifTags.Base.StripOffsets, TiffTags.LONG, 1, pixel_offset),
                entry(ExifTags.Base.SamplesPerPixel, TiffTags.SHORT, 1, 1),
                entry(ExifTags.Base.RowsPerStrip, TiffTags.SHORT, 1, 1),
                entry(ExifTags.Base.StripByteCounts, TiffTags.LONG, 1, 1),
            ]
            if index in (xmp_frames or {}):
                packet = xmp_frames[index]
                entries.append(entry(ExifTags.Base.XMLPacket, TiffTags.BYTE, len(packet), append(packet)))
            if index in gps_frames:
                latitude_ref = struct.pack("<HHI", ExifTags.GPS.GPSLatitudeRef, TiffTags.ASCII, 2) + b"N\x00\x00\x00"
                gps_offset = append(struct.pack("<H", 1) + latitude_ref + struct.pack("<I", 0))
                entries.append(entry(ExifTags.IFD.GPSInfo, TiffTags.LONG, 1, gps_offset))
            ifd_offset = append(struct.pack("<H", len(entries)) + b"".join(entries))
            struct.pack_into("<I", data, next_ifd_pointer, ifd_offset)
            next_ifd_pointer = append(struct.pack("<I", 0))
        return io.BytesIO(bytes(data))

    def _frames(self, content):
        """Vrátí pro každý snímek výrobce, přítomnost GPS a hodnotu pixelu.

        :param content: Stream TIFF ke kontrole.
        :return: Seznam trojic ``(make, has_gps, pixel)`` v pořadí snímků.
        """
        content.seek(0)
        result = []
        with Image.open(content) as image:
            for index in range(image.n_frames):
                image.seek(index)
                exif = image.getexif()
                result.append(
                    (exif.get(ExifTags.Base.Make), bool(exif.get_ifd(ExifTags.IFD.GPSInfo)), image.getpixel((0, 0)))
                )
        content.seek(0)
        return result

    def test_multi_frame_tiff_keeps_all_frames_without_gps(self):
        """GPS v libovolném snímku se odstraní a všechny snímky i jejich EXIF zůstanou."""
        expected = [(f"Cam{index}", False, value) for index, value in enumerate(self.FRAME_VALUES)]
        for gps_frames in ({0, 2}, {2}, {0, 1, 2}):
            with self.subTest(gps_frames=gps_frames):
                content = self._multi_frame_tiff(gps_frames)
                source = [(f"Cam{index}", index in gps_frames, value) for index, value in enumerate(self.FRAME_VALUES)]
                self.assertEqual(self._frames(content), source)
                result = Soubor.remove_gps_data(content)
                self.assertIsNot(result, content)
                self.assertEqual(result.tell(), 0)
                self.assertEqual(self._frames(result), expected)
                self.assertEqual(Soubor().calculate_rozsah(result, "photo.tiff"), len(self.FRAME_VALUES))

    def test_multi_frame_tiff_without_gps_is_unchanged(self):
        """Vícesnímkový TIFF bez GPS se vrátí beze změny."""
        content = self._multi_frame_tiff(set())
        original = content.getvalue()
        self.assertIs(Soubor.remove_gps_data(content), content)
        self.assertEqual(content.getvalue(), original)
        self.assertEqual(content.tell(), 0)

    def test_multi_frame_tiff_with_lost_frames_is_rejected(self):
        """Výstup s menším počtem snímků se nesmí archivovat."""
        content = self._multi_frame_tiff({0})
        original_save = Image.Image.save

        def save_first_frame_only(image, output, **kwargs):
            kwargs.pop("save_all", None)
            kwargs.pop("append_images", None)
            original_save(image, output, **kwargs)

        with patch.object(Image.Image, "save", autospec=True, side_effect=save_first_frame_only):
            with self.assertRaises(ValueError):
                Soubor.remove_gps_data(content)

    def test_unreadable_image_is_rejected(self):
        """Nečitelný obrázek se nesmí vrátit volajícímu jako vyčištěný."""
        with self.assertRaises(ValueError):
            Soubor.remove_gps_data(io.BytesIO(b"unreadable image"))

    def test_unreadable_exif_is_rejected(self):
        """Chyba parsování EXIF zabrání předání originálu k archivaci."""
        broken = image_location._segment(
            image_location.JPEG_MARKER_APP1, image_location.EXIF_SIGNATURE + b"XX*\x00\x08\x00\x00\x00"
        )
        with self.assertRaises(GpsDataRemovalError):
            Soubor.remove_gps_data(fx.jpeg(segments=[broken]))

    def test_encoder_failure_is_rejected(self):
        """Selhání zápisu obrázku nesmí vrátit původní GPS metadata."""
        content = self._photo("PNG")
        with patch.object(Image.Image, "save", side_effect=OSError("encoder failed")):
            with self.assertRaises(ValueError):
                Soubor.remove_gps_data(content)

    def test_saved_image_with_remaining_gps_is_rejected(self):
        """Kontrola výstupu odhalí kodér, který GPS metadata neodstranil."""
        content = self._photo("PNG")
        original = content.getvalue()
        with patch.object(Image.Image, "save", side_effect=lambda output, **kwargs: output.write(original)):
            with self.assertRaises(ValueError):
                Soubor.remove_gps_data(content)

    def test_remaining_xmp_location_is_rejected(self):
        """Kontrola výstupu odhalí XMP, ze kterého se poloha neodstranila."""
        content = fx.jpeg(xmp_packet=fx.XMP_GPS_ATTRIBUTE)
        with patch("core.image_location.rewrite_xmp", side_effect=lambda packet, *args, **kwargs: packet):
            with self.assertRaises(GpsDataRemovalError):
                Soubor.remove_gps_data(content)

    def test_image_count_change_is_rejected(self):
        """Výstup, který ztratí vedlejší obrázek MPF, se nesmí archivovat."""
        content = fx.mpo(secondary_exif=fx.exif_bytes())
        with patch("core.image_location.remove_location_metadata", return_value=fx.jpeg()):
            with self.assertRaises(GpsDataRemovalError):
                Soubor.remove_gps_data(content)

    def test_jpeg_is_cleaned_without_recompression(self):
        """JPEG s GPS se vyčistí bez rekomprese: obrazová data, tabulky i ICC zůstanou."""
        icc = fx.icc_profile()
        content = fx.jpeg(exif=fx.exif_bytes(), icc=icc)
        result = Soubor.remove_gps_data(content)
        self.assertEqual(result.tell(), 0)
        self.assertEqual(len(result.getvalue()), len(content.getvalue()))
        self.assertEqual(fx.scan_data(result.getvalue()), fx.scan_data(content.getvalue()))
        with Image.open(result) as stored, Image.open(io.BytesIO(content.getvalue())) as original:
            self.assertNotIn(ExifTags.IFD.GPSInfo, stored.getexif())
            self.assertEqual(stored.quantization, original.quantization)
            self.assertEqual(stored.info["icc_profile"], icc)

    def test_location_outside_exif_is_removed(self):
        """Poloha jen v XMP, surovém profilu PNG nebo vedlejším obrázku MPF se odstraní."""
        cases = {
            "jpeg_xmp": fx.jpeg(xmp_packet=fx.XMP_GPS_ELEMENT),
            "png_xmp": fx.png(xmp_packet=fx.XMP_DJI),
            "png_raw_profile": fx.png(texts=[("Raw profile type exif", fx.raw_profile("exif", fx.exif_bytes()))]),
            "mpo_secondary": fx.mpo(secondary_exif=fx.exif_bytes()),
            "heif_xmp": fx.heif(xmp_packet=fx.XMP_LOCATION_CREATED),
        }
        for name, content in cases.items():
            with self.subTest(case=name):
                self.assertTrue(Soubor.find_location_metadata(content))
                result = Soubor.remove_gps_data(content)
                self.assertIsNot(result, content)
                self.assertEqual(Soubor.find_location_metadata(result), [])
                self.assertEqual(image_location.image_count(result), image_location.image_count(content))

    def test_multi_frame_tiff_xmp_location(self):
        """XMP s polohou v posledním snímku se vyčistí, XMP ostatních snímků zůstane."""
        content = self._multi_frame_tiff(set(), {0: fx.XMP_CLEAN, 2: fx.XMP_GPS_ATTRIBUTE})
        self.assertEqual(Soubor.find_location_metadata(content), ["tiff[2].xmp"])
        result = Soubor.remove_gps_data(content)
        self.assertEqual(Soubor.find_location_metadata(result), [])
        with Image.open(result) as stored:
            self.assertEqual(stored.n_frames, len(self.FRAME_VALUES))
            self.assertEqual(image_location.tiff_xmp(stored), fx.XMP_CLEAN)
            stored.seek(1)
            self.assertIsNone(image_location.tiff_xmp(stored))
            stored.seek(2)
            packet = image_location.tiff_xmp(stored)
        self.assertIn(b'format="image/jpeg"', packet)
        self.assertNotIn(b"GPSLatitude", packet)

    def test_location_blocks_are_logged_without_values(self):
        """Log uvede jen identifikátory bloků, nikdy hodnoty souřadnic."""
        content = fx.jpeg(exif=fx.exif_bytes(), xmp_packet=fx.XMP_GPS_ATTRIBUTE)
        with self.assertLogs("core.models", "DEBUG") as logs:
            Soubor.remove_gps_data(content)
        found = [record for record in logs.records if record.msg.endswith(".location_found")]
        self.assertEqual(found[0].blocks, ["jpeg[0].exif.gps", "jpeg[0].xmp"])
        for record in logs.records:
            self.assertNotIn("50,5.0N", str(record.__dict__))

    def test_clean_and_gps_free_photos(self):
        """JPEG, PNG a TIFF se vyčistí; obsah bez GPS zůstane beze změny."""
        for fmt in ("JPEG", "PNG", "TIFF"):
            with self.subTest(format=fmt):
                result = Soubor.remove_gps_data(self._photo(fmt))
                self.assertEqual(result.tell(), 0)
                with Image.open(result) as image:
                    self.assertFalse(image.getexif().get_ifd(ExifTags.IFD.GPSInfo))
                content = self._photo(fmt, gps=False)
                original = content.getvalue()
                self.assertIs(Soubor.remove_gps_data(content), content)
                self.assertEqual(content.getvalue(), original)
                self.assertEqual(content.tell(), 0)


class WebGpsRejectionTests(unittest.TestCase):
    """Nečitelná fotografie se neuloží ani při přepsání existujícího souboru."""

    def test_cleanup_failure_blocks_both_web_upload_paths(self):
        """Web vrátí chybu, neuloží binární data a zruší Fedora transakci."""
        from core.constants import SAMOSTATNY_NALEZ_RELATION_TYPE

        for view_class in (NewFileUploadView, UpdateExistingFileUploadView):
            with self.subTest(view=view_class.__name__):
                view = view_class()
                record = Mock(spec=SamostatnyNalez)
                view._resolve_object_and_name = Mock(return_value=(record, "photo.jpg"))
                view._check_update_permissions = Mock(return_value=None)
                existing = Mock()
                existing.nazev = "photo.jpg"
                existing.vazba.typ_vazby = SAMOSTATNY_NALEZ_RELATION_TYPE
                existing.vazba.navazany_objekt = record
                request = SimpleNamespace(
                    POST={"source-url": "soubor/nahrat/pas/example"},
                    FILES={"file": SimpleUploadedFile("photo.jpg", b"unreadable image")},
                    user=Mock(is_authenticated=True),
                )
                with (
                    patch("core.views.FedoraTransaction") as transaction_class,
                    patch("core.views.FedoraRepositoryConnector") as connector_class,
                    patch("core.views.Soubor.check_mime_for_url", return_value=True),
                    patch("core.views.Soubor.check_antivirus", return_value=None),
                    patch("core.views.Soubor.get_mime_types", return_value="image/jpeg"),
                    patch("core.views.Soubor.get_file_extension_by_mime", return_value=("jpg",)),
                    patch("core.views.check_soubor_vazba"),
                    patch("core.views.get_object_or_404", return_value=existing),
                ):
                    transaction_class.return_value.status = FedoraTransactionStatus.ACTIVE
                    response = view.post(request, typ_vazby="pas", ident_cely="example", file_id=1)
                    self.assertEqual(response.status_code, 500)
                    self.assertEqual(
                        json.loads(response.content)["error"], _("core.views.post_upload.gps_cleanup_failed")
                    )
                    connector_class.return_value.save_binary_file.assert_not_called()
                    connector_class.return_value.update_binary_file.assert_not_called()
                    transaction_class.return_value.rollback_transaction.assert_called_once()


class ApiGpsRejectionTests(unittest.TestCase):
    """Selhání GPS v API nesmí uložit soubor ani ponechat zamčený nález."""

    def test_cleanup_failure_releases_lock_and_marks_request_failed(self):
        """Skutečný API handler uvolní zámek, zruší transakci a vrátí HTTP 500."""
        view = SamostatnyNalezFotografieUploadView()
        view._has_upload_permissions = Mock(return_value=True)
        view._verify_content_digest = Mock(return_value=None)
        view.get_client_ip = Mock(return_value="127.0.0.1")
        request = SimpleNamespace(
            FILES=MultiValueDict({"file": [SimpleUploadedFile("photo.jpg", b"unreadable image")]}),
            user=Mock(),
            path="/api/pas/nalez/example/upload-foto",
        )
        cache.delete(f"{_RECORD_LOCK_PREFIX}example")
        self.addCleanup(cache.delete, f"{_RECORD_LOCK_PREFIX}example")
        with (
            patch("api.views.ApiRequestLog.objects.create") as create_log,
            patch("api.views.SamostatnyNalez.objects.get"),
            patch("api.views.FedoraTransaction") as transaction_class,
            patch("api.views.FedoraRepositoryConnector") as connector_class,
            patch("api.views.Soubor.check_mime_for_url", return_value=True),
            patch("api.views.Soubor.check_antivirus", return_value=None),
            patch("api.views.Soubor.get_mime_types", return_value="image/jpeg"),
            patch("api.views.Soubor.get_file_extension_by_mime", return_value=("jpg",)),
            patch("api.views.get_next_soubor_name", return_value="photo.jpg"),
            patch.object(PasApiBaseView, "get_record_lock_params", return_value=(0, 1)),
            patch.object(PasApiBaseView, "get_record_lock_ttl", return_value=60),
        ):
            transaction_class.return_value.status = FedoraTransactionStatus.ACTIVE
            response = view.post(request, "example")
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.data["detail"], _("core.views.post_upload.gps_cleanup_failed"))
            connector_class.assert_not_called()
            transaction_class.return_value.rollback_transaction.assert_called_once()
            self.assertEqual(create_log.return_value.status, API_REQUEST_LOG_STATUS_FAILURE)
            self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}example"), 0)
