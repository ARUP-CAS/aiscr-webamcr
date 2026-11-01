"""Spouštění explicitních Django CI sad a souhrn jejich skutečného výsledku."""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "webclient"
MANIFEST = Path(__file__).with_name("django_ci_suites.json")


def test_modules(project):
    """Najde moduly testů v kořenových Python balíčcích, nikoliv lokální kopie repozitáře.

    :param project: Kořen Django projektu obsahující balíčky aplikací.
    :return: Množina názvů modulů odpovídajících výchozímu vzoru test*.py.
    """
    modules = set()
    for app in project.iterdir():
        if not app.is_dir() or not (app / "__init__.py").is_file():
            continue
        for path in app.rglob("test*.py"):
            modules.add(".".join(path.relative_to(project).with_suffix("").parts))
    return modules


def load_suites(manifest=MANIFEST, project=PROJECT):
    """Ověří úplné a jednoznačné zařazení všech modulů bez automatického dělení.

    :param manifest: JSON soubor s explicitním rozdělením modulů.
    :param project: Kořen projektu pro ověření úplnosti manifestu.
    :return: Ověřené seznamy modulů a zdůvodněných výjimek.
    :raises ValueError: Pokud manifest vynechává, duplikuje nebo nesprávně zařazuje modul.
    """
    suites = json.loads(manifest.read_text(encoding="utf-8"))
    if set(suites) != {"fast", "database", "excluded"}:
        raise ValueError("Expected fast, database and excluded lists")
    if any(not isinstance(suites[key], list) or not suites[key] for key in ("fast", "database")):
        raise ValueError("Runnable suites must be non-empty lists")
    if not isinstance(suites["excluded"], dict) or any(not reason for reason in suites["excluded"].values()):
        raise ValueError("Every exclusion needs a reason")
    labels = suites["fast"] + suites["database"] + list(suites["excluded"])
    if any(not isinstance(label, str) for label in labels) or len(labels) != len(set(labels)):
        raise ValueError("Duplicate, overlapping or invalid module labels")
    actual = test_modules(project)
    if set(labels) != actual:
        raise ValueError(
            f"Unassigned modules: {sorted(actual - set(labels))}; missing modules: {sorted(set(labels) - actual)}"
        )
    return suites


def run_child(labels):
    """Nastaví izolaci ještě před načtením Django; použije standardní management command.

    :param labels: Přesné názvy modulů jedné schválené sady.
    """
    from django_ci_network import install

    install()
    os.environ["DJANGO_SETTINGS_MODULE"] = "webclient.settings.github_ci"
    sys.path.insert(0, str(PROJECT))
    os.chdir(PROJECT)
    from django.core.management import execute_from_command_line

    # Dočasná média nemění data v checkoutu ani ve sdíleném lokálním prostředí.
    with tempfile.TemporaryDirectory(prefix="amcr-ci-media-") as media:
        from django.conf import settings

        settings.MEDIA_ROOT = media
        settings.STATIC_ROOT = str(Path(media) / "static")
        settings.COMPRESS_ROOT = settings.STATIC_ROOT
        execute_from_command_line(["manage.py", "test", *labels, "--noinput", "--verbosity=2"])


def run_suite(suite, output_dir):
    """Spustí podproces, uloží log a souhrn; zachová selhání i zachycené síťové pokusy.

    :param suite: Název sady fast nebo database z manifestu.
    :param output_dir: Adresář pro úplný log, síťová odmítnutí a Markdown souhrn.
    :return: Nenulový kód při selhání testů, spuštění nebo síťové izolace.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    network_log = output_dir / "network.log"
    network_log.write_text("", encoding="utf-8")
    env = {**os.environ, "AMCR_CI_NETWORK_LOG": str(network_log.resolve()), "PYTHONUNBUFFERED": "1"}
    command = [sys.executable, str(Path(__file__).resolve()), "--child", "--suite", suite]
    tail = deque(maxlen=50)
    failures = []
    totals = []
    start = time.monotonic()
    code = 2
    with (output_dir / "test.log").open("w", encoding="utf-8") as log:
        try:
            with subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env
            ) as child:
                for line in child.stdout:
                    print(line, end="", flush=True)
                    log.write(line)
                    tail.append(line)
                    if re.match(r"^(FAIL|ERROR):", line):
                        failures.append(line.strip())
                    if re.match(r"^(Ran \d+ tests?|OK\b|FAILED\b|Found \d+ test)", line):
                        totals.append(line.strip())
                code = child.wait()
        except OSError as error:
            tail.append(f"Could not start tests: {error}\n")
            log.write(tail[-1])
    blocked = network_log.read_text(encoding="utf-8")
    if blocked:
        code = code or 1
    status = "PASS" if code == 0 else "FAIL"
    summary = f"## Django {suite}: {status}\n\nExit code: {code}; elapsed: {time.monotonic() - start:.1f}s.\n\n"
    summary += "\n".join(totals) + "\n\n"
    if failures:
        summary += "### Failing tests\n\n" + "\n".join(f"- `{entry}`" for entry in failures) + "\n\n"
    if blocked:
        summary += "### Forbidden network attempts\n\n```text\n" + blocked[:6000].replace("```", "'''") + "\n```\n\n"
    if code:
        summary += "### Diagnostic log tail\n\n```text\n" + "".join(tail)[-12000:].replace("```", "'''") + "\n```\n"
    summary += "\nFull output: `test.log` in the job's log artifact.\n"
    (output_dir / "summary.md").write_text(summary, encoding="utf-8")
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(summary)
    return code if code >= 0 else 1


def main():
    """Ověří manifest nebo spustí jednu explicitní sadu a vrátí stav procesu."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--suite", choices=("fast", "database"))
    parser.add_argument("--output-dir", type=Path, default=Path(tempfile.gettempdir()) / "amcr-ci-results")
    args = parser.parse_args()
    try:
        suites = load_suites()
    except (OSError, ValueError) as error:
        parser.exit(2, f"Invalid CI inventory: {error}\n")
    if args.validate:
        print("CI inventory: " + ", ".join(f"{key}={len(value)}" for key, value in suites.items()))
        return 0
    if not args.suite:
        parser.error("--suite or --validate is required")
    if args.child:
        run_child(suites[args.suite])
        return 0
    return run_suite(args.suite, args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
