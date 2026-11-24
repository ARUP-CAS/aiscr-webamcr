"""Spustí zvolené testy a ověří jejich skutečný výsledek před zveřejněním."""

import argparse
import logging
import os
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from threading import Lock, Thread

SETTINGS = "webclient.settings.dev_test"
logger = logging.getLogger("webamcr.test_runner")
DEFAULT_TESTS = [
    "core.tests.test_selenium",
    "core.tests.test_selenium_distribuce",
    "projekt.tests.test_selenium",
    "dokument.tests.test_selenium",
    "lokalita.tests.test_selenium",
    "arch_z.tests.test_selenium",
    "pas.tests.test_selenium",
    "oznameni.tests.test_selenium",
    "ez.tests.test_selenium",
    "uzivatel.tests.test_selenium",
    "heslar.tests.test_selenium",
    "core.tests.test_fedora_integration_child_walk",
    "core.tests.test_fedora_integration_paradata",
    "core.tests.test_organization_ownership",
    "core.tests.test_mappers.test_organizace_mapper",
    "cron.tests.test_run_data_import_organizace",
    "heslar.tests.test_organization_import_guard",
]


def configure_logging():
    """Zachová provozní značky běhu odesílané do Logstash."""
    import logstash

    if not logger.handlers:
        logger.addHandler(logstash.TCPLogstashHandler(host="logstash", version=1, tags="dev_test"))


def select_tests(mode, number, spreadsheet):
    """Vybere testy z předchozí tabulky; prázdný výběr připouští jen režim neúspěšných.

    :param mode: Režim vsechny, neuspesne nebo konkretni.
    :param number: Požadované číslo testu nebo prázdný řetězec.
    :param spreadsheet: Předchozí výsledky používané pouze jako vstup výběru.
    :return: Seznam úplných názvů vybraných testů.
    :raises ValueError: Při chybějící, neplatné nebo nevyhovující tabulce.
    """
    if mode == "vsechny":
        return list(DEFAULT_TESTS)
    import pandas

    try:
        data = pandas.read_excel(spreadsheet)
        if list(data.columns) != ["index", "date", "test name", "result"]:
            raise ValueError("Neplatné sloupce výsledků")
        selected = []
        indexes, names = set(), set()
        for index, _, name, result in data.itertuples(index=False, name=None):
            index_value = int(index)
            if isinstance(index, bool) or index_value <= 0 or index_value != index or index_value in indexes:
                raise ValueError("Neplatné nebo duplicitní číslo testu")
            indexes.add(index_value)
            empty_name = pandas.isna(name) or name == ""
            empty_result = pandas.isna(result) or result == ""
            if empty_name and empty_result:
                continue
            if result not in ("OK", "FAIL", "ERROR") or not isinstance(name, str):
                raise ValueError("Neplatný řádek výsledků")
            if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+", name, re.ASCII):
                raise ValueError("Neplatný název testu")
            if name in names:
                raise ValueError("Duplicitní název testu")
            names.add(name)
            if mode == "konkretni" and index != int(number):
                continue
            if mode == "neuspesne" and result == "OK":
                continue
            selected.append(name)
        if mode == "konkretni" and len(selected) != 1:
            raise ValueError(f"Test {number} nebyl jednoznačně nalezen")
        return selected
    except (OSError, ValueError, TypeError, ImportError, OverflowError) as exc:
        raise ValueError(f"Nelze vybrat testy z předchozích výsledků: {exc}") from exc


def parse_result(output, returncode):
    """Ověří úplný souhrn unittest proti skutečnému návratovému kódu.

    :param output: Úplný zachycený výstup obou proudů.
    :param returncode: Návratový kód testovacího procesu.
    :return: Úplné počty skutečně úspěšných, neúspěšných, přeskočených a očekávaně selhaných testů.
    :raises ValueError: Při neúplném, nulovém nebo rozporném výsledku.
    """
    ran = re.findall(r"^Ran ([0-9]+) tests? in [^\r\n]+\r?$", output, re.MULTILINE)
    statuses = re.findall(r"^(OK|FAILED)(?: \(([^\r\n]*)\))?\r?$", output, re.MULTILINE)
    if len(ran) != 1 or len(statuses) != 1 or int(ran[0]) <= 0:
        raise ValueError("Chybí jednoznačný úplný výsledek provedených testů")
    status, details = statuses[0]
    counters = {}
    for entry in details.split(", ") if details else []:
        match = re.fullmatch(r"(failures|errors|skipped|expected failures|unexpected successes)=([0-9]+)", entry)
        if not match or match[1] in counters:
            raise ValueError("Neplatný souhrn testů")
        counters[match[1]] = int(match[2])
    failed = sum(counters.get(key, 0) for key in ("failures", "errors", "unexpected successes"))
    total = int(ran[0])
    if sum(counters.values()) > total or (status == "OK") != (failed == 0):
        raise ValueError("Rozporné počty testů")
    if (returncode == 0) != (status == "OK") or returncode not in (0, 1):
        raise ValueError("Návratový kód neodpovídá úplnému výsledku testů")
    skipped, expected = counters.get("skipped", 0), counters.get("expected failures", 0)
    if total - skipped <= 0:
        raise ValueError("Nebylo provedeno žádné tělo testu")
    return dict(
        total=total,
        passed=total - failed - skipped - expected,
        failed=failed,
        skipped=skipped,
        expected_failures=expected,
    )


def execute_tests(labels, directory, file_logging=False):
    """Zachytí oba proudy až do konce a teprve potom vyhodnotí proces.

    :param labels: Úplné názvy spouštěných testů.
    :param directory: Adresář aktuálního pokusu pro diagnostiku.
    :param file_logging: Zapisovat průběh jen do souboru místo konzole.
    :return: Návratový kód a úplný výstup.
    :raises RuntimeError: Pokud některý čtecí proud selže.
    """
    command = [sys.executable, "manage.py", "test", *labels, f"--settings={SETTINGS}", "--noinput", "--verbosity=2"]
    parts, errors = [], []
    lock = Lock()
    with (directory / "test_output.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        def read_stream(stream):
            """Dočte proud a předá chybu hlavnímu vláknu.

            :param stream: Výstupní proud testovacího procesu.
            """
            try:
                with stream:
                    for line in stream:
                        with lock:
                            parts.append(line)
                            log.write(line)
                            log.flush()
                            if not file_logging:
                                print(line, end="", flush=True)
            except Exception as exc:
                errors.append(exc)
                try:
                    process.terminate()
                except OSError:
                    pass

        readers = [Thread(target=read_stream, args=(stream,)) for stream in (process.stdout, process.stderr)]
        for reader in readers:
            reader.start()
        try:
            returncode = process.wait()
        except BaseException:
            process.terminate()
            process.wait()
            raise
        finally:
            for reader in readers:
                reader.join()
    if errors:
        raise RuntimeError("Zachycení výstupu testů selhalo") from errors[0]
    return returncode, "".join(parts)


def selection_content(root, directory, mode):
    """Připraví kompatibilní tabulku bez ztráty dříve známých testů.

    :param root: Kořen předchozího vstupu výběru.
    :param directory: Výstup aktuálního pokusu.
    :param mode: Režim právě dokončeného výběru.
    :return: Bajty tabulky nebo None, pokud testy tabulku nevytvářejí.
    """
    current = directory / "results.xlsx"
    if not current.exists():
        return None
    select_tests("neuspesne", "", current)
    if mode == "vsechny":
        return current.read_bytes()
    import pandas

    previous = pandas.read_excel(root / "results.xlsx")
    updated = pandas.read_excel(current)
    rows = {}
    for table in (previous, updated):
        for row in table.itertuples(index=False, name=None):
            if isinstance(row[2], str) and row[2]:
                rows[int(row[0])] = row
    output = BytesIO()
    pandas.DataFrame([rows[key] for key in sorted(rows)], columns=previous.columns).to_excel(output, index=False)
    return output.getvalue()


def main(argv=None):
    """Vybere testy a zveřejní výsledek pouze po ověření dokončeného pokusu.

    :param argv: Volitelné argumenty příkazové řádky.
    :return: Nula při úspěchu či výslovném no-op, jinak jedna.
    """
    from test_run_results import create_attempt, publish_outcome, write_summary
    from test_run_retention import AttemptLease

    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("-f", "--fail", action="store_true", help="provede neúspěšné testy")
    modes.add_argument("-a", "--all", action="store_true", help="provede všechny testy")
    modes.add_argument("-t", "--test", type=int, help="provede test daného čísla")
    parser.add_argument("-s", "--soubor", action="store_true", help="uloží výstup do souboru")
    parser.add_argument("--results-root", default=os.environ.get("AMCR_TEST_RESULTS_ROOT"))
    parser.add_argument("--attempt-id", default=os.environ.get("AMCR_TEST_ATTEMPT_ID"))
    args = parser.parse_args(argv)
    mode = "neuspesne" if args.fail else "konkretni" if args.test is not None else "vsechny"
    number = str(args.test) if args.test is not None else ""
    directory = None
    lease = None
    status = 1
    previous_output = os.environ.get("AMCR_TEST_OUTPUT_DIR")
    stage = "initialization"
    try:
        configure_logging()
        logger.info("amcr_test_runner.start")
        stage = "configuration"
        if args.results_root is None:
            from webclient.settings.dev_test import TEST_SCREENSHOT_PATH

            args.results_root = TEST_SCREENSHOT_PATH
        root = Path(args.results_root)
        stage = "attempt"
        lease = AttemptLease(root, args.attempt_id, create_attempt)
        directory, identity = lease.directory, lease.identity
        print(f"Pokus testů: {identity}")
        stage = "selection"
        labels = select_tests(mode, number, root / "results.xlsx")
        if not labels:
            stage = "publication"
            write_summary(directory, 0, 0)
            publish_outcome(directory, identity, mode, number, "no-tests", 0)
            print("Žádné neúspěšné testy k opakování")
            status = 0
        else:
            os.environ["AMCR_TEST_OUTPUT_DIR"] = str(directory) + os.sep
            logger.info("amcr_test_runner.start_test")
            stage = "migration"
            migration = subprocess.run([sys.executable, "manage.py", "migrate", f"--settings={SETTINGS}"], check=False)
            if migration.returncode:
                raise RuntimeError("Migrace testovací databáze selhala")
            stage = "execution"
            returncode, output = execute_tests(labels, directory, args.soubor)
            stage = "summary"
            counts = parse_result(output, returncode)
            passed, failed = counts["passed"], counts["failed"]
            write_summary(directory, passed, failed)
            spreadsheet_required = any("test_selenium" in label for label in labels)
            stage = "publication"
            publish_outcome(
                directory,
                identity,
                mode,
                number,
                "completed",
                returncode,
                spreadsheet_required,
                selection_data=selection_content(root, directory, mode),
                counts=counts,
            )
            status = returncode
    except Exception:
        message = f"Chyba testovacího běhu ({stage})"
        print(message, file=sys.stderr)
        if directory is not None:
            try:
                publish_outcome(directory, identity, mode, number, "error", 1, message=message)
            except Exception:
                print("Zveřejnění chybového výsledku selhalo (publication)", file=sys.stderr)
        status = 1
    finally:
        logger.info("amcr_test_runner.end")
        if previous_output is None:
            os.environ.pop("AMCR_TEST_OUTPUT_DIR", None)
        else:
            os.environ["AMCR_TEST_OUTPUT_DIR"] = previous_output
        if lease is not None:
            try:
                lease.close()
            except Exception:
                message = "Chyba testovacího běhu (retention)"
                print(message, file=sys.stderr)
                if status == 0:
                    try:
                        publish_outcome(directory, identity, mode, number, "error", 1, message=message)
                    except Exception:
                        print("Zveřejnění chybového výsledku selhalo (publication)", file=sys.stderr)
                status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
