"""
Testy sémantiky zámku záznamu v Django cache (typicky Redis).

Účel
====
Reviewer upozornil, že chování zámku v ``PasApiBaseView._acquire_record_lock`` /
``_release_record_lock`` závisí na atomicitě konkrétního cache backendu:

- ``acquire`` používá ``cache.add(key, 1, ttl)`` (atomické v Redis) plus fallback
  ``cache.get(key) != 1`` → ``cache.set(key, 1, ttl)`` (samostatně NENÍ atomické).
- ``release`` používá ``cache.set(key, 0, ttl)`` — tj. zámek se „uvolní" tím, že
  hodnota klíče se sníží na ``0``, ne smazáním klíče. Re-acquire pak musí projít
  fallbackovou větví.

Testy reálně volají Django cache s nakonfigurovaným backendem projektu
a ověřují jednotlivé scénáře. Nejde o čisté unit-testy — chceme exercise
proti **produkčnímu** backendu (Redis), kde se případné vady atomicity
skutečně projeví.

Pokrytí
=======
1. Backend probe — varuje při ne-Redis backendu.
2. Acquire → release → re-acquire (single thread).
3. Re-entrant acquire selže (zámek držený).
4. Release-then-reacquire prochází fallbackovou větví
   (``cache.add`` selže, ``cache.get == 0``, fallback ``cache.set(1)``).
5. TTL expiry — krátký TTL skutečně způsobí automatické uvolnění klíče.
6. Konkurence threadů — právě jeden získá zámek.
7. Konkurence procesů (fork) — právě jeden získá zámek (atomicita ``cache.add``).
"""

import multiprocessing
import threading
import time

from api.views import _RECORD_LOCK_PREFIX, PasApiBaseView
from django.core.cache import cache
from django.test import TransactionTestCase


def _process_worker(ident, results_q):
    """Worker pro multiprocessing scénář — re-bootstrapuje Django state."""
    import django

    if not django.apps.apps.ready:
        django.setup()
    from api.views import PasApiBaseView as _PV

    results_q.put(_PV._acquire_record_lock(ident))


class RecordLockCacheTests(TransactionTestCase):
    """Scénáře ověřující chování record-lock vůči Django cache backendu.

    Použit ``TransactionTestCase`` (ne ``SimpleTestCase``), protože
    ``PasApiBaseView._acquire_record_lock`` volá ``get_record_lock_params``,
    který čte ``CustomAdminSettings`` z DB. Zároveň ``TransactionTestCase``
    umožňuje DB přístup z dalších threadů/procesů (commit po každém testu),
    což je nutné pro scénáře konkurence.
    """

    @staticmethod
    def _clear(ident):
        """Vymazat lock klíč mezi testy."""
        cache.delete(f"{_RECORD_LOCK_PREFIX}{ident}")

    def test_backend_is_redis(self):
        """Ověří, že je nakonfigurován Redis backend (jinak výsledky nemusí odpovídat produkci)."""
        underlying = cache._cache if hasattr(cache, "_cache") else cache
        backend_cls = type(underlying).__module__ + "." + type(underlying).__name__
        self.assertIn("redis", backend_cls.lower(), f"Očekáván Redis backend, je: {backend_cls}")

    def test_acquire_release_reacquire(self):
        """Sekvenční acquire → release → acquire prochází."""
        ident = "TEST_RL_BASIC"
        self._clear(ident)
        try:
            self.assertTrue(PasApiBaseView._acquire_record_lock(ident))
            PasApiBaseView._release_record_lock(ident)
            self.assertTrue(PasApiBaseView._acquire_record_lock(ident))
        finally:
            self._clear(ident)

    def test_reentrant_acquire_fails(self):
        """Druhý acquire bez release selže (zámek držený)."""
        ident = "TEST_RL_REENTRANT"
        self._clear(ident)
        try:
            self.assertTrue(PasApiBaseView._acquire_record_lock(ident))
            self.assertFalse(PasApiBaseView._acquire_record_lock(ident))
        finally:
            self._clear(ident)

    def test_release_uses_fallback_path(self):
        """Po release je klíč s hodnotou 0; další acquire musí projít fallbackem."""
        ident = "TEST_RL_FALLBACK"
        key = f"{_RECORD_LOCK_PREFIX}{ident}"
        self._clear(ident)
        try:
            PasApiBaseView._acquire_record_lock(ident)
            PasApiBaseView._release_record_lock(ident)
            self.assertEqual(cache.get(key), 0)
            self.assertTrue(PasApiBaseView._acquire_record_lock(ident))
            self.assertEqual(cache.get(key), 1)
        finally:
            self._clear(ident)

    def test_ttl_expiry(self):
        """Klíč s krátkým TTL expiruje a další ``cache.add`` projde."""
        ident = "TEST_RL_TTL"
        key = f"{_RECORD_LOCK_PREFIX}{ident}"
        short_ttl = 2
        self._clear(ident)
        try:
            cache.add(key, 1, timeout=short_ttl)
            self.assertEqual(cache.get(key), 1)
            time.sleep(short_ttl + 1)
            self.assertIsNone(cache.get(key))
            self.assertTrue(cache.add(key, 1, timeout=short_ttl))
        finally:
            self._clear(ident)

    def test_thread_contention_single_winner(self):
        """N threadů soutěží — právě jeden získá zámek."""
        ident = "TEST_RL_THREADS"
        self._clear(ident)
        n_threads = 16
        results = []
        barrier = threading.Barrier(n_threads)
        result_lock = threading.Lock()

        def worker():
            barrier.wait()
            ok = PasApiBaseView._acquire_record_lock(ident)
            with result_lock:
                results.append(ok)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        try:
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)
            winners = sum(1 for r in results if r)
            self.assertEqual(winners, 1, f"winners={winners}/{n_threads}; all_results={results}")
        finally:
            self._clear(ident)

    def test_process_contention_single_winner(self):
        """N procesů soutěží — právě jeden získá zámek."""
        ident = "TEST_RL_PROCS"
        self._clear(ident)
        n_procs = 8
        ctx = multiprocessing.get_context("fork")
        results_q = ctx.Queue()
        procs = [ctx.Process(target=_process_worker, args=(ident, results_q)) for _ in range(n_procs)]
        try:
            for p in procs:
                p.start()
            for p in procs:
                p.join(timeout=30)
            winners_results = []
            while not results_q.empty():
                winners_results.append(results_q.get())
            winners = sum(1 for r in winners_results if r)
            self.assertEqual(winners, 1, f"winners={winners}/{n_procs}; all_results={winners_results}")
        finally:
            self._clear(ident)
