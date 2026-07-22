"""
Copy user-level workspace-safety config from repo templates to the current user's home.

Merges evidence-backed safety templates into user-level assistant configs under the
selected home directory: ``~/.codex/config.toml`` and ``~/.claude/settings.json``,
using ``workspace_safety_registry`` as the single target list (keeps bootstrap doctor
checks aligned). The Cursor sandbox and Gemini snippet targets were removed because
their keys were documented vendor defaults or non-portable overrides without a
verifiable safety benefit.

Codex uses the current top-level ``sandbox_mode`` shape. An existing legacy nested
``[sandbox].mode`` is migrated to ``sandbox_mode`` without being treated as canonical
output; an existing ``sandbox_mode`` or ``[windows].sandbox`` is preserved (the merge
never silently switches the Windows elevated/unelevated sandbox). When a target Codex
config selects the native Windows ``elevated`` sandbox, ``--list``/``--dry-run`` print
an advisory about the upstream TEMP-profile side effect and the WSL2 / ``unelevated``
mitigations without changing the setting.

Templates are validated (JSON Schema + TOML structure) before any write.
Use --dry-run to preview. Run from repo venv when in aiscr-management (see .agents/scripts/README.md).
Missing ``jsonschema`` / ``tomli_w`` are installed automatically from pinned lines in
``requirements-ci.txt`` when needed (see requirements_subset_install.py).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import time
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


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
    from requirements_subset_install import ensure_imports_from_requirements

    ensure_imports_from_requirements(
        get_repo_root() / "requirements-ci.txt",
        (("jsonschema", "jsonschema"), ("tomli-w", "tomli_w")),
    )


_ensure_port_script_dependencies()

import jsonschema  # noqa: E402  # pylint: disable=import-error
import tomli_w  # noqa: E402  # pylint: disable=import-error
from log_utils import log_error, log_info  # noqa: E402
from workspace_safety_registry import WORKSPACE_SAFETY_PORT_TARGETS  # noqa: E402


def get_templates_dir(repo_root: Path) -> Path:
    """Return path to safety_config_templates (under canonical_configs)."""
    return repo_root / ".agents" / "canonical_configs" / "safety_config_templates"


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

    The canonical shape is top-level ``sandbox_mode``. A legacy nested ``[sandbox].mode``
    is accepted only as migratable input (handled by ``merge_codex_dict``), never as
    valid canonical output.
    """
    if "approval_policy" not in data:
        raise ValueError(f"{label}: missing approval_policy")
    if "sandbox_mode" not in data:
        raise ValueError(f"{label}: missing top-level sandbox_mode (legacy [sandbox].mode is migrated, not canonical)")


def validate_codex_template_toml(path: Path) -> None:
    """Parse Codex TOML template and assert required keys/sections."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    validate_codex_data(data, label="codex_user_config.toml")


def validate_all_templates(templates: Path, schemas: Path) -> str | None:
    """Validate retained template files (Codex TOML + Claude snippet); return error or None."""
    try:
        snippet_data = load_json_file(templates / "claude_safety_snippet.json")
        validate_json_instance(
            snippet_data,
            load_schema(schemas / "claude_safety_snippet.schema.json"),
            label="claude_safety_snippet.json",
        )
        validate_codex_template_toml(templates / "codex_user_config.toml")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return str(exc)
    return None


def _union_deny_lists(sn_deny: Any, existing_deny: Any) -> list[str]:
    """Snippet deny entries first, then existing entries not already present."""
    if not isinstance(sn_deny, list):
        sn_deny = []
    if not isinstance(existing_deny, list):
        existing_deny = []
    seen: set[str] = set()
    out: list[str] = []
    for x in sn_deny:
        if isinstance(x, str) and x not in seen:
            seen.add(x)
            out.append(x)
    for x in existing_deny:
        if isinstance(x, str) and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _merge_permissions_block(base_perm: Dict[str, Any], sn_perm: Dict[str, Any]) -> Dict[str, Any]:
    merged_perm = dict(base_perm)
    if "deny" in sn_perm:
        merged_perm["deny"] = _union_deny_lists(sn_perm.get("deny"), base_perm.get("deny"))
    for key, val in sn_perm.items():
        if key != "deny":
            merged_perm[key] = val
    return merged_perm


def _migrate_legacy_codex_sandbox(out: Dict[str, Any]) -> None:
    """Migrate legacy nested ``[sandbox].mode`` to top-level ``sandbox_mode`` (shape only).

    Preserves any other ``[sandbox]`` subkeys and never changes the effective mode value.
    """
    sandbox = out.get("sandbox")
    if not (isinstance(sandbox, dict) and "mode" in sandbox):
        return
    if "sandbox_mode" not in out:
        out["sandbox_mode"] = sandbox["mode"]
    rest = {k: v for k, v in sandbox.items() if k != "mode"}
    if rest:
        out["sandbox"] = rest
    else:
        out.pop("sandbox", None)


def merge_codex_dict(existing: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the Codex safety template, preserving user values and migrating legacy shape.

    - A legacy nested ``[sandbox].mode`` is migrated to top-level ``sandbox_mode``.
    - An existing top-level ``sandbox_mode`` or ``approval_policy`` is preserved.
    - Template values fill only missing top-level keys (baseline for a fresh config).
    - ``[windows].sandbox`` and all unrelated settings are preserved untouched.
    """
    out = copy.deepcopy(existing)
    _migrate_legacy_codex_sandbox(out)
    for key, val in template.items():
        if key == "sandbox":
            # The template no longer ships a nested [sandbox] table; ignore defensively.
            continue
        if key not in out:
            out[key] = copy.deepcopy(val)
    return out


def codex_windows_sandbox_diagnostic(existing: Dict[str, Any]) -> str | None:
    """Return an advisory when the Codex config selects the native Windows elevated sandbox.

    The elevated Windows sandbox can leak ``C:\\Users\\TEMP*`` profiles (upstream behavior,
    no repository-level fix). This is advisory only and never changes the setting.
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


def merge_claude_settings(existing: Dict[str, Any], snippet: Dict[str, Any]) -> Dict[str, Any]:
    """Merge snippet into a copy of existing settings (snippet wins for overlapping sandbox keys)."""
    result: Dict[str, Any] = copy.deepcopy(existing)
    if "sandbox" in snippet:
        base = result.get("sandbox")
        if not isinstance(base, dict):
            base = {}
        overlay = snippet["sandbox"]
        if isinstance(overlay, dict):
            result["sandbox"] = {**base, **overlay}
        else:
            result["sandbox"] = overlay
    if "permissions" not in snippet:
        return result
    base_perm = result.get("permissions")
    if not isinstance(base_perm, dict):
        base_perm = {}
    sn_perm = snippet["permissions"]
    if not isinstance(sn_perm, dict):
        result["permissions"] = sn_perm
    else:
        result["permissions"] = _merge_permissions_block(base_perm, sn_perm)
    return result


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


def load_existing_settings(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Load ~/.claude/settings.json (see load_existing_json_object)."""
    return load_existing_json_object(path, label="settings.json")


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


def _skip_target_ids(args: argparse.Namespace) -> set[str]:
    """Return target_id set for targets skipped via CLI flags."""
    skip: set[str] = set()
    if args.skip_codex:
        skip.add("codex")
    if args.skip_claude:
        skip.add("claude")
    return skip


def _preflight_existing_targets(home: Path, *, skip: set[str]) -> str | None:
    """Return an error message if an existing target file is invalid, else None."""
    for target in WORKSPACE_SAFETY_PORT_TARGETS:
        if target.target_id in skip:
            continue
        path = home.joinpath(*target.relative_parts)
        if target.merge_kind == "codex_toml":
            _, err = load_existing_codex_toml(path)
        else:
            _, err = load_existing_json_object(path, label=path.name)
        if err:
            return err
    return None


def port_codex_config(
    home: Path,
    template: Union[Path, Dict[str, Any]],
    *,
    dry_run: bool,
    backup: bool,
) -> Tuple[str, str | None]:
    """Merge template into ~/.codex/config.toml (path to TOML file or parsed dict).

    Emits the advisory Windows elevated-sandbox diagnostic (if applicable) without
    modifying the Windows sandbox mode.
    """
    dst = home / ".codex" / "config.toml"
    existing, err = load_existing_codex_toml(dst)
    if err:
        return "error", err
    assert existing is not None
    diag = codex_windows_sandbox_diagnostic(existing)
    if diag:
        log_info(f"[advisory] {diag}")
    if isinstance(template, Path):
        template_dict = tomllib.loads(template.read_text(encoding="utf-8"))
    else:
        template_dict = template
    merged = merge_codex_dict(existing, template_dict)
    try:
        validate_codex_data(merged, label="merged codex config.toml")
    except ValueError as exc:
        return "error", str(exc)
    if dry_run:
        return "would merge", None
    write_toml_file(dst, merged, backup=backup)
    return "merged", None


def port_claude_settings(
    home: Path,
    snippet: Union[Path, Dict[str, Any]],
    *,
    dry_run: bool,
    backup: bool,
) -> Tuple[str, str | None]:
    """Merge snippet into ~/.claude/settings.json (path or dict). Returns (status, error_message)."""
    dst = home / ".claude" / "settings.json"
    existing, err = load_existing_settings(dst)
    if err:
        return "error", err
    assert existing is not None
    snippet_data = load_json_file(snippet) if isinstance(snippet, Path) else snippet
    merged = merge_claude_settings(existing, snippet_data)
    if dry_run:
        return "would merge", None
    status = write_json_file(dst, merged, backup=backup)
    return status, None


def main() -> int:  # pylint: disable=too-many-locals,too-many-statements,too-many-return-statements,too-many-branches
    """Parse CLI, validate templates, merge retained registry targets (Codex, Claude)."""
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
    parser.add_argument(
        "--skip-claude",
        action="store_true",
        help="Do not merge Claude safety snippet into ~/.claude/settings.json.",
    )
    parser.add_argument(
        "--skip-codex",
        action="store_true",
        help="Do not merge Codex template into ~/.codex/config.toml.",
    )
    args = parser.parse_args()

    repo_root = get_repo_root()
    templates = get_templates_dir(repo_root)
    schemas = get_schemas_dir(templates)
    if not templates.exists():
        log_error(f"Templates dir not found: {templates}")
        return 1
    if not schemas.exists():
        log_error(f"Schemas dir not found: {schemas}")
        return 1

    home = get_home(args.target_dir)

    if args.list:
        print("Template -> Destination")
        for target in WORKSPACE_SAFETY_PORT_TARGETS:
            print(f"  {templates / target.template_filename} -> merge into {home.joinpath(*target.relative_parts)}")
        return 0

    err = validate_all_templates(templates, schemas)
    if err:
        log_error(f"Template validation failed: {err}")
        return 1

    pre_err = _preflight_existing_targets(home, skip=_skip_target_ids(args))
    if pre_err:
        log_error(pre_err)
        return 1

    backup = bool(args.backup) and not args.dry_run
    reports: list[str] = []

    src_codex = templates / "codex_user_config.toml"
    if not args.skip_codex:
        cx_status, cx_err = port_codex_config(home, src_codex, dry_run=args.dry_run, backup=backup)
        if cx_err:
            log_error(cx_err)
            return 1
        reports.append(f"codex config.toml: {cx_status}")
    else:
        reports.append("codex config.toml: skipped")

    if not args.skip_claude:
        snippet_path = templates / "claude_safety_snippet.json"
        claude_status, claude_err = port_claude_settings(home, snippet_path, dry_run=args.dry_run, backup=backup)
        if claude_err:
            log_error(claude_err)
            return 1
        reports.append(f"claude settings.json: {claude_status}")
    else:
        reports.append("claude settings.json: skipped")

    for r in reports:
        log_info(r)

    print()
    print("Optional: Cursor Workspace Trust — in Cursor Settings set")
    print('  "security.workspace.trust.enabled": true')
    print("  See CLAUDE.md and AGENTS.md for full workspace-safety setup.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
