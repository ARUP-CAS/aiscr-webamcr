"""Regrese omezené historie, živých zámků a hranic mazání výstupu testů."""

import io
import json
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

    def test_thirty_day_boundary_and_unknown_ownership(self):
        """Přerušené pokusy vyžadují třicet dní i ověřené neaktivní vlastnictví."""
        now = time.time()
        young = self.attempt("young")
        old = self.attempt("old")
        unknown, _ = protocol.create_attempt(self.results, "unknown")
        self.age(young, now - retention.STALE_SECONDS + 1)
        self.age(old, now - retention.STALE_SECONDS)
        self.age(unknown, now - retention.STALE_SECONDS - 1)
        with redirect_stdout(io.StringIO()) as output:
            removed = retention.prune_attempts(self.results, now=now)
        self.assertEqual(removed, ["old"])
        self.assertTrue(young.exists())
        self.assertTrue(unknown.exists())
        self.assertIn("neověřené vlastnictví", output.getvalue())

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
        self.assertEqual(retention.prune_attempts(self.results), ["legacy-00", "legacy-01"])

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
