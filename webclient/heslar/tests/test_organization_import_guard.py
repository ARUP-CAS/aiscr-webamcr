"""Testy zákazu změn organizací v adminu během importu bez databázových zámků."""

from unittest.mock import MagicMock, patch

from core.connectors import RedisConnector
from core.tests.fake_redis import FakeRedis
from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from heslar.admin import HeslarAdmin, OrganizaceAdmin
from heslar.models import Heslar
from redis.exceptions import ConnectionError
from uzivatel.models import Organizace


class OrganizationImportGuardTest(TestCase):
    """Ověří čtení, oprávnění a odmítnutí přímého POST na organizační administraci."""

    def setUp(self):
        """Připraví admin modelu, oprávněného správce a stav aktivního importu."""
        self.admin = OrganizaceAdmin(Organizace, AdminSite())
        self.request = RequestFactory().get("/admin/uzivatel/organizace/")
        self.request.user = MagicMock(is_active=True, is_staff=True, is_superuser=True)
        self.redis = FakeRedis(
            {
                RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY: "job",
                RedisConnector.IMPORT_DATA_LOCK_KEY: "token",
                "import_data_lock_token_job": "token",
                "import_data_phase_job": "importing",
            }
        )

    def test_import_blocks_add_change_delete_but_allows_view(self):
        """Probíhající import omezí organizace na čtení a skryje hromadné smazání."""
        with patch.object(RedisConnector, "get_connection", return_value=self.redis):
            self.assertFalse(self.admin.has_add_permission(self.request))
            self.assertFalse(self.admin.has_change_permission(self.request))
            self.assertFalse(self.admin.has_delete_permission(self.request, MagicMock(has_connections=False)))
            self.assertTrue(self.admin.has_view_permission(self.request))
            self.assertNotIn("delete_selected", self.admin.get_actions(self.request))
            self.assertTrue(HeslarAdmin(Heslar, AdminSite()).has_change_permission(self.request))

    def test_post_from_previously_opened_form_is_rejected(self):
        """Formulář otevřený před importem nezapíše změnu přes přímý POST."""
        request = RequestFactory().post("/admin/uzivatel/organizace/1/change/", {"nazev": "Changed"})
        request.user = self.request.user
        request._dont_enforce_csrf_checks = True
        with patch.object(RedisConnector, "get_connection", return_value=self.redis), patch.object(
            self.admin, "message_user"
        ), patch.object(self.admin, "get_object", return_value=MagicMock()), patch.object(
            self.admin, "save_model"
        ) as save:
            with self.assertRaises(PermissionDenied):
                self.admin.changeform_view(request, "1")
        save.assert_not_called()

    def test_delete_post_is_rejected(self):
        """Přímý požadavek na smazání organizace během importu je odmítnut."""
        request = RequestFactory().post("/admin/uzivatel/organizace/1/delete/", {"post": "yes"})
        request.user = self.request.user
        request._dont_enforce_csrf_checks = True
        with patch.object(RedisConnector, "get_connection", return_value=self.redis), patch.object(
            self.admin, "get_object", return_value=MagicMock()
        ), patch.object(self.admin, "delete_model") as delete:
            with self.assertRaises(PermissionDenied):
                self.admin.delete_view(request, "1")
        delete.assert_not_called()

    def test_approval_validation_and_terminal_phases_allow_changes(self):
        """Čekání na schválení, validace ani ukončený import změny neblokují."""
        for phase in ("validating", "awaiting_approval", "finished", "failed", "stopped"):
            with self.subTest(phase=phase):
                self.redis.set("import_data_phase_job", phase)
                request = RequestFactory().get("/")
                request.user = self.request.user
                with patch.object(RedisConnector, "get_connection", return_value=self.redis):
                    self.assertTrue(self.admin.has_change_permission(request))

    def test_stale_pointer_and_expired_or_replaced_lock_do_not_block(self):
        """Osiřelý ukazatel ani cizí nebo expirovaný token neblokují administraci."""
        for value in (None, "replacement"):
            with self.subTest(value=value):
                if value is None:
                    self.redis.delete(RedisConnector.IMPORT_DATA_LOCK_KEY)
                else:
                    self.redis.set(RedisConnector.IMPORT_DATA_LOCK_KEY, value)
                self.assertFalse(RedisConnector.is_data_import_running(self.redis))
        self.redis.delete(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY)
        self.assertFalse(RedisConnector.is_data_import_running(self.redis))

    def test_decoded_redis_connection_is_supported(self):
        """Kontrola importu pracuje i s dekódovanými odpověďmi Redis."""
        redis = FakeRedis(decode_responses=True)
        for key in (RedisConnector.IMPORT_DATA_LOCK_KEY, "import_data_lock_token_job"):
            redis.set(key, "token")
        redis.set(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, "job")
        redis.set("import_data_phase_job", "importing")
        self.assertTrue(RedisConnector.is_data_import_running(redis))

    def test_redis_failure_denies_writes_without_breaking_view_permission(self):
        """Výpadek Redis nezpůsobí chybu stránky a zabrání neověřenému zápisu."""
        with patch.object(RedisConnector, "get_connection", side_effect=ConnectionError("offline")):
            with self.assertLogs("heslar.admin", level="ERROR"):
                self.assertFalse(self.admin.has_change_permission(self.request))
            self.assertTrue(self.admin.has_view_permission(self.request))
