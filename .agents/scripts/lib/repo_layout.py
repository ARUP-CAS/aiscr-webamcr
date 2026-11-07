# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: 96a1e289289a180161258baa10f7547b8cd9f719 2026-11-07T11:55:51+01:00

"""Single owner for the hub's governed root-tree locations.

Some layout facts are needed by validators, generators, hooks, and runners alike, so whichever module happened to
declare a constant first became their de-facto owner. Per the single-owner-truth doctrine in
``aiscr-mgmt-doc-dynamic-sets`` ("give an unowned fact a home, then repoint"), those facts live here instead.

This module imports nothing but the standard library and must stay that way. Facts already owned by the module named for
them stay there -- ``asset_manifest.MANIFEST_RELPATH``, ``digest_builder.GOVERNANCE_RULES_RELPATH``,
``sibling_delivery_policy.SYNC_POLICY_DIR``.

Each location is exported twice on purpose. The ``Path`` form composes with a repository root; the ``*_PREFIX`` string
form is what repo-relative POSIX classification (``rel.startswith(...)``) needs.

Contract: documentation/durable-documentation
Class: library
Exit codes: Library with no entrypoint; exports path constants and repo_root() only.
"""

from __future__ import annotations

from pathlib import Path

# Production Python for the hub's automation, and its test tree.
AGENTS_SCRIPTS_DIR = Path(".agents") / "scripts"
AGENTS_SCRIPTS_PREFIX = f"{AGENTS_SCRIPTS_DIR.as_posix()}/"
AGENTS_SCRIPTS_TESTS_DIR = AGENTS_SCRIPTS_DIR / "tests"

# Active OpenSpec change folders, and the archive beneath them.
OPENSPEC_CHANGES_DIR = Path("openspec") / "changes"
OPENSPEC_CHANGES_PREFIX = f"{OPENSPEC_CHANGES_DIR.as_posix()}/"
OPENSPEC_ARCHIVE_DIR = OPENSPEC_CHANGES_DIR / "archive"

# Durable capability specs.
OPENSPEC_SPECS_DIR = Path("openspec") / "specs"
OPENSPEC_SPECS_PREFIX = f"{OPENSPEC_SPECS_DIR.as_posix()}/"

# Where npm installs. Needed by the bootstrap probe, the pin check, the MCP
# workstation setup, and several scan-exclusion sets, none of which is the others'
# natural owner. A single segment rather than a ``Path``, because most uses join it
# onto a root and the rest test it as a directory name.
NODE_MODULES = "node_modules"

# GitHub Copilot's committed entry surface: GitHub-native, so it sits outside the
# per-vendor assistant roots and is referenced by name across several checks.
COPILOT_INSTRUCTIONS_FILE = Path(".github") / "copilot-instructions.md"
COPILOT_INSTRUCTIONS_REL = COPILOT_INSTRUCTIONS_FILE.as_posix()

# Pinned OpenSpec CLI entry, relative to ``node_modules`` and to the repository root.
# Bootstrap probes, corpus loaders, and relationship reports all need this location
# and none of them is the others' natural owner.
OPENSPEC_PACKAGE_CLI = Path("@fission-ai") / "openspec" / "bin" / "openspec.js"
OPENSPEC_CLI_RELATIVE = Path(NODE_MODULES) / OPENSPEC_PACKAGE_CLI

# Workstation-safety templates consumed by the permission-syntax check, the posture
# report, the port setup tool, and the registry validator.
WORKSTATION_SAFETY_TEMPLATES_DIR = Path(".agents") / "canonical_configs" / "templates" / "workstation_safety"


def repo_root() -> Path:
    """Return the repository root, derived from this module's own location.

    The depth is this module's own — ``.agents/scripts/lib/`` — and not a claim about where callers sit, because they no
    longer sit at one depth: an entrypoint is flat, a packaged tool one level down, a library here. Deriving it from
    ``__file__`` rather than the working directory or ``git rev-parse`` keeps it correct when a script is invoked from a
    subdirectory, from a git hook, or without git on PATH.
    """
    return Path(__file__).resolve().parents[3]
