# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00

"""Shared loader for the product-level vendor matrix registry.

The machine source of truth lives in ``.agents/canonical_configs/mandatory_vendor_doc_urls.toml`` and contains:

- ``[[product]]`` rows: product-level onboarding metadata
- ``[[entry]]`` rows: per-(product, asset_type) documentation/path matrix

This module keeps the product registry semantics in one place.

Contract: agent/agent-vendor-lifecycle
Class: library
Exit codes: library with no entrypoint
"""

from __future__ import annotations

import json
import tomllib
from collections.abc import Collection
from pathlib import Path
from typing import Any

DEFAULT_TOML = Path(".agents/canonical_configs/mandatory_vendor_doc_urls.toml")

# The registry's human-readable twin, owned here beside the TOML it mirrors because more than one
# consumer needs it: the matrix validator decides the twin against the registry, and the
# citation-source reporter scans the twin for inline citations. Owning it in either consumer would
# force the other to import a validator or to re-encode the path.
DEFAULT_MATRIX_MD = Path(".agents/canonical_configs/references/agent_tool_feature_matrix.md")

INTEGRATION_CLASSES = frozenset({"agent_folders", "repo_root", "review_only", "digest_only"})
REVIEW_VALIDATION_MODES = frozenset({"skip", "shared_surface", "dedicated_surface"})
SUBAGENT_MODES = frozenset({"filesystem", "custom_modes", "none"})
SKILL_MODES = frozenset({"committed_aiscr", "third_party_only", "none"})

ASSET_TYPES = (
    "rules",
    "subagents",
    "skills",
    "commands",
    "hooks",
    "mcp",
    "project_instructions",
    "workflow_registry_vendor",
    "workflow_registry_hub",
    "review",
)

ASSET_TYPE_LABELS = {
    "rules": "Rules",
    "subagents": "Subagents / custom agents",
    "skills": "Skills",
    "commands": "Slash / custom commands",
    "hooks": "Hooks & automation",
    "mcp": "MCP support",
    "project_instructions": "Project instructions",
    "workflow_registry_vendor": "Workflow registry (vendor)",
    "workflow_registry_hub": "Workflow registry (hub)",
    "review": "Review",
}


def _string_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def _normalize_product(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(raw.get("id", "")).strip(),
        "label": str(raw.get("label", "")).strip(),
        "matrix_column": str(raw.get("matrix_column", "")).strip(),
        "integration_class": str(raw.get("integration_class", "")).strip(),
        "agent_folder": str(raw.get("agent_folder", "")).strip(),
        "sync_token": str(raw.get("sync_token", "")).strip(),
        "workflow_skill_tool": str(raw.get("workflow_skill_tool", "")).strip(),
        "governance_vendor_id": str(raw.get("governance_vendor_id", "")).strip(),
        "hub_entry_docs": _string_list(raw.get("hub_entry_docs")),
        "documentation_hosts": _string_list(raw.get("documentation_hosts")),
        "review_validation_mode": str(raw.get("review_validation_mode", "")).strip(),
        "subagent_mode": str(raw.get("subagent_mode", "")).strip(),
        "skill_mode": str(raw.get("skill_mode", "")).strip(),
    }


def load_vendor_matrix(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load and normalize product + entry rows from the matrix TOML."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return {
        "product": [_normalize_product(row) for row in data.get("product", []) if isinstance(row, dict)],
        "entry": [row for row in data.get("entry", []) if isinstance(row, dict)],
    }


def load_products(path: Path) -> list[dict[str, Any]]:
    """Return normalized product rows from the matrix TOML."""
    return load_vendor_matrix(path)["product"]


def governance_vendor_ids(path: Path) -> list[str]:
    """Return distinct governance vendor ids in product-registry order."""
    vendor_ids: list[str] = []
    seen: set[str] = set()
    for row in load_products(path):
        vendor_id = str(row.get("governance_vendor_id", "")).strip()
        if not vendor_id or vendor_id in seen:
            continue
        seen.add(vendor_id)
        vendor_ids.append(vendor_id)
    return vendor_ids


def skill_tool_dirs(path: Path) -> dict[str, str]:
    """Return the committed workflow-skill tree each product resolves, keyed by tool id.

    The tree comes from the product's ``skills`` ``[[entry]]`` row rather than from its ``agent_folder``, because a
    shared path serves several products: deriving ``<agent_folder>/skills`` would re-invent one tree per vendor and
    contradict the row that records which tree the product actually resolves.
    """
    committed: dict[str, str] = {}
    for row in load_vendor_matrix(path)["entry"]:
        if str(row.get("asset_type", "")).strip() != "skills":
            continue
        product = str(row.get("product", "")).strip()
        value = str(row.get("hub_committed_path", "")).strip().replace("\\", "/").rstrip("/")
        if product and value:
            committed[product] = value

    tool_dirs: dict[str, str] = {}
    for row in load_products(path):
        tool = str(row.get("workflow_skill_tool", "")).strip()
        if not tool or row.get("skill_mode") != "committed_aiscr":
            continue
        tree = committed.get(str(row.get("id", "")).strip(), "")
        if not tree or not tree.startswith("."):
            continue
        tool_dirs.setdefault(tool, tree)
    return tool_dirs


def skill_tree_dirs(path: Path) -> list[str]:
    """Return the distinct committed skill trees, in product-registry order.

    Generation and parity both work on trees: a product served by a shared tree is checked against that tree, and the
    tree is written once however many products read it.
    """
    trees: list[str] = []
    for tree in skill_tool_dirs(path).values():
        if tree not in trees:
            trees.append(tree)
    return trees


def workflow_skill_tools(path: Path) -> list[str]:
    """Return distinct committed AIS CR workflow-skill tool ids in matrix order."""
    return list(skill_tool_dirs(path))


def workflow_emitter_tools(
    path: Path,
    auxiliary_vendor_ids: Collection[str],
) -> list[str]:
    """Return selected workflow-emitter ids in product-registry order.

    Products with a committed AIS CR skill tree contribute their ``workflow_skill_tool``. Products that only expose a
    registered auxiliary workflow surface contribute their ``governance_vendor_id`` when that id is present in
    ``auxiliary_vendor_ids``.
    """
    auxiliary_ids = {str(value).strip() for value in auxiliary_vendor_ids if str(value).strip()}
    tools: list[str] = []
    seen: set[str] = set()
    for row in load_products(path):
        candidates: list[str] = []
        skill_tool = str(row.get("workflow_skill_tool", "")).strip()
        if row.get("skill_mode") == "committed_aiscr" and skill_tool:
            candidates.append(skill_tool)
        vendor_id = str(row.get("governance_vendor_id", "")).strip()
        if vendor_id in auxiliary_ids:
            candidates.append(vendor_id)
        for tool in candidates:
            if tool in seen:
                continue
            seen.add(tool)
            tools.append(tool)
    return tools


def _strip_jsonc_comments(text: str) -> str:
    """Return JSON text with JSONC comments removed while preserving strings."""
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(text) and text[index : index + 2] != "*/":
                index += 1
            index += 2
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _dotted_key_exists(document: Any, dotted_key: str) -> bool:
    """Return whether every object key in ``dotted_key`` exists in ``document``."""
    current = document
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True


def _configuration_declaration_errors(
    label: str,
    config_path: str,
    selecting_key: str,
    expected_keys: list[str],
) -> list[str]:
    """Validate the key-presence metadata declared by one registry row."""
    errors: list[str] = []
    if not config_path:
        errors.append(f"{label}: load_configuration_path required when configuration keys are declared")
        return errors
    if not selecting_key:
        errors.append(f"{label}: load_configuration_key required for {config_path}")
    if not expected_keys:
        errors.append(f"{label}: expected_configuration_keys required for {config_path}")
    elif selecting_key and selecting_key not in expected_keys:
        errors.append(f"{label}: load_configuration_key {selecting_key!r} is absent from expected_configuration_keys")
    return errors


def configuration_key_presence_errors(root: Path, entries: list[dict[str, Any]]) -> list[str]:
    """Validate registry-declared configuration keys against delivered JSON/JSONC files."""
    errors: list[str] = []
    parsed: dict[Path, Any] = {}
    parse_errors: dict[Path, str] = {}
    for entry in entries:
        config_path = str(entry.get("load_configuration_path", "") or "").strip()
        selecting_key = str(entry.get("load_configuration_key", "") or "").strip()
        expected_keys = _string_list(entry.get("expected_configuration_keys"))
        if not config_path and not selecting_key and not expected_keys:
            continue
        product = str(entry.get("product", "") or "").strip() or "<unknown>"
        asset_type = str(entry.get("asset_type", "") or "").strip() or "<unknown>"
        label = f"{product}/{asset_type}"
        errors.extend(_configuration_declaration_errors(label, config_path, selecting_key, expected_keys))
        if not config_path:
            continue
        target = root.joinpath(*Path(config_path.replace("\\", "/")).parts)
        if target not in parsed and target not in parse_errors:
            if not target.is_file():
                parse_errors[target] = "file not found"
            else:
                try:
                    parsed[target] = json.loads(_strip_jsonc_comments(target.read_text(encoding="utf-8")))
                except (OSError, json.JSONDecodeError) as exc:
                    parse_errors[target] = str(exc)
        if target in parse_errors:
            errors.append(f"{label}: cannot inspect {config_path}: {parse_errors[target]}")
            continue
        for dotted_key in expected_keys:
            if not _dotted_key_exists(parsed[target], dotted_key):
                errors.append(f"{label}: expected configuration key {dotted_key!r} missing from {config_path}")
    return errors
