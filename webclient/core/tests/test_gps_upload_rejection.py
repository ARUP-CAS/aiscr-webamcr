"""Regrese odmítnutí fotografií, jejichž GPS nelze bezpečně odstranit."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from api.views import _RECORD_LOCK_PREFIX, PasApiBaseView, SamostatnyNalezFotografieUploadView
from core.constants import API_REQUEST_LOG_STATUS_FAILURE
from core.repository_connector import FedoraTransactionStatus
from core.views import NewFileUploadView, UpdateExistingFileUploadView
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext as _
from pas.models import SamostatnyNalez


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
                    self.assertEqual(json.loads(response.content)["error"], _("core.views.post_upload.unknown_error"))
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
            self.assertEqual(
                response.data["detail"], _("api.views.SamostatnyNalezFotografieUploadView.post.internal_error")
            )
            connector_class.assert_not_called()
            transaction_class.return_value.rollback_transaction.assert_called_once()
            self.assertEqual(create_log.return_value.status, API_REQUEST_LOG_STATUS_FAILURE)
            self.assertEqual(cache.get(f"{_RECORD_LOCK_PREFIX}example"), 0)
