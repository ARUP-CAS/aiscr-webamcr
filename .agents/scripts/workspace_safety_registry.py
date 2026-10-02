"""
Single source of truth for workspace-safety port targets (user home merge).

Used by ``port_workspace_safety_config.py`` and ``bootstrap_hub_clone.py`` so
bootstrap doctor checks and the port workflow stay aligned (drift prevention).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

MergeKind = Literal["codex_toml", "claude_snippet_json"]


@dataclass(frozen=True)
class WorkspaceSafetyPortTarget:
    """One template-backed merge destination under a user home (or --target-dir)."""

    target_id: str
    template_filename: str
    relative_parts: tuple[str, ...]
    skip_flag: str
    merge_kind: MergeKind
    schema_filename: str | None  # JSON Schema under templates/schemas/, when merge_kind uses JSON validation


# Only evidence-backed safety targets remain (Decision 1 retention test). The Cursor
# sandbox and Gemini snippets were removed because their keys were either documented
# vendor defaults or platform-specific/non-portable overrides with no verifiable safety
# benefit; see the config setting audit and design Decisions 3/4/7.
WORKSPACE_SAFETY_PORT_TARGETS: tuple[WorkspaceSafetyPortTarget, ...] = (
    WorkspaceSafetyPortTarget(
        "codex",
        "codex_user_config.toml",
        (".codex", "config.toml"),
        "--skip-codex",
        "codex_toml",
        None,
    ),
    WorkspaceSafetyPortTarget(
        "claude",
        "claude_safety_snippet.json",
        (".claude", "settings.json"),
        "--skip-claude",
        "claude_snippet_json",
        "claude_safety_snippet.schema.json",
    ),
)


def iter_workspace_safety_target_paths(home: Path) -> list[Path]:
    """Return expected absolute paths for all port targets under *home*."""
    return [home.joinpath(*t.relative_parts) for t in WORKSPACE_SAFETY_PORT_TARGETS]
