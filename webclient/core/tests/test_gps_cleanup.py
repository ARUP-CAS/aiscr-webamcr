"""Regrese odmítnutí fotografií, jejichž GPS nelze bezpečně odstranit."""

import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import piexif
from api.views import _RECORD_LOCK_PREFIX, PasApiBaseView, SamostatnyNalezFotografieUploadView
from core.constants import API_REQUEST_LOG_STATUS_FAILURE
from core.models import Soubor
from core.repository_connector import FedoraTransactionStatus
from core.views import NewFileUploadView, UpdateExistingFileUploadView
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext as _
from pas.models import SamostatnyNalez
from PIL import Image


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
        exif = piexif.dump({"GPS": {1: b"N", 2: ((50, 1), (5, 1), (0, 1))} if gps else {}})
        Image.new("RGB", (32, 32), "red").save(content, format=fmt, exif=exif)
        content.seek(0)
        return content

    def test_unreadable_image_is_rejected(self):
        """Nečitelný obrázek se nesmí vrátit volajícímu jako vyčištěný."""
        with self.assertRaises(ValueError):
            Soubor.remove_gps_data(io.BytesIO(b"unreadable image"))

    def test_unreadable_exif_is_rejected(self):
        """Chyba parsování EXIF zabrání předání originálu k archivaci."""
        content = self._photo()
        with patch("core.models.piexif.load", side_effect=ValueError("broken EXIF")):
            with self.assertRaises(ValueError):
                Soubor.remove_gps_data(content)

    def test_unrepairable_exif_is_rejected(self):
        """Neznámá chyba i vyčerpání oprav EXIF musí zastavit upload."""
        for message in ("cannot serialize EXIF", "41729 in Exif IFD"):
            with self.subTest(message=message):
                content = self._photo()
                with patch("core.models.piexif.dump", side_effect=ValueError(message)):
                    with self.assertRaises(ValueError):
                        Soubor.remove_gps_data(content)

    def test_encoder_failure_is_rejected(self):
        """Selhání zápisu obrázku nesmí vrátit původní GPS metadata."""
        content = self._photo()
        with patch.object(Image.Image, "save", side_effect=OSError("encoder failed")):
            with self.assertRaises(ValueError):
                Soubor.remove_gps_data(content)

    def test_saved_image_with_remaining_gps_is_rejected(self):
        """Kontrola výstupu odhalí kodér, který GPS metadata neodstranil."""
        content = self._photo()
        original = content.getvalue()
        with patch.object(Image.Image, "save", side_effect=lambda output, **kwargs: output.write(original)):
            with self.assertRaises(ValueError):
                Soubor.remove_gps_data(content)

    def test_clean_and_gps_free_photos(self):
        """JPEG, PNG a TIFF se vyčistí; obsah bez GPS zůstane beze změny."""
        for fmt in ("JPEG", "PNG", "TIFF"):
            with self.subTest(format=fmt):
                result = Soubor.remove_gps_data(self._photo(fmt))
                self.assertEqual(result.tell(), 0)
                with Image.open(result) as image:
                    self.assertFalse(image.getexif().get_ifd(34853))
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
