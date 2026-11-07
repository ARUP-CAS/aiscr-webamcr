# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00

"""Single source of truth for workspace-safety port targets.

Used by ``setup_workstation_assistant_safety.py`` and ``setup_hub_clone.py`` so bootstrap doctor checks and the port
workflow stay aligned.

Cursor and Gemini were re-admitted: the Cursor CLI permissions surface and the Gemini settings-file chain are documented
and probe-verified surfaces that preserve a protected boundary, which is the re-evaluation trigger the workspace-safety
capability requires for a withdrawn template. Each re-admitted template carries its own setting evidence in the
workstation template directory.

The endpoint-managed destination records the guaranteed-layer carrier the port never writes: centrally deployed policy
that a session using a non-default provider endpoint does not receive. The port and doctor report its presence; delivery
is an operator/organization action, not a merge.

Each target declares its **governed unit** — the part of the recipient file the port owns: the top-level keys, a nested
block, or a delimited text region — and its **reconciliation policy** for content the recipient already carries:
``fill-if-absent``, ``overlay``, ``union-lists``, or ``replace-governed-unit``. Documented deviations (a pinned key, a
legacy-shape migration, a platform-conditional omission) are declared alongside as exceptions. The resolver and the port
dispatch on these declarations, never on target identity.

Contract: agent/workspace-safety-config
Class: library
Exit codes: library with no entrypoint
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

MergeKind = Literal[
    "codex_toml",
    "claude_snippet_json",
    "cursor_cli_config_json",
    "gemini_user_settings_json",
    "kilo_user_config_jsonc",
    "codex_user_rules_text",
]

GovernedUnitKind = Literal["top-level-keys", "nested-block", "text-region"]

ReconciliationPolicy = Literal["fill-if-absent", "overlay", "union-lists", "replace-governed-unit"]

# The delimited text region a text-region target governs. The markers are
# Starlark comments, so a rules file carrying them still parses; the region
# between them (markers inclusive) is the unit the port replaces wholesale
# and the byte range whose boundaries the merge must never cross.
TEXT_REGION_BEGIN = "# >>> BEGIN AIS CR WORKSTATION SAFETY MANAGED REGION >>>"
TEXT_REGION_END = "# <<< END AIS CR WORKSTATION SAFETY MANAGED REGION <<<"
TEXT_REGION_KEY = "workstation-safety-managed-region"


@dataclass(frozen=True)
class DeclaredException:
    """One documented deviation from a target's declared reconciliation policy."""

    subject: str  # the key or shape the exception concerns
    behaviour: str  # what the merge does instead of the declared policy


# The declared contract is the dataclass: one field per declared fact.
@dataclass(frozen=True)
class WorkspaceSafetyPortTarget:  # pylint: disable=too-many-instance-attributes
    """One template-backed merge destination under a user home (or --target-dir)."""

    target_id: str
    template_filename: str
    relative_parts: tuple[str, ...]
    skip_flag: str
    merge_kind: MergeKind
    schema_filename: str | None  # JSON Schema under templates/schemas/, when merge_kind uses JSON validation
    governed_unit: GovernedUnitKind
    reconciliation: ReconciliationPolicy
    governed_block_key: str | None = None  # locator for nested-block targets
    exceptions: tuple[DeclaredException, ...] = ()


# Only evidence-backed safety targets remain. Retention is owned by
# openspec/specs/agent/workspace-safety-config/spec.md, requirement
# "Safety templates remain minimal and evidence-backed"; the Cursor and Gemini
# re-admissions are recorded there through the agent-safety floor change's delta.
WORKSPACE_SAFETY_PORT_TARGETS: tuple[WorkspaceSafetyPortTarget, ...] = (
    WorkspaceSafetyPortTarget(
        "codex",
        "codex_user_config.toml",
        (".codex", "config.toml"),
        "--skip-codex",
        "codex_toml",
        None,
        "top-level-keys",
        "fill-if-absent",
        exceptions=(
            DeclaredException(
                "approval_policy",
                "pinned from the template: an existing value is overwritten so re-running the port "
                "repairs configs a retired value broke",
            ),
            DeclaredException(
                "sandbox.mode",
                "a legacy nested [sandbox].mode is migrated to top-level sandbox_mode before the fill",
            ),
            DeclaredException(
                "sandbox",
                "a template [sandbox] table is ignored defensively; only the legacy migration reads [sandbox]",
            ),
        ),
    ),
    WorkspaceSafetyPortTarget(
        "codex_user_rules",
        "codex_user_rules.rules",
        (".codex", "rules", "default.rules"),
        "--skip-codex-user-rules",
        "codex_user_rules_text",
        None,
        "text-region",
        "replace-governed-unit",
    ),
    WorkspaceSafetyPortTarget(
        "claude",
        "claude_safety_snippet.json",
        (".claude", "settings.json"),
        "--skip-claude",
        "claude_snippet_json",
        "claude_safety_snippet.schema.json",
        "top-level-keys",
        "overlay",
        exceptions=(
            DeclaredException(
                "permissions",
                "union-merged: snippet deny entries are unioned ahead of existing entries; "
                "the other permission keys are overlaid",
            ),
            DeclaredException(
                "sandbox.enabled",
                "omitted from the overlay on native Windows together with sandbox.allowUnsandboxedCommands: "
                "the pair enforces nothing there and blanket-refuses the PowerShell tool",
            ),
            DeclaredException(
                "sandbox.allowUnsandboxedCommands",
                "omitted from the overlay on native Windows together with sandbox.enabled",
            ),
        ),
    ),
    WorkspaceSafetyPortTarget(
        "cursor",
        "cursor_cli_config.json",
        (".cursor", "cli-config.json"),
        "--skip-cursor",
        "cursor_cli_config_json",
        "cursor_cli_config.schema.json",
        "top-level-keys",
        "union-lists",
        exceptions=(
            DeclaredException(
                "approvalMode",
                "pinned from the template regardless of the existing value",
            ),
            DeclaredException(
                "permissions",
                "deny entries are unioned; the non-deny permission keys are overlaid rather than unioned",
            ),
        ),
    ),
    WorkspaceSafetyPortTarget(
        "gemini",
        "gemini_user_settings.json",
        (".gemini", "settings.json"),
        "--skip-gemini",
        "gemini_user_settings_json",
        "gemini_user_settings.schema.json",
        "top-level-keys",
        "overlay",
    ),
    WorkspaceSafetyPortTarget(
        "kilo",
        "kilo_user_config.jsonc",
        (".config", "kilo", "kilo.jsonc"),
        "--skip-kilo",
        "kilo_user_config_jsonc",
        "kilo_user_config.schema.json",
        "nested-block",
        "replace-governed-unit",
        "permission",
    ),
)


# A merge kind is an implementation of exactly one governed-unit shape and
# reconciliation policy. Keeping that compatibility contract next to the
# declarations lets validation and runtime dispatch reject a declaration that
# uses individually valid fields in a combination the implementation does not
# actually honour.
MERGE_CONTRACTS: dict[MergeKind, tuple[GovernedUnitKind, ReconciliationPolicy]] = {
    "codex_toml": ("top-level-keys", "fill-if-absent"),
    "codex_user_rules_text": ("text-region", "replace-governed-unit"),
    "claude_snippet_json": ("top-level-keys", "overlay"),
    "cursor_cli_config_json": ("top-level-keys", "union-lists"),
    "gemini_user_settings_json": ("top-level-keys", "overlay"),
    "kilo_user_config_jsonc": ("nested-block", "replace-governed-unit"),
}


def merge_contract_errors(target: WorkspaceSafetyPortTarget) -> list[str]:
    """Return incompatibilities between a target declaration and its merge implementation."""
    expected = MERGE_CONTRACTS.get(target.merge_kind)
    if expected is None:
        return [f"{target.target_id}: unsupported merge_kind {target.merge_kind!r}"]
    expected_unit, expected_reconciliation = expected
    errors: list[str] = []
    if target.governed_unit != expected_unit:
        errors.append(
            f"{target.target_id}: merge_kind {target.merge_kind!r} requires "
            f"governed_unit={expected_unit!r}, not {target.governed_unit!r}"
        )
    if target.reconciliation != expected_reconciliation:
        errors.append(
            f"{target.target_id}: merge_kind {target.merge_kind!r} requires "
            f"reconciliation={expected_reconciliation!r}, not {target.reconciliation!r}"
        )
    return errors


@dataclass(frozen=True)
class EndpointManagedDestination:
    """A guaranteed-layer carrier the port reports on but never writes."""

    product: str
    relative_parts: tuple[str, ...]
    note: str


# The guaranteed layer is endpoint-managed, not merged: a session using a
# non-default provider endpoint does not receive centrally fetched policy, so
# that channel cannot carry the guaranteed set alone. The reference workstation
# shows the distinction concretely (organisation restrictions populated, the
# managed file empty). Deployment through this channel is an organization
# action; the port's contract is to report presence, never to write.
ENDPOINT_MANAGED_DESTINATIONS: tuple[EndpointManagedDestination, ...] = (
    EndpointManagedDestination(
        "claude_code",
        ("..", "..", "ProgramData", "ClaudeCode", "managed-settings.json"),
        "organization-deployed managed settings; not delivered to non-default provider endpoints",
    ),
)


def iter_workspace_safety_target_paths(home: Path) -> list[Path]:
    """Return expected absolute paths for all port targets under *home*."""
    return [home.joinpath(*t.relative_parts) for t in WORKSPACE_SAFETY_PORT_TARGETS]


def iter_endpoint_managed_destination_paths(home: Path) -> list[Path]:
    """Return expected absolute paths for endpoint-managed destinations near *home*."""
    return [home.joinpath(*d.relative_parts) for d in ENDPOINT_MANAGED_DESTINATIONS]


MANIFEST_SCHEMA_VERSION = 2
MANIFEST_RELATIVE_PARTS = (".aiscr", "workspace-safety-port-manifest.json")


def manifest_path(home: Path) -> Path:
    """Return the contribution manifest path under *home*."""
    return home.joinpath(*MANIFEST_RELATIVE_PARTS)


def template_revision_bytes(content: bytes) -> str:
    """Return a stable SHA-256 hex digest for template content."""
    return hashlib.sha256(content).hexdigest()


def template_revision_file(path: Path) -> str:
    """Return the revision digest for a template file."""
    return template_revision_bytes(path.read_bytes())


def text_region_span(text: str) -> tuple[int, int] | None:
    """Return the ``[begin, end)`` span of the managed region in *text*.

    Returns ``None`` when *text* carries no region. A begin marker whose end marker is missing is not "no region": it is
    a region whose boundaries cannot be delimited, so it raises rather than letting a caller treat the whole file as
    operator content (or vice versa). The span owns its line breaks: a newline immediately after the end marker is part
    of the span, so the region occupies whole lines and a merge or prune never leaves a stray blank line or drops the
    file's final newline.
    """
    begin = text.find(TEXT_REGION_BEGIN)
    if begin < 0:
        return None
    end = text.find(TEXT_REGION_END, begin + len(TEXT_REGION_BEGIN))
    if end < 0:
        raise ValueError("text carries the managed-region begin marker without its end marker")
    end += len(TEXT_REGION_END)
    if text[end : end + 2] == "\r\n":
        end += 2
    elif text[end : end + 1] == "\n":
        end += 1
    return begin, end


def extract_text_region(text: str) -> str:
    """Return the managed region (markers inclusive) from *text*."""
    span = text_region_span(text)
    if span is None:
        raise ValueError("text carries no managed region")
    return text[span[0] : span[1]]


def remove_text_region(text: str) -> str:
    """Return *text* with the managed region removed; unchanged when absent."""
    span = text_region_span(text)
    if span is None:
        return text
    return text[: span[0]] + text[span[1] :]


def _union_deny_lists(template_deny: Any, existing_deny: Any) -> list[str]:
    """Return template deny entries first, then unique existing entries."""
    if not isinstance(template_deny, list):
        template_deny = []
    if not isinstance(existing_deny, list):
        existing_deny = []
    seen: set[str] = set()
    merged: list[str] = []
    for entry in template_deny:
        if isinstance(entry, str) and entry not in seen:
            seen.add(entry)
            merged.append(entry)
    for entry in existing_deny:
        if isinstance(entry, str) and entry not in seen:
            seen.add(entry)
            merged.append(entry)
    return merged


def _merge_permissions_block(base: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """Overlay a permissions block while unioning its deny list."""
    merged = dict(base)
    if "deny" in template:
        merged["deny"] = _union_deny_lists(template.get("deny"), base.get("deny"))
    for key, value in template.items():
        if key != "deny":
            merged[key] = value
    return merged


def _migrate_legacy_codex_sandbox(output: dict[str, Any]) -> None:
    """Migrate legacy nested ``[sandbox].mode`` to top-level ``sandbox_mode``."""
    sandbox = output.get("sandbox")
    if not (isinstance(sandbox, dict) and "mode" in sandbox):
        return
    if "sandbox_mode" not in output:
        output["sandbox_mode"] = sandbox["mode"]
    remaining = {key: value for key, value in sandbox.items() if key != "mode"}
    if remaining:
        output["sandbox"] = remaining
    else:
        output.pop("sandbox", None)


def merge_codex_dict(existing: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """Apply the Codex fill policy, including its declared pin and migration exceptions."""
    output = copy.deepcopy(existing)
    _migrate_legacy_codex_sandbox(output)
    for key, value in template.items():
        if key == "sandbox":
            continue
        if key == "approval_policy":
            output[key] = copy.deepcopy(value)
        elif key not in output:
            output[key] = copy.deepcopy(value)
    return output


def merge_claude_settings(
    existing: dict[str, Any],
    template: dict[str, Any],
    *,
    native_windows: bool | None = None,
) -> dict[str, Any]:
    """Apply the Claude overlay policy and its declared permissions/platform exceptions."""
    if native_windows is None:
        native_windows = sys.platform == "win32"
    result = copy.deepcopy(existing)
    if "sandbox" in template:
        overlay = template["sandbox"]
        if isinstance(overlay, dict) and native_windows:
            native_windows_omissions = {"enabled", "allowUnsandboxedCommands"}
            overlay = {key: value for key, value in overlay.items() if key not in native_windows_omissions}
        base = result.get("sandbox")
        if not isinstance(base, dict):
            base = {}
        result["sandbox"] = {**base, **overlay} if isinstance(overlay, dict) else overlay
    if "permissions" not in template:
        return result
    base_permissions = result.get("permissions")
    if not isinstance(base_permissions, dict):
        base_permissions = {}
    template_permissions = template["permissions"]
    result["permissions"] = (
        _merge_permissions_block(base_permissions, template_permissions)
        if isinstance(template_permissions, dict)
        else template_permissions
    )
    return result


def merge_cursor_cli_config(existing: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """Apply the Cursor union-list policy and its pinned approval-mode exception."""
    result = copy.deepcopy(existing)
    if "approvalMode" in template:
        result["approvalMode"] = template["approvalMode"]
    if "permissions" not in template:
        return result
    base_permissions = result.get("permissions")
    if not isinstance(base_permissions, dict):
        base_permissions = {}
    result["permissions"] = _merge_permissions_block(base_permissions, template["permissions"])
    return result


def merge_kilo_user_config(existing: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """Replace Kilo's governed permission block and preserve every other key."""
    result = copy.deepcopy(existing)
    if "permission" in template:
        result["permission"] = copy.deepcopy(template["permission"])
    return result


def merge_gemini_settings(existing: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    """Apply Gemini's one-level overlay while preserving unrelated keys."""
    result = copy.deepcopy(existing)
    for key, value in template.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            merged = dict(result[key])
            merged.update(value)
            result[key] = merged
        else:
            result[key] = copy.deepcopy(value)
    return result


def merge_codex_user_rules_text(existing: str, template: str) -> str:
    """Replace the managed rules region while preserving every byte outside it."""
    region = extract_text_region(template)
    span = text_region_span(existing)
    if span is None:
        if not existing:
            return region
        if not existing.endswith("\n"):
            existing += "\n"
        return existing + region
    return existing[: span[0]] + region + existing[span[1] :]


_MERGE_FUNCTIONS = {
    "codex_toml": merge_codex_dict,
    "codex_user_rules_text": merge_codex_user_rules_text,
    "claude_snippet_json": merge_claude_settings,
    "cursor_cli_config_json": merge_cursor_cli_config,
    "gemini_user_settings_json": merge_gemini_settings,
    "kilo_user_config_jsonc": merge_kilo_user_config,
}


def merge_target_payload(
    existing: dict[str, Any] | str,
    template: dict[str, Any] | str,
    target: WorkspaceSafetyPortTarget,
) -> dict[str, Any] | str:
    """Merge one payload through the implementation compatible with its declaration."""
    errors = merge_contract_errors(target)
    if errors:
        raise ValueError("; ".join(errors))
    if target.governed_unit == "text-region":
        if not isinstance(existing, str) or not isinstance(template, str):
            raise ValueError(f"{target.target_id}: text-region merge requires text payloads")
    elif not isinstance(existing, dict) or not isinstance(template, dict):
        raise ValueError(f"{target.target_id}: structured merge requires object payloads")
    return _MERGE_FUNCTIONS[target.merge_kind](existing, template)


def resolve_governed_unit(template: dict[str, Any] | str, target: WorkspaceSafetyPortTarget) -> dict[str, Any]:
    """Resolve the governed-unit record for *target* from its declaration.

    Structured templates resolve to the unit kind plus the key list the current template governs; a nested block
    resolves to its block key, recorded only while the template carries the block; a text template resolves to the
    delimited region, recorded only while the template carries it. Selecting behaviour by target identity is what this
    resolver exists to replace: the declaration is the only input.
    """
    if target.governed_unit == "text-region":
        if not isinstance(template, str):
            raise ValueError(f"{target.target_id}: text-region templates must be loaded as text")
        keys = [TEXT_REGION_KEY] if text_region_span(template) is not None else []
        return {"kind": "text-region", "keys": keys}
    if not isinstance(template, dict):
        raise ValueError(f"{target.target_id}: {target.governed_unit!r} templates must be loaded as structured data")
    if target.governed_unit == "top-level-keys":
        return {"kind": "top-level-keys", "keys": sorted(str(k) for k in template)}
    if target.governed_unit == "nested-block":
        if not target.governed_block_key:
            raise ValueError(f"{target.target_id}: nested-block target declares no governed_block_key")
        keys = [target.governed_block_key] if target.governed_block_key in template else []
        return {"kind": "nested-block", "keys": keys}
    raise ValueError(f"{target.target_id}: {target.governed_unit!r} templates are not dict-shaped")


def governed_unit_keys(unit: dict[str, Any] | None) -> list[str]:
    """Return the sorted key list a structured governed-unit record carries."""
    return sorted(str(k) for k in ((unit or {}).get("keys")) or [])


def empty_manifest() -> dict[str, Any]:
    """Return a fresh manifest object."""
    return {"schema_version": MANIFEST_SCHEMA_VERSION, "targets": {}}


def load_manifest(path: Path) -> dict[str, Any] | None:
    """Load the manifest or return None when absent."""
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: manifest must be a JSON object")
    return data


def save_manifest(path: Path, data: dict[str, Any]) -> None:
    """Write the manifest, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def normalize_manifest(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a prior-version manifest to the current schema, in place.

    A schema-1 entry's ``contributed_keys`` become the key list of a governed-unit record whose kind comes from the
    target's declaration, so a manifest written before the governed-unit contract is read without losing the
    contribution history it records. Entries for targets no longer registered are left untouched, exactly as the port
    ignores them.
    """
    version = data.get("schema_version")
    if version == MANIFEST_SCHEMA_VERSION:
        return data
    if version is not None and version != 1:
        raise ValueError(f"unsupported manifest schema_version: {version!r}")
    by_id = {t.target_id: t for t in WORKSPACE_SAFETY_PORT_TARGETS}
    for target_id, entry in (data.get("targets") or {}).items():
        target = by_id.get(target_id)
        if not isinstance(entry, dict) or target is None or "governed_unit" in entry:
            continue
        keys = sorted(str(k) for k in entry.pop("contributed_keys") or [])
        entry["governed_unit"] = {"kind": target.governed_unit, "keys": keys}
    data["schema_version"] = MANIFEST_SCHEMA_VERSION
    return data


def record_target_contribution(  # pylint: disable=too-many-arguments
    manifest: dict[str, Any],
    *,
    target_id: str,
    relative_parts: tuple[str, ...],
    template_filename: str,
    template_revision: str,
    governed_unit: dict[str, Any],
) -> None:
    """Upsert one target's contribution record in *manifest*."""
    targets = manifest.setdefault("targets", {})
    targets[target_id] = {
        "relative_parts": list(relative_parts),
        "template_filename": template_filename,
        "template_revision": template_revision,
        "governed_unit": governed_unit,
    }


def retired_governed_keys(
    manifest_entry: dict[str, Any], current_template: dict[str, Any] | str, target: WorkspaceSafetyPortTarget
) -> list[str]:
    """Return recorded governed keys the current template no longer governs."""
    recorded = set(governed_unit_keys(manifest_entry.get("governed_unit")))
    current = set(governed_unit_keys(resolve_governed_unit(current_template, target)))
    return sorted(recorded - current)


def prune_top_level_keys(existing: dict[str, Any], keys_to_remove: set[str]) -> dict[str, Any]:
    """Return a copy of *existing* with only the named top-level keys removed."""
    if not keys_to_remove:
        return copy.deepcopy(existing)
    out = copy.deepcopy(existing)
    for key in keys_to_remove:
        out.pop(key, None)
    return out


def drop_retired_governed_keys(manifest_entry: dict[str, Any], retired: set[str]) -> None:
    """Remove *retired* keys from a manifest entry's governed-unit record."""
    if not retired:
        return
    unit = manifest_entry.get("governed_unit")
    if not isinstance(unit, dict):
        return
    unit["keys"] = [k for k in governed_unit_keys(unit) if k not in retired]


def load_template_dict(templates_dir: Path, target: WorkspaceSafetyPortTarget) -> dict[str, Any]:
    """Load one registry template as a dict for manifest and prune logic."""
    path = templates_dir / target.template_filename
    if target.merge_kind == "codex_toml":
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: template must be an object")
    return data


def load_template_payload(templates_dir: Path, target: WorkspaceSafetyPortTarget) -> dict[str, Any] | str:
    """Load one registry template in the shape its governed unit declares.

    A text-region target's template is text, not structured data, so the payload is the file's text; every other
    governed unit loads through :func:`load_template_dict`. The declaration — never the target's identity — selects the
    loader.
    """
    if target.governed_unit == "text-region":
        path = templates_dir / target.template_filename
        return path.read_text(encoding="utf-8")
    return load_template_dict(templates_dir, target)
