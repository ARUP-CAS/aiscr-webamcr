"""Regrese omezené historie, živých zámků a hranic mazání výstupu testů."""

import io
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "webclient"))
import test_run_results as protocol  # noqa: E402
import test_run_retention as retention  # noqa: E402


def simultaneous_attempt(root, identity, publication, acquired, owner, contender):
    """Vytvoří pokus až po souběžném zveřejnění markeru a ověření výlučnosti.

    :param root: Sdílený dočasný kořen výsledků.
    :param identity: Vlastní identita procesu.
    :param publication: Bariéra před zveřejněním dvou úplných markerů.
    :param acquired: Signál prvního držitele zámku.
    :param owner: Identita procesu, který má vstoupit první.
    :param contender: Signál, že druhý proces ověřil obsazený zámek.
    """
    operation = "rename" if os.name == "nt" else "link"
    publish = getattr(os, operation)
    acquire = retention.FileLease.acquire
    first_root_acquire = True

    def synchronize_publish(source, target):
        """Seřadí oba procesy těsně před skutečným zveřejněním souboru.

        :param source: Cesta k inicializovanému markeru.
        :param target: Kanonická cesta zámku.
        :return: Výsledek vytvoření odkazu.
        """
        assert Path(source).read_bytes() == retention.LOCK_MARKER
        if Path(target).name == ".retention.lock":
            publication.wait(10)
        return publish(source, target)

    def check_acquire(lease, blocking=True):
        """Ověří obsazený skutečný zámek druhým procesem.

        :param lease: Zámek pokusu nebo kořene.
        :param blocking: Zda má získání zámku čekat.
        :return: Výsledek skutečného získání zámku.
        """
        nonlocal first_root_acquire
        if lease.path.name == ".retention.lock" and first_root_acquire:
            first_root_acquire = False
            if identity != owner:
                assert acquired.wait(10), "First process did not acquire the canonical lock"
                assert not acquire(lease, blocking=False), "Second process acquired a held root lock"
                contender.set()
        return acquire(lease, blocking)

    def create(results, attempt_id):
        """Ponechá první zámek obsazený, dokud druhý proces neověří výlučnost.

        :param results: Kořen úložiště výsledků.
        :param attempt_id: Ověřená identita běhu.
        :return: Adresář a identita vytvořeného pokusu.
        """
        if identity == owner:
            acquired.set()
            assert contender.wait(10), "Second process did not verify mutual exclusion"
        return protocol.create_attempt(results, attempt_id)

    with patch.object(retention.os, operation, synchronize_publish), patch.object(
        retention.FileLease, "acquire", check_acquire
    ):
        lease = retention.AttemptLease(root, identity, create)
        lease.close()


class RetentionTests(unittest.TestCase):
    """Maže pouze vlastní dočasné adresáře; externí data chrání canary."""

    def setUp(self):
        """Připraví explicitní soukromý kořen všech testovacích dat."""
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TEMP_ROOT")))).resolve()
        self.results = self.root / "results"
        self.results.mkdir()
        self.selection = self.results / "results.xlsx"
        self.selection.write_bytes(b"previous selection")

    def attempt(self, identity, state=None):
        """Založí vlastní pokus a případně publikuje terminální stav.

        :param identity: Identita pokusu.
        :param state: Terminální stav nebo None pro přerušený pokus.
        :return: Adresář pokusu.
        """
        lease = retention.AttemptLease(self.results, identity, protocol.create_attempt)
        directory = lease.directory
        if state is not None:
            if state != "error":
                protocol.write_summary(directory, 0 if state == "no-tests" else 1, 0)
            counts = dict(total=1, passed=1, failed=0, skipped=0, expected_failures=0) if state == "completed" else None
            protocol.publish_outcome(
                directory,
                identity,
                "neuspesne" if state == "no-tests" else "vsechny",
                "",
                state,
                1 if state == "error" else 0,
                counts=counts,
            )
        lease.close()
        return directory

    def age(self, directory, timestamp):
        """Nastaví stáří pouze vlastnímu adresáři a jeho souborům.

        :param directory: Vlastní dočasný pokus.
        :param timestamp: Požadovaný čas poslední aktivity.
        """
        for path in [*directory.rglob("*"), directory]:
            os.utime(path, (timestamp, timestamp))

    def test_latest_ten_finished_attempts_include_failures_and_noops(self):
        """Normální, neúspěšné i prázdné terminální pokusy sdílí limit deseti."""
        for index in range(13):
            self.attempt(f"run-{index:02}", ("completed", "error", "no-tests")[index % 3])
        remaining = sorted(path.name for path in (self.results / "runs").iterdir() if not path.name.startswith("."))
        self.assertEqual(remaining, [f"run-{index:02}" for index in range(3, 13)])
        self.assertEqual(self.selection.read_bytes(), b"previous selection")

    def test_first_concurrent_use_publishes_one_complete_lock(self):
        """Dva procesy zveřejní úplný marker a respektují stejný živý zámek."""
        context = multiprocessing.get_context("spawn")
        publication, acquired, contender = context.Barrier(2), context.Event(), context.Event()
        identities = ("first", "second")
        children = [
            context.Process(
                target=simultaneous_attempt,
                args=(self.results, identity, publication, acquired, identities[0], contender),
            )
            for identity in identities
        ]
        for child in children:
            child.start()
        try:
            for child in children:
                child.join(25)
                self.assertEqual(child.exitcode, 0)
            runs = self.results / "runs"
            self.assertEqual(sorted(path.name for path in runs.iterdir()), [".leases", ".retention.lock", *identities])
            self.assertEqual((runs / ".retention.lock").read_bytes(), retention.LOCK_MARKER)
        finally:
            for child in children:
                if child.is_alive():
                    child.terminate()
                child.join()
                child.close()

    def test_invalid_existing_root_marker_is_not_replaced(self):
        """Prázdný či jinak neověřený marker zůstane beze změny a retence selže."""
        runs, _ = retention.layout(self.results)
        root_lock = runs / ".retention.lock"
        for marker in (b"", b"unrecognized"):
            root_lock.write_bytes(marker)
            with self.assertRaises(ValueError):
                retention.prune_attempts(self.results)
            self.assertEqual(root_lock.read_bytes(), marker)

    def test_thirty_day_boundary_and_unknown_ownership(self):
        """Přerušené pokusy vyžadují třicet dní i ověřené neaktivní vlastnictví."""
        now = time.time()
        young = self.attempt("young")
        old = self.attempt("old")
        unknown, _ = protocol.create_attempt(self.results, "unknown")
        invalid = self.attempt("invalid")
        invalid_marker = self.results / "runs/.leases/invalid.lock"
        invalid_marker.write_bytes(b"unknown marker")
        nonfile, _ = protocol.create_attempt(self.results, "nonfile")
        nonfile_marker = self.results / "runs/.leases/nonfile.lock"
        nonfile_marker.mkdir()
        self.age(young, now - retention.STALE_SECONDS + 1)
        self.age(old, now - retention.STALE_SECONDS)
        self.age(unknown, now - retention.STALE_SECONDS - 1)
        self.age(invalid, now - retention.STALE_SECONDS - 1)
        self.age(nonfile, now - retention.STALE_SECONDS - 1)
        with redirect_stdout(io.StringIO()) as output:
            removed = retention.prune_attempts(self.results, now=now)
        self.assertEqual(removed, ["old"])
        self.assertTrue(young.exists())
        self.assertTrue(unknown.exists())
        self.assertTrue(invalid.exists())
        self.assertEqual(invalid_marker.read_bytes(), b"unknown marker")
        self.assertTrue(nonfile.is_dir())
        self.assertTrue(nonfile_marker.is_dir())
        self.assertIn("neověřené vlastnictví", output.getvalue())

    def test_explicit_reuse_of_old_finished_attempt_is_refused_before_pruning(self):
        """Kolize nevyvolá retenci ani u pokusu mimo deset nejnovějších."""
        with patch.object(retention, "prune_locked", return_value=[]):
            old = self.attempt("old", "completed")
            os.utime(old / "outcome.json", (1000, 1000))
            for index in range(10):
                self.attempt(f"new-{index}", "completed")
        evidence = {path.name: path.read_bytes() for path in old.iterdir()}
        with self.assertRaises(FileExistsError):
            retention.AttemptLease(self.results, "old", protocol.create_attempt)
        self.assertEqual({path.name: path.read_bytes() for path in old.iterdir()}, evidence)
        self.assertEqual(self.selection.read_bytes(), b"previous selection")
        self.assertEqual(retention.prune_attempts(self.results), ["old"])

    def test_interrupted_creation_has_valid_ownership_before_publication(self):
        """Přerušení před i po vzniku adresáře ponechá platný a odemčený zámek."""
        for published in (False, True):
            identity = f"interrupted-{published}"
            directory = self.results / "runs" / identity
            marker = directory.parent / ".leases" / f"{identity}.lock"
            acquire = retention.FileLease.acquire
            acquired = []

            def track_acquire(lease, blocking=True):
                """Zaznamená úspěšné uzamčení skutečného souboru.

                :param lease: Soubor zámku z produkčního kódu.
                :param blocking: Zda čekat na zámek.
                :return: Skutečný výsledek pokusu o uzamčení.
                """
                ok = acquire(lease, blocking)
                if ok:
                    acquired.append(lease.path)
                return ok

            def interrupted(root, attempt_id):
                """Přeruší založení pokusu na straně zapisujícího procesu.

                :param root: Kořen pokusů.
                :param attempt_id: Již uzamčená identita.
                """
                self.assertIn(marker, acquired)
                self.assertFalse(directory.exists())
                if published:
                    protocol.create_attempt(root, attempt_id)
                raise KeyboardInterrupt

            with patch.object(retention.FileLease, "acquire", track_acquire), self.assertRaises(KeyboardInterrupt):
                retention.AttemptLease(self.results, identity, interrupted)
            self.assertEqual(directory.exists(), published)
            self.assertEqual(marker.read_bytes(), retention.LOCK_MARKER)
            if published:
                self.age(directory, time.time() - retention.STALE_SECONDS - 10)
                self.assertEqual(retention.prune_attempts(self.results), [identity])
            else:
                self.assertEqual(self.attempt(identity), directory)

    def test_failed_lease_creation_prevents_publication(self):
        """Přerušená inicializace nezveřejní marker a neblokuje další pokus."""
        retention.prune_attempts(self.results)
        with patch.object(retention.os, "fsync", side_effect=OSError("fixture")), self.assertRaises(OSError):
            retention.AttemptLease(self.results, "failed", protocol.create_attempt)
        runs = self.results / "runs"
        self.assertFalse((runs / "failed").exists())
        self.assertEqual(list((runs / ".leases").iterdir()), [])
        self.assertEqual(self.attempt("failed"), runs / "failed")

    def test_existing_unverified_attempt_markers_are_preserved(self):
        """Neznámá či přesměrovaná cesta zámku nepovolí publikaci pokusu."""
        runs, leases = retention.layout(self.results)
        unknown = leases / "unknown.lock"
        for marker in (b"", b"unrecognized lease"):
            unknown.write_bytes(marker)
            with self.assertRaises(ValueError):
                retention.AttemptLease(self.results, "unknown", protocol.create_attempt)
            self.assertFalse((runs / "unknown").exists())
            self.assertEqual(unknown.read_bytes(), marker)

        redirected = leases / "redirected.lock"
        redirected.write_bytes(retention.LOCK_MARKER)
        linked = retention.linked
        with patch.object(retention, "linked", side_effect=lambda path: path == redirected or linked(path)):
            with self.assertRaises(ValueError):
                retention.AttemptLease(self.results, "redirected", protocol.create_attempt)
        self.assertFalse((runs / "redirected").exists())
        self.assertEqual(redirected.read_bytes(), retention.LOCK_MARKER)

    def test_active_old_attempt_is_protected_across_processes(self):
        """Skutečný zámek jiného procesu chrání i pokus starší než třicet dní."""
        directory = self.attempt("active")
        self.age(directory, time.time() - retention.STALE_SECONDS - 10)
        lock = self.results / "runs/.leases/active.lock"
        code = "from pathlib import Path; from test_run_retention import FileLease; import sys; lease=FileLease(Path(sys.argv[1])); lease.acquire(); print('locked',flush=True); sys.stdin.read(); lease.close()"
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", code, str(lock)],
            env=dict(os.environ, PYTHONPATH=str(ROOT / "webclient")),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.assertEqual(child.stdout.readline().strip(), "locked")
            self.assertEqual(retention.prune_attempts(self.results), [])
            self.assertTrue(directory.exists())
        finally:
            child.communicate(input="release", timeout=10)
        self.assertEqual(child.returncode, 0)
        self.assertEqual(retention.prune_attempts(self.results), ["active"])

    def test_current_attempt_is_protected_and_cleanup_failure_is_visible(self):
        """Aktuální pokus se nemaže; chyba mazání zachová data a vrátí neúspěch."""
        directory = self.attempt("current")
        self.age(directory, time.time() - retention.STALE_SECONDS - 10)
        self.assertEqual(retention.prune_attempts(self.results, current="current"), [])
        with patch.object(retention.shutil, "rmtree", side_effect=PermissionError("fixture")), self.assertRaises(
            PermissionError
        ):
            retention.prune_attempts(self.results)
        self.assertTrue(directory.exists())
        self.assertEqual(self.selection.read_bytes(), b"previous selection")

    def test_symlinks_and_reparse_points_cannot_remove_external_canary(self):
        """Odkaz uvnitř kandidáta ani odkaz místo kandidáta neopustí kořen."""
        outside = self.root / "outside"
        outside.mkdir()
        canary = outside / "keep"
        canary.write_bytes(b"external canary")
        directory = self.attempt("linked", "completed")
        marker = directory / "outcome.json"
        os.utime(marker, (1000, 1000))
        try:
            (directory / "external").symlink_to(outside, target_is_directory=True)
            (self.results / "runs/external").symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            for link in (directory / "external", self.results / "runs/external"):
                if not link.exists():
                    subprocess.run(
                        [
                            "powershell",
                            "-NoProfile",
                            "-NonInteractive",
                            "-Command",
                            "New-Item -ItemType Junction -Path $env:FIXTURE_LINK -Target $env:FIXTURE_TARGET | Out-Null",
                        ],
                        env=dict(os.environ, FIXTURE_LINK=str(link), FIXTURE_TARGET=str(outside)),
                        check=True,
                        capture_output=True,
                    )
        with redirect_stdout(io.StringIO()):
            for index in range(11):
                self.attempt(f"new-{index:02}", "completed")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(retention.prune_attempts(self.results), [])
        self.assertEqual(canary.read_bytes(), b"external canary")
        self.assertTrue(directory.exists())

    def test_runner_retention_failure_preserves_nonzero_and_original_test_failure(self):
        """Chyba retence nezaloží úspěch ani nepřepíše původní neúspěšné počty."""
        from contextlib import redirect_stderr
        from types import SimpleNamespace

        import run_tests as runner

        for native in (0, 1):
            identity = f"cleanup-{native}"
            output = "Ran 1 test in 0s\n\n" + ("OK\n" if native == 0 else "FAILED (failures=1)\n")
            with patch.object(runner, "configure_logging"), patch.object(
                runner, "select_tests", return_value=["sample.tests.one"]
            ), patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)), patch.object(
                runner, "execute_tests", return_value=(native, output)
            ), patch.object(
                retention, "prune_attempts", side_effect=PermissionError("sensitive cleanup error")
            ), redirect_stdout(
                io.StringIO()
            ), redirect_stderr(
                io.StringIO()
            ) as errors:
                code = runner.main(["--results-root", str(self.results), "--attempt-id", identity])
            self.assertEqual(code, 1)
            self.assertIn("(retention)", errors.getvalue())
            self.assertNotIn("sensitive cleanup error", errors.getvalue())
            path = self.results / "runs" / identity
            record = protocol.load_record(path, identity, "vsechny", "")
            self.assertEqual(record["state"], "error" if native == 0 else "completed")
            if native:
                self.assertEqual(protocol.validate_bundle(path, record), (0, 1))

    def test_legacy_terminal_history_is_recognized_without_accepting_old_counts(self):
        """Vlastněný terminální záznam verze 1 lze uklidit při migraci historie."""
        retention.prune_attempts(self.results)
        for index in range(12):
            directory, identity = protocol.create_attempt(self.results, f"legacy-{index:02}")
            protocol.write_summary(directory, 1, 0)
            protocol.publish_outcome(
                directory,
                identity,
                "vsechny",
                "",
                "completed",
                0,
                counts=dict(total=1, passed=1, failed=0, skipped=0, expected_failures=0),
            )
            path = directory / "outcome.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["version"] = 1
            record.pop("counts", None)
            path.write_text(json.dumps(record), encoding="utf-8")
            os.utime(path, (1000 + index, 1000 + index))
        leases = self.results / "runs/.leases"
        with patch.object(retention.os, "fsync", side_effect=OSError("fixture")), self.assertRaises(OSError):
            retention.prune_attempts(self.results)
        self.assertEqual(list(leases.iterdir()), [])
        self.assertTrue((self.results / "runs/legacy-00").is_dir())
        self.assertEqual(retention.prune_attempts(self.results), ["legacy-00", "legacy-01"])
        self.assertEqual((leases / "legacy-11.lock").read_bytes(), retention.LOCK_MARKER)

    def test_redirected_runs_or_lease_root_is_rejected(self):
        """Junction nebo symlink v hranici úložiště zabrání práci s cizí cestou."""
        with patch.object(retention, "linked", return_value=True), self.assertRaises(ValueError):
            retention.layout(self.results)

    def test_unrelated_and_invalid_terminal_data_remain_intact(self):
        """Neznámý adresář či poškozená metadata nezískají oprávnění k mazání."""
        directory = self.attempt("malformed")
        (directory / "outcome.json").write_text('{"version": 999}', encoding="utf-8")
        self.age(directory, time.time() - retention.STALE_SECONDS - 10)
        unrelated = self.results / "runs/unrelated.txt"
        unrelated.write_bytes(b"keep")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(retention.prune_attempts(self.results), [])
        self.assertTrue(directory.exists())
        self.assertEqual(unrelated.read_bytes(), b"keep")

    def test_terminal_record_is_read_once_and_rejects_bad_metadata(self):
        """Retence i konzument používají stejné omezení, jediný čtecí průchod a přísný JSON."""
        directory = self.attempt("terminal", "completed")
        outcome = directory / "outcome.json"
        raw = outcome.read_bytes()
        max_size = protocol.OUTCOME_LIMIT
        outcome.write_bytes(raw.ljust(max_size, b" "))
        with patch.object(Path, "open", autospec=True, side_effect=Path.open) as opened:
            record = retention.terminal_record(directory)
        opened.assert_called_once_with(outcome, "rb")
        self.assertEqual(record["attempt_id"], directory.name)
        for invalid in (raw.ljust(max_size + 1, b" "), raw[:-1] + b', "version":2}', b"{"):
            outcome.write_bytes(invalid)
            with self.assertRaises(ValueError):
                protocol.load_record(directory, directory.name, "vsechny", "")
            self.age(directory, time.time() - retention.STALE_SECONDS - 10)
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(retention.prune_attempts(self.results), [])
            self.assertTrue(directory.is_dir())
            self.assertEqual(outcome.read_bytes(), invalid)
            self.assertIn("neověřený kandidát", output.getvalue())
