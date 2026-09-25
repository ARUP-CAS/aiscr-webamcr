"""Jednotkové testy sdíleného úklidu per-job klíčů importní úlohy (``expire_import_job_keys``).

Klíče se na terminální cestě pouze expirují, nikdy nemažou — report musí zůstat stažitelný.
``FakeRedis`` TTL nesleduje, takže se testuje zaznamenaná posloupnost operací v pipeline.
"""

from unittest import mock

from core.tests.fake_redis import FakeRedis
from cron import tasks
from django.test import SimpleTestCase

JOB = "job-expire-1"


def _fake(**initial):
    """Sestaví ``FakeRedis`` s předvyplněnými klíči úlohy.

    :param initial: Klíče a hodnoty, které se do fake Redisu zapíšou.
    :return: Instance ``FakeRedis``.
    """
    return FakeRedis(initial=initial)


def _expired_keys(fake, ttl):
    """Spustí úklid a vrátí klíče, kterým byla nastavena expirace.

    :param fake: ``FakeRedis``, nad kterým úklid proběhne.
    :param ttl: Doba retence předaná úklidu.
    :return: Množina klíčů, na které bylo zavoláno ``expire``.
    """
    expired = set()
    original = FakeRedis.FakePipeline.expire

    def spy(self, key, seconds):
        expired.add(key)
        return original(self, key, seconds)

    with mock.patch.object(FakeRedis.FakePipeline, "expire", spy):
        tasks.expire_import_job_keys(fake, JOB, ttl)
    return expired


class ExpireImportJobKeysTest(SimpleTestCase):
    """Testy pro ``cron.tasks.expire_import_job_keys``."""

    def test_record_keys_are_expired_according_to_the_counter(self):
        """S platným čítačem se expirují právě klíče záznamů v jeho rozsahu."""
        fake = _fake(
            **{
                f"import_data_count_{JOB}": 3,
                f"import_data_{JOB}_record_0": "{}",
                f"import_data_{JOB}_record_1": "{}",
                f"import_data_{JOB}_record_2": "{}",
            }
        )

        expired = _expired_keys(fake, tasks.IMPORT_DATA_EXPIRATION_SECONDS)

        for index in range(3):
            self.assertIn(f"import_data_{JOB}_record_{index}", expired)

    def test_record_keys_are_found_by_scan_when_the_counter_is_gone(self):
        """Bez čítače se klíče záznamů dohledají scanem — jinak by zůstaly bez TTL napořád.

        Validace je na úspěšné cestě ``persist``uje, takže by je bez expirace nic nesmazalo.
        """
        fake = _fake(
            **{
                f"import_data_{JOB}_record_0": "{}",
                f"import_data_{JOB}_record_1": "{}",
            }
        )

        expired = _expired_keys(fake, tasks.IMPORT_DATA_EXPIRATION_SECONDS)

        self.assertIn(f"import_data_{JOB}_record_0", expired)
        self.assertIn(f"import_data_{JOB}_record_1", expired)

    def test_unparseable_counter_falls_back_to_scan(self):
        """Nečíselný čítač se ignoruje a klíče se dohledají scanem."""
        fake = _fake(
            **{
                f"import_data_count_{JOB}": "not-a-number",
                f"import_data_{JOB}_record_0": "{}",
            }
        )

        expired = _expired_keys(fake, tasks.IMPORT_DATA_EXPIRATION_SECONDS)

        self.assertIn(f"import_data_{JOB}_record_0", expired)

    def test_scan_does_not_touch_another_jobs_keys(self):
        """Scan je omezen vzorem na jednu úlohu — klíče jiné úlohy zůstanou nedotčené."""
        fake = _fake(
            **{
                f"import_data_{JOB}_record_0": "{}",
                "import_data_other-job_record_0": "{}",
            }
        )

        expired = _expired_keys(fake, tasks.IMPORT_DATA_EXPIRATION_SECONDS)

        self.assertIn(f"import_data_{JOB}_record_0", expired)
        self.assertNotIn("import_data_other-job_record_0", expired)

    def test_all_per_job_suffixes_are_expired(self):
        """Expirace se nastaví všem per-job klíčům ze sdíleného seznamu suffixů."""
        fake = _fake(**{f"import_data_count_{JOB}": 0})

        expired = _expired_keys(fake, tasks.IMPORT_DATA_EXPIRATION_SECONDS)

        for suffix in tasks.IMPORT_DATA_JOB_KEY_SUFFIXES:
            self.assertIn(f"{suffix}_{JOB}", expired)
