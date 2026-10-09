"""Zachytí staged změny CI a vykreslí stejné údaje ve všech reportech.

Reporty žijí v RUNNER_TEMP mimo stageované soubory. Změny se zachytí po hookách;
vykreslení po publikaci doplní její výsledek bez opakovaného čtení diffu.
Metadata workflow a diagnostický text se předávají pouze přes proměnné prostředí.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

MARKER = "<!-- precommit-bot-comment -->"
STEPS = ("compile", "install", "tests", "docs", "hooks", "stage")
DIAGNOSTICS = {
    "LOG_WARNINGS": "Log warnings",
    "DOC_WARNINGS": "Docstring warnings",
    "FLAKE_ERRORS": "Flake8 errors",
    "IMAGE_PARITY_LOG": "Container image reference parity",
    "NPM_VENDOR_LOG": "NPM / static vendor libraries",
}
CHANGE_TYPES = {"A": "Added", "M": "Modified", "D": "Deleted", "R": "Renamed", "C": "Copied", "T": "Type changed"}


def git_output(*args: str) -> str:
    """Načte údaje indexu bez shellové interpolace a závislosti na locale.

    :param args: Další argumenty příkazu ``git diff --cached --find-renames``.
    :return: Výstup diffu dekódovaný jako UTF-8 se zachováním neplatných bajtů pomocí surrogateescape.
    :raises subprocess.CalledProcessError: Pokud Git nedokáže přečíst staged diff.
    """
    return subprocess.run(
        ["git", "diff", "--cached", "--find-renames", *args],
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="surrogateescape",
    ).stdout


def parse_changes(names: str, numstat: str) -> list[dict]:
    """Spojí NUL záznamy názvů, stavů a počtů řádků včetně přejmenování.

    :param names: Výstup ``git diff --name-status -z`` pro zachycený index.
    :param numstat: Výstup ``git diff --numstat -z`` pro tentýž index.
    :return: Seznam změn s cestami, stavy a počty řádků; binární soubory mají počty ``None``.
    """
    counts = {}
    tokens = iter(numstat.rstrip("\0").split("\0")) if numstat else iter(())
    for token in tokens:
        additions, deletions, path = token.split("\t", 2)
        if not path:
            next(tokens)  # The old name; the new name joins the name/status record.
            path = next(tokens)
        counts[path] = {
            "additions": None if additions == "-" else int(additions),
            "deletions": None if deletions == "-" else int(deletions),
        }
    changes = []
    tokens = iter(names.rstrip("\0").split("\0")) if names else iter(())
    for status in tokens:
        path = next(tokens)
        old_path = None
        if status.startswith(("R", "C")):
            old_path, path = path, next(tokens)
        changes.append({"status": status, "path": path, "old_path": old_path, **counts[path]})
    return changes


def write_json(path: Path, record: dict) -> None:
    """Uloží čitelný snapshot beze ztráty neobvyklých znaků v cestách Gitu.

    :param path: Cílový soubor JSON mimo stageované soubory.
    :param record: Zachycené změny, výsledky kroků a metadata reportu.
    """
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def capture(path: Path) -> dict:
    """Zachytí staged změny a provedené operace před commitem oprav.

    :param path: Soubor JSON ve kterém se snapshot uchová pro reporty po publikaci.
    :return: Snapshot výsledků workflow a změn indexu; při neúspěšném stage je seznam změn prázdný.
    """
    outcomes = {step: os.environ.get(f"{step.upper()}_OUTCOME", "skipped") for step in STEPS}
    captured = outcomes["stage"] == "success"
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    hook_exit = os.environ.get("HOOK_EXIT_CODE", "")
    record = {
        "mode": os.environ.get("RUN_MODE", "checks"),
        "source_sha": os.environ.get("SOURCE_SHA", ""),
        "repository_url": f"{server}/{repository}",
        "destination": os.environ.get("FIX_DESTINATION", ""),
        "workflow_url": f"{server}/{repository}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
        "outcomes": outcomes,
        "hook_exit": int(hook_exit) if hook_exit else None,
        "captured": captured,
        "changes": parse_changes(git_output("--name-status", "-z"), git_output("--numstat", "-z")) if captured else [],
        "diagnostics": {title: os.environ.get(key, "") for key, title in DIAGNOSTICS.items()},
        "publication": "pending" if captured else "none",
        "fix_pr_url": "",
    }
    if not record["changes"]:
        record["publication"] = "none"
    write_json(path, record)
    return record


def inline(value: str) -> str:
    """Uzavře cestu nebo větev tak, aby její znaky nezměnily Markdown.

    :param value: Doslovný název souboru, větve nebo režimu pro report.
    :return: Inline blok kódu s bezpečným oddělovačem a escapovanými řídicími znaky.
    """
    value = value.encode("utf-8", "backslashreplace").decode("utf-8")
    value = value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    fence = "`" * (max((len(match) for match in re.findall(r"`+", value)), default=0) + 1)
    return f"{fence} {value} {fence}"


def fenced(value: str) -> str:
    """Zachová doslovný diagnostický text včetně vložených značek bloku kódu.

    :param value: Víceřádkový diagnostický výstup hooku.
    :return: Blok kódu s oddělovačem delším než značky obsažené v diagnostice.
    """
    fence = "`" * max(3, max((len(match) + 1 for match in re.findall(r"`+", value)), default=3))
    return f"{fence}\n{value.rstrip()}\n{fence}"


def processing_failures(record: dict) -> list[str]:
    """Najde selhané či zrušené kroky zpracování odděleně od výsledku hooků.

    :param record: Snapshot obsahující výsledky kroků workflow v položce ``outcomes``.
    :return: Názvy kroků se stavem ``failure`` nebo ``cancelled``.
    """
    return [step for step, outcome in record["outcomes"].items() if outcome in ("failure", "cancelled")]


def result_description(record: dict) -> str:
    """Popíše výsledek bez příslibu, že staged opravy vyřešily všechna selhání.

    :param record: Snapshot změn, výsledků zpracování, hooků a publikace.
    :return: Stavová zpráva rozlišující selhání, navržené opravy a dokončení bez změn.
    """
    failures = processing_failures(record)
    if failures or not record["captured"]:
        reason = f"Processing failed ({', '.join(failures)})" if failures else "Processing did not complete"
        return f"{reason}; no fix PR was published."
    if record["publication"] == "failed":
        return "Publication failed; inspect the workflow logs before relying on the fix branch or PR."
    if record["hook_exit"] not in (None, 0):
        suffix = " A fix PR was published for review." if record["publication"] == "published" else ""
        return f"Checks reported failures (hook exit code {record['hook_exit']}).{suffix}"
    if record["changes"]:
        return (
            "Changes proposed for review."
            if record["publication"] == "published"
            else "Changes staged for publication."
        )
    if any(record["diagnostics"].get(title) for title in ("Log warnings", "Docstring warnings", "Flake8 errors")):
        return "Checks completed with diagnostics; no file changes were staged."
    return "Checks passed without file changes."


def staged_section(record: dict) -> str:
    """Popíše pouze soubory v zachyceném snapshotu indexu.

    :param record: Snapshot se seznamem změn a příznakem dokončeného zachycení indexu.
    :return: Sekce Markdown se soubory, typy změn a počty řádků nebo vysvětlením chybějících změn.
    """
    lines = ["### Staged changes", ""]
    if not record["captured"]:
        lines.append("No staged-change snapshot is available because processing did not complete.")
    elif not record["changes"]:
        lines.append("No file changes were staged.")
    else:
        for change in record["changes"]:
            label = CHANGE_TYPES.get(change["status"][0], change["status"])
            name = inline(change["path"])
            if change["old_path"] is not None:
                name = f"{inline(change['old_path'])} → {name}"
            counts = (
                "binary change"
                if change["additions"] is None
                else f"+{change['additions']} / −{change['deletions']} lines"
            )
            lines.append(f"- {label}: {name} ({counts})")
    return "\n".join(lines)


def common_report(record: dict) -> str:
    """Vykreslí společné údaje pro popis PR, komentář a summary.

    :param record: Snapshot s metadaty běhu, výsledky operací, změnami a diagnostikou.
    :return: Společný report v Markdown včetně dostupného odkazu na opravné PR.
    """
    compile_action = "Pin refresh" if record["mode"] == "refresh" else "Compilation preserving pins"
    hook_exit = record["hook_exit"] if record["hook_exit"] is not None else "unavailable"
    lines = [
        "## CI changes and check results",
        "",
        result_description(record),
        "",
        f"- Mode: {inline(record['mode'])}",
        f"- Source commit: [{record['source_sha'][:12]}]({record['repository_url']}/commit/{record['source_sha']})",
        f"- Fix destination: {inline(record['destination'])}",
        f"- Workflow run: [View logs]({record['workflow_url']})",
    ]
    if record["fix_pr_url"]:
        lines.append(f"- Fix PR: [Review proposed changes]({record['fix_pr_url']})")
    lines.extend(
        [
            "",
            "### Operations",
            "",
            f"- Requirements: {compile_action}; {record['outcomes']['compile']}.",
            f"- Dependency installation: {record['outcomes']['install']}.",
            f"- Dependency documentation: {record['outcomes']['docs']}.",
            f"- Hooks: {record['outcomes']['hooks']}; exit code {hook_exit}.",
            "",
            staged_section(record),
        ]
    )
    for title, value in record["diagnostics"].items():
        if value.strip():
            lines.extend(["", f"### {title}", "", fenced(value)])
    return "\n".join(lines) + "\n"


def render(record: dict, output_dir: Path) -> None:
    """Použije jeden report bez samostatných kopií jeho údajů pro jednotlivé výstupy.

    :param record: Snapshot použitý pro všechny tři reporty bez opětovného čtení diffu.
    :param output_dir: Adresář pro soubory popisu PR, sticky komentáře a Actions summary.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    report = common_report(record)
    outputs = {
        "fix-pr-body.md": (
            "This PR was automatically generated by CI. "
            "Review the staged changes and any remaining diagnostics.\n\n" + report
        ),
        "pr-comment.md": MARKER + "\n" + report,
        "summary.md": report,
    }
    for name, content in outputs.items():
        (output_dir / name).write_text(content, encoding="utf-8", newline="\n")


def update_publication(record: dict) -> None:
    """Doplní výsledky publikace bez změny snapshotu diffu.

    :param record: Snapshot upravený na místě podle výsledku publikace a URL opravného PR z prostředí.
    """
    record["fix_pr_url"] = os.environ.get("FIX_PR_URL", "")
    if processing_failures(record) or not record["changes"]:
        record["publication"] = "none"
    elif os.environ.get("APP_OUTCOME") in ("failure", "cancelled") or os.environ.get("PUBLISH_OUTCOME") in (
        "failure",
        "cancelled",
    ):
        record["publication"] = "failed"
    elif os.environ.get("PUBLISH_OUTCOME") == "success" and record["fix_pr_url"]:
        record["publication"] = "published"
    elif "PUBLISH_OUTCOME" in os.environ:
        record["publication"] = "failed"


def main() -> int:
    """Zachytí změny jednou, vykreslí report před i po publikaci a vrátí stav checku.

    :return: Kód 0 při dokončeném příkazu nebo 1, pokud příkaz ``check`` zjistí selhání běhu.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("capture", "render", "check"))
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.command == "capture":
        record = capture(args.record)
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as handle:
                handle.write(f"changed={'true' if record['changes'] else 'false'}\n")
        return 0
    record = json.loads(args.record.read_text(encoding="utf-8"))
    if args.command == "check":
        return int(
            bool(processing_failures(record))
            or not record["captured"]
            or record["publication"] == "failed"
            or record["hook_exit"] not in (None, 0)
        )
    if args.output_dir is None:
        parser.error("render requires --output-dir")
    update_publication(record)
    write_json(args.record, record)
    render(record, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
