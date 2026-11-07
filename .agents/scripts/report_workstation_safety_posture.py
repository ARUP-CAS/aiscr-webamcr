#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: c35418343fe8896348732bd54f8256de17338f8d 2026-11-07T14:33:16+01:00

"""Read-only workstation safety posture report.

Reads the ``workspace_safety_registry`` port targets through the shared ``redacting_reader`` module; reports
endpoint-managed destinations and instruction-carrier metadata without reading their prose. Each target is classified
against its template as absent, empty (present but carrying none of the governed unit), drifted, or present. Structured
content is present only when applying the target's declared merge is idempotent.

Exists separately from ``setup_workstation_assistant_safety.py`` so posture inspection never invokes the mutating port.

With ``--verbose``, each structured target's effective governed lists show the declared merge of the current target
content with its template, so a session can evaluate the merged result without invoking the port. The deny-entry
carriage is stateless: it pairs the deny entries the current template carries with the entries the delivered config
carries, and the surplus — delivered entries the template does not carry — is what a prune would report. No
machine-local deny-entry record is consulted.

Contract: agent/workspace-safety-config
Class: script
Stable id: report.workstation-safety-posture
Exit codes: 0 report printed; 2 the report cannot be built
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:  # pragma: no cover -- direct script startup already supplies this path
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib import repo_layout  # noqa: E402
from lib.log_utils import log_error, log_info  # noqa: E402
from lib.redacting_reader import (  # noqa: E402
    instruction_carrier_metadata,
    read_json_redacted,
    read_toml_text_redacted,
    redact_mapping,
)
from lib.vendor_matrix_registry import _strip_jsonc_comments  # noqa: E402
from lib.workspace_safety_registry import (  # noqa: E402
    ENDPOINT_MANAGED_DESTINATIONS,
    TEXT_REGION_BEGIN,
    WORKSPACE_SAFETY_PORT_TARGETS,
    extract_text_region,
    governed_unit_keys,
    load_manifest,
    load_template_payload,
    manifest_path,
    merge_target_payload,
    resolve_governed_unit,
)


def get_home(target_dir: Path | None) -> Path:
    """Return the workstation home directory."""
    if target_dir is not None:
        return Path(target_dir)
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME") or "."
    return Path(home)


def read_jsonc_redacted(path: Path) -> tuple[Any, list[str]]:
    """Read a JSONC file as structured redacted content."""
    text = path.read_text(encoding="utf-8")
    data = json.loads(_strip_jsonc_comments(text))
    return redact_mapping(data)


def read_target_redacted(path: Path, merge_kind: str) -> dict[str, Any]:
    """Read one target through the redacting reader; never write."""
    if not path.is_file():
        return {"present": False, "content": None, "redacted_keys": []}
    if merge_kind == "codex_toml":
        text, redacted = read_toml_text_redacted(path)
        return {"present": True, "format": "toml", "content": text, "redacted_keys": redacted}
    if merge_kind == "kilo_user_config_jsonc":
        content, redacted = read_jsonc_redacted(path)
        return {"present": True, "format": "json", "content": content, "redacted_keys": redacted}
    if merge_kind == "codex_user_rules_text":
        # The rules file is command-pattern text with no credentials; only its
        # state is reported, so the content is not carried into the report.
        return {"present": True, "format": "text", "content": None, "redacted_keys": []}
    content, redacted = read_json_redacted(path)
    return {"present": True, "format": "json", "content": content, "redacted_keys": redacted}


def _classify_target(  # pylint: disable=too-many-return-statements,too-many-branches
    target, path: Path, templates: Path
) -> tuple[str, str | None]:
    """Classify one target against its template: absent, empty, drifted, present, or unknown.

    Absent: no file. Empty: the file exists but carries none of the governed unit — a one-byte ``default.rules`` is that
    state's subject, not a delivered control and not a missing file either. Drifted: the managed text region differs, or
    the structured target is not idempotent under its declared merge. Present: the region matches or the declared
    structured merge is idempotent. Unknown: classification cannot safely be evaluated.
    """
    if not path.is_file():
        return "absent", None
    try:
        payload = load_template_payload(templates, target)
    except (OSError, ValueError) as exc:
        return "unknown", f"template unreadable: {exc}"
    if target.governed_unit == "text-region":
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return "unknown", f"target unreadable: {exc}"
        if TEXT_REGION_BEGIN not in text:
            return "empty", None
        try:
            same = extract_text_region(text) == extract_text_region(payload)
        except ValueError:
            return "drifted", "managed region markers are unbalanced"
        return ("present", None) if same else ("drifted", "managed region differs from the template")
    try:
        if target.merge_kind == "codex_toml":
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        else:
            data = json.loads(_strip_jsonc_comments(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return "unknown", f"target unparseable: {exc}"
    if not isinstance(payload, dict) or not isinstance(data, dict):
        return "unknown", "structured target and template must both be objects"
    try:
        governed = set(governed_unit_keys(resolve_governed_unit(payload, target)))
    except ValueError as exc:
        return "unknown", f"governed unit cannot be resolved: {exc}"
    carried = {str(key) for key in data}
    if governed.isdisjoint(carried):
        return "empty", None
    try:
        merged = merge_target_payload(data, payload, target)
    except ValueError as exc:
        return "unknown", f"declared merge cannot be evaluated: {exc}"
    if merged == data:
        return "present", None
    return "drifted", "governed content differs from the declared merge result"


def _kilo_permission_lists(permission: dict[str, Any]) -> dict[str, list[str]]:
    """Bucket Kilo's governed permission block by decision value.

    The block is a decision map rather than two lists, so its keys are bucketed by decision value and section-prefixed
    where they come from a nested map.
    """
    lists: dict[str, list[str]] = {"allow": [], "deny": [], "ask": []}
    for key, value in permission.items():
        if isinstance(value, dict):
            for sub_key, decision in value.items():
                bucket = lists.get(str(decision))
                if bucket is not None:
                    bucket.append(f"{key}:{sub_key}")
        else:
            bucket = lists.get(str(value))
            if bucket is not None:
                bucket.append(key)
    return {name: values for name, values in lists.items() if values}


def _flat_permission_lists(permissions: dict[str, Any]) -> dict[str, list[str]] | None:
    """Extract the flat deny and allow lists a Claude or Cursor merge governs."""
    result = {
        name: [str(v) for v in permissions.get(name) or [] if isinstance(v, str)]
        for name in ("deny", "allow")
        if isinstance(permissions.get(name), list)
    }
    return result or None


def _effective_governed_lists(
    target,
    content: Any,
    templates: Path,
) -> dict[str, list[str]] | None:
    """Extract the effective governed allow and deny lists from the declared merge.

    The merge of the current target content (already read redacted) with the template is what an apply would leave in
    place, so the lists let a session evaluate the merged result without invoking the port. ``None`` means the target
    carries no governed permission surface or the merge cannot be evaluated, so the report stays silent rather than
    guessing.
    """
    if target.merge_kind not in ("claude_snippet_json", "cursor_cli_config_json", "kilo_user_config_jsonc"):
        return None
    try:
        payload = load_template_payload(templates, target)
        merged = merge_target_payload(content if isinstance(content, dict) else {}, payload, target)
    except (OSError, ValueError):
        return None
    if not isinstance(merged, dict):
        return None
    if target.merge_kind == "kilo_user_config_jsonc":
        permission = merged.get("permission")
        return _kilo_permission_lists(permission) if isinstance(permission, dict) else None
    permissions = merged.get("permissions")
    return _flat_permission_lists(permissions) if isinstance(permissions, dict) else None


def _permissions_deny_entries(payload: Any) -> list[str]:
    """Return the string deny entries of a payload's flat permissions block."""
    if not isinstance(payload, dict):
        return []
    permissions = payload.get("permissions")
    if not isinstance(permissions, dict):
        return []
    return [str(v) for v in permissions.get("deny") or [] if isinstance(v, str)]


def _deny_carriage(
    target,
    content: Any,
    templates: Path,
) -> dict[str, Any] | None:
    """Assemble the deny-entry carriage of one target for the verbose report.

    Stateless: the carriage pairs the deny entries the current template carries with the entries the delivered config
    carries; the surplus — delivered entries the template does not carry — is what a prune would report for operator
    review, and it may hold operator-authored entries alongside retired contributions. ``None`` means the carriage
    cannot be evaluated (a target without a union-merged deny list, or the template unavailable), so the report stays
    silent rather than guessing.
    """
    if target.merge_kind not in ("claude_snippet_json", "cursor_cli_config_json"):
        return None
    try:
        payload = load_template_payload(templates, target)
    except (OSError, ValueError):
        return None
    carried = _permissions_deny_entries(payload)
    delivered = _permissions_deny_entries(content)
    return {
        "template_carried": carried,
        "delivered": delivered,
        "surplus_pending_prune": sorted(set(delivered) - set(carried)),
    }


def _verbose_sections(
    targets: dict[str, Any],
    templates: Path,
) -> dict[str, Any]:
    """Assemble the verbose-only report sections; the default shape stays untouched."""
    effective: dict[str, dict[str, list[str]]] = {}
    by_id = {t.target_id: t for t in WORKSPACE_SAFETY_PORT_TARGETS}
    for target_id, entry in targets.items():
        target = by_id.get(target_id)
        if target is None:
            continue
        lists = _effective_governed_lists(target, entry.get("content"), templates)
        if lists is not None:
            effective[target_id] = lists
    carriages: dict[str, Any] = {}
    for target in WORKSPACE_SAFETY_PORT_TARGETS:
        entry = targets.get(target.target_id)
        carriage = _deny_carriage(target, entry.get("content") if isinstance(entry, dict) else None, templates)
        if carriage is not None:
            carriages[target.target_id] = carriage
    sections: dict[str, Any] = {"verbose_deny_carriage": carriages}
    if effective:
        sections["verbose_effective_lists"] = effective
    return sections


def build_report(home: Path, verbose: bool = False) -> dict[str, Any]:
    """Assemble the full read-only posture report for *home*."""
    templates = repo_layout.repo_root() / repo_layout.WORKSTATION_SAFETY_TEMPLATES_DIR
    targets: dict[str, Any] = {}
    for target in WORKSPACE_SAFETY_PORT_TARGETS:
        path = home.joinpath(*target.relative_parts)
        entry = read_target_redacted(path, target.merge_kind)
        entry["path"] = str(path)
        state, note = _classify_target(target, path, templates)
        entry["state"] = state
        if note:
            entry["state_note"] = note
        targets[target.target_id] = entry

    manifest_file = manifest_path(home)
    manifest = load_manifest(manifest_file)
    endpoint_managed = []
    for dest in ENDPOINT_MANAGED_DESTINATIONS:
        resolved = home.joinpath(*dest.relative_parts)
        endpoint_managed.append(
            {
                "product": dest.product,
                "path": str(resolved),
                "present": resolved.is_file(),
                "note": dest.note,
            }
        )

    report = {
        "home": str(home),
        "targets": targets,
        "contribution_manifest": {
            "path": str(manifest_file),
            "present": manifest is not None,
            "content": manifest,
        },
        "endpoint_managed_destinations": endpoint_managed,
        "instruction_carriers": instruction_carrier_metadata(home),
    }
    if verbose:
        report.update(_verbose_sections(targets, templates))
    return report


def _render_carriage_lines(carriage: dict[str, Any]) -> list[str]:
    """Render the deny-entry carriage section body."""
    lines: list[str] = []
    printed = False
    for target_id, target_carriage in carriage.items():
        carried = target_carriage["template_carried"]
        delivered = target_carriage["delivered"]
        surplus = target_carriage["surplus_pending_prune"]
        if not carried and not delivered:
            continue
        printed = True
        lines.append(
            f"    {target_id}: template {len(carried)}, delivered {len(delivered)}, "
            f"surplus {len(surplus)} (pending prune review — may be operator-authored)"
        )
        lines.extend(f"      surplus: {entry}" for entry in surplus)
    if not printed:
        lines.append("    no governed deny entries carried or delivered")
    return lines


def _render_verbose_sections(report: dict[str, Any]) -> list[str]:
    """Render the verbose-only sections; the default report renders nothing here."""
    lines: list[str] = []
    effective = report.get("verbose_effective_lists")
    if effective is not None:
        lines.append("  effective governed lists (declared merge of current target and template):")
        for target_id, lists in effective.items():
            allow = lists.get("allow") or []
            deny = lists.get("deny") or []
            ask = lists.get("ask") or []
            ask_note = f", ask {len(ask)}" if ask else ""
            lines.append(f"    {target_id}: allow {len(allow)}, deny {len(deny)}{ask_note}")
            for name, values in (("deny", deny), ("allow", allow), ("ask", ask)):
                lines.extend(f"      {name}: {value}" for value in values)
    carriage = report.get("verbose_deny_carriage")
    if carriage is not None:
        lines.append("  deny-entry carriage (template vs delivered):")
        lines.extend(_render_carriage_lines(carriage))
    return lines


def format_report_text(report: dict[str, Any]) -> str:
    """Render a human-readable report."""
    lines = [f"workstation safety posture (read-only) for {report['home']}"]
    for target_id, entry in report["targets"].items():
        note = f"; {entry['state_note']}" if entry.get("state_note") else ""
        if not entry.get("present"):
            lines.append(f"  {target_id}: absent ({entry['path']})")
            continue
        redacted = entry.get("redacted_keys") or []
        redacted_note = f", redacted keys: {', '.join(redacted)}" if redacted else ""
        lines.append(f"  {target_id}: {entry.get('state', 'unknown')} ({entry['path']}{redacted_note}{note})")
    manifest = report["contribution_manifest"]
    if manifest["present"]:
        lines.append(f"  contribution manifest: present ({manifest['path']})")
    else:
        lines.append(f"  contribution manifest: absent ({manifest['path']})")
    for dest in report["endpoint_managed_destinations"]:
        state = "present" if dest["present"] else "absent"
        lines.append(f"  endpoint-managed {dest['product']}: {state} ({dest['path']})")
    carriers = [c for c in report["instruction_carriers"] if c.get("present")]
    lines.append(f"  instruction carriers present: {len(carriers)}")
    lines.extend(_render_verbose_sections(report))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Parse CLI and print the read-only posture report."""
    parser = argparse.ArgumentParser(
        description="Report workstation safety targets with redaction; writes nothing.",
    )
    parser.add_argument(
        "--target-dir",
        metavar="PATH",
        default=None,
        help="Workstation home directory to inspect (default: user home).",
    )
    parser.add_argument(
        "--output",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Add the effective governed allow and deny lists per target (the declared merge "
            "of current content and template) and the stateless deny-entry carriage: what "
            "the template carries, what the delivered config carries, and the surplus a "
            "prune would report for operator review."
        ),
    )
    args = parser.parse_args(argv)
    home = get_home(args.target_dir)
    try:
        report = build_report(home, verbose=args.verbose)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        log_error(str(exc))
        return 2
    if args.output == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_report_text(report))
    log_info("read-only report complete; no files were written")
    return 0


if __name__ == "__main__":  # pragma: no cover -- exercised through main(argv)
    sys.exit(main())
