# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: c35418343fe8896348732bd54f8256de17338f8d 2026-11-07T14:33:16+01:00

"""Ensure workspace-safety templates and registry stay aligned.

Contract: agent/workspace-safety-config
Class: script
Stable id: validation.workspace-safety-registry
Exit codes: 0 no mismatches; 1 errors reported on stderr
"""

from __future__ import annotations

import sys
import typing
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:  # pragma: no cover -- direct script startup already supplies this path
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib import repo_layout  # noqa: E402
from lib.log_utils import log_info  # noqa: E402
from lib.workspace_safety_registry import (  # noqa: E402
    TEXT_REGION_BEGIN,
    TEXT_REGION_END,
    WORKSPACE_SAFETY_PORT_TARGETS,
    GovernedUnitKind,
    ReconciliationPolicy,
    iter_workspace_safety_target_paths,
    load_template_payload,
    merge_contract_errors,
    resolve_governed_unit,
)

VALID_GOVERNED_UNITS = typing.get_args(GovernedUnitKind)
VALID_RECONCILIATION_POLICIES = typing.get_args(ReconciliationPolicy)


def _declaration_errors(target, templates: Path) -> list[str]:
    """Return declaration-field errors for one target; the declaration is the contract."""
    errors: list[str] = []
    if target.governed_unit not in VALID_GOVERNED_UNITS:
        errors.append(f"Invalid governed_unit for {target.target_id}: {target.governed_unit!r}")
    if target.reconciliation not in VALID_RECONCILIATION_POLICIES:
        errors.append(f"Invalid reconciliation for {target.target_id}: {target.reconciliation!r}")
    errors.extend(merge_contract_errors(target))
    if target.governed_unit == "nested-block" and not target.governed_block_key:
        errors.append(f"nested-block target {target.target_id} declares no governed_block_key")
    if target.governed_unit != "nested-block" and target.governed_block_key:
        errors.append(f"non-nested-block target {target.target_id} declares governed_block_key")
    for exc in target.exceptions:
        if not exc.subject or not exc.behaviour:
            errors.append(f"Malformed declared exception on {target.target_id}: {exc!r}")
    template_path = templates / target.template_filename
    if template_path.is_file() and not errors:
        try:
            template_payload = load_template_payload(templates, target)
            unit = resolve_governed_unit(template_payload, target)
        except ValueError as exc:
            errors.append(f"Governed-unit resolution failed for {target.target_id}: {exc}")
            return errors
        if target.governed_unit == "nested-block" and not unit["keys"]:
            errors.append(f"Template for {target.target_id} lacks the governed block {target.governed_block_key!r}")
        if target.governed_unit == "text-region" and not unit["keys"]:
            errors.append(
                f"Template for {target.target_id} lacks the delimited managed region "
                f"({TEXT_REGION_BEGIN!r} ... {TEXT_REGION_END!r})"
            )
    return errors


def main() -> int:
    """Verify registry declarations, on-disk templates, and schema references stay aligned."""
    repo_root = repo_layout.repo_root()
    templates = repo_root / repo_layout.WORKSTATION_SAFETY_TEMPLATES_DIR
    schemas = templates / "schemas"
    errors: list[str] = []

    for target in WORKSPACE_SAFETY_PORT_TARGETS:
        tpath = templates / target.template_filename
        if not tpath.is_file():
            errors.append(f"Missing template for {target.target_id}: {tpath}")
        if target.schema_filename and not (schemas / target.schema_filename).is_file():
            errors.append(f"Missing schema for {target.target_id}: {target.schema_filename}")
        errors.extend(_declaration_errors(target, templates))

    sample_home = Path("/tmp/workspace-safety-registry-check")
    paths = iter_workspace_safety_target_paths(sample_home)
    if len(paths) != len(WORKSPACE_SAFETY_PORT_TARGETS):
        errors.append("iter_workspace_safety_target_paths length mismatch vs WORKSPACE_SAFETY_PORT_TARGETS")
    for target, path in zip(WORKSPACE_SAFETY_PORT_TARGETS, paths):
        expected = sample_home.joinpath(*target.relative_parts)
        if path != expected:
            errors.append(f"Path order mismatch for {target.target_id}: {path} vs {expected}")

    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        return 1
    log_info("Checked workspace-safety declarations, templates, schemas, and target paths; no mismatches.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
