# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

"""Ledger for proposed and applied translation changes.

The ledger is the single structured record of a revision: ``key -> {cs, en, batch,
reason}``. Every proposed text change is recorded here with its batch and reason, and a catalogue is written as the
source keys plus the ledger. The Markdown review tables the operator reads are rendered from this JSON, never authored
beside it.

A scoped record may also carry **removals**: keys a proven-unused id leaves behind. A removal is recorded separately
from the text entries, with a reason and the unused-evidence that established non-emission, so deleting an entry is an
explicitly reviewed act rather than a side effect of a missing proposal.

A rebuild compares the working tree against the **committed** catalogue, so a change already applied to the working tree
stays recorded instead of disappearing the next time the ledger is rebuilt.

Contract: review/translation-revision
Class: library
Exit codes: Library with no entrypoint.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

__all__ = ["applied_changes", "dump", "load", "render_scoped_review", "scoped_record", "select_scope", "write_review"]


def _key_cell(key: str) -> str:
    """Use HTML code for escaped keys so character entities render as their values."""
    escaped = _cell(key)
    return f"`{key}`" if escaped == key else f"<code>{escaped}</code>"


def _cell(value) -> str:
    """Display literal catalogue text without letting it change Markdown structure."""
    text = html.escape(str(value), quote=False).replace("\\", "&#92;")
    for token in ("|", "`", "*", "_", "[", "]"):
        text = text.replace(token, f"&#{ord(token)};")
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def load(path: str | Path) -> dict:
    """Read a ledger from JSON."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(ledger: dict) -> str:
    """Render a ledger in its canonical JSON form."""
    return json.dumps(ledger, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def write_review(path: str | Path, record_data: dict, title: str) -> None:
    """Write a rendered scoped review table with LF line endings."""
    Path(path).write_bytes(render_scoped_review(record_data, title).encode("utf-8"))


def select_scope(context: dict, baseline: dict, current: dict) -> dict:
    """Select changed texts/callers, explicit removals, or whole-catalogue review.

    Baseline catalogues are supplied from a resolved PR/release reference by the workflow. This library does not reach
    siblings or invent a missing reference.
    """
    mode = context.get("mode", "targeted")
    if mode not in ("targeted", "pre-release", "full"):
        raise ValueError("unknown review mode")
    keys = set(context.get("keys", []))
    removals = [item["key"] if isinstance(item, dict) else item for item in context.get("removals", [])]
    if mode == "pre-release" or context.get("comparison"):
        if not context.get("baseline") or not baseline:
            raise ValueError("comparison scope requires a resolved baseline and its catalogues")
    languages = set(current)
    if not languages:
        raise ValueError("no catalogue languages supplied")
    if baseline and (mode == "pre-release" or context.get("comparison") or not keys):
        for language in languages:
            keys.update(
                key
                for key in set(current[language]) | set(baseline.get(language, {}))
                if current[language].get(key) != baseline.get(language, {}).get(key)
            )
    keys.update(site["key"] for site in context.get("changed_callers", []))
    if mode == "full":
        keys = set().union(*(set(texts) for texts in current.values()))
    elif not baseline and not context.get("keys") and not context.get("changed_callers") and not removals:
        raise ValueError("targeted scope needs named keys/callers or a resolved catalogue comparison")
    # A key is either a text entry or a removal, never both.
    keys.difference_update(removals)
    removals = sorted(set(removals))
    return {
        "mode": mode,
        "baseline": context.get("baseline"),
        "head": context.get("head"),
        "keys": sorted(keys),
        "removals": removals,
        "languages": sorted(languages),
        "paths": context.get("paths", []),
    }


# Both languages, the removal list and the pre-write values are separate fields of one record.
# pylint: disable-next=too-many-arguments,too-many-locals
def scoped_record(
    scope: dict,
    before: dict,
    proposed: dict,
    previous: dict | None = None,
    removal_evidence: dict | None = None,
) -> dict:
    """Record scoped proposals; retain original and pre-write values separately.

    A removal is recorded apart from the text entries. Its key must exist in the pre-write snapshot, and it must carry a
    non-empty reason and unused-evidence before it is accepted.
    """
    entries = {}
    prior = (previous or {}).get("entries", {})
    prior_removals = (previous or {}).get("removals", {})
    if set(prior) - set(scope["keys"]):
        raise ValueError("previous ledger entries lie outside the selected scope")
    if set(prior_removals) - set(scope.get("removals", [])):
        raise ValueError("previous ledger removals lie outside the selected scope")
    for key in scope["keys"]:
        old = {lang: before[lang].get(key) for lang in scope["languages"]}
        new = {lang: proposed[lang].get(key) for lang in scope["languages"]}
        if any(value is None for value in new.values()):
            raise ValueError(f"missing proposed translation for {key}")
        entries[key] = {
            "old": prior.get(key, {}).get("old", old),
            "expected": old,
            "texts": new,
            "batch": prior.get(key, {}).get("batch", "SCOPED"),
            "reason": prior.get(key, {}).get("reason", "scoped translation correction"),
        }
    evidence = removal_evidence or {}
    removals = {}
    for key in scope.get("removals", []):
        old = {lang: before[lang].get(key) for lang in scope["languages"]}
        if all(value is None for value in old.values()):
            raise ValueError(f"removal target is absent from the pre-write catalogue: {key}")
        prior_entry = prior_removals.get(key, {})
        item = evidence.get(key) or {}
        reason = (item.get("reason") or prior_entry.get("reason") or "").strip()
        unused = (item.get("unused") or prior_entry.get("unused") or "").strip()
        if not reason or not unused:
            raise ValueError(f"removal {key} requires a reason and unused-evidence")
        removals[key] = {
            "old": prior_entry.get("old", old),
            "expected": old,
            "reason": reason,
            "unused": unused,
        }
    return {"version": 2, "scope": scope, "entries": entries, "removals": removals}


def render_scoped_review(record_data: dict, title: str) -> str:
    """Render old/proposed text in each selected language without a full catalogue table."""
    lines = [
        f"# {title}",
        "",
        f"Scope: {_cell(record_data['scope']['mode'])}; baseline: {_cell(record_data['scope'].get('baseline'))}",
        "",
        "| Key | Language | Before | Proposed | Reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for key, entry in sorted(record_data["entries"].items()):
        for lang in record_data["scope"]["languages"]:
            lines.append(
                f"| {_key_cell(key)} | {_cell(lang)} | {_cell(entry['old'].get(lang))} | "
                f"{_cell(entry['texts'][lang])} | {_cell(entry['reason'])} |"
            )
    for key, entry in sorted(record_data.get("removals", {}).items()):
        for lang in record_data["scope"]["languages"]:
            reason = f"remove: {entry['reason']} (unused: {entry['unused']})"
            lines.append(
                f"| {_key_cell(key)} | {_cell(lang)} | {_cell(entry['old'].get(lang))} | "
                f"{_cell('— removed —')} | {_cell(reason)} |"
            )
    return "\n".join(lines) + "\n"


def applied_changes(record_data: dict | None, current: dict, scope: dict, catalogues: dict) -> dict:
    """Compare applied scoped texts and removals with the reviewed record."""
    layer = {
        "status": "unverified",
        "method": "current scoped texts compared with the approved ledger",
        "scope": scope["keys"] + scope.get("removals", []),
        "problems": [],
        "unverified": [],
    }
    if record_data is None or record_data.get("version") != 2:
        layer["unverified"] = ["a scoped approved ledger is unavailable"]
        return layer
    recorded = record_data["scope"]
    entries = record_data["entries"]
    removed = record_data.get("removals", {})
    paths_match = set(record_data["catalogues"]) == set(catalogues) and all(
        Path(record_data["catalogues"][lang]).resolve() == Path(path).resolve() for lang, path in catalogues.items()
    )
    if not paths_match or any(recorded.get(name) != scope.get(name) for name in ("mode", "baseline")):
        layer["problems"].append({"kind": "ledger-scope-mismatch"})
    if set(entries) - set(recorded["keys"]):
        layer["problems"].append({"kind": "ledger-entries-outside-scope"})
    if set(removed) - set(recorded.get("removals", [])):
        layer["problems"].append({"kind": "ledger-removals-outside-scope"})
    for key in scope["keys"]:
        if key not in entries:
            layer["problems"].append({"key": key, "kind": "unapproved-key"})
            continue
        for language, texts in current.items():
            if key not in texts or texts[key] != entries[key]["texts"].get(language):
                layer["problems"].append({"key": key, "kind": "approved-text-mismatch", "language": language})
    for key in scope.get("removals", []):
        if key not in removed:
            layer["problems"].append({"key": key, "kind": "unapproved-removal"})
            continue
        for language, texts in current.items():
            if key in texts:
                layer["problems"].append({"key": key, "kind": "removal-not-applied", "language": language})
    layer["status"] = "failed" if layer["problems"] else "passed"
    return layer
