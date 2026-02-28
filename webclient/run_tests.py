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
    ]


output_buffer = StringIO()


def reader_and_capture(pipe):
    """
    Provádí operaci reader and capture.

    :param pipe: Vstupní hodnota ``pipe`` pro danou operaci.
    """
    while True:
        line = pipe.readline()
        if not line:
            break
        print(line, end="")
        output_buffer.write(line)


def filelog(pipe):
    """
    Provádí operaci filelog.

    :param pipe: Vstupní hodnota ``pipe`` pro danou operaci.
    """
    with open("/vol/web/selenium_test/test.log", "a") as file:
        while True:
            line = pipe.read(1)
            file.write(line)
            if not line:
                break


logger.info("amcr_test_runner.start_test")
subprocess.run(f"python3 manage.py migrate --database test_db --settings={SETTINGS}", text=True, shell=True)

process = subprocess.Popen(
    f"python3 manage.py test {' '.join(test_list)} --settings={SETTINGS} --noinput --verbosity=2",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    shell=True,
)
if args.soubor is True:
    t1 = Thread(target=filelog, args=[process.stdout]).start()
    t2 = Thread(target=filelog, args=[process.stderr]).start()
else:
    t1 = Thread(target=reader_and_capture, args=[process.stdout]).start()
    t2 = Thread(target=reader_and_capture, args=[process.stderr]).start()
process.wait()

logger.info("amcr_test_runner.end")

stdout_text = output_buffer.getvalue()

# Zápis do logu
with open("/vol/web/selenium_test/test_output.log", "w") as f:
    f.write(stdout_text)
# Parsování z výstupu
ran_match = re.search(r"Ran (\d+) tests?", stdout_text)
failures_match = re.search(r"failures=(\d+)", stdout_text)
errors_match = re.search(r"errors=(\d+)", stdout_text)
ok_match = re.search(r"\nOK\n", stdout_text)

ran = int(ran_match.group(1)) if ran_match else 0
failures = int(failures_match.group(1)) if failures_match else 0
errors = int(errors_match.group(1)) if errors_match else 0
passed = ran - failures - errors if ran > 0 else 0

# Výstup do souboru pro GitHub Actions
with open("/vol/web/selenium_test/test_summary.env", "w") as f:
    f.write(f"PASSED={passed}\n")
    f.write(f"FAILED={failures + errors}\n")

# Výsledek
if failures + errors > 0:
    exit(1)
else:
    exit(0)
