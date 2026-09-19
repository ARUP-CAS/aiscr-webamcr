"""Ochrana odstávky během importu včetně skutečného souběhu databázových transakcí."""

from concurrent.futures import ThreadPoolExecutor
from copy import copy
from datetime import datetime, timedelta
from threading import Event
from unittest.mock import MagicMock, patch

from core.admin import OdstavkaSystemuAdmin
from core.admin_sites import AmcrCustomAdminSite
from core.connectors import RedisConnector
from core.import_maintenance import (
    MaintenanceImportConflict,
    acquire_import_lock_during_maintenance,
    ensure_maintenance_change_allowed,
    lock_maintenance_configuration,
)
from core.models import OdstavkaSystemu
from core.tests.fake_redis import FakeRedis
from django.contrib.admin import AdminSite, ModelAdmin
from django.db import connections, transaction
from django.test import RequestFactory, SimpleTestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from redis.exceptions import ConnectionError

urlpatterns = []


def active_maintenance():
    """Vrátí neuloženou konfiguraci odstávky, která začala včera."""
    yesterday = datetime.today().date() - timedelta(days=1)
    return OdstavkaSystemu(info_od=yesterday, datum_odstavky=yesterday, cas_odstavky=datetime.min.time(), status=True)


@override_settings(ROOT_URLCONF=__name__)
class MaintenanceImportGuardTest(SimpleTestCase):
    """Ověřuje všechny fáze a odmítnutí ukončení při nedostupném Redis."""

    def setUp(self):
        """Připraví aktivní odstávku a izolovaný stav importu."""
        self.current = active_maintenance()
        self.current.cas_odstavky = datetime.min.time()
        self.disabled = copy(self.current)
        self.disabled.status = False
        self.redis = FakeRedis(decode_responses=True)
        self.enterContext(patch.object(RedisConnector, "get_connection_decode", return_value=self.redis))

    def test_nonterminal_or_missing_phase_blocks_shutdown_without_lock(self):
        """Aktivní ukazatel chrání import i při chybějícím locku nebo fázi."""
        self.redis.set(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, "job")
        for phase in ("validating", "awaiting_approval", "importing", "unknown", None):
            with self.subTest(phase=phase):
                if phase is None:
                    self.redis.delete("import_data_phase_job")
                else:
                    self.redis.set("import_data_phase_job", phase)
                with self.assertRaises(MaintenanceImportConflict):
                    ensure_maintenance_change_allowed(self.current, self.disabled)

    def test_lock_protects_staging_and_terminal_cleanup(self):
        """Držený lock blokuje vypnutí před založením metadat i po zápisu terminální fáze."""
        self.redis.set(RedisConnector.IMPORT_DATA_LOCK_KEY, "token")
        for phase in (None, "finished", "stopped", "failed", "canceled"):
            with self.subTest(phase=phase):
                if phase:
                    self.redis.set(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, "job")
                    self.redis.set("import_data_phase_job", phase)
                with self.assertRaises(MaintenanceImportConflict):
                    ensure_maintenance_change_allowed(self.current, self.disabled)

    def test_terminal_job_allows_manual_shutdown_without_changing_maintenance(self):
        """Po úklidu se povolí ruční vypnutí, samotný guard konfiguraci nemění."""
        self.redis.set(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, "job")
        for phase in ("finished", "stopped", "failed", "canceled"):
            with self.subTest(phase=phase):
                self.redis.set("import_data_phase_job", phase)
                ensure_maintenance_change_allowed(self.current, self.disabled)
                self.assertTrue(self.current.status)

    def test_stop_request_does_not_release_protection(self):
        """Stop sentinel sám neznamená ukončení importu."""
        self.redis.set(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, "job")
        self.redis.set("import_data_phase_job", "importing")
        self.redis.set("import_data_stop_job", "1")
        with self.assertRaises(MaintenanceImportConflict):
            ensure_maintenance_change_allowed(self.current, self.disabled)

    def test_rescheduling_start_or_publication_is_blocked(self):
        """Nelze obejít ochranu přesunutím začátku nebo zveřejnění odstávky do budoucnosti."""
        self.redis.set(RedisConnector.IMPORT_DATA_LOCK_KEY, "token")
        for field in ("info_od", "datum_odstavky"):
            with self.subTest(field=field):
                proposed = copy(self.current)
                setattr(proposed, field, datetime.today().date() + timedelta(days=1))
                with self.assertRaises(MaintenanceImportConflict):
                    ensure_maintenance_change_allowed(self.current, proposed)

    def test_message_only_edit_does_not_require_redis(self):
        """Úprava textů při zachování odstávky nečte stav importu."""
        with patch.object(RedisConnector, "get_connection_decode", side_effect=ConnectionError):
            ensure_maintenance_change_allowed(self.current, copy(self.current))

    def test_redis_failure_blocks_shutdown_and_deletion(self):
        """Při chybě spojení nelze odstávku vypnout ani smazat."""
        with patch.object(RedisConnector, "get_connection_decode", side_effect=ConnectionError):
            for replacement in (None, self.disabled):
                with self.subTest(replacement=replacement), self.assertRaises(MaintenanceImportConflict):
                    ensure_maintenance_change_allowed(self.current, replacement)

    def test_inactive_maintenance_remains_editable(self):
        """Importní guard neomezuje konfiguraci již neaktivní odstávky."""
        with patch.object(RedisConnector, "get_connection_decode", side_effect=ConnectionError):
            ensure_maintenance_change_allowed(self.disabled)

    def test_admin_conflict_is_reported_for_save_delete_and_bulk_delete(self):
        """Administrátor dostane srozumitelnou zprávu místo serverové chyby."""
        model_admin = OdstavkaSystemuAdmin(OdstavkaSystemu, AdminSite())
        request = RequestFactory().post("/admin/core/odstavkasystemu/")
        # Transakce hromadné akce se ověřuje integračně; zde testujeme zobrazení zprávy.
        with patch("core.admin.transaction.atomic"), patch.object(model_admin, "message_user") as message:
            for method, args in (
                ("changeform_view", (request, "1")),
                ("delete_view", (request, "1")),
                ("response_action", (request, MagicMock())),
            ):
                with self.subTest(method=method), patch.object(
                    ModelAdmin, method, side_effect=MaintenanceImportConflict("Import is active")
                ):
                    response = getattr(model_admin, method)(*args)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response.url, request.path)
                    self.assertEqual(message.call_args.args[1], "Import is active")

    def test_upload_url_opts_out_of_request_transaction(self):
        """Zámek uploadu se uvolní před stagingem ZIPu, nikoli až na konci HTTP požadavku."""
        site = AmcrCustomAdminSite()
        callback = next(url.callback for url in site.get_urls() if url.name == "import_data")
        self.assertIn("default", callback._non_atomic_requests)


@override_settings(LANGUAGES=(), ROSETTA_WSGI_AUTO_RELOAD=False, ROSETTA_UWSGI_AUTO_RELOAD=False)
class MaintenanceImportDatabaseTest(TransactionTestCase):
    """Ověřuje skutečné zápisy administrace a serializaci přes databázový row lock."""

    def setUp(self):
        """Uloží odstávku a připraví request a izolovaný Redis."""
        self.maintenance = active_maintenance()
        self.maintenance.cas_odstavky = datetime.min.time()
        self.maintenance.save()
        self.redis = FakeRedis(decode_responses=True)
        self.enterContext(patch.object(RedisConnector, "get_connection_decode", return_value=self.redis))
        self.model_admin = OdstavkaSystemuAdmin(OdstavkaSystemu, AdminSite())
        self.request = RequestFactory().post("/admin/core/odstavkasystemu/")
        self.cache_delete = self.enterContext(patch("core.admin.cache.delete"))

    def test_blocked_save_has_no_file_or_cache_side_effects(self):
        """Odmítnuté vypnutí nemění databázi, překlady, stránky ani cache."""
        self.redis.set(RedisConnector.IMPORT_DATA_LOCK_KEY, "token")
        proposed = copy(self.maintenance)
        proposed.status = False
        with patch("core.admin.pofile") as po, patch.object(self.model_admin, "file_handler") as files:
            with self.assertRaises(MaintenanceImportConflict):
                self.model_admin.save_model(self.request, proposed, MagicMock(), True)
        self.maintenance.refresh_from_db()
        self.assertTrue(self.maintenance.status)
        po.assert_not_called()
        files.assert_not_called()
        self.cache_delete.assert_not_called()

    def test_individual_and_bulk_deletion_are_blocked(self):
        """Obě administrační cesty smazání zachovají aktivní odstávku."""
        self.redis.set(RedisConnector.IMPORT_DATA_LOCK_KEY, "token")
        with self.assertRaises(MaintenanceImportConflict):
            self.model_admin.delete_model(self.request, self.maintenance)
        with self.assertRaises(MaintenanceImportConflict):
            self.model_admin.delete_queryset(self.request, OdstavkaSystemu.objects.all())
        self.assertTrue(OdstavkaSystemu.objects.filter(pk=self.maintenance.pk, status=True).exists())
        self.cache_delete.assert_not_called()

    def test_message_only_save_is_allowed_during_import(self):
        """Uložení textů neukončuje odstávku a zůstává povoleno."""
        self.redis.set(RedisConnector.IMPORT_DATA_LOCK_KEY, "token")
        self.model_admin.save_model(self.request, self.maintenance, MagicMock(), True)
        self.maintenance.refresh_from_db()
        self.assertTrue(self.maintenance.status)
        self.cache_delete.assert_called_once_with("maintenance")

    def test_manual_shutdown_after_cleanup_invalidates_cache_on_commit(self):
        """Cache se invaliduje až po potvrzení ručního vypnutí."""
        self.maintenance.status = False
        with transaction.atomic():
            self.model_admin.save_model(self.request, self.maintenance, MagicMock(), True)
            self.cache_delete.assert_not_called()
        self.cache_delete.assert_called_once_with("maintenance")
        self.maintenance.refresh_from_db()
        self.assertFalse(self.maintenance.status)

    def test_deletion_after_cleanup_invalidates_cache(self):
        """Povolené jednotlivé i hromadné smazání invaliduje cache odstávky."""
        self.model_admin.delete_model(self.request, self.maintenance)
        self.cache_delete.assert_called_once_with("maintenance")
        self.cache_delete.reset_mock()
        active_maintenance().save()
        self.model_admin.delete_queryset(self.request, OdstavkaSystemu.objects.all())
        self.assertFalse(OdstavkaSystemu.objects.exists())
        self.cache_delete.assert_called_once_with("maintenance")

    def test_upload_requires_current_database_state(self):
        """Starý kladný údaj z cache nesmí umožnit upload po vypnutí odstávky."""
        OdstavkaSystemu.objects.filter(pk=self.maintenance.pk).update(status=False)
        self.assertIsNone(acquire_import_lock_during_maintenance(self.redis, "token", 100))
        self.assertIsNone(self.redis.get(RedisConnector.IMPORT_DATA_LOCK_KEY))

    def test_upload_preserves_existing_import_lock(self):
        """Druhý upload nemůže přepsat vlastnící token běžícího importu."""
        self.assertTrue(acquire_import_lock_during_maintenance(self.redis, "first", 100))
        self.assertFalse(acquire_import_lock_during_maintenance(self.redis, "second", 100))
        self.assertEqual(self.redis.get(RedisConnector.IMPORT_DATA_LOCK_KEY), "first")

    @skipUnlessDBFeature("has_select_for_update")
    def test_upload_wins_race_against_shutdown(self):
        """Upload pod row lockem zabrání souběžnému vypnutí odstávky."""
        self._race(upload_first=True)

    @skipUnlessDBFeature("has_select_for_update")
    def test_shutdown_wins_race_against_upload(self):
        """Vypnutí pod row lockem zabrání souběžnému přijetí uploadu."""
        self._race(upload_first=False)

    def _race(self, upload_first):
        """Spustí oba požadavky na různých DB spojeních s řízeným pořadím zámku.

        :param upload_first: Zda konfiguraci nejprve zamkne upload.
        """
        first_locked = Event()
        release_first = Event()
        second_started = Event()
        second_done = Event()

        def upload():
            return acquire_import_lock_during_maintenance(self.redis, "token", 100)

        def shutdown():
            proposed = copy(self.maintenance)
            proposed.status = False
            try:
                self.model_admin.save_model(self.request, proposed, MagicMock(), True)
            except MaintenanceImportConflict:
                return "blocked"
            return "disabled"

        def first():
            try:
                with transaction.atomic():
                    lock_maintenance_configuration()
                    first_locked.set()
                    if not release_first.wait(5):
                        raise AssertionError("První transakce nedostala signál k pokračování")
                    return upload() if upload_first else shutdown()
            finally:
                connections.close_all()

        def second():
            try:
                second_started.set()
                return shutdown() if upload_first else upload()
            finally:
                second_done.set()
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            first_result = executor.submit(first)
            try:
                self.assertTrue(first_locked.wait(5))
                second_result = executor.submit(second)
                self.assertTrue(second_started.wait(5))
                self.assertFalse(second_done.wait(0.1))
            finally:
                release_first.set()
            self.assertEqual(first_result.result(timeout=5), True if upload_first else "disabled")
            self.assertEqual(second_result.result(timeout=5), "blocked" if upload_first else None)
        self.maintenance.refresh_from_db()
        self.assertEqual(self.maintenance.status, upload_first)
