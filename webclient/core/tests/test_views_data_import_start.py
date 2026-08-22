"""Test pro ``DataImportStart`` — atomický claim fáze proti souběžným Start požadavkům
(review r3703505178 / r3747341985).

Testuje výhradně přes ``RequestFactory``/``FakeRedis`` (bez DB), stejným stylem jako
``core.tests.test_admin_sites_import_data``. Dokud ``FakeRedis.eval`` skutečně nevykonával
``RedisConnector._CLAIM_AWAITING_IMPORT_SCRIPT`` (jen vracel ``1``), nešlo tento souběh
otestovat vůbec — ``claimed, token = connection.eval(...)`` spadlo na ``TypeError``.
"""

import json
from unittest.mock import patch

from core.connectors import RedisConnector
from core.tests.fake_redis import FakeRedis
from core.views import DataImportStart
from cron import tasks
from django.test import RequestFactory, SimpleTestCase

USER_ID = 42
JOB_ID = "job-under-test"
LOCK_TOKEN = "lock-token-abc"


class _StubUser:
    """Minimální náhrada uživatele pro ``RequestFactory`` — nese jen atributy čtené view."""

    def __init__(self, user_id):
        self.id = user_id
        self.pk = user_id
        self.is_superuser = True
        self.is_staff = True
        self.is_active = True
        self.is_authenticated = True


class DataImportStartConcurrencyTest(SimpleTestCase):
    """Ověřuje, že ze dvou souběžných Start požadavků nad stejnou úlohou uspěje jen jeden."""

    def setUp(self):
        """Připraví ``RequestFactory`` a ``FakeRedis`` s úlohou ve fázi ``awaiting_approval``."""
        self.factory = RequestFactory()
        self.fake = FakeRedis(decode_responses=True)
        self.fake.set(f"import_data_user_{JOB_ID}", USER_ID)
        self.fake.set(f"import_data_phase_{JOB_ID}", tasks.IMPORT_PHASE_AWAITING_APPROVAL)
        self.fake.set(f"import_data_valid_{JOB_ID}", "1")
        self.fake.set(f"import_data_lock_token_{JOB_ID}", LOCK_TOKEN)
        self.fake.set(RedisConnector.IMPORT_DATA_LOCK_KEY, LOCK_TOKEN)

    def _post(self):
        """Zavolá ``DataImportStart.post`` s mocknutým superuživatelem nad sdíleným ``FakeRedis``."""
        request = self.factory.post(f"/core/data-import/{JOB_ID}/start/")
        request.user = _StubUser(USER_ID)
        with patch.object(RedisConnector, "get_connection_decode", return_value=self.fake), patch(
            "core.views.is_maintenance_in_progress", return_value=True
        ), patch("cron.tasks.run_data_import.delay") as delay_mock:
            response = DataImportStart.as_view()(request, job_id=JOB_ID)
        return response, delay_mock

    def test_only_one_of_two_concurrent_starts_is_claimed(self):
        """Dva Start požadavky nad stejnou úlohou: první nárokuje fázi a dispatchne task,
        druhý narazí na již přepnutou fázi a je odmítnut — task se nedispatchne dvakrát."""
        first_response, first_delay = self._post()
        second_response, second_delay = self._post()

        self.assertEqual(first_response.status_code, 200)
        first_delay.assert_called_once_with(JOB_ID, USER_ID, LOCK_TOKEN)

        self.assertNotEqual(second_response.status_code, 200)
        second_delay.assert_not_called()

        self.assertEqual(self.fake.get(f"import_data_phase_{JOB_ID}"), tasks.IMPORT_PHASE_IMPORTING)

    def test_claim_transitions_phase_and_keeps_lock_token(self):
        """Úspěšný claim přepne fázi na ``importing`` a nesmaže vlastnící token locku."""
        response, delay_mock = self._post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["result"], "ok")
        delay_mock.assert_called_once_with(JOB_ID, USER_ID, LOCK_TOKEN)
        self.assertEqual(self.fake.get(f"import_data_phase_{JOB_ID}"), tasks.IMPORT_PHASE_IMPORTING)
        self.assertEqual(self.fake.get(RedisConnector.IMPORT_DATA_LOCK_KEY), LOCK_TOKEN)

    def test_claim_fails_when_global_lock_token_does_not_match(self):
        """Pokud globální lock mezitím ztratil vlastnictví (jiný token), claim selže a fáze se
        přepne na ``failed`` — reflektuje větev „lock lost“ ve view."""
        self.fake.set(RedisConnector.IMPORT_DATA_LOCK_KEY, "someone-elses-token")

        response, delay_mock = self._post()

        self.assertEqual(response.status_code, 409)
        delay_mock.assert_not_called()
        self.assertEqual(self.fake.get(f"import_data_phase_{JOB_ID}"), tasks.IMPORT_PHASE_FAILED)
