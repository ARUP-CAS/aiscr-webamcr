import argparse
import logging
import os
import re
import subprocess
from io import StringIO
from threading import Thread

import logstash

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--fail", help="provede neúspěšné testy", action="store_true")
parser.add_argument("-a", "--all", help="provede všechny testy", action="store_true")
parser.add_argument("-t", "--test", type=int, help="provede test daného čísla")
parser.add_argument("-s", "--soubor", help="uloží výstup do souboru", action="store_true")
args = parser.parse_args()

SETTINGS = "webclient.settings.dev_test"
# Fedora modules need DEBUG=True for the loopback SITE_URL, so they run in their own process.
FEDORA_MODULES = (
    "core.tests.test_fedora_integration_child_walk",
    "core.tests.test_fedora_integration_paradata",
)

logger = logging.getLogger("webamcr.test_runner")
# logger.setLevel(logging.INFO)
logger.addHandler(logstash.TCPLogstashHandler(host="logstash", version=1, tags="dev_test"))
logger.info("amcr_test_runner.start")

if args.fail is True:
    import pandas

    from webclient.settings.dev_test import TEST_SCREENSHOT_PATH

    if os.path.isfile(f"{TEST_SCREENSHOT_PATH}results.xlsx"):
        data = pandas.read_excel(f"{TEST_SCREENSHOT_PATH}results.xlsx")
        d = data.values.tolist()
        test_list = []
        for line in d:
            if line[3] != "OK" and isinstance(line[3], float) is not True:
                test_list.append(line[2])
        if len(test_list) == 0:
            print("Všechny testy OK")
            exit()

    else:
        print("Nenalezn soubor s výsledky")
        exit()
elif args.test is not None:
    import pandas

    from webclient.settings.dev_test import TEST_SCREENSHOT_PATH

    if os.path.isfile(f"{TEST_SCREENSHOT_PATH}results.xlsx"):
        data = pandas.read_excel(f"{TEST_SCREENSHOT_PATH}results.xlsx")
        d = data.values.tolist()
        test_list = []
        for line in d:
            if line[0] == args.test:
                test_list.append(line[2])
                break
        if len(test_list) == 0:
            print(f"Test {args.test} nenalezen.")
            exit()
else:
    test_list = [
        "core.tests.test_selenium",
        "projekt.tests.test_selenium",
        "dokument.tests.test_selenium",
        "lokalita.tests.test_selenium",
        "arch_z.tests.test_selenium",
        "pas.tests.test_selenium",
        "oznameni.tests.test_selenium",
        "ez.tests.test_selenium",
        "uzivatel.tests.test_selenium",
        "heslar.tests.test_selenium",
    ] + list(FEDORA_MODULES)


def reader_and_capture(pipe, buffer):
    """
    Průběžně vypisuje výstup podprocesu na terminál a ukládá jej do bufferu.

    :param pipe: Stream (pipe), ze kterého se průběžně čte výstup podprocesu.
    :param buffer: Buffer, do kterého se ukládá výstup pro pozdější vyhodnocení.
    """
    while True:
        line = pipe.readline()
        if not line:
            break
        print(line, end="")
        buffer.write(line)


def filelog(pipe, buffer):
    """
    Průběžně zapisuje výstup podprocesu do ``test.log`` a ukládá jej do bufferu.

    :param pipe: Stream (pipe), ze kterého se průběžně čte výstup podprocesu.
    :param buffer: Buffer, do kterého se ukládá výstup pro pozdější vyhodnocení.
    """
    with open("/vol/web/selenium_test/test.log", "a") as file:
        while True:
            line = pipe.read(1)
            file.write(line)
            buffer.write(line)
            if not line:
                break


def run_suite(modules, extra_args=""):
    """
    Spustí ``manage.py test`` pro zadané moduly a počká na dokončení čtení jeho výstupu.

    :param modules: Seznam testovacích modulů, tříd nebo metod předaných Django test runneru.
    :param extra_args: Další argumenty příkazu ``manage.py test``.
    :return: Slovník s počty ``ran``, ``failures``, ``errors`` a ``skipped`` z výstupu runneru.
    """
    buffer = StringIO()
    process = subprocess.Popen(
        f"python3 manage.py test {' '.join(modules)} --settings={SETTINGS} --noinput --verbosity=2 {extra_args}",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )
    target = filelog if args.soubor is True else reader_and_capture
    threads = [Thread(target=target, args=[stream, buffer]) for stream in (process.stdout, process.stderr)]
    for thread in threads:
        thread.start()
    process.wait()
    for thread in threads:
        thread.join()
    text = buffer.getvalue()
    with open("/vol/web/selenium_test/test_output.log", "a") as f:
        f.write(text)
    counts = {"ran": 0, "failures": 0, "errors": 0, "skipped": 0}
    ran_match = re.search(r"Ran (\d+) tests?", text)
    if ran_match:
        counts["ran"] = int(ran_match.group(1))
    for key in ("failures", "errors", "skipped"):
        match = re.search(rf"{key}=(\d+)", text)
        if match:
            counts[key] = int(match.group(1))
    return counts


logger.info("amcr_test_runner.start_test")
subprocess.run(f"python3 manage.py migrate --database test_db --settings={SETTINGS}", text=True, shell=True)

# Truncate the log; each run_suite() call appends its output.
open("/vol/web/selenium_test/test_output.log", "w").close()
fedora_tests = [test for test in test_list if test.startswith(FEDORA_MODULES)]
selenium_tests = [test for test in test_list if not test.startswith(FEDORA_MODULES)]

ran = failures = errors = 0
if selenium_tests:
    result = run_suite(selenium_tests)
    ran += result["ran"]
    failures += result["failures"]
    errors += result["errors"]
if fedora_tests:
    result = run_suite(fedora_tests, "--debug-mode")
    ran += result["ran"]
    failures += result["failures"]
    errors += result["errors"]
    # A skipped or missing Fedora run means no protocol coverage, so count it as a failure.
    if result["ran"] == 0 or result["skipped"] > 0:
        print(f"Fedora integration tests did not run completely (ran={result['ran']}, skipped={result['skipped']}).")
        errors += max(result["skipped"], 1)

logger.info("amcr_test_runner.end")

passed = max(ran - failures - errors, 0)

# Výstup do souboru pro GitHub Actions
with open("/vol/web/selenium_test/test_summary.env", "w") as f:
    f.write(f"PASSED={passed}\n")
    f.write(f"FAILED={failures + errors}\n")

# Výsledek
if failures + errors > 0:
    exit(1)
else:
    exit(0)
