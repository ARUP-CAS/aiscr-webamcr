# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

"""Portable translation records, guarded scoped writes and PO/JSON checks.

The workflow supplies a context JSON with catalogue paths by language, explicit keys or a resolved comparison baseline,
explicit removals, changed callers and optional verification evidence. Proposed texts may be supplied inline
(``proposed_texts``) or as ``proposed`` files. No native pipeline, source extractor, sibling bridge or full hub engine
is imported. Use an existing ignored directory for --work-dir; no venv or configuration is created.

Contract: review/translation-revision
Class: tool
Exit codes: 0 local operation succeeded (see evidence limits); 1 refusal/findings; 2 unusable input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:  # pragma: no cover -- direct script startup supplies this path
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.translation import checks, ledger, ngx_catalogue, po_catalogue  # noqa: E402


def catalogue_maps(paths: dict, format_name: str) -> dict:
    """Read language maps without a mandatory source-language catalogue."""
    result = {}
    for language, path in paths.items():
        texts, _ = checks.catalogue(path, format_name)
        result[language] = {
            key: value[0] if isinstance(value, list) and len(value) == 1 else value for key, value in texts.items()
        }
    return result


def _inline_proposed(before: dict, proposed_texts: dict) -> dict:
    """Overlay inline proposed texts by language onto the pre-write catalogue maps."""
    proposed = {language: dict(texts) for language, texts in before.items()}
    for language, mapping in (proposed_texts or {}).items():
        if language not in proposed:
            raise ValueError(f"inline proposal names an unknown language: {language}")
        proposed[language].update(mapping)
    return proposed


def _removal_evidence(context: dict) -> dict:
    """Map each declared removal key to its reason and unused-evidence."""
    evidence = {}
    for item in context.get("removals", []):
        if isinstance(item, dict):
            if "key" not in item:
                raise ValueError("a removal entry requires a key")
            evidence[item["key"]] = {"reason": item.get("reason", ""), "unused": item.get("unused", "")}
    return evidence


def prepare(context: dict, previous: dict | None = None) -> dict:
    """Build a scoped record against pre-write snapshots, not arbitrary dirty-tree diffs."""
    format_name = context.get("format", "ngx")
    if format_name in ("po", "ngx"):
        before = catalogue_maps(context["catalogues"], format_name)
        proposed = _inline_proposed(before, context.get("proposed_texts", {}))
        file_proposals = catalogue_maps(context.get("proposed", {}), format_name)
        if set(file_proposals) - set(before):
            raise ValueError("proposed catalogue languages must belong to the pre-write catalogues")
        proposed.update(file_proposals)
        baseline = catalogue_maps(context.get("baseline_catalogues", {}), format_name)
    else:
        before = context.get("texts", {})
        proposed = context.get("proposed_texts", before)
        baseline = context.get("baseline_texts", {})
    scope = ledger.select_scope(context, baseline, proposed)
    if set(before) != set(proposed):
        raise ValueError("pre-write and proposed catalogue languages must agree")
    record_data = ledger.scoped_record(scope, before, proposed, previous, _removal_evidence(context))
    record_data["catalogues"] = dict(context["catalogues"])
    record_data["context"] = {name: context.get(name) for name in ("authority", "conventions", "changed_callers")}
    return record_data


# A scoped record plus its removals make the validation a long, branch-heavy gate.
# pylint: disable-next=too-many-branches
def write_record(target: str | Path, format_name: str, record_data: dict, language: str) -> None:
    """Validate all scoped edits and removals before writing one catalogue, preserving unrelated bytes."""
    if record_data.get("version") != 2 or language not in record_data["scope"]["languages"]:
        raise ValueError("write requires a scoped ledger and a recorded language")
    entries = record_data["entries"]
    removals = record_data.get("removals", {})
    if Path(record_data["catalogues"][language]).resolve() != Path(target).resolve():
        raise ValueError("target catalogue is outside the recorded scope")
    if set(entries) - set(record_data["scope"]["keys"]):
        raise ValueError("ledger entries exceed approved scope")
    if set(removals) - set(record_data["scope"].get("removals", [])):
        raise ValueError("ledger removals exceed approved scope")
    current = catalogue_maps({language: target}, format_name)[language]
    for key, entry in entries.items():
        value = entry["texts"][language]
        if current.get(key) not in (entry["expected"].get(language), value):
            raise ValueError(f"pre-write conflict for {key}; preserve the user's edit")
        if current.get(key) == value:
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"unsupported or empty proposed text for {key}")
        texts = [text for text in entry["texts"].values() if isinstance(text, str)]
        if any(checks.unsupported_placeholders(text) for text in texts):
            raise ValueError(f"unsupported placeholder grammar for {key}; use a native formatter check")
        if checks.text_contract_problems(key, texts):
            raise ValueError(f"placeholder or markup mismatch for {key}")
    for key, removal in removals.items():
        if not (removal.get("reason") or "").strip() or not (removal.get("unused") or "").strip():
            raise ValueError(f"removal {key} requires a reason and unused-evidence")
        present = current.get(key)
        if present is None:
            continue
        if present != removal["expected"].get(language):
            raise ValueError(f"pre-write conflict for removal {key}; preserve the user's edit")
    payload = _render_changes(target, format_name, entries, removals, current, language)
    Path(target).write_bytes(payload)


# One renderer per supported format, with removal alongside the upsert path.
# pylint: disable-next=too-many-arguments,too-many-positional-arguments,too-many-branches
def _render_changes(
    target: str | Path, format_name: str, entries: dict, removals: dict, current: dict, language: str
) -> bytes:
    """Apply validated scoped values and removals using a lossless catalogue profile."""
    if format_name == "ngx":
        obj, _ = ngx_catalogue.assert_preserving(target)
        for key, entry in entries.items():
            if current.get(key) == entry["texts"][language]:
                continue
            ngx_catalogue.set_value(obj, key, entry["texts"][language])
        for key in removals:
            if current.get(key) is None:
                continue
            ngx_catalogue.remove(obj, key)
        payload = ngx_catalogue.render_like(target, obj)
    elif format_name == "po":
        obj, eol = po_catalogue.load_preserving(target)
        existing = {item.msgid: item for item in obj}
        for key, entry in entries.items():
            if current.get(key) == entry["texts"][language]:
                continue
            item = existing.get(key)
            if item is None:
                obj.append(po_catalogue.new_entry(key, entry["texts"][language]))
            else:
                if item.msgid_plural:
                    raise ValueError(f"plural correction requires a native plural-aware writer: {key}")
                item.msgstr = entry["texts"][language]
                item.flags = [flag for flag in item.flags if flag != "fuzzy"]
        for key in removals:
            if current.get(key) is None:
                continue
            item = existing.get(key)
            if item is not None:
                obj.remove(item)
        payload = po_catalogue.dumps(obj, eol)
    else:
        raise ValueError("unsupported write format; prepare wording and hand over its application")
    return payload


def run(args) -> int:
    """Execute one local operation; verification layers remain explicit in JSON output."""
    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    if not isinstance(context, dict):
        raise ValueError("run context must be an object")
    for field in ("catalogues", "proposed", "baseline_catalogues"):
        if field in context:
            context[field] = {
                language: str((Path(args.root) / path).resolve()) for language, path in context[field].items()
            }
    work = Path(args.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    record_path = Path(args.ledger) if args.ledger else work / "ledger.json"
    if args.command == "prepare":
        previous = ledger.load(args.previous) if args.previous else None
        record_data = prepare(context, previous)
        record_path.write_bytes(ledger.dump(record_data).encode("utf-8"))
        ledger.write_review(work / "review.md", record_data, args.title)
        print(
            f"translation.local: {len(record_data['entries'])} scoped change(s), "
            f"{len(record_data.get('removals', {}))} removal(s)"
        )
        return 0
    if args.command == "write":
        if not args.approve:
            print("translation.local: refused: operator text approval is required", file=sys.stderr)
            return 1
        write_record(
            Path(args.root) / args.target, context.get("format", "ngx"), ledger.load(record_path), args.language
        )
        return 0
    format_name = context.get("format", "ngx")
    current = catalogue_maps(context["catalogues"], format_name)
    baseline = catalogue_maps(context.get("baseline_catalogues", {}), format_name)
    scope = ledger.select_scope(context, baseline, current)
    record_data = ledger.load(record_path) if record_path.is_file() else None
    if record_data is not None and record_data.get("version") == 2:
        scope["keys"] = sorted(set(scope["keys"]) | set(record_data["scope"]["keys"]))
        scope["removals"] = sorted(set(scope.get("removals", [])) | set(record_data["scope"].get("removals", [])))
        scope["keys"] = sorted(set(scope["keys"]) - set(scope["removals"]))
    report = checks.verify_languages(
        context["catalogues"], format_name, scope["keys"], context.get("evidence"), scope.get("removals")
    )
    report["layers"]["approved_changes"] = ledger.applied_changes(record_data, current, scope, context["catalogues"])
    report["fully_verified"] = all(layer["status"] == "passed" for layer in report["layers"].values())
    (work / "verify.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({name: layer["status"] for name, layer in report["layers"].items()}))
    return 1 if any(layer["status"] == "failed" for layer in report["layers"].values()) else 0


def build_parser() -> argparse.ArgumentParser:
    """Return the portable command grammar, with explicit context and ignored output path."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="Subject root; paths in the context are supplied explicitly.")
    parser.add_argument("--context", required=True, help="Run context JSON (paths by language, scope and evidence).")
    parser.add_argument("--work-dir", required=True, help="Existing repository-approved ignored output directory.")
    parser.add_argument("--ledger", default=None, help="Scoped ledger path (default: work directory).")
    commands = parser.add_subparsers(dest="command", required=True)
    review = commands.add_parser("prepare")
    review.add_argument("--previous", default=None, help="Previous scoped record, retaining applied changes.")
    review.add_argument("--title", default="Translation review")
    write = commands.add_parser("write")
    write.add_argument("--target", required=True)
    write.add_argument("--language", required=True)
    write.add_argument("--approve", action="store_true", help="Confirm operator approval of every recorded text.")
    commands.add_parser("verify")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Return an exit code; missing adapters and unsupported input are explicit limits."""
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except (OSError, ValueError, KeyError, po_catalogue.CatalogueError, ngx_catalogue.CatalogueError) as exc:
        print(f"translation.local: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover -- subprocess bootstrap
    raise SystemExit(main())
