"""Test pro ``AmcrCustomAdminSite.import_data`` — pořadí zápisu recovery metadat.

Testuje výhradně přes ``RequestFactory``/``FakeRedis`` (bez DB) — mirror stylu
``core.tests.test_data_import_views``. Admin-menu plumbing (``get_app_list``/``each_context``)
je odmockována, protože testovaný scénář se týká pouze pořadí zápisů do Redis.
"""

from unittest.mock import MagicMock, patch

from core.admin_sites import AmcrCustomAdminSite
from core.connectors import RedisConnector
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

USER_ID = 42


class _StubUser:
    """Minimální náhrada uživatele pro ``RequestFactory`` — nese jen atributy čtené view."""

    def __init__(self, user_id):
        self.id = user_id
        self.pk = user_id
        self.is_superuser = True
        self.is_staff = True
        self.is_active = True
        self.is_authenticated = True


class ImportDataUploadRecoveryMetadataTest(SimpleTestCase):
    """Ověřuje, že routing/recovery metadata se zapíší PŘED rizikovým ``data_file.read()``."""

    def setUp(self):
        """Připraví ``RequestFactory`` sdílenou napříč testy."""
        self.factory = RequestFactory()

    def _post(self, data_file):
        """Zavolá ``AmcrCustomAdminSite.import_data`` s mocknutým formulářem a daným souborem.

        :param data_file: Mock nahrávaného souboru (``read()`` vrací bajty nebo simuluje pád).
        :return: Trojice ``(response, fake, fake_bytes)`` — HTTP odpověď, ``FakeRedis`` použitý
            jako ``redis_connector`` (decode režim, jako reálná admin site) a bytová varianta
            použitá pro chunk pipeline.
        """
        fake = FakeRedis(decode_responses=True)
        fake_bytes = FakeRedis()

        form_mock = MagicMock()
        form_mock.is_valid.return_value = True
        form_mock.cleaned_data = {
            "performed_action": ImportDataAdminForm.PERFORMED_ACTION_INSERT,
            "data_file": data_file,
        }

        request = self.factory.post("/admin/core/import-data/")
        request.user = _StubUser(USER_ID)
        request._dont_enforce_csrf_checks = True

        with patch.object(AmcrCustomAdminSite, "get_app_list", return_value=[]), patch.object(
            AmcrCustomAdminSite, "each_context", return_value={}
        ), patch.object(
            AmcrCustomAdminSite, "_render_import_polling_ui", return_value=HttpResponse(status=200)
        ), patch.object(
            AmcrCustomAdminSite, "redis_connector", fake
        ), patch(
            "core.admin_sites.RedisConnector.get_connection", return_value=fake_bytes
        ), patch(
            "core.admin_sites.ImportDataAdminForm", return_value=form_mock
        ), patch(
            "core.admin_sites.is_maintenance_in_progress", return_value=True
        ), patch(
            "core.admin_sites.check_import_report_directory",
            return_value=("/tmp/fake-import-dir", "/tmp/fake-import-dir/reports", None),
        ):
            site = AmcrCustomAdminSite()
            response = site.import_data(request)
        return response, fake, fake_bytes

    def test_recovery_metadata_published_before_risky_file_read(self):
        """Aktivní job pointer, fáze a lock token musí existovat PŘED voláním ``data_file.read()``.

        Simuluje pád web workeru (OOM kill) uprostřed čtení nahrávaného souboru — zachytí stav
        Redis přesně v okamžiku volání ``read()``, poté pád simuluje výjimkou.
        """
        observed = {}
        store = {}

        def crashing_read():
            fake = store["fake"]
            job_id = fake.get(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY)
            observed["active_job_id"] = job_id
            observed["phase"] = fake.get(f"import_data_phase_{job_id}") if job_id else None
            observed["lock_token"] = fake.get(f"import_data_lock_token_{job_id}") if job_id else None
            observed["current_job_pointer"] = fake.get(f"import_data_current_job_{USER_ID}")
            raise MemoryError("simulated OOM during upload read")

        data_file = MagicMock()
        data_file.read.side_effect = crashing_read

        fake = FakeRedis(decode_responses=True)
        fake_bytes = FakeRedis()
        store["fake"] = fake

        form_mock = MagicMock()
        form_mock.is_valid.return_value = True
        form_mock.cleaned_data = {
            "performed_action": ImportDataAdminForm.PERFORMED_ACTION_INSERT,
            "data_file": data_file,
        }
        request = self.factory.post("/admin/core/import-data/")
        request.user = _StubUser(USER_ID)
        request._dont_enforce_csrf_checks = True

        with patch.object(AmcrCustomAdminSite, "get_app_list", return_value=[]), patch.object(
            AmcrCustomAdminSite, "each_context", return_value={}
        ), patch.object(AmcrCustomAdminSite, "redis_connector", fake), patch(
            "core.admin_sites.RedisConnector.get_connection", return_value=fake_bytes
        ), patch(
            "core.admin_sites.ImportDataAdminForm", return_value=form_mock
        ), patch(
            "core.admin_sites.is_maintenance_in_progress", return_value=True
        ), patch(
            "core.admin_sites.check_import_report_directory",
            return_value=("/tmp/fake-import-dir", "/tmp/fake-import-dir/reports", None),
        ):
            site = AmcrCustomAdminSite()
            response = site.import_data(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(
            observed.get("active_job_id"),
            "IMPORT_DATA_ACTIVE_JOB_KEY musí být nastaven před data_file.read().",
        )
        self.assertEqual(observed.get("phase"), tasks.IMPORT_PHASE_VALIDATING)
        self.assertIsNotNone(
            observed.get("lock_token"),
            "import_data_lock_token_{job_id} musí existovat před data_file.read(), jinak "
            "reset_import_job nemůže lock uvolnit.",
        )
        self.assertEqual(observed.get("current_job_pointer"), observed.get("active_job_id"))

        # Post-crash cleanup: the except handler must still release the lock and clear pointers.
        self.assertFalse(bool(fake.get(RedisConnector.IMPORT_DATA_LOCK_KEY)))
        self.assertIsNone(fake.get(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY))
        self.assertIsNone(fake.get(f"import_data_current_job_{USER_ID}"))

    def test_dispatch_failure_cleanup_preserves_racing_job_pointers(self):
        """Compare-then-delete cleanup nesmí smazat pointery nové úlohy, která je přepsala po
        uvolnění locku.

        Simuluje: dispatch selže → ``release_import_lock`` uvolní lock → mezitím jiný upload stihne
        získat lock a přepsat ``import_data_current_job_{user}``/``IMPORT_DATA_ACTIVE_JOB_KEY`` na
        svůj vlastní ``job_id`` → následný compare-then-delete úklid selhavší úlohy nesmí tyto
        pointery smazat, protože už neodpovídají jejímu ``job_id``.
        """
        fake = FakeRedis(decode_responses=True)
        fake_bytes = FakeRedis()
        racing_job_id = "racing-job-id"

        def release_lock_and_simulate_race(connection, token):
            connection.set(f"import_data_current_job_{USER_ID}", racing_job_id)
            connection.set(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, racing_job_id)
            return True

        data_file = MagicMock()
        data_file.read.side_effect = RuntimeError("simulated dispatch failure")

        form_mock = MagicMock()
        form_mock.is_valid.return_value = True
        form_mock.cleaned_data = {
            "performed_action": ImportDataAdminForm.PERFORMED_ACTION_INSERT,
            "data_file": data_file,
        }
        request = self.factory.post("/admin/core/import-data/")
        request.user = _StubUser(USER_ID)
        request._dont_enforce_csrf_checks = True

        with patch.object(AmcrCustomAdminSite, "get_app_list", return_value=[]), patch.object(
            AmcrCustomAdminSite, "each_context", return_value={}
        ), patch.object(AmcrCustomAdminSite, "redis_connector", fake), patch(
            "core.admin_sites.RedisConnector.get_connection", return_value=fake_bytes
        ), patch(
            "core.admin_sites.ImportDataAdminForm", return_value=form_mock
        ), patch(
            "core.admin_sites.is_maintenance_in_progress", return_value=True
        ), patch(
            "core.admin_sites.check_import_report_directory",
            return_value=("/tmp/fake-import-dir", "/tmp/fake-import-dir/reports", None),
        ), patch(
            "core.admin_sites.RedisConnector.release_import_lock", side_effect=release_lock_and_simulate_race
        ):
            site = AmcrCustomAdminSite()
            response = site.import_data(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            fake.get(f"import_data_current_job_{USER_ID}"),
            racing_job_id,
            "Compare-then-delete nesmí smazat pointer, který mezitím přepsala nová úloha.",
        )
        self.assertEqual(
            fake.get(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY),
            racing_job_id,
            "Compare-then-delete nesmí smazat pointer, který mezitím přepsala nová úloha.",
        )

    def test_successful_upload_still_dispatches_validation(self):
        """Přesun zápisů metadat před čtení souboru nesmí rozbít úspěšnou cestu (task se stále dispatchne)."""
        data_file = MagicMock()
        data_file.read.return_value = b"PK\x03\x04fake-zip-bytes"

        with patch("cron.tasks.run_data_import_validation.delay") as delay_mock:
            response, fake, _fake_bytes = self._post(data_file)

        self.assertEqual(response.status_code, 200)
        delay_mock.assert_called_once()
        job_id = delay_mock.call_args[0][0]
        self.assertEqual(fake.get(f"import_data_phase_{job_id}"), tasks.IMPORT_PHASE_VALIDATING)
        self.assertEqual(fake.get(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY), job_id)
        self.assertEqual(fake.get(f"import_data_current_job_{USER_ID}"), job_id)


class ImportDataReportDirectoryGateTest(SimpleTestCase):
    """Ověřuje, že bez nakonfigurovaného/zapisovatelného adresáře reportů import nejde ani spustit
    (customer requirement — report je jediný trvalý záznam běhu)."""

    def setUp(self):
        """Připraví ``RequestFactory`` sdílenou napříč testy."""
        self.factory = RequestFactory()

    def _call(self, method, data_file=None):
        """Zavolá ``AmcrCustomAdminSite.import_data`` s nekonfigurovaným adresářem reportů.

        :param method: ``"get"`` nebo ``"post"``.
        :param data_file: Mock nahrávaného souboru pro POST (ignorováno pro GET).
        :return: ``TemplateResponse`` vrácená view.
        """
        fake = FakeRedis(decode_responses=True)
        request_factory_method = getattr(self.factory, method)
        if method == "post":
            form_mock = MagicMock()
            form_mock.is_valid.return_value = True
            form_mock.cleaned_data = {
                "performed_action": ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                "data_file": data_file,
            }
            request = request_factory_method("/admin/core/import-data/")
        else:
            form_mock = None
            request = request_factory_method("/admin/core/import-data/")
        request.user = _StubUser(USER_ID)
        request._dont_enforce_csrf_checks = True

        with patch.object(AmcrCustomAdminSite, "get_app_list", return_value=[]), patch.object(
            AmcrCustomAdminSite, "each_context", return_value={}
        ), patch.object(AmcrCustomAdminSite, "redis_connector", fake), patch(
            "core.admin_sites.is_maintenance_in_progress", return_value=True
        ), patch(
            "core.admin_sites.check_import_report_directory",
            return_value=(None, None, "Missing required DIRECTORY_PATH setting"),
        ), patch(
            "core.admin_sites.ImportDataAdminForm", return_value=form_mock
        ):
            site = AmcrCustomAdminSite()
            response = site.import_data(request)
        return response, fake

    def test_get_shows_error_instead_of_upload_form(self):
        """GET bez nakonfigurovaného adresáře reportů nesmí vykreslit upload formulář."""
        response, _fake = self._call("get")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("form", response.context_data)
        self.assertIn("error_message", response.context_data)

    def test_post_does_not_dispatch_validation(self):
        """POST bez nakonfigurovaného adresáře reportů nesmí založit job ani dispatchnout validaci."""
        data_file = MagicMock()
        data_file.read.return_value = b"PK\x03\x04fake-zip-bytes"

        with patch("cron.tasks.run_data_import_validation.delay") as delay_mock:
            response, fake = self._call("post", data_file=data_file)

        self.assertEqual(response.status_code, 200)
        delay_mock.assert_not_called()
        self.assertIsNone(fake.get(f"import_data_current_job_{USER_ID}"))
        data_file.read.assert_not_called()


class ImportDataMaintenanceGateTest(SimpleTestCase):
    """Ověřuje zpětnou vazbu při odeslání formuláře mimo režim údržby."""

    def setUp(self):
        """Připraví ``RequestFactory`` sdílenou napříč testy."""
        self.factory = RequestFactory()

    def _call(self, method):
        """Zavolá ``import_data`` mimo režim údržby zadanou HTTP metodou.

        :param method: ``"get"`` nebo ``"post"``.
        :return: ``TemplateResponse`` vrácená view.
        """
        fake = FakeRedis(decode_responses=True)
        request = getattr(self.factory, method)("/admin/core/import-data/")
        request.user = _StubUser(USER_ID)
        request._dont_enforce_csrf_checks = True

        with patch.object(AmcrCustomAdminSite, "get_app_list", return_value=[]), patch.object(
            AmcrCustomAdminSite, "each_context", return_value={}
        ), patch.object(AmcrCustomAdminSite, "redis_connector", fake), patch(
            "core.admin_sites.is_maintenance_in_progress", return_value=False
        ):
            return AmcrCustomAdminSite().import_data(request)

    def test_post_outside_maintenance_reports_why_nothing_happened(self):
        """POST mimo údržbu musí vysvětlit, proč se import nespustil — ne jen překreslit stránku."""
        response = self._call("post")

        self.assertIn("error_message", response.context_data)
        self.assertEqual(
            str(response.context_data["error_message_details"]),
            "core.templates.admin.import_data.not_maintenance",
        )

    def test_get_outside_maintenance_shows_no_error(self):
        """Pouhé otevření stránky mimo údržbu chybu nehlásí — uživatel zatím nic neodeslal."""
        response = self._call("get")

        self.assertNotIn("error_message", response.context_data)
        self.assertIn("form", response.context_data)
