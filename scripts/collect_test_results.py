"""Ověří stažené výsledky konkrétního pokusu před publikací do GitHub Actions."""

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "webclient"))
from test_run_results import load_record, validate_bundle  # noqa: E402


def command_data(text):
    """Zakóduje text jako data příkazu workflow, aby nemohl začít další příkaz.

    :param text: Zobrazovaná diagnostika.
    :return: Text s ``%``, CR a LF zakódovanými podle pravidel GitHub Actions.
    """
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def code_span(text):
    """Vloží text do kódového úseku Markdownu bez ohledu na obsažené zpětné apostrofy.

    :param text: Jednořádkový text.
    :return: Kódový úsek s oddělovačem delším než nejdelší běh apostrofů v textu.
    """
    fence = "`" * (max((len(run) for run in re.findall("`+", text)), default=0) + 1)
    return f"{fence} {text} {fence}"


def report(directory, identity, mode, number, output_path, summary_path):
    """Zveřejní pouze úplný aktuální výsledek a zachová neúspěch procesu.

    U chybového výsledku uvede zaznamenanou příčinu v souhrnu kroku
    a v jediné chybové anotaci zakódované jako data příkazu workflow.

    :param directory: Adresář staženého pokusu.
    :param identity: Očekávaná identita.
    :param mode: Očekávaný režim.
    :param number: Očekávané číslo testu.
    :param output_path: Soubor GITHUB_OUTPUT.
    :param summary_path: Soubor GITHUB_STEP_SUMMARY.
    :return: Návratový kód pokusu.
    """
    record = load_record(directory, identity, mode, number)
    counts = validate_bundle(directory, record)
    summary = f"## 🧪 Výsledky testů\n\nPokus: `{identity}`; stav: `{record['state']}`.\n"
    cause = (record["message"] or "Chyba testovacího běhu") if record["state"] == "error" else None
    if cause is not None:
        summary += f"\nPříčina: {code_span(cause)}\n"
    if counts is not None:
        passed, failed = counts
        summary += f"\n| Stav | Počet |\n|------|-------|\n| ✅ Prošlo | {passed} |\n| ❌ Selhalo | {failed} |\n"
        skipped, expected = record["counts"]["skipped"], record["counts"]["expected_failures"]
        summary += f"| Přeskočeno | {skipped} |\n| Očekávaná selhání | {expected} |\n"
    with Path(output_path).open("a", encoding="utf-8") as stream:
        stream.write("ARTIFACTS=true\n")
    with Path(summary_path).open("a", encoding="utf-8") as stream:
        stream.write(summary)
    if counts is not None and counts[1] > 0:
        print(f"::error::Selhalo {counts[1]} testů")
    if cause is not None:
        print(f"::error::{command_data(cause)}")
    return record["exit_code"]


def main(argv=None):
    """Nejprve určí bezpečné názvy ke stažení, potom ověří celý balík.

    :param argv: Volitelné argumenty příkazové řádky.
    :return: Nula při úspěchu, jinak nenulový výsledek.
    """
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("plan", "report"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--number", default="")
    args = parser.parse_args(argv)
    try:
        if args.action == "plan":
            record = load_record(args.directory, args.attempt_id, args.mode, args.number)
            for name in sorted(record["files"]):
                print(name)
            return 0
        return report(
            args.directory,
            args.attempt_id,
            args.mode,
            args.number,
            os.environ["GITHUB_OUTPUT"],
            os.environ["GITHUB_STEP_SUMMARY"],
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"::error::Invalid current test result: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
