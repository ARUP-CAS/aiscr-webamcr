"""
Discover instruction-bearing documentation and config files for doc-hygiene audits.

Outputs a structured list (JSON or text) of files with path, line count, classification
category, and optional metadata so that downstream steps (e.g. audit prompt) can consume
it without agent-based discovery. Used in CI in "check" mode to ensure discovery runs;
full audit remains agent-driven with this script's output as input.

The `lines` field per file can be used to approximate token cost for reports and
long-lived assets (e.g. under .agents/reports/) in the C8 reports-cleanup phase
(roughly 1–2 tokens per line for English Markdown).

Discovery includes `.agents/canonical_configs/references/agent_tool_feature_matrix.md`
and short **pointer** files for hub tool trees (`.cursor/README.md`, `.claude/GOVERNANCE.md`,
`.codex/GOVERNANCE.md`, `.gemini/README_en.md`). Hub vendor dirs are committed at repo root.
Other `local_configs` subtrees stay excluded.

OpenSpec coverage: discovery also classifies durable capability specs under
``openspec/specs/**/*.md`` as ``openspec_specs``, active change artifacts under
``openspec/changes/<slug>/**/*.md`` (excluding ``archive/``) as
``openspec_active_changes``, and archived artifacts under
``openspec/changes/archive/**/*.md`` as ``openspec_archived_changes`` so audit findings
can distinguish current requirements from active proposals and historical records.

With `--check`, the repo must also contain **required** instruction paths (CI gate): the feature matrix,
`mandatory_vendor_doc_urls.toml`, `governance_by_tool.md`, and the hub-root pointer paths
(`.cursor`/`.claude`/`.codex`/`.gemini` committed directly at repo root).

Usage:
  python .agents/scripts/doc_discovery.py [--output json|text] [--check]
  --output json   Machine-readable list (default: text).
  --check         Exit 1 if discovery is empty or a REQUIRED_INSTRUCTION_PATHS file is missing (CI).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


ROOT = _default_root()

# Paths that must exist when using --check (in addition to non-empty discovery).
REQUIRED_INSTRUCTION_PATHS = (
    ".agents/canonical_configs/references/agent_tool_feature_matrix.md",
    ".agents/canonical_configs/references/mandatory_vendor_doc_urls.toml",
    ".agents/canonical_configs/references/governance_by_tool.md",
    ".cursor/README.md",
    ".claude/GOVERNANCE.md",
    ".codex/GOVERNANCE.md",
    ".gemini/README_en.md",
)

# Stable category keys for downstream audit classification.
CATEGORY_GOVERNANCE = "governance"
CATEGORY_RULES = "rules"
CATEGORY_PROMPTS = "prompts"
CATEGORY_PLANS = "plans"
CATEGORY_REFERENCES = "references"
CATEGORY_AGENTS_DOCS = "agents_docs"
CATEGORY_REPORTS = "reports"
CATEGORY_TOOL_ENTRY = "tool_entry"
CATEGORY_OPENSPEC_SPECS = "openspec_specs"
CATEGORY_OPENSPEC_ACTIVE_CHANGES = "openspec_active_changes"
CATEGORY_OPENSPEC_ARCHIVED_CHANGES = "openspec_archived_changes"
CATEGORY_OTHER = "other"

# Glob patterns relative to repo root (instruction-bearing files per audit_doc_hygiene C1;
# .agents/reports/*.md is included for C8 reports and long-lived assets cleanup evaluation).
# Each entry pairs a glob with the audit category to assign to matching paths. First match wins.
DISCOVERY_GLOB_RULES: tuple[tuple[str, str], ...] = (
    ("README*.md", CATEGORY_GOVERNANCE),
    ("CONTRIBUTING.md", CATEGORY_GOVERNANCE),
    ("AGENTS.md", CATEGORY_GOVERNANCE),
    ("CLAUDE.md", CATEGORY_GOVERNANCE),
    ("CODEX.md", CATEGORY_GOVERNANCE),
    ("GEMINI.md", CATEGORY_GOVERNANCE),
    ("COPILOT.md", CATEGORY_GOVERNANCE),
    (".cursorrules", CATEGORY_RULES),
    (".github/CODEOWNERS", CATEGORY_GOVERNANCE),
    (".github/PULL_REQUEST_TEMPLATE.md", CATEGORY_GOVERNANCE),
    (".cursor/rules/*.mdc", CATEGORY_RULES),
    (".agents/prompts/*.md", CATEGORY_PROMPTS),
    (".agents/plans/*.plan.md", CATEGORY_PLANS),
    (".agents/README.md", CATEGORY_GOVERNANCE),
    (".agents/plans/README.md", CATEGORY_PLANS),
    (".agents/prompts/README.md", CATEGORY_PROMPTS),
    (".agents/scripts/README.md", CATEGORY_REFERENCES),
    (".agents/canonical_configs/README.md", CATEGORY_REFERENCES),
    (".agents/canonical_configs/references/agent_tool_feature_matrix.md", CATEGORY_REFERENCES),
    (".agents/canonical_configs/references/mandatory_vendor_doc_urls.toml", CATEGORY_REFERENCES),
    (".agents/canonical_configs/references/governance_by_tool.md", CATEGORY_REFERENCES),
    (".agents/local_configs/README.md", CATEGORY_REFERENCES),
    (".agents/reports/*.md", CATEGORY_REPORTS),
    (".cursor/README.md", CATEGORY_TOOL_ENTRY),
    (".claude/GOVERNANCE.md", CATEGORY_TOOL_ENTRY),
    (".codex/GOVERNANCE.md", CATEGORY_TOOL_ENTRY),
    (".gemini/README_en.md", CATEGORY_TOOL_ENTRY),
    # OpenSpec durable capability specs.
    ("openspec/specs/**/*.md", CATEGORY_OPENSPEC_SPECS),
    # OpenSpec change artifacts (active + archived; classifier below distinguishes them).
    ("openspec/changes/**/*.md", CATEGORY_OPENSPEC_ACTIVE_CHANGES),
)
# Back-compat alias: the old list-of-globs constant, derived from DISCOVERY_GLOB_RULES.
DISCOVERY_GLOBS: tuple[str, ...] = tuple(pattern for pattern, _ in DISCOVERY_GLOB_RULES)
# Exclude paths that are not instruction-bearing (e.g. local_configs content).
EXCLUDE_PREFIXES = (".agents/local_configs/",)

OPENSPEC_ARCHIVE_PREFIX = "openspec/changes/archive/"
OPENSPEC_ACTIVE_CHANGES_PREFIX = "openspec/changes/"
OPENSPEC_SPECS_PREFIX = "openspec/specs/"


def _classify_openspec_change(rel_str: str) -> str:
    """Return the archived/active category for an OpenSpec change Markdown file."""
    if rel_str.startswith(OPENSPEC_ARCHIVE_PREFIX):
        return CATEGORY_OPENSPEC_ARCHIVED_CHANGES
    return CATEGORY_OPENSPEC_ACTIVE_CHANGES


HUB_LOCAL_CONFIGS_ALLOW_PREFIX = ""
HUB_LOCAL_CONFIGS_ALLOW_FILES: frozenset[str] = frozenset()


def _is_discovery_excluded(rel_str: str) -> bool:
    """True when path should be skipped (local_configs mirror trees except hub pointer paths)."""
    if rel_str in HUB_LOCAL_CONFIGS_ALLOW_FILES:
        return False
    if rel_str.startswith(HUB_LOCAL_CONFIGS_ALLOW_PREFIX):
        return False
    return any(rel_str.startswith(p) for p in EXCLUDE_PREFIXES)


def count_lines(path: Path) -> int:
    """Return the number of lines in a file, or -1 on read error."""
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return -1


def _classify_path(rel_str: str, default_category: str) -> str:
    """Return the audit category for a discovered path.

    Centralises classification so OpenSpec active-vs-archived change separation
    and other path-derived adjustments stay in one place.
    """
    if rel_str.startswith(OPENSPEC_SPECS_PREFIX):
        return CATEGORY_OPENSPEC_SPECS
    if rel_str.startswith(OPENSPEC_ACTIVE_CHANGES_PREFIX):
        return _classify_openspec_change(rel_str)
    return default_category


def discover(root: Path) -> list[dict]:
    """Discover instruction-bearing files under the given repo root.

    Each item carries an explicit ``category`` field so downstream audit
    consumers can distinguish OpenSpec specs, active OpenSpec change artifacts,
    archived OpenSpec change artifacts, governance docs, plans, prompts,
    references, reports, rules, and tool entry pointers without re-deriving the
    path taxonomy.
    """
    seen: set[Path] = set()
    out: list[dict] = []
    for pattern, default_category in DISCOVERY_GLOB_RULES:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            try:
                rel = path.relative_to(root)
            except ValueError:
                continue
            rel_str = str(rel).replace("\\", "/")
            if _is_discovery_excluded(rel_str):
                continue
            if path in seen:
                continue
            seen.add(path)
            lines = count_lines(path)
            category = _classify_path(rel_str, default_category)
            out.append(
                {
                    "path": rel_str,
                    "lines": lines,
                    "category": category,
                }
            )
    return sorted(out, key=lambda x: (x["path"].lower(), x["path"]))


def main() -> None:
    """CLI entry point for discovering instruction-bearing files."""
    parser = argparse.ArgumentParser(
        description=("Discover instruction-bearing files for doc-hygiene audits."),
    )
    parser.add_argument(
        "--output",
        choices=("json", "text"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if discovery is empty or required instruction paths are missing (for CI).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repo root (default: derived from script location). Used for testing.",
    )
    args = parser.parse_args()

    root = ROOT if args.root is None else args.root.resolve()
    files = discover(root)
    if args.check:
        if not files:
            print("No instruction-bearing files found.")
            raise SystemExit(1)
        missing_required = [rel for rel in REQUIRED_INSTRUCTION_PATHS if not (root / Path(rel)).is_file()]
        if missing_required:
            print("Missing required instruction files (doc_discovery --check):")
            for rel in missing_required:
                print(f"  - {rel}")
            raise SystemExit(1)

    if args.output == "json":
        print(json.dumps({"root": str(root), "files": files}, indent=2))
    else:
        for item in files:
            print(f"{item['path']}\t{item['lines']}\t{item['category']}")

    raise SystemExit(0)


if __name__ == "__main__":
    main()
