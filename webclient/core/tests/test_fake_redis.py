"""Jednotkové testy dispatche ``FakeRedis.eval()``.

Testy zde volají výhradně reálné metody ``RedisConnector`` (nikoli ručně opsané kopie Lua textu), takže při jakékoli změně skriptu v
``connectors.py`` automaticky ověří, že ``FakeRedis`` danou konstantu stále rozpozná a chová se
k ní odpovídajícím způsobem.
"""

from core.connectors import RedisConnector
from core.tests.fake_redis import FakeRedis
from django.test import SimpleTestCase

JOB = "job-fake-redis-1"
TOKEN = "tok-abc"


class FakeRedisEvalDispatchTests(SimpleTestCase):
    """Ověřuje, že ``FakeRedis.eval`` rozlišuje skripty přesnou shodou, ne heuristikou."""

    def test_unrecognized_script_raises_instead_of_silently_matching(self):
        """Neznámý skript nesmí tiše spadnout do žádné existující větve dispatche."""
        fake = FakeRedis()
        with self.assertRaises(ValueError):
            fake.eval("-- nejde o žádný ze skriptů RedisConnector", 1, "some_key", "some_arg")

    def test_edited_script_constant_is_still_recognized_by_value(self):
        """Dispatch je vázán na aktuální hodnotu konstanty, ne na její identitu při importu."""
        fake = FakeRedis(initial={RedisConnector.IMPORT_DATA_LOCK_KEY: TOKEN})
        # Simulate reading the script text fresh off RedisConnector, as production code does.
        released = fake.eval(RedisConnector._RELEASE_LOCK_SCRIPT, 1, RedisConnector.IMPORT_DATA_LOCK_KEY, TOKEN)
        self.assertEqual(released, 1)
        self.assertIsNone(fake.get(RedisConnector.IMPORT_DATA_LOCK_KEY))

    def test_release_lock_script_rejects_mismatched_token(self):
        """Compare-then-delete skript lock nesmí smazat, pokud token nesedí."""
        fake = FakeRedis(initial={RedisConnector.IMPORT_DATA_LOCK_KEY: TOKEN})
        result = RedisConnector.release_import_lock(fake, "wrong-token")
        self.assertFalse(result)
        self.assertEqual(fake.get(RedisConnector.IMPORT_DATA_LOCK_KEY), TOKEN.encode("utf-8"))

    def test_release_lock_script_deletes_on_matching_token(self):
        """Compare-then-delete skript lock smaže, pokud token sedí."""
        fake = FakeRedis(initial={RedisConnector.IMPORT_DATA_LOCK_KEY: TOKEN})
        result = RedisConnector.release_import_lock(fake, TOKEN)
        self.assertTrue(result)
        self.assertIsNone(fake.get(RedisConnector.IMPORT_DATA_LOCK_KEY))

    def test_delete_if_value_matches_reuses_release_lock_script(self):
        """``delete_if_value_matches`` používá tentýž skript jako ``release_import_lock``."""
        key = f"import_data_current_job_{7}"
        fake = FakeRedis(initial={key: JOB})
        self.assertFalse(RedisConnector.delete_if_value_matches(fake, key, "other-job"))
        self.assertTrue(RedisConnector.delete_if_value_matches(fake, key, JOB))
        self.assertIsNone(fake.get(key))

    def test_refresh_lock_script_extends_ttl_only_on_matching_token(self):
        """Compare-then-expire skript prodlouží TTL pouze při shodě tokenu."""
        fake = FakeRedis(initial={RedisConnector.IMPORT_DATA_LOCK_KEY: TOKEN})
        self.assertFalse(RedisConnector.refresh_import_lock(fake, "wrong-token", 60))
        self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), -1)
        self.assertTrue(RedisConnector.refresh_import_lock(fake, TOKEN, 60))
        self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), 60)

    def test_persist_lock_script_clears_ttl_only_on_matching_token(self):
        """Compare-then-persist skript zruší TTL pouze při shodě tokenu."""
        fake = FakeRedis()
        fake.set(RedisConnector.IMPORT_DATA_LOCK_KEY, TOKEN, ex=30)
        self.assertFalse(RedisConnector.persist_import_lock(fake, "wrong-token"))
        self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), 30)
        self.assertTrue(RedisConnector.persist_import_lock(fake, TOKEN))
        self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), -1)

    def _claimable_state(self):
        """Sestaví stav Redis, ve kterém lze úlohu ``JOB`` nárokovat ze stavu ``awaiting_approval``."""
        return {
            f"import_data_phase_{JOB}": "awaiting_approval",
            f"import_data_valid_{JOB}": "1",
            f"import_data_lock_token_{JOB}": TOKEN,
            RedisConnector.IMPORT_DATA_LOCK_KEY: TOKEN,
        }

    def test_claim_awaiting_import_transitions_phase_on_success(self):
        """Nárokování úspěšně přepne fázi a vrátí vlastnický token."""
        fake = FakeRedis(initial=self._claimable_state())
        claimed, token = RedisConnector.claim_awaiting_import(fake, JOB, "awaiting_approval", "importing", 60)
        self.assertTrue(claimed)
        self.assertEqual(token, TOKEN.encode("utf-8"))
        self.assertEqual(fake.get(f"import_data_phase_{JOB}"), b"importing")
        self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), 60)

    def test_rejected_claim_preserves_phase_and_lock_ttl(self):
        """Odmítnutý nárok nesmí změnit fázi ani TTL cizího nebo vlastního locku."""
        for key, value in (
            (f"import_data_phase_{JOB}", "importing"),
            (f"import_data_valid_{JOB}", "0"),
            (f"import_data_lock_token_{JOB}", "stale-token"),
            (RedisConnector.IMPORT_DATA_LOCK_KEY, "other-token"),
        ):
            with self.subTest(key=key):
                state = self._claimable_state()
                state[key] = value
                fake = FakeRedis(initial=state)
                fake.expire(RedisConnector.IMPORT_DATA_LOCK_KEY, 30)
                claimed, token = RedisConnector.claim_awaiting_import(fake, JOB, "awaiting_approval", "importing", 60)
                self.assertFalse(claimed)
                self.assertIsNone(token)
                self.assertEqual(fake.get(f"import_data_phase_{JOB}"), state[f"import_data_phase_{JOB}"].encode())
                self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), 30)
                self.assertEqual(
                    fake.get(RedisConnector.IMPORT_DATA_LOCK_KEY), state[RedisConnector.IMPORT_DATA_LOCK_KEY].encode()
                )

    def test_claim_awaiting_import_rejects_wrong_phase(self):
        """Nárokování selže, pokud úloha není v očekávané fázi (souběžný druhý Start)."""
        state = self._claimable_state()
        state[f"import_data_phase_{JOB}"] = "importing"
        fake = FakeRedis(initial=state)
        claimed, token = RedisConnector.claim_awaiting_import(fake, JOB, "awaiting_approval", "importing", 60)
        self.assertFalse(claimed)
        self.assertIsNone(token)

    def test_claim_awaiting_import_rejects_stale_lock_token(self):
        """Nárokování selže, pokud globální lock mezitím převzala jiná úloha."""
        state = self._claimable_state()
        state[RedisConnector.IMPORT_DATA_LOCK_KEY] = "other-token"
        fake = FakeRedis(initial=state)
        claimed, token = RedisConnector.claim_awaiting_import(fake, JOB, "awaiting_approval", "importing", 60)
        self.assertFalse(claimed)
        self.assertIsNone(token)

    def _cancelable_state(self):
        """Sestaví stav Redis pro úlohu ``JOB`` čekající na zrušení ze stavu ``awaiting_approval``."""
        return {
            f"import_data_phase_{JOB}": "awaiting_approval",
            f"import_data_lock_token_{JOB}": TOKEN,
            RedisConnector.IMPORT_DATA_LOCK_KEY: TOKEN,
            f"import_data_current_job_{7}": JOB,
            RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY: JOB,
        }

    def test_cancel_awaiting_import_clears_pointers_on_success(self):
        """Zrušení přepne fázi, uloží stavovou zprávu a uklidí ukazatele i globální lock."""
        fake = FakeRedis(initial=self._cancelable_state())
        result = RedisConnector.cancel_awaiting_import(fake, JOB, "7", "status.canceled")
        self.assertTrue(result)
        self.assertEqual(fake.get(f"import_data_phase_{JOB}"), b"canceled")
        self.assertEqual(fake.get(f"import_data_status_message_tr_{JOB}"), b"status.canceled")
        self.assertIsNone(fake.get(RedisConnector.IMPORT_DATA_LOCK_KEY))
        self.assertIsNone(fake.get(f"import_data_current_job_{7}"))
        self.assertIsNone(fake.get(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY))

    def test_cancel_awaiting_import_rejects_already_started_job(self):
        """Zrušení nesmí zasáhnout úlohu, kterou mezitím převzal Start (jiná fáze)."""
        state = self._cancelable_state()
        state[f"import_data_phase_{JOB}"] = "importing"
        fake = FakeRedis(initial=state)
        result = RedisConnector.cancel_awaiting_import(fake, JOB, "7", "status.canceled")
        self.assertFalse(result)
        self.assertEqual(fake.get(f"import_data_phase_{JOB}"), b"importing")

    def _validating_state(self):
        """Sestaví stav Redis pro úlohu ``JOB`` probíhající ve fázi ``validating``."""
        return {
            f"import_data_phase_{JOB}": "validating",
            f"import_data_lock_token_{JOB}": TOKEN,
            RedisConnector.IMPORT_DATA_LOCK_KEY: TOKEN,
        }

    def test_finalize_validation_transitions_on_success(self):
        """Finalizace validace přepne fázi do ``awaiting_approval``, pokud nedošlo ke stopu."""
        fake = FakeRedis(initial=self._validating_state())
        fake.expire(RedisConnector.IMPORT_DATA_LOCK_KEY, 30)
        result = RedisConnector.finalize_validation(fake, JOB)
        self.assertTrue(result)
        self.assertEqual(fake.get(f"import_data_phase_{JOB}"), b"awaiting_approval")
        self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), -1)

    def test_rejected_finalization_preserves_phase_and_lock_ttl(self):
        """Odmítnutá finalizace nesmí přepnout fázi ani odstranit expiraci locku."""
        for key, value in (
            (f"import_data_phase_{JOB}", "importing"),
            (f"import_data_stop_{JOB}", "1"),
            (f"import_data_lock_token_{JOB}", "stale-token"),
            (RedisConnector.IMPORT_DATA_LOCK_KEY, "other-token"),
        ):
            with self.subTest(key=key):
                state = self._validating_state()
                state[key] = value
                fake = FakeRedis(initial=state)
                fake.expire(RedisConnector.IMPORT_DATA_LOCK_KEY, 30)
                self.assertFalse(RedisConnector.finalize_validation(fake, JOB))
                self.assertEqual(fake.get(f"import_data_phase_{JOB}"), state[f"import_data_phase_{JOB}"].encode())
                self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), 30)
                self.assertEqual(
                    fake.get(RedisConnector.IMPORT_DATA_LOCK_KEY), state[RedisConnector.IMPORT_DATA_LOCK_KEY].encode()
                )

    def test_finalize_then_claim_restores_lock_expiry(self):
        """Lock při čekání na schválení neexpiruje a při spuštění získá požadované TTL."""
        fake = FakeRedis(initial=self._validating_state())
        fake.expire(RedisConnector.IMPORT_DATA_LOCK_KEY, 30)
        fake.set(f"import_data_valid_{JOB}", "1")
        self.assertTrue(RedisConnector.finalize_validation(fake, JOB))
        self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), -1)
        claimed, token = RedisConnector.claim_awaiting_import(fake, JOB, "awaiting_approval", "importing", 48 * 3600)
        self.assertTrue(claimed)
        self.assertEqual(token, TOKEN.encode())
        self.assertEqual(fake.ttl(RedisConnector.IMPORT_DATA_LOCK_KEY), 48 * 3600)

    def test_finalize_validation_rejects_when_stop_requested(self):
        """Finalizace selže, pokud byl mezitím zapsán stop příznak validace."""
        state = self._validating_state()
        state[f"import_data_stop_{JOB}"] = "1"
        fake = FakeRedis(initial=state)
        result = RedisConnector.finalize_validation(fake, JOB)
        self.assertFalse(result)
        self.assertEqual(fake.get(f"import_data_phase_{JOB}"), b"validating")
