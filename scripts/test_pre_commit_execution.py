"""Regrese skutečných výsledků runneru a protokolu jednotlivých pokusů."""

import io
import json
import os
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "webclient"))
import run_tests as runner  # noqa: E402
import test_run_results as protocol  # noqa: E402


class ExecutionTests(unittest.TestCase):
    """Ověří procesní stav, dokončený výstup a oddělené výsledky pokusů."""

    def setUp(self):
        """Připraví pouze dočasné soubory bez Django či služeb."""
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TEMP_ROOT")))).resolve()
        self.enterContext(patch.object(runner, "configure_logging"))

    def attempt(self, identity="123-1", mode="vsechny", number="", state="completed", code=0, counts=(1, 0)):
        """Připraví úplný výsledek přes produkční publikační funkci.

        :param identity: Identita testovacího pokusu.
        :param mode: Režim výběru.
        :param number: Číslo testu.
        :param state: Stav výsledku.
        :param code: Výsledek procesu.
        :param counts: Počty testů.
        :return: Adresář pokusu a záznam výsledku.
        """
        directory, identity = protocol.create_attempt(self.root, identity)
        if state != "error":
            protocol.write_summary(directory, *counts)
        metadata = dict(total=sum(counts), passed=counts[0], failed=counts[1], skipped=0, expected_failures=0)
        protocol.publish_outcome(
            directory, identity, mode, number, state, code, counts=metadata if state == "completed" else None
        )
        return directory, protocol.load_record(directory, identity, mode, number)

    def test_crash_zero_missing_and_inconsistent_results_fail(self):
        """Traceback ani chybějící či rozporný souhrn nezaloží úspěch."""
        for output, code in (
            ("Traceback: startup failed\n", 1),
            ("Ran 0 tests in 0s\n\nOK\n", 0),
            ("Ran 1 test in 0s\n", 0),
            ("Ran 1 test in 0s\n\nOK\n", 1),
            ("Ran 1 test in 0s\n\nFAILED (errors=1)\n", 0),
            ("Ran 1 test in 0s\n\nFAILED (errors=2)\n", 1),
            ("Ran 1 test in 0s\n\nOK\n", -9),
        ):
            with self.subTest(output=output, code=code), self.assertRaises(ValueError):
                runner.parse_result(output, code)

    def test_complete_success_failures_and_unexpected_success(self):
        """Úplné souhrny respektují nativní výsledek včetně unexpected successes."""
        self.assertEqual(
            runner.parse_result("Ran 3 tests in 1s\n\nOK (skipped=1)\n", 0),
            dict(total=3, passed=2, failed=0, skipped=1, expected_failures=0),
        )
        self.assertEqual(
            runner.parse_result("Ran 3 tests in 1s\n\nFAILED (failures=1, errors=1)\n", 1),
            dict(total=3, passed=1, failed=2, skipped=0, expected_failures=0),
        )
        self.assertEqual(
            runner.parse_result("Ran 1 test in 1s\n\nFAILED (unexpected successes=1)\n", 1),
            dict(total=1, passed=0, failed=1, skipped=0, expected_failures=0),
        )

    def test_readers_finish_in_console_and_file_modes(self):
        """Dokončení procesu před koncem čtení nezkrátí zachycený výstup."""

        class Delayed(io.StringIO):
            """Odloží čtení simulovaného posledního výstupu."""

            def __next__(self):
                """Vrátí řádek až po malém zpoždění.

                :return: Řádek simulovaného proudu.
                """
                time.sleep(0.005)
                return super().__next__()

        for file_mode in (False, True):
            process = SimpleNamespace(
                stdout=Delayed("body\n"), stderr=Delayed("Ran 1 test in 1s\n\nOK\n"), wait=lambda: 0
            )
            with patch.object(runner.subprocess, "Popen", return_value=process), redirect_stdout(io.StringIO()):
                code, text = runner.execute_tests(["sample.tests.test_one"], self.root, file_mode)
            self.assertEqual(
                runner.parse_result(text, code), dict(total=1, passed=1, failed=0, skipped=0, expected_failures=0)
            )
            self.assertEqual((self.root / "test_output.log").read_text(encoding="utf-8"), text)

    def test_migration_failure_stops_tests_and_publishes_error(self):
        """Chyba migrace nepustí testy a nevytvoří úspěšné nulové počty."""
        with patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=7)), patch.object(
            runner, "execute_tests"
        ) as execute, redirect_stderr(io.StringIO()):
            code = runner.main(["--results-root", str(self.root), "--attempt-id", "123-1"])
        self.assertEqual(code, 1)
        execute.assert_not_called()
        record = protocol.load_record(self.root / "runs/123-1", "123-1", "vsechny", "")
        self.assertEqual(record["state"], "error")
        self.assertNotIn("test_summary.env", record["files"])

    def test_capture_failure_reaps_child_and_unwritable_log_does_not_start_it(self):
        """Chyba čtení ukončí vlastní proces; neotevřitelný log jej vůbec nespustí."""
        from unittest.mock import Mock

        class Broken(io.StringIO):
            """Proud, který při čtení selže."""

            def __next__(self):
                """Simuluje chybu proudového vstupu.

                :raises OSError: Při pokusu přečíst další řádek.
                """
                raise OSError("capture failed")

        process = SimpleNamespace(
            stdout=Broken(""), stderr=io.StringIO(""), wait=Mock(return_value=1), terminate=Mock()
        )
        with patch.object(runner.subprocess, "Popen", return_value=process), self.assertRaises(RuntimeError):
            runner.execute_tests(["sample.tests.one"], self.root)
        process.terminate.assert_called_once()
        process.wait.assert_called_once()
        with patch.object(Path, "open", side_effect=PermissionError("log failed")), patch.object(
            runner.subprocess, "Popen"
        ) as start, self.assertRaises(PermissionError):
            runner.execute_tests(["sample.tests.one"], self.root)
        start.assert_not_called()

    def test_runner_crash_does_not_publish_passing_counts(self):
        """Chyba startu procesu dostane error místo completed s nulou."""
        with patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)), patch.object(
            runner, "execute_tests", return_value=(1, "Traceback: startup failed\n")
        ), redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(["--results-root", str(self.root), "--attempt-id", "123-1"]), 1)
        record = protocol.load_record(self.root / "runs/123-1", "123-1", "vsechny", "")
        self.assertEqual(record["state"], "error")

    def test_runner_diagnostics_hide_explicit_and_secret_backed_roots(self):
        """Pokus lze sledovat podle identity bez zveřejnění cesty z konfigurace."""
        for configured in (False, True):
            with self.subTest(secret_backed=configured), ExitStack() as stack:
                root = self.root / f"sensitive-output-root-{configured}"
                identity = f"safe-{configured}"
                stdout, stderr = io.StringIO(), io.StringIO()
                stack.enter_context(patch.dict(os.environ))
                os.environ.pop("AMCR_TEST_RESULTS_ROOT", None)
                stack.enter_context(
                    patch.dict(
                        sys.modules,
                        {"webclient.settings.dev_test": SimpleNamespace(TEST_SCREENSHOT_PATH=str(root))},
                    )
                )
                stack.enter_context(patch.object(runner, "select_tests", return_value=["sample.tests.one"]))
                stack.enter_context(patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)))
                stack.enter_context(patch.object(runner, "execute_tests", return_value=(0, "Ran 1 test in 0s\n\nOK\n")))
                stack.enter_context(redirect_stdout(stdout))
                stack.enter_context(redirect_stderr(stderr))
                args = ["--attempt-id", identity]
                if not configured:
                    args += ["--results-root", str(root)]
                self.assertEqual(runner.main(args), 0)
                record = protocol.load_record(root / "runs" / identity, identity, "vsechny", "")
                self.assertEqual(protocol.validate_bundle(root / "runs" / identity, record), (1, 0))
                self.assertIn(identity, stdout.getvalue())
                diagnostics = stdout.getvalue() + stderr.getvalue() + json.dumps(record)
                self.assertNotIn(str(root), diagnostics)
                self.assertNotIn("sensitive-output-root", diagnostics)

    def test_failures_before_attempt_creation_hide_sensitive_exceptions(self):
        """Chyba inicializace, konfigurace či adresáře nezveřejní hodnotu výjimky."""
        sensitive = f"{self.root}/private-root\ncredential-canary"
        for stage, target, attribute in (
            ("initialization", runner, "configure_logging"),
            ("configuration", runner, "Path"),
            ("attempt", protocol, "create_attempt"),
        ):
            with self.subTest(stage=stage), patch.object(target, attribute, side_effect=OSError(sensitive)):
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = runner.main(["--results-root", str(self.root), "--attempt-id", "private-attempt"])
                self.assertEqual(code, 1)
                self.assertIn(f"({stage})", stderr.getvalue())
                diagnostics = stdout.getvalue() + stderr.getvalue()
                self.assertNotIn("credential-canary", diagnostics)
                self.assertNotIn(str(self.root), diagnostics)
                self.assertFalse((self.root / "runs/private-attempt").exists())

    def test_runner_error_stages_and_metadata_hide_sensitive_exceptions(self):
        """Provozní chyby zachovají fázi a nepropustí citlivý text do konzole ani JSON."""
        sensitive = f"{self.root}/private-root\ncredential-canary"
        publish = protocol.publish_outcome

        def fail_completed_publication(*args, **kwargs):
            """První publikaci odmítne, chybový výsledek zapíše skutečnou funkcí.

            :param args: Argumenty publikovaného pokusu.
            :param kwargs: Volitelná metadata výsledku.
            :return: Výsledek skutečné publikace chyby.
            :raises OSError: Při pokusu zveřejnit dokončený běh.
            """
            if args[4] != "error":
                raise OSError(sensitive)
            return publish(*args, **kwargs)

        for case, stage, target, attribute in (
            ("selection", "selection", runner, "select_tests"),
            ("migration", "migration", runner.subprocess, "run"),
            ("execution", "execution", runner, "execute_tests"),
            ("summary", "summary", runner, "parse_result"),
            ("summary-write", "summary", protocol, "write_summary"),
            ("publication", "publication", protocol, "publish_outcome"),
            ("noop-publication", "publication", protocol, "write_summary"),
        ):
            with self.subTest(case=case), ExitStack() as stack:
                identity = f"safe-{case}"
                stdout, stderr = io.StringIO(), io.StringIO()
                stack.enter_context(
                    patch.object(
                        runner, "select_tests", return_value=[] if case == "noop-publication" else ["sample.tests.one"]
                    )
                )
                stack.enter_context(patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)))
                stack.enter_context(patch.object(runner, "execute_tests", return_value=(0, "Ran 1 test in 0s\n\nOK\n")))
                stack.enter_context(
                    patch.object(
                        target,
                        attribute,
                        side_effect=fail_completed_publication if case == "publication" else OSError(sensitive),
                    )
                )
                stack.enter_context(redirect_stdout(stdout))
                stack.enter_context(redirect_stderr(stderr))
                args = ["--results-root", str(self.root), "--attempt-id", identity]
                mode = "neuspesne" if case == "noop-publication" else "vsechny"
                if mode == "neuspesne":
                    args.append("-f")
                self.assertEqual(runner.main(args), 1)
                directory = self.root / "runs" / identity
                record = protocol.load_record(directory, identity, mode, "")
                self.assertEqual(record["state"], "error")
                self.assertIn(f"({stage})", record["message"])
                self.assertIn(f"({stage})", stderr.getvalue())
                diagnostics = stdout.getvalue() + stderr.getvalue() + (directory / "outcome.json").read_text()
                self.assertNotIn("credential-canary", diagnostics)
                self.assertNotIn(str(self.root), diagnostics)
                self.assertNotIn("Traceback", diagnostics)
                self.assertIsNone(protocol.validate_bundle(directory, record))

    def test_failed_error_publication_does_not_escape_or_disclose_exception(self):
        """Druhá chyba publikace zachová neúspěch bez tracebacku s citlivou cestou."""
        stdout, stderr = io.StringIO(), io.StringIO()
        sensitive = f"{self.root}/private-root\ncredential-canary"
        with patch.object(runner, "select_tests", side_effect=OSError(sensitive)), patch.object(
            protocol, "publish_outcome", side_effect=OSError(sensitive)
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            code = runner.main(["--results-root", str(self.root), "--attempt-id", "safe-error"])
        self.assertEqual(code, 1)
        self.assertIn("(selection)", stderr.getvalue())
        self.assertIn("(publication)", stderr.getvalue())
        diagnostics = stdout.getvalue() + stderr.getvalue()
        self.assertNotIn("credential-canary", diagnostics)
        self.assertNotIn(str(self.root), diagnostics)
        self.assertNotIn("Traceback", diagnostics)
        self.assertFalse((self.root / "runs/safe-error/outcome.json").exists())

    def test_runner_publishes_completed_pass_and_failure(self):
        """Dokončené testy zachovají skutečný status a zveřejní aktuální počty."""
        for code, status, counts in ((0, "OK", (2, 0)), (1, "FAILED (errors=1)", (1, 1))):
            identity = f"123-{code + 1}"
            with patch.object(runner, "select_tests", return_value=["sample.tests.test_one"]), patch.object(
                runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)
            ), patch.object(
                runner, "execute_tests", return_value=(code, f"Ran 2 tests in 1s\n\n{status}\n")
            ), redirect_stdout(
                io.StringIO()
            ):
                self.assertEqual(runner.main(["--results-root", str(self.root), "--attempt-id", identity]), code)
            directory = self.root / "runs" / identity
            record = protocol.load_record(directory, identity, "vsechny", "")
            self.assertEqual(protocol.validate_bundle(directory, record), counts)

    def test_selective_workbook_keeps_unselected_tests(self):
        """Aktuální artefakt je nový, ale příští výběr nepřijde o dřívější testy."""
        import pandas

        columns = ["index", "date", "test name", "result"]
        previous = pandas.DataFrame(
            [[1, "old", "sample.tests.one", "OK"], [2, "old", "sample.tests.two", "FAIL"]], columns=columns
        )
        current = pandas.DataFrame([[1, None, None, None], [2, "now", "sample.tests.two", "OK"]], columns=columns)
        directory, _ = protocol.create_attempt(self.root, "123-1")
        previous.to_excel(self.root / "results.xlsx", index=False)
        current.to_excel(directory / "results.xlsx", index=False)
        merged = runner.selection_content(self.root, directory, "neuspesne")
        table = pandas.read_excel(io.BytesIO(merged))
        self.assertEqual(list(table["test name"]), ["sample.tests.one", "sample.tests.two"])
        self.assertEqual(list(table["result"]), ["OK", "OK"])

    def test_selection_preserves_previous_workbook_and_reports_noop(self):
        """No-op má novou identitu a stará tabulka zůstane vstupem výběru."""
        import pandas

        table = pandas.DataFrame(
            [[42, "date", "sample.tests.test_one", "OK"]], columns=["index", "date", "test name", "result"]
        )
        previous = self.root / "results.xlsx"
        previous.write_bytes(b"previous-input")
        with patch.object(pandas, "read_excel", return_value=table), patch.object(runner.subprocess, "run") as migrate:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(["-f", "--results-root", str(self.root), "--attempt-id", "123-1"]), 0)
            migrate.assert_not_called()
            self.assertEqual(runner.select_tests("konkretni", "42", previous), ["sample.tests.test_one"])
            with self.assertRaises(ValueError):
                runner.select_tests("konkretni", "43", previous)
        record = protocol.load_record(self.root / "runs/123-1", "123-1", "neuspesne", "")
        self.assertEqual(record["state"], "no-tests")
        self.assertEqual(protocol.validate_bundle(self.root / "runs/123-1", record), (0, 0))
        self.assertEqual(previous.read_bytes(), b"previous-input")

    def test_missing_and_malformed_selection_fail(self):
        """Chybějící nebo neplatný vstup výběru není no-op."""
        import pandas

        with self.assertRaises(ValueError):
            runner.select_tests("neuspesne", "", self.root / "absent.xlsx")
        for table in (
            pandas.DataFrame([[1]]),
            pandas.DataFrame([[1, "", "$(bad)", "FAIL"]], columns=["index", "date", "test name", "result"]),
        ):
            with patch.object(pandas, "read_excel", return_value=table), self.assertRaises(ValueError):
                runner.select_tests("neuspesne", "", self.root / "results.xlsx")
        columns = ["index", "date", "test name", "result"]
        for rows in (
            [[1, "", "sample.tests.one", None]],
            [[1, "", "$(bad)", "OK"]],
            [[1.5, "", "sample.tests.one", "FAIL"]],
            [[1, "", "sample.tests.one", "OK"], [1, "", "sample.tests.two", "FAIL"]],
            [[1, "", "sample.tests.one", "OK"], [2, "", "sample.tests.one", "FAIL"]],
        ):
            table = pandas.DataFrame(rows, columns=columns)
            with patch.object(pandas, "read_excel", return_value=table), self.assertRaises(ValueError):
                runner.select_tests("neuspesne", "", self.root / "results.xlsx")

    def test_attempts_are_unique_and_cannot_escape(self):
        """Opakování má jiný adresář; stejný pokus ani cesta se nepřepíše."""
        first, _ = self.attempt()
        second, _ = self.attempt("123-2")
        self.assertNotEqual(first, second)
        with self.assertRaises(FileExistsError):
            protocol.create_attempt(self.root, "123-1")
        for identity in ("../outside", "a/b", "$(bad)", "a\nb", ""):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                protocol.validate_identity(identity)

    def test_stale_mixed_and_incomplete_results_are_rejected(self):
        """Platný starý souhrn, jiné identity i změněné soubory jsou odmítnuty."""
        directory, record = self.attempt()
        with self.assertRaises(ValueError):
            protocol.load_record(directory, "123-2", "vsechny", "")
        with self.assertRaises(ValueError):
            protocol.load_record(directory, "123-1", "konkretni", "42")
        (directory / "test_summary.env").write_text("PASSED=99\nFAILED=0\n", encoding="ascii")
        with self.assertRaises(ValueError):
            protocol.validate_bundle(directory, record)
        (directory / "test_summary.env").unlink()
        with self.assertRaises(ValueError):
            protocol.validate_bundle(directory, record)

    def test_required_workbook_and_interrupted_publication_fail(self):
        """Chybějící tabulka ani přerušený zápis nevytvoří dokončený výsledek."""
        directory, identity = protocol.create_attempt(self.root, "123-1")
        protocol.write_summary(directory, 1, 0)
        with self.assertRaises(ValueError):
            protocol.publish_outcome(
                directory,
                identity,
                "vsechny",
                "",
                "completed",
                0,
                True,
                counts=dict(total=1, passed=1, failed=0, skipped=0, expected_failures=0),
            )
        self.assertFalse((directory / "outcome.json").exists())
        with patch.object(protocol.os, "replace", side_effect=OSError("interrupted")), self.assertRaises(OSError):
            protocol.publish_outcome(
                directory,
                identity,
                "vsechny",
                "",
                "completed",
                0,
                counts=dict(total=1, passed=1, failed=0, skipped=0, expected_failures=0),
            )
        self.assertFalse((directory / "outcome.json").exists())
        self.assertEqual(list(directory.glob("*.tmp")), [])

    def test_manifest_schema_and_duplicate_keys_fail(self):
        """Názvy cest, duplicitní klíče a typy nelze podvrhnout jako metadata."""
        directory, record = self.attempt()
        for key, value in (
            ("files", {"../outside": "a" * 64}),
            ("version", True),
            ("exit_code", False),
            ("state", "$(bad)"),
        ):
            candidate = dict(record)
            candidate[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                protocol.validate_record(candidate, "123-1", "vsechny", "")
        (directory / "outcome.json").write_text(
            json.dumps(record).replace('"version": 2', '"version": 2, "version": 2'), encoding="utf-8"
        )
        with self.assertRaises(ValueError):
            protocol.load_record(directory, "123-1", "vsechny", "")

    def test_runner_publishes_new_spreadsheet_and_rejects_failed_write(self):
        """Selenium běh vyžaduje tabulku tohoto pokusu, nikoli starou kopii."""
        import pandas

        columns = ["index", "date", "test name", "result"]
        previous = self.root / "results.xlsx"
        previous.write_bytes(b"previous-selection")

        def execute(labels, directory, file_logging):
            """Zapíše testovací tabulku do přesměrovaného adresáře.

            :param labels: Testovací výběr.
            :param directory: Adresář pokusu.
            :param file_logging: Režim výstupu.
            :return: Dokončený souhrn.
            """
            self.assertEqual(Path(os.environ["AMCR_TEST_OUTPUT_DIR"]), directory)
            pandas.DataFrame([[1, "now", labels[0], "OK"]], columns=columns).to_excel(
                directory / "results.xlsx", index=False
            )
            return 0, "Ran 1 test in 1s\n\nOK\n"

        with patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)), patch.object(
            runner, "execute_tests", side_effect=execute
        ), redirect_stdout(io.StringIO()):
            self.assertEqual(runner.main(["--results-root", str(self.root), "--attempt-id", "123-1"]), 0)
        directory = self.root / "runs/123-1"
        record = protocol.load_record(directory, "123-1", "vsechny", "")
        self.assertTrue(record["spreadsheet_required"])
        self.assertEqual(protocol.digest(previous), record["files"]["results.xlsx"])
        with patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)), patch.object(
            runner, "execute_tests", return_value=(0, "Ran 1 test in 1s\n\nOK\n")
        ), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(["--results-root", str(self.root), "--attempt-id", "123-2"]), 1)
        failed = protocol.load_record(self.root / "runs/123-2", "123-2", "vsechny", "")
        self.assertEqual(failed["state"], "error")
        self.assertEqual(protocol.digest(previous), record["files"]["results.xlsx"])

        def partial_write(labels, directory, file_logging):
            """Napodobí poškozenou tabulku po chybě zápisu.

            :param labels: Výběr testů.
            :param directory: Adresář pokusu.
            :param file_logging: Režim logování.
            :return: Neúspěšný úplný souhrn testů.
            """
            (directory / "results.xlsx").write_bytes(b"partial workbook")
            return 1, "Ran 1 test in 1s\n\nFAILED (errors=1)\n"

        with patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)), patch.object(
            runner, "execute_tests", side_effect=partial_write
        ), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(["--results-root", str(self.root), "--attempt-id", "123-3"]), 1)
        failed = protocol.load_record(self.root / "runs/123-3", "123-3", "vsechny", "")
        self.assertEqual(failed["state"], "error")
        self.assertEqual(protocol.digest(previous), record["files"]["results.xlsx"])

    def test_summary_validation_is_non_evaluating(self):
        """Celý souhrn má právě dva desetinné záznamy a nepřipouští příkazy."""
        path = self.root / "summary"
        for raw in (b"FAILED=0002\r\nPASSED=0001", b"PASSED=1\nFAILED=2\n"):
            path.write_bytes(raw)
            self.assertEqual(protocol.read_summary(path), (1, 2))
        for raw in (
            b"",
            b"PASSED=1\n",
            b"PASSED=1\x00\nFAILED=0",
            b"PASSED=1\nFAILED=0\n\n",
            b"PASSED=1\nFAILED=0\nOTHER=2",
            b"PASSED=$(bad)\nFAILED=0",
            b"PASSED=1\nPASSED=2\nFAILED=0",
        ):
            path.write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                protocol.read_summary(path)

    def test_summary_read_is_bounded_before_allocation(self):
        """Odmítne velký proud po nejvýše 4097 bajtech a přijme přesnou hranici."""
        stream = io.BytesIO(b"x" * 100000)
        from unittest.mock import Mock

        stream.read = Mock(wraps=stream.read)
        path = SimpleNamespace(open=Mock(return_value=stream))
        with self.assertRaises(ValueError):
            protocol.read_summary(path)
        stream.read.assert_called_once_with(4097)
        path = self.root / "bounded-summary"
        suffix = b"\nFAILED=0\n"
        valid = b"PASSED=" + b"0" * (4096 - len(b"PASSED=") - len(suffix)) + suffix
        path.write_bytes(valid)
        self.assertEqual(protocol.read_summary(path), (0, 0))
        path.write_bytes(valid + b"\n")
        with self.assertRaises(ValueError):
            protocol.read_summary(path)

    def test_explicit_categories_cross_runner_and_result_consumer(self):
        """Skips a očekávaná selhání nezvýší PASSED ani nezničí platný zero/zero běh."""
        from scripts.collect_test_results import report

        for index, (total, details, native, expected) in enumerate(
            (
                (5, "OK (skipped=2, expected failures=1)", 0, (2, 0, 2, 1)),
                (2, "OK (expected failures=2)", 0, (0, 0, 0, 2)),
                (2, "OK (skipped=2)", 0, None),
                (1, "FAILED (unexpected successes=1)", 1, (0, 1, 0, 0)),
            )
        ):
            identity = f"categories-{index}"
            with patch.object(runner, "select_tests", return_value=["sample.tests.one"]), patch.object(
                runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)
            ), patch.object(
                runner, "execute_tests", return_value=(native, f"Ran {total} tests in 0s\n\n{details}\n")
            ), redirect_stdout(
                io.StringIO()
            ), redirect_stderr(
                io.StringIO()
            ):
                code = runner.main(["--results-root", str(self.root), "--attempt-id", identity])
            directory = self.root / "runs" / identity
            record = protocol.load_record(directory, identity, "vsechny", "")
            self.assertEqual(record["version"], 2)
            outputs, summary = self.root / f"outputs-{index}", self.root / f"summary-{index}"
            status = report(directory, identity, "vsechny", "", outputs, summary)
            self.assertEqual(outputs.read_text(encoding="utf-8"), "ARTIFACTS=true\n")
            report_text = summary.read_text(encoding="utf-8")
            if expected is None:
                self.assertEqual((code, status, record["state"]), (1, 1, "error"))
                self.assertIsNone(record["counts"])
                self.assertIn("stav: `error`", report_text)
                self.assertNotIn("| Stav | Počet |", report_text)
            else:
                passed, failed, skipped, xfail = expected
                self.assertEqual((code, status), (native, native))
                self.assertEqual(
                    record["counts"],
                    dict(total=total, passed=passed, failed=failed, skipped=skipped, expected_failures=xfail),
                )
                self.assertIn(f"| ✅ Prošlo | {passed} |", report_text)
                self.assertIn(f"| ❌ Selhalo | {failed} |", report_text)
                self.assertIn(f"| Přeskočeno | {skipped} |", report_text)
                self.assertIn(f"| Očekávaná selhání | {xfail} |", report_text)

    def test_counter_consistency_and_legacy_rejection(self):
        """Neplatné typy, kategorie či stará verze neprojdou do nového výsledku."""
        directory, record = self.attempt()
        for key, value in (("total", True), ("passed", -1), ("skipped", False), ("total", 2)):
            candidate = dict(record, counts=dict(record["counts"], **{key: value}))
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                protocol.validate_record(candidate, "123-1", "vsechny", "")
        candidate = dict(record, counts=dict(total=2, passed=2, failed=0, skipped=0, expected_failures=0))
        with self.assertRaises(ValueError):
            protocol.validate_bundle(directory, candidate)
        legacy = dict(record, version=1)
        legacy.pop("counts")
        path = directory / "outcome.json"
        path.write_text(json.dumps(legacy), encoding="utf-8")
        with self.assertRaises(ValueError):
            protocol.load_record(directory, "123-1", "vsechny", "")
        owned = protocol.load_record(directory, "123-1", "vsechny", "", allow_legacy=True)
        self.assertEqual(owned["version"], 1)
        with self.assertRaises(ValueError):
            protocol.validate_bundle(directory, owned)

    def test_all_mode_aliases_and_mutual_exclusion_remain_compatible(self):
        """Bez příznaku i s -a/--all se volí vsechny a konfliktní režimy se odmítnou."""
        for index, flags in enumerate(([], ["-a"], ["--all"])):
            with patch.object(runner, "select_tests", return_value=["sample.tests.one"]) as select, patch.object(
                runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)
            ), patch.object(runner, "execute_tests", return_value=(0, "Ran 1 test in 0s\n\nOK\n")), redirect_stdout(
                io.StringIO()
            ):
                self.assertEqual(
                    runner.main(["--results-root", str(self.root), "--attempt-id", f"aliases-{index}", *flags]), 0
                )
            self.assertEqual(select.call_args.args[:2], ("vsechny", ""))
        for flags in (["-a", "-f"], ["--all", "-t", "42"]):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                runner.main(flags)
            self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
