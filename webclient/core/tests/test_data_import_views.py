"""Jednotkové testy autorizace a fázového větvení importních view.

Pokrývá ``DataImportCancel`` (uvolnění locku / stop podle fáze) a kontrolu vlastnictví
úlohy (``_check_import_ownership``) na ``DataImportStop`` a ``DataImportProgress``. Všechna
tři view pracují výhradně s Redis (žádný přístup do DB), takže se testují přes
``RequestFactory`` s odlehčeným uživatelem a ``FakeRedis`` v decode režimu — bez databáze.
"""

import json
from unittest import mock

from core.connectors import RedisConnector
from core.tests.fake_redis import FakeRedis
from core.views import DataImportCancel, DataImportProgress, DataImportReset, DataImportStop
from cron import tasks
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase

JOB = "job-abc-123"
OWNER_ID = 7
OTHER_ID = 99


class _StubUser:
    """Minimální náhrada uživatele pro ``RequestFactory`` — nese jen atributy čtené view/mixinem."""

    def __init__(self, user_id, is_superuser=True):
        """
        :param user_id: Hodnota ``id`` porovnávaná s vlastníkem úlohy v Redis.
        :param is_superuser: Zda je uživatel superuživatel (brána na začátku view).
        """
        self.id = user_id
        self.pk = user_id
        self.is_superuser = is_superuser
        self.is_active = True
        self.is_authenticated = True


def _fake(phase, *, user_id=OWNER_ID, extra=None):
    """Sestaví ``FakeRedis`` v decode režimu se stavem jedné importní úlohy.

    :param phase: Hodnota ``import_data_phase_{JOB}``.
    :param user_id: Vlastník úlohy zapsaný do ``import_data_user_{JOB}``.
    :param extra: Volitelné další klíče/hodnoty k předvyplnění.
    :return: Instance ``FakeRedis`` emulující ``get_connection_decode()``.
    """
    initial = {
        f"import_data_phase_{JOB}": phase,
        f"import_data_user_{JOB}": user_id,
        f"import_data_lock_token_{JOB}": "tok-xyz",
        f"import_data_current_job_{user_id}": JOB,
    }
    if extra:
        initial.update(extra)
    return FakeRedis(initial=initial, decode_responses=True)


class DataImportCancelTest(SimpleTestCase):
    """Testy fázového větvení a autorizace view ``DataImportCancel``."""

    def setUp(self):
        """Připraví ``RequestFactory`` sdílenou napříč testy."""
        self.factory = RequestFactory()

    def _post(self, fake, user_id=OWNER_ID, is_superuser=True):
        """Zavolá ``DataImportCancel`` přes ``RequestFactory`` s daným uživatelem a fakem Redis.

        :param fake: ``FakeRedis`` vrácený z ``get_connection_decode()``.
        :param user_id: ``id`` přihlášeného uživatele.
        :param is_superuser: Zda je uživatel superuživatel.
        :return: HTTP odpověď view.
        """
        request = self.factory.post(f"/data-import-cancel/{JOB}")
        request.user = _StubUser(user_id, is_superuser)
        # RequestFactory nemá CSRF token; obejdi csrf_protect stejně jako testovací Client.
        request._dont_enforce_csrf_checks = True
        with mock.patch("core.views.RedisConnector.get_connection_decode", return_value=fake):
            return DataImportCancel.as_view()(request, job_id=JOB)

    def test_awaiting_approval_releases_lock_and_marks_canceled(self):
        """awaiting_approval: kterýkoli superuživatel uvolní lock, fáze → canceled, ukazatel zmizí."""
        fake = _fake(tasks.IMPORT_PHASE_AWAITING_APPROVAL)

        # Force-cancel smí provést i jiný než vlastník — proto OTHER_ID.
        response = self._post(fake, user_id=OTHER_ID)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["result"], "ok")
        self.assertEqual(fake.get(f"import_data_phase_{JOB}"), tasks.IMPORT_PHASE_CANCELED)
        self.assertEqual(
            fake.get(f"import_data_status_message_tr_{JOB}"),
            tasks.translation_value("cron.tasks.run_data_import.cancelled"),
        )
        self.assertIsNone(fake.get(f"import_data_current_job_{OWNER_ID}"))

    def test_validating_owner_sets_stop_sentinel(self):
        """validating: vlastník cancel ≡ stop — nastaví stop sentinel, fázi nemění."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING)

        response = self._post(fake, user_id=OWNER_ID)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["result"], "ok")
        self.assertIsNotNone(fake.get(f"import_data_stop_{JOB}"))
        self.assertEqual(fake.get(f"import_data_phase_{JOB}"), tasks.IMPORT_PHASE_VALIDATING)

    def test_validating_non_owner_forbidden(self):
        """validating: cizí superuživatel je odmítnut (403) a stop se nenastaví."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING)

        response = self._post(fake, user_id=OTHER_ID)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content)["result"], "error")
        self.assertIsNone(fake.get(f"import_data_stop_{JOB}"))

    def test_importing_phase_conflict(self):
        """importing: cancel se odmítne (409) — běžící import se ukončuje přes Stop."""
        fake = _fake(tasks.IMPORT_PHASE_IMPORTING)

        response = self._post(fake, user_id=OWNER_ID)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(json.loads(response.content)["result"], "error")

    def test_terminal_phase_conflict(self):
        """Terminální fáze (finished): není co rušit → 409."""
        fake = _fake(tasks.IMPORT_PHASE_FINISHED)

        response = self._post(fake, user_id=OWNER_ID)

        self.assertEqual(response.status_code, 409)

    def test_requires_superuser(self):
        """Ne-superuživatel dostane PermissionDenied bez ohledu na fázi."""
        fake = _fake(tasks.IMPORT_PHASE_AWAITING_APPROVAL)

        with self.assertRaises(PermissionDenied):
            self._post(fake, user_id=OWNER_ID, is_superuser=False)


class DataImportOwnershipTest(SimpleTestCase):
    """Testy kontroly vlastnictví úlohy na ``DataImportStop`` a ``DataImportProgress``."""

    def setUp(self):
        """Připraví ``RequestFactory`` sdílenou napříč testy."""
        self.factory = RequestFactory()

    def _get(self, view, fake, user_id):
        """Zavolá GET view přes ``RequestFactory`` s daným uživatelem a fakem Redis.

        :param view: Třída view (``DataImportStop`` / ``DataImportProgress``).
        :param fake: ``FakeRedis`` vrácený z ``get_connection_decode()``.
        :param user_id: ``id`` přihlášeného uživatele.
        :return: HTTP odpověď view.
        """
        request = self.factory.get(f"/data-import/{JOB}")
        request.user = _StubUser(user_id, is_superuser=True)
        with mock.patch("core.views.RedisConnector.get_connection_decode", return_value=fake):
            return view.as_view()(request, job_id=JOB)

    def test_stop_owner_allowed(self):
        """Vlastník smí zastavit svou úlohu — stop sentinel se nastaví."""
        fake = _fake(tasks.IMPORT_PHASE_IMPORTING)

        response = self._get(DataImportStop, fake, OWNER_ID)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["result"], "ok")
        self.assertIsNotNone(fake.get(f"import_data_stop_{JOB}"))

    def test_stop_non_owner_forbidden(self):
        """Cizí superuživatel nesmí zastavit cizí úlohu (403) a stop se nenastaví."""
        fake = _fake(tasks.IMPORT_PHASE_IMPORTING)

        response = self._get(DataImportStop, fake, OTHER_ID)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content)["result"], "error")
        self.assertIsNone(fake.get(f"import_data_stop_{JOB}"))

    def test_progress_non_owner_forbidden(self):
        """Progress endpoint vystavuje validační data — cizímu uživateli vrátí 403."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING)

        response = self._get(DataImportProgress, fake, OTHER_ID)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content)["result"], "error")


class DataImportProgressValidationCursorTest(SimpleTestCase):
    """Testy pro ``DataImportProgress`` — ``validation_since``/``validation_cursor``."""

    def setUp(self):
        """Připraví ``RequestFactory`` sdílenou napříč testy."""
        self.factory = RequestFactory()

    def _get(self, fake, validation_since=None, user_id=OWNER_ID):
        """Zavolá ``DataImportProgress`` s volitelným query parametrem ``validation_since``.

        :param fake: ``FakeRedis`` vrácený z ``get_connection_decode()``.
        :param validation_since: Hodnota query parametru, nebo ``None`` pro jeho vynechání.
        :param user_id: ``id`` přihlášeného uživatele.
        :return: HTTP odpověď view.
        """
        url = f"/data-import/{JOB}"
        if validation_since is not None:
            url += f"?validation_since={validation_since}"
        request = self.factory.get(url)
        request.user = _StubUser(user_id, is_superuser=True)
        with mock.patch("core.views.RedisConnector.get_connection_decode", return_value=fake):
            return DataImportProgress.as_view()(request, job_id=JOB)

    @staticmethod
    def _push_validation_rows(fake, count):
        """Přidá ``count`` validačních řádků do ``import_data_validation_details_{JOB}``.

        :param fake: ``FakeRedis``, do kterého se řádky zapíší.
        :param count: Počet řádků k zápisu.
        """
        for i in range(count):
            fake.rpush(
                f"import_data_validation_details_{JOB}",
                json.dumps(
                    {"item_order": i, "file_name": "f", "primary_key_import": str(i), "validation_result": "ok"}
                ),
            )

    def test_no_since_param_returns_all_rows_and_cursor(self):
        """Bez ``validation_since`` vrátí všechny řádky a ``validation_cursor`` rovný jejich počtu."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING)
        self._push_validation_rows(fake, 3)

        response = self._get(fake)

        data = json.loads(response.content)
        self.assertEqual(len(data["validation_results"]), 3)
        self.assertEqual(data["validation_cursor"], 3)

    def test_since_param_returns_only_appended_rows(self):
        """S ``validation_since`` vrátí jen řádky přidané od tohoto indexu, cursor je nová celková délka."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING)
        self._push_validation_rows(fake, 5)

        response = self._get(fake, validation_since=3)

        data = json.loads(response.content)
        self.assertEqual(len(data["validation_results"]), 2)
        self.assertEqual(data["validation_cursor"], 5)

    def test_since_param_beyond_list_length_returns_empty_and_stable_cursor(self):
        """``validation_since`` za koncem seznamu vrátí prázdný delta a cursor beze změny."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING)
        self._push_validation_rows(fake, 2)

        response = self._get(fake, validation_since=2)

        data = json.loads(response.content)
        self.assertEqual(data["validation_results"], [])
        self.assertEqual(data["validation_cursor"], 2)

    def test_invalid_since_param_falls_back_to_zero(self):
        """Neplatný (nečíselný) ``validation_since`` se chová jako 0 (vrátí vše)."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING)
        self._push_validation_rows(fake, 2)

        response = self._get(fake, validation_since="not-a-number")

        data = json.loads(response.content)
        self.assertEqual(len(data["validation_results"]), 2)
        self.assertEqual(data["validation_cursor"], 2)

    def test_negative_since_param_clamped_to_zero(self):
        """Záporný ``validation_since`` se ořeže na 0 (vrátí vše), nikoli chybný záporný lrange."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING)
        self._push_validation_rows(fake, 2)

        response = self._get(fake, validation_since=-5)

        data = json.loads(response.content)
        self.assertEqual(len(data["validation_results"]), 2)
        self.assertEqual(data["validation_cursor"], 2)


class DataImportResetTest(SimpleTestCase):
    """Testy ručního superuživatelského resetu zaseklé importní úlohy (``DataImportReset``)."""

    def setUp(self):
        """Připraví ``RequestFactory`` sdílenou napříč testy."""
        self.factory = RequestFactory()

    def _post(self, fake, user_id=OWNER_ID, is_superuser=True, job_id=JOB):
        """Zavolá ``DataImportReset`` přes ``RequestFactory``.

        :param fake: ``FakeRedis`` vrácený z ``get_connection_decode()``.
        :param user_id: ``id`` přihlášeného uživatele.
        :param is_superuser: Zda je uživatel superuživatel.
        :param job_id: ``job_id`` v URL; ``None`` testuje no-arg variantu (přes active_job_id).
        :return: HTTP odpověď view.
        """
        request = self.factory.post("/data-import-reset")
        request.user = _StubUser(user_id, is_superuser)
        request._dont_enforce_csrf_checks = True
        kwargs = {"job_id": job_id} if job_id is not None else {}
        with mock.patch("core.views.RedisConnector.get_connection_decode", return_value=fake):
            return DataImportReset.as_view()(request, **kwargs)

    def _assert_reset(self, fake):
        """Ověří společné efekty úspěšného resetu na fake Redis."""
        self.assertEqual(fake.get(f"import_data_phase_{JOB}"), tasks.IMPORT_PHASE_FAILED)
        self.assertEqual(fake.get(f"import_data_failure_reason_{JOB}"), tasks.IMPORT_FAILURE_REASON_ERROR)
        self.assertEqual(
            fake.get(f"import_data_status_message_tr_{JOB}"),
            tasks.translation_value("cron.tasks.run_data_import.reset_by_admin"),
        )
        self.assertIsNotNone(fake.get(f"import_data_stop_{JOB}"))
        self.assertIsNone(fake.get(f"import_data_current_job_{OWNER_ID}"))
        self.assertIsNone(fake.get(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY))

    def test_reset_validating_job(self):
        """validating: reset ukončí úlohu (failed), uvolní lock a vyčistí ukazatele."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING, extra={RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY: JOB})

        response = self._post(fake, user_id=OWNER_ID)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["result"], "ok")
        self._assert_reset(fake)

    def test_reset_importing_job(self):
        """importing: reset zaseklého importu je povolen a ukončí úlohu."""
        fake = _fake(tasks.IMPORT_PHASE_IMPORTING, extra={RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY: JOB})

        response = self._post(fake, user_id=OWNER_ID)

        self.assertEqual(response.status_code, 200)
        self._assert_reset(fake)

    def test_reset_by_any_superuser(self):
        """Reset smí provést kterýkoli superuživatel, ne jen vlastník (dead-worker recovery)."""
        fake = _fake(tasks.IMPORT_PHASE_IMPORTING, extra={RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY: JOB})

        response = self._post(fake, user_id=OTHER_ID)

        self.assertEqual(response.status_code, 200)
        self._assert_reset(fake)

    def test_reset_awaiting_approval_job(self):
        """awaiting_approval: reset je rovněž povolen (superset force-cancelu)."""
        fake = _fake(tasks.IMPORT_PHASE_AWAITING_APPROVAL, extra={RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY: JOB})

        response = self._post(fake, user_id=OWNER_ID)

        self.assertEqual(response.status_code, 200)
        self._assert_reset(fake)

    def test_reset_no_arg_resolves_active_job(self):
        """No-arg varianta dohledá job přes ``IMPORT_DATA_ACTIVE_JOB_KEY`` (blokovaný admin)."""
        fake = _fake(tasks.IMPORT_PHASE_IMPORTING, extra={RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY: JOB})

        response = self._post(fake, user_id=OTHER_ID, job_id=None)

        self.assertEqual(response.status_code, 200)
        self._assert_reset(fake)

    def test_reset_terminal_phase_conflict(self):
        """Terminální fáze (finished): není co resetovat → 409, stav se nemění."""
        fake = _fake(tasks.IMPORT_PHASE_FINISHED, extra={RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY: JOB})

        response = self._post(fake, user_id=OWNER_ID)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(json.loads(response.content)["result"], "error")
        self.assertEqual(fake.get(f"import_data_phase_{JOB}"), tasks.IMPORT_PHASE_FINISHED)

    def test_reset_requires_superuser(self):
        """Ne-superuživatel dostane PermissionDenied."""
        fake = _fake(tasks.IMPORT_PHASE_VALIDATING, extra={RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY: JOB})

        with self.assertRaises(PermissionDenied):
            self._post(fake, user_id=OWNER_ID, is_superuser=False)
