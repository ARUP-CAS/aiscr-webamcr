# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: c35418343fe8896348732bd54f8256de17338f8d 2026-11-07T14:33:16+01:00

"""Copy user-level workspace-safety config from repo templates to the current user's home.

Merges evidence-backed safety templates into user-level assistant configs under the selected home directory, using
``workspace_safety_registry`` as the single target list (keeps bootstrap doctor checks aligned). The governed unit each
target owns — top-level keys, a nested block, or a delimited text region — comes from its registry declaration, and the
dispatch in this script reads those declared fields, never the target's identity. The Cursor and Gemini targets were
re-admitted on documented, probe-verified permission surfaces.

The Codex rules target (``~/.codex/rules/default.rules``) is a text region: the merge replaces the delimited managed
region wholesale and preserves every byte outside it, and the template is validated with
``codex execpolicy check --rules`` — the runtime's own parser — before any write. A skipped target is neither ported nor
validated, so a machine without the codex CLI can port the structured targets without shipping the rules template
unvalidated.

Read-path discipline: the merge-internal reads load real values because their content never reaches an agent context and
the port writes those values back unchanged; every read whose content can surface to an operator or agent routes through
the shared ``redacting_reader`` module instead.

Platform scoping: the Claude sandbox keys are correct only where a sandbox runs (macOS/Linux/WSL2), so on native Windows
the port applies the snippet without the sandbox block. The credential and filesystem lists inside the block bind
wherever the sandbox runs and are inert elsewhere; that residual is recorded in the agent safety control registry.

Codex uses the current top-level ``sandbox_mode`` shape. An existing legacy nested ``[sandbox].mode`` is migrated to
``sandbox_mode`` without being treated as canonical output; an existing ``sandbox_mode`` or ``[windows].sandbox`` is
preserved (the merge never silently switches the Windows elevated/unelevated sandbox). The configuration-family decision
retains legacy ``sandbox_mode``: the beta permission profiles do not compose with it, and the invocation override caps
either family, so the documented mechanism in force is retained with its residual recorded. When a target Codex config
selects the native Windows ``elevated`` sandbox, ``--dry-run`` and an approved merge print an advisory about the
upstream TEMP-profile side effect and the WSL2 / ``unelevated`` mitigations without changing the setting. ``--list``
does not read target config and does not emit that advisory.

Templates are validated (JSON Schema + TOML structure) before any write. A non-dry-run invocation warns on stderr,
naming the user-profile files it is about to modify, so a write outside the repository is never silent; the script
cannot observe the workflow's explicit confirmation and therefore warns rather than blocking. Use --dry-run to preview.
Both ``--dry-run`` and an approved merge print a per-target merge report: what the template governs, what the port adds
or changes, what the merge supersedes, and which existing config keys are disjoint (preserved but not governed) —
identical output in both modes so a dry run predicts the apply exactly and a later cleanup can target the port's own
contributions. A successful apply records each target's governed unit in
``~/.aiscr/workspace-safety-port-manifest.json``, and ``--prune`` retires recorded governed keys the current templates
no longer govern. Deny-entry pruning is stateless and reporting-based: a union-merged deny list keeps entries the merge
stops carrying, so ``--prune`` reports every delivered deny entry the current templates no longer carry — retired
contributions and operator-authored entries look the same without a machine-local record, which is why none is kept —
and removes the reported entries only on a run the operator has reviewed through ``--prune --dry-run``. Read-only
inspection without invoking the port uses ``report_workstation_safety_posture.py``. Run from repo venv when in
aiscr-management (see .agents/scripts/README.md). Missing ``jsonschema`` / ``tomli_w`` are installed automatically from
pinned lines in ``requirements-ci.txt`` when needed (see requirements_subset_install.py).

Contract: agent/workspace-safety-config
Class: script
Exit codes: 0 success; 1 validation, preflight, port, or prune error; 2 templates or schemas dir missing
"""

# pylint: disable=too-many-lines

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:  # pragma: no cover -- direct script startup already supplies this path
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib import repo_layout  # noqa: E402
from lib import workspace_safety_registry as safety_registry  # noqa: E402
from lib.log_utils import log_error, log_info, log_warn  # noqa: E402
from lib.proc_utils import run_diagnostic  # noqa: E402
from lib.workspace_safety_registry import (  # noqa: E402
    TEXT_REGION_BEGIN,
    WORKSPACE_SAFETY_PORT_TARGETS,
    WorkspaceSafetyPortTarget,
    drop_retired_governed_keys,
    empty_manifest,
    extract_text_region,
    load_manifest,
    load_template_payload,
    manifest_path,
    normalize_manifest,
    prune_top_level_keys,
    record_target_contribution,
    remove_text_region,
    resolve_governed_unit,
    retired_governed_keys,
    save_manifest,
    template_revision_file,
)


def get_script_root() -> Path:
    """Return the directory containing this script."""
    if "__file__" in globals():
        return Path(__file__).resolve().parent
    return Path.cwd()


def get_repo_root() -> Path:
    """Resolve repo root from script location (.agents/scripts/ -> repo root)."""
    return get_script_root().parent.parent


def _ensure_port_script_dependencies() -> None:
    """Install jsonschema/tomli-w from requirements-ci.txt before importing them (current interpreter)."""
    # pylint: disable-next=import-outside-toplevel
    from lib.requirements_subset_install import ensure_imports_from_requirements

    ensure_imports_from_requirements(
        get_repo_root() / "requirements-ci.txt",
        (("jsonschema", "jsonschema"), ("tomli-w", "tomli_w")),
    )


_ensure_port_script_dependencies()

import jsonschema  # noqa: E402  # pylint: disable=import-error
import tomli_w  # noqa: E402  # pylint: disable=import-error


def get_templates_dir(repo_root: Path) -> Path:
    """Return path to workstation safety templates (under canonical_configs/templates)."""
    return repo_root / repo_layout.WORKSTATION_SAFETY_TEMPLATES_DIR


def get_schemas_dir(templates: Path) -> Path:
    """Return path to JSON Schema files."""
    return templates / "schemas"


def get_home(target_dir: Path | None) -> Path:
    """Return target directory or user home (Windows + Unix)."""
    if target_dir is not None:
        return Path(target_dir)
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME") or "."
    return Path(home)


def load_json_file(path: Path) -> Any:
    """Load JSON from path."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(path: Path) -> Dict[str, Any]:
    """Load a JSON Schema file."""
    return load_json_file(path)


def validate_json_instance(instance: Any, schema: Dict[str, Any], *, label: str) -> None:
    """Validate instance against schema; raise ValueError on failure."""
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as exc:
        raise ValueError(f"{label}: {exc.message}") from exc


def validate_codex_data(data: dict, *, label: str = "codex config") -> None:
    """Assert required Codex user config keys: approval_policy and top-level sandbox_mode.

    The canonical shape is top-level ``sandbox_mode``. A legacy nested ``[sandbox].mode`` is accepted only as migratable
    input (handled by ``merge_codex_dict``), never as valid canonical output.
    """
    if "approval_policy" not in data:
        raise ValueError(f"{label}: missing approval_policy")
    if "sandbox_mode" not in data:
        raise ValueError(f"{label}: missing top-level sandbox_mode (legacy [sandbox].mode is migrated, not canonical)")


def validate_codex_template_toml(path: Path) -> None:
    """Parse Codex TOML template and assert required keys/sections."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    validate_codex_data(data, label="codex_user_config.toml")


def _codex_execpolicy_argv(rules_path: Path) -> list[str]:
    """Return a launchable ``codex execpolicy check`` argument vector.

    ``shutil.which`` resolves npm-style ``.cmd``/``.bat`` shims, which ``CreateProcess`` cannot execute directly on
    Windows, so those run through ``cmd /c``; a bare ``codex`` is kept for PATH resolution everywhere else.
    """
    resolved = shutil.which("codex")
    argv = ["execpolicy", "check", "--rules", str(rules_path), "git", "status"]
    if resolved and resolved.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", resolved, *argv]
    return [resolved or "codex", *argv]


def validate_codex_rules_template(path: Path) -> None:
    """Parse an execpolicy rules template with the runtime's own parser; raise ValueError on rejection.

    ``codex execpolicy check --rules <path> <probe>`` resolves the same syntax the consuming runtime resolves, so a
    template the parser rejects is a template the runtime would decline to load — a floor in place and enforcing
    nothing. A benign probe command is evaluated only to force the parse; the verdict is not consulted. A missing codex
    binary is a validation failure (fail-closed), not a skip: the rules template has no JSON Schema and ships no other
    way.
    """
    try:
        proc = run_diagnostic(
            _codex_execpolicy_argv(path),
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"{path.name}: codex execpolicy unavailable to validate the rules template: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        first = detail[0] if detail else f"exit code {proc.returncode}"
        raise ValueError(f"{path.name}: codex execpolicy rejected the rules template: {first}")


def validate_all_templates(templates: Path, schemas: Path, *, skip: set[str] = frozenset()) -> str | None:
    """Validate the registry's templates (JSON Schema + TOML structure + execpolicy); return error or None.

    Targets named in *skip* are not being ported by this run, so their templates are not validated either: a skipped
    target writes nothing, and a machine without the codex CLI can still port the structured targets by skipping the
    rules target rather than shipping it unvalidated.
    """
    try:
        for target in WORKSPACE_SAFETY_PORT_TARGETS:
            if target.target_id in skip:
                continue
            if target.merge_kind == "codex_toml":
                validate_codex_template_toml(templates / target.template_filename)
            elif target.merge_kind == "codex_user_rules_text":
                validate_codex_rules_template(templates / target.template_filename)
            elif target.schema_filename:
                validate_json_instance(
                    load_json_file(templates / target.template_filename),
                    load_schema(schemas / target.schema_filename),
                    label=target.template_filename,
                )
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        return str(exc)
    return None


def codex_windows_sandbox_diagnostic(existing: Dict[str, Any]) -> str | None:
    r"""Return an advisory when the Codex config selects the native Windows elevated sandbox.

    The elevated Windows sandbox can leak ``C:\\Users\\TEMP*`` profiles (upstream behavior, no repository-level fix).
    This is advisory only and never changes the setting.
    """
    windows = existing.get("windows")
    if not isinstance(windows, dict):
        return None
    if windows.get("sandbox") != "elevated":
        return None
    return (
        'Codex [windows].sandbox = "elevated": this native Windows sandbox can leak '
        "C:\\Users\\TEMP* profiles (upstream limitation; no repository setting fixes it). "
        'Prefer WSL2 isolation where available; the native "unelevated" sandbox is a weaker '
        "fallback. Removing the Microsoft Store PowerShell (install pwsh via scoop) makes PATH "
        "deterministic. This workflow does NOT change the Windows sandbox mode."
    )


_MISSING = object()
_MAX_DETAIL = 6


def _stable_repr(value: Any) -> str:
    """Stable single-line representation for diff reporting (never raises)."""
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except (TypeError, ValueError):  # pragma: no cover -- defensive: default=str covers it
        return repr(value)


def _short(text: str, limit: int = 60) -> str:
    """Truncate a detail string for one report line."""
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _fmt_path(path: list) -> str:
    """Render a key path ('.'-joined); list indexes collapse to the list key."""
    return ".".join(str(part) for part in path) or "(root)"


def _collect_diff(existing: Any, merged: Any, path: list, diff: Dict[str, list]) -> None:
    """Categorize leaf differences between existing and merged at *path*.

    Dicts recurse per key; lists compare as multisets of stable reprs (union merges reorder, so order is noise);
    everything else is a leaf. Keys present only in existing are *superseded* (dropped by the merge), only in merged are
    *added*, present in both with different values are *changed*.
    """
    if isinstance(existing, dict) and isinstance(merged, dict):
        for key in sorted(set(existing) | set(merged), key=str):
            _collect_diff(existing.get(key, _MISSING), merged.get(key, _MISSING), path + [key], diff)
        return
    if isinstance(existing, list) and isinstance(merged, list):
        old_elems = sorted(_stable_repr(e) for e in existing)
        new_elems = sorted(_stable_repr(e) for e in merged)
        if old_elems != new_elems:
            added = [e for e in new_elems if old_elems.count(e) < new_elems.count(e)]
            dropped = [e for e in old_elems if new_elems.count(e) < old_elems.count(e)]
            if added:
                diff["added"].append((_fmt_path(path), len(added)))
            if dropped:
                diff["superseded"].append((_fmt_path(path), len(dropped)))
        return
    if existing is _MISSING:
        diff["added"].append((_fmt_path(path), _short(_stable_repr(merged))))
    elif merged is _MISSING:
        diff["superseded"].append((_fmt_path(path), _short(_stable_repr(existing))))
    elif existing != merged:
        diff["changed"].append((_fmt_path(path), _short(_stable_repr(existing)), _short(_stable_repr(merged))))


def _collect_disjoint(existing: Any, merged: Any, template: Any, path: list, out: list) -> None:
    """Collect key paths present in existing, surviving in merged, and not governed by the template.

    A governed key (present in the template) recurses so nested user keys inside a governed section are still found; a
    non-governed surviving key is reported at its own level, not per leaf, so the disjoint line stays a key list.
    """
    if not isinstance(existing, dict):
        return
    for key in existing:
        governed = isinstance(template, dict) and key in template
        survives = isinstance(merged, dict) and key in merged
        if governed:
            _collect_disjoint(
                existing[key],
                merged.get(key) if isinstance(merged, dict) else _MISSING,
                template[key],
                path + [key],
                out,
            )
        elif survives:
            out.append(_fmt_path(path + [key]))


def _join_detail(items: list) -> str:
    """Render capped detail items for one report line."""
    shown = ", ".join(str(i) for i in items[:_MAX_DETAIL])
    extra = len(items) - _MAX_DETAIL
    return shown + (f" (+{extra} more)" if extra > 0 else "")


def merge_report_lines(existing: Dict[str, Any], merged: Dict[str, Any], template: Dict[str, Any]) -> list:
    """Build the per-target merge report: governed, added, changed, superseded, disjoint.

    The report mirrors the merge functions' real semantics rather than a generic guess: the wholesale-replaced Kilo
    permission block surfaces dropped keys as *superseded*, union-merged deny lists surface their contributed elements
    as *added*, and everything the template does not govern survives as *disjoint*.
    """
    diff: Dict[str, list] = {"added": [], "changed": [], "superseded": []}
    _collect_diff(existing, merged, [], diff)
    disjoint: list = []
    _collect_disjoint(existing, merged, template, [], disjoint)

    governed = ", ".join(str(k) for k in template) or "(nothing)"
    lines = [f"  governed by template: {governed}"]
    if diff["added"]:
        lines.append(
            f"  added: {_join_detail([f'{p} +{n}' if isinstance(n, int) else f'{p} = {n}' for p, n in diff['added']])}"
        )
    if diff["changed"]:
        lines.append(f"  changed: {_join_detail([f'{p}: {old} -> {new}' for p, old, new in diff['changed']])}")
    if diff["superseded"]:
        dropped = [f"{p} x{n}" if isinstance(n, int) else p for p, n in diff["superseded"]]
        lines.append(f"  superseded (dropped by the merge): {_join_detail(dropped)}")
    if disjoint:
        lines.append(f"  disjoint (in config, preserved, not governed): {_join_detail(disjoint)}")
    if not (diff["added"] or diff["changed"] or diff["superseded"]):
        lines.append("  no changes: the config already carries everything the template governs")
    return lines


def text_merge_report_lines(existing: str, merged: str, template: str) -> list:
    """Build the merge report for a text-region target: the region, not keys.

    The governed unit is a delimited region, so the report states what happened to it and that everything outside
    survived, rather than faking a key diff.
    """
    region = extract_text_region(template)
    rule_count = region.count("prefix_rule(")
    lines = [f"  governed by template: the delimited managed region ({rule_count} prefix_rule entries)"]
    if TEXT_REGION_BEGIN in existing:
        if extract_text_region(existing) == region:
            lines.append("  no changes: the region already carries everything the template governs")
        else:
            lines.append("  changed: the managed region (replaced wholesale)")
    else:
        lines.append("  added: the managed region (the file carried no region; its bytes are preserved)")
    outside = len(merged) - len(region)
    if outside > 0:
        lines.append(f"  disjoint (outside the region, preserved): {outside} characters of operator content")
    return lines


def load_existing_json_object(path: Path, *, label: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Load JSON object from path, or ({}, None) if missing. On invalid JSON, (None, error)."""
    if not path.exists():
        return {}, None
    try:
        data = load_json_file(path)
        if not isinstance(data, dict):
            return None, f"existing {label} must be a JSON object"
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in existing {label}: {exc}"


def load_existing_codex_toml(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Load Codex config TOML or ({}, None) if missing. On parse error, (None, error)."""
    if not path.exists():
        return {}, None
    try:
        return tomllib.loads(path.read_text(encoding="utf-8")), None
    except tomllib.TOMLDecodeError as exc:
        return None, f"invalid TOML in existing codex config.toml: {exc}"


def load_existing_text(path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Load a text target as exact text, or ("", None) if missing. On decode error, (None, error).

    Newline translation is disabled in both directions so operator content is preserved byte-for-byte: a mixed-ending
    file round-trips unchanged instead of being silently normalized by the merge.
    """
    if not path.exists():
        return "", None
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return handle.read(), None
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"cannot read existing {path.name} as UTF-8 text: {exc}"


def _maybe_backup(path: Path, *, backup: bool) -> None:
    if backup and path.exists():
        bak = path.with_suffix(path.suffix + f".bak.{int(time.time())}")
        shutil.copy2(path, bak)


def write_json_file(path: Path, data: Any, *, backup: bool) -> str:
    """Write JSON (object or array) with optional backup."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _maybe_backup(path, backup=backup)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return "merged"


def write_toml_file(path: Path, data: Dict[str, Any], *, backup: bool) -> str:
    """Write TOML with optional backup (comments in original file are not preserved)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _maybe_backup(path, backup=backup)
    path.write_text(tomli_w.dumps(data) + "\n", encoding="utf-8")
    return "merged"


def write_text_file(path: Path, text: str, *, backup: bool) -> str:
    """Write exact text with optional backup and no newline translation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _maybe_backup(path, backup=backup)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return "merged"


def apply_warning(home: Path, *, skip: set[str]) -> str:
    """Return the pre-write warning naming the user-profile files a non-dry-run run will modify.

    The workflow requires list and dry-run review plus explicit user confirmation before any home write
    (``openspec/specs/agent/workspace-safety-config/spec.md``, *Explicit confirmation before external writes*). This
    script cannot observe that confirmation, so it never blocks; it warns, so a write outside the repository is never
    silent.
    """
    targets = [
        str(home.joinpath(*target.relative_parts))
        for target in WORKSPACE_SAFETY_PORT_TARGETS
        if target.target_id not in skip
    ]
    listed = ", ".join(targets) if targets else "no targets (all skipped)"
    return (
        "About to write user-profile assistant configuration outside this repository: "
        f"{listed}. Run with --dry-run first and apply only after explicit user confirmation."
    )


def _skip_target_ids(args: argparse.Namespace) -> set[str]:
    """Return target_id set for targets skipped via their registry-declared skip flags."""
    skip: set[str] = set()
    for target in WORKSPACE_SAFETY_PORT_TARGETS:
        attr = target.skip_flag.lstrip("-").replace("-", "_")
        if getattr(args, attr, False):
            skip.add(target.target_id)
    return skip


def _preflight_existing_targets(home: Path, *, skip: set[str]) -> str | None:
    """Return an error message if an existing target file is invalid, else None."""
    for target in WORKSPACE_SAFETY_PORT_TARGETS:
        if target.target_id in skip:
            continue
        path = home.joinpath(*target.relative_parts)
        if target.merge_kind == "codex_toml":
            _, err = load_existing_codex_toml(path)
        elif target.merge_kind == "codex_user_rules_text":
            _, err = load_existing_text(path)
        else:
            _, err = load_existing_json_object(path, label=path.name)
        if err:
            return err
    return None


def _load_existing_target(
    home: Path, target: WorkspaceSafetyPortTarget
) -> Tuple[Optional[Dict[str, Any] | str], Optional[str]]:
    """Load an existing target config in the shape its merge kind declares."""
    path = home.joinpath(*target.relative_parts)
    if target.merge_kind == "codex_toml":
        return load_existing_codex_toml(path)
    if target.merge_kind == "codex_user_rules_text":
        return load_existing_text(path)
    return load_existing_json_object(path, label=path.name)


# The declared merge_kind — a registry field, not the target's identity — selects
# the merge function that implements the target's declared reconciliation policy.
def port_target(
    home: Path,
    target: WorkspaceSafetyPortTarget,
    templates: Path,
    *,
    dry_run: bool,
    backup: bool,
) -> Tuple[str, str | None, list]:
    """Merge one registry target's template per its declared contract.

    The dispatch reads the target's declared fields only — *merge_kind* selects the loader, merge function, report, and
    writer — never the target's identity. The Codex advisory diagnostic is emitted for the TOML format in both modes,
    before any write. Returns (status, error, report_lines).
    """
    dst = home.joinpath(*target.relative_parts)
    existing, err = _load_existing_target(home, target)
    if err:
        return "error", err, []
    assert existing is not None
    if target.merge_kind == "codex_toml":
        diag = codex_windows_sandbox_diagnostic(existing)
        if diag:
            log_info(f"[advisory] {diag}")
    template_data = load_template_payload(templates, target)
    try:
        merged = safety_registry.merge_target_payload(existing, template_data, target)
        if target.merge_kind == "codex_user_rules_text":
            report = text_merge_report_lines(existing, merged, template_data)
        else:
            report = merge_report_lines(existing, merged, template_data)
    except ValueError as exc:
        return "error", str(exc), []
    if target.merge_kind == "codex_toml":
        try:
            validate_codex_data(merged, label=f"merged {dst.name}")
        except ValueError as exc:
            return "error", str(exc), []
    if dry_run:
        return "would merge", None, report
    if target.merge_kind == "codex_toml":
        write_toml_file(dst, merged, backup=backup)
    elif target.merge_kind == "codex_user_rules_text":
        write_text_file(dst, merged, backup=backup)
    else:
        write_json_file(dst, merged, backup=backup)
    return "merged", None, report


def _record_port_contribution(
    manifest: dict[str, Any],
    *,
    target: WorkspaceSafetyPortTarget,
    templates: Path,
) -> None:
    """Record the governed unit and revision the port just applied for *target*."""
    record_target_contribution(
        manifest,
        target_id=target.target_id,
        relative_parts=target.relative_parts,
        template_filename=target.template_filename,
        template_revision=template_revision_file(templates / target.template_filename),
        governed_unit=resolve_governed_unit(load_template_payload(templates, target), target),
    )


# The union-merged deny lists: the registry's merge unions these paths, so an
# entry survives there after the template withdraws it — the stateless prune's
# only subjects. Replace-governed targets (kilo, the codex rules region) are
# refreshed wholesale by apply and never need a prune.
_UNION_DENY_LIST_PATHS: dict[str, tuple[tuple[str, ...], ...]] = {
    "claude_snippet_json": (("permissions", "deny"),),
    "cursor_cli_config_json": (("permissions", "deny"),),
}


def _dict_at(payload: Any, path: tuple[str, ...]) -> Dict[str, Any] | None:
    """Return the dict holding the final key of *path* in *payload* (None when absent)."""
    node: Any = payload
    for part in path[:-1]:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node if isinstance(node, dict) else None


def _string_list_at(payload: Any, path: tuple[str, ...]) -> list[str]:
    """Return the string entries of the list at *path* in *payload* (empty when absent)."""
    parent = _dict_at(payload, path)
    if parent is None or not isinstance(parent.get(path[-1]), list):
        return []
    return [entry for entry in parent[path[-1]] if isinstance(entry, str)]


def delivered_deny_surplus(
    existing: Dict[str, Any], template_payload: Dict[str, Any], target: WorkspaceSafetyPortTarget
) -> list[str]:
    """Return delivered deny entries the current template does not carry.

    Stateless: the current templates are the only source of truth, so the difference is computed from the delivered
    state itself and resolves the same on every workstation, with or without a contribution manifest. The surplus cannot
    distinguish a retired contribution from an operator-authored entry — that judgment belongs to the operator reviewing
    the report.
    """
    surplus: list[str] = []
    for path in _UNION_DENY_LIST_PATHS.get(target.merge_kind, ()):
        carried = set(_string_list_at(template_payload, path))
        surplus.extend(entry for entry in _string_list_at(existing, path) if entry not in carried)
    return surplus


def remove_delivered_deny_entries(
    existing: Dict[str, Any], entries: set[str], target: WorkspaceSafetyPortTarget
) -> Dict[str, Any]:
    """Return a copy of *existing* with *entries* removed from the union-merged deny lists."""
    result = copy.deepcopy(existing)
    for path in _UNION_DENY_LIST_PATHS.get(target.merge_kind, ()):
        parent = _dict_at(result, path)
        if parent is not None and isinstance(parent.get(path[-1]), list):
            parent[path[-1]] = [
                entry for entry in parent[path[-1]] if not (isinstance(entry, str) and entry in entries)
            ]
    return result


def prune_warning(home: Path, *, skip: set[str]) -> str:
    """Return the pre-prune warning naming files a non-dry-run run will modify."""
    targets = [
        str(home.joinpath(*target.relative_parts))
        for target in WORKSPACE_SAFETY_PORT_TARGETS
        if target.target_id not in skip
    ]
    listed = ", ".join(targets) if targets else "no targets (all skipped)"
    return (
        "About to remove retired governed keys and reviewed surplus deny entries from "
        f"user-profile assistant configuration: {listed}. The dry-run report is the review "
        "surface — surplus deny entries may be operator-authored — so run with --dry-run "
        "first and prune only after explicit user confirmation."
    )


def run_prune(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    home: Path,
    templates: Path,
    *,
    dry_run: bool,
    backup: bool,
    skip: set[str],
) -> int:
    """Preview or remove retired governed keys and surplus deny entries.

    Governed-key retirement reads the contribution manifest. Deny-entry pruning is stateless and reporting-based: every
    delivered deny entry the current templates no longer carry is reported for operator review — a retired contribution
    and an operator-authored entry look the same — and removed only on a run the operator has reviewed through the
    dry-run preview.
    """
    manifest_file = manifest_path(home)
    manifest = load_manifest(manifest_file)
    if manifest is None:
        log_info(
            f"No contribution manifest at {manifest_file}: governed-key retirement unavailable; "
            "deny-entry pruning is stateless and still runs."
        )
    else:
        manifest = normalize_manifest(manifest)

    if not dry_run:
        log_warn(prune_warning(home, skip=skip))

    any_action = False
    for target in WORKSPACE_SAFETY_PORT_TARGETS:
        if target.target_id in skip:
            log_info(f"{target.target_id}: skipped")
            continue
        entry = (manifest.get("targets") or {}).get(target.target_id) if manifest else None
        if entry is None:
            log_info(f"{target.target_id}: no manifest entry (governed-key retirement unavailable)")
        template_payload = load_template_payload(templates, target)
        retired = retired_governed_keys(entry, template_payload, target) if entry else []
        dst = home.joinpath(*target.relative_parts)
        if target.governed_unit == "text-region":
            if not retired:
                log_info(f"{target.target_id}: no retired or surplus entries")
                continue
            text, err = load_existing_text(dst)
            if err:
                log_error(err)
                return 1
            assert text is not None
            pruned_text = remove_text_region(text)
            log_info(f"{target.target_id}: would remove the managed region")
            any_action = True
            if dry_run:
                continue
            write_text_file(dst, pruned_text, backup=backup)
            drop_retired_governed_keys(entry, set(retired))
            entry["template_revision"] = template_revision_file(templates / target.template_filename)
            continue
        existing, err = _load_existing_target(home, target)
        if err:
            log_error(err)
            return 1
        assert existing is not None
        assert isinstance(existing, dict)
        surplus = delivered_deny_surplus(existing, template_payload, target)
        if not retired and not surplus:
            log_info(f"{target.target_id}: no retired or surplus entries")
            continue
        pruned = prune_top_level_keys(existing, set(retired)) if retired else existing
        if surplus:
            pruned = remove_delivered_deny_entries(pruned, set(surplus), target)
        removed = []
        if retired:
            removed.append(f"retired governed keys: {', '.join(retired)}")
        if surplus:
            removed.append(
                "surplus deny entries not carried by the current templates (review — they may "
                f"be operator-authored): {', '.join(surplus)}"
            )
        log_info(f"{target.target_id}: would remove {'; '.join(removed)}")
        any_action = True
        if dry_run:
            continue
        if target.merge_kind == "codex_toml":
            write_toml_file(dst, pruned, backup=backup)
        else:
            write_json_file(dst, pruned, backup=backup)
        if entry is not None and retired:
            drop_retired_governed_keys(entry, set(retired))
            entry["template_revision"] = template_revision_file(templates / target.template_filename)

    if not dry_run and any_action and manifest is not None:
        save_manifest(manifest_file, manifest)
    if not any_action:
        log_info("nothing to prune")
    return 0


def main(  # pylint: disable=too-many-locals,too-many-statements,too-many-return-statements,too-many-branches
    argv: list[str] | None = None,
) -> int:
    """Parse CLI, validate templates, and merge the registry's targets per their declarations."""
    log_info("Starting workspace safety config port...")
    parser = argparse.ArgumentParser(description="Copy user-level workspace-safety config from repo templates to home.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be copied, no writes.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List template files and destinations.",
    )
    parser.add_argument(
        "--target-dir",
        metavar="PATH",
        default=None,
        help="Override home directory (for testing).",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Before overwriting, copy each existing target to .bak.<timestamp> next to it.",
    )
    for target in WORKSPACE_SAFETY_PORT_TARGETS:
        parser.add_argument(
            target.skip_flag,
            action="store_true",
            help=f"Do not merge {target.template_filename} into {'/'.join(target.relative_parts)}.",
        )
    parser.add_argument(
        "--prune",
        action="store_true",
        help=(
            "Retire recorded governed keys the current templates no longer govern, and remove "
            "delivered deny entries the current templates no longer carry (stateless: review the "
            "--dry-run report first — surplus entries may be operator-authored)."
        ),
    )
    args = parser.parse_args(argv)

    repo_root = get_repo_root()
    templates = get_templates_dir(repo_root)
    schemas = get_schemas_dir(templates)
    if not templates.exists():
        log_error(f"Templates dir not found: {templates}")
        return 2
    if not schemas.exists():
        log_error(f"Schemas dir not found: {schemas}")
        return 2

    home = get_home(args.target_dir)

    if args.list:
        print("Template -> Destination")
        for target in WORKSPACE_SAFETY_PORT_TARGETS:
            print(f"  {templates / target.template_filename} -> merge into {home.joinpath(*target.relative_parts)}")
        return 0

    skip = _skip_target_ids(args)

    err = validate_all_templates(templates, schemas, skip=skip)
    if err:
        log_error(f"Template validation failed: {err}")
        return 1

    if args.prune:
        return run_prune(
            home, templates, dry_run=args.dry_run, backup=bool(args.backup) and not args.dry_run, skip=skip
        )

    pre_err = _preflight_existing_targets(home, skip=skip)
    if pre_err:
        log_error(pre_err)
        return 1

    if not args.dry_run:
        log_warn(apply_warning(home, skip=skip))

    backup = bool(args.backup) and not args.dry_run
    reports: list[tuple[str, list]] = []
    manifest = normalize_manifest(load_manifest(manifest_path(home)) or empty_manifest())
    ported_targets: list[WorkspaceSafetyPortTarget] = []

    for target in WORKSPACE_SAFETY_PORT_TARGETS:
        label = f"{target.target_id} {target.relative_parts[-1]}"
        if target.target_id in skip:
            reports.append((f"{label}: skipped", []))
            continue
        status, err, detail = port_target(home, target, templates, dry_run=args.dry_run, backup=backup)
        if err:
            log_error(err)
            return 1
        reports.append((f"{label}: {status}", detail))
        if not args.dry_run:
            ported_targets.append(target)

    for line, detail in reports:
        log_info(line)
        for detail_line in detail:
            log_info(detail_line)

    if not args.dry_run:
        for target in ported_targets:
            _record_port_contribution(manifest, target=target, templates=templates)
        save_manifest(manifest_path(home), manifest)

    print()
    print("Optional: Cursor Workspace Trust — in Cursor Settings set")
    print('  "security.workspace.trust.enabled": true')
    print("  See CLAUDE.md and AGENTS.md for full workspace-safety setup.")

    return 0


if __name__ == "__main__":  # pragma: no cover -- exercised through main(argv)
    sys.exit(main())
