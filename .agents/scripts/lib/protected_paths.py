# delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

"""Own the protected set: load the deny floor's protected-path table and resolve a path to the kind that governs it.

The deny floor's ``[[protected_path]]`` table is the single owner of the protected set: each row declares a path — a
file, or a directory written ``dir/**`` — its kind (``A``, ``B`` or ``C``) and a rationale. A path can fall under more
than one row, as the sibling write surface does under the kind C sibling directory, and the more specific declaration
wins: an exact file row beats any directory row, and a deeper directory beats a shallower one. The close-out listing
resolves kinds here, and so does the tool-call guard, so the two cannot disagree about what a path is.

**Why the loader reads only the table's tail.** The table sits after every entry of the deny floor, so the loader parses
from the first ``[[protected_path]]`` header onward instead of the whole source. A guard on every tool call pays this
load each time, and the full source costs tens of milliseconds to parse where its tail costs well under one. The module
imports only the standard library at load time for the same reason; git is imported where it is used.

Contract: agent/agent-operation-safety
Class: library
Exit codes: Library module; no entrypoint.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

DENY_FLOOR_RELPATH = Path(".agents") / "canonical_configs" / "command_deny_floor.toml"
PROTECTION_KINDS = frozenset({"A", "B", "C"})
_TABLE_HEADER = "[[protected_path]]"


def load_protected_paths(root: Path) -> Dict[str, Dict[str, Any]]:
    """Load the protected-path table keyed by path.

    A row missing a field, declaring an unknown kind, or repeating a path is refused rather than defaulted. A source
    with no table loads as an empty mapping.
    """
    text = (root / DENY_FLOOR_RELPATH).read_text(encoding="utf-8")
    start = text.find(_TABLE_HEADER)
    rows = tomllib.loads(text[start:]).get("protected_path", []) if start != -1 else []
    table: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        for field in ("path", "kind", "rationale"):
            if field not in row:
                raise ValueError(f"protected_path row missing {field}: {row}")
        if row["kind"] not in PROTECTION_KINDS:
            raise ValueError(f"protected_path {row['path']!r} declares unknown kind {row['kind']!r}")
        if row["path"] in table:
            raise ValueError(f"protected_path {row['path']!r} is declared twice")
        table[row["path"]] = row
    return table


def _specificity(declared: str, path: str) -> Tuple[int, int] | None:
    """Return how specifically *declared* covers *path* — exact rows outrank directory rows — or ``None``."""
    if declared == path:
        return (1, len(declared))
    if declared.endswith("/**") and path.startswith(declared[:-2]):
        return (0, len(declared))
    return None


def protected_kind_of(path: str, table: Mapping[str, Mapping[str, Any]]) -> str | None:
    """Return the kind of the most specific protected-path row covering *path*, or ``None`` when no row covers it."""
    normalized = path.replace("\\", "/").removeprefix("./")
    best_score: Tuple[int, int] = (-1, -1)
    best_kind: str | None = None
    for declared, row in table.items():
        score = _specificity(declared, normalized)
        if score is not None and score > best_score:
            best_score, best_kind = score, str(row["kind"])
    return best_kind


def change_set_paths(root: Path) -> List[str]:
    """Return the paths the uncommitted change set touches.

    The set is the tracked changes against ``HEAD``, deletions included, plus the untracked files git does not ignore.
    """
    # Imported here so the guard, which never lists a change set, does not pay for it.
    from lib.proc_utils import run_exact  # pylint: disable=import-outside-toplevel

    tracked = run_exact(["git", "diff", "--name-only", "-z", "HEAD"], cwd=root, check=True).stdout
    untracked = run_exact(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=root, check=True).stdout
    return sorted({name for name in (tracked + "\0" + untracked).split("\0") if name})


def kind_c_touches(root: Path) -> List[str]:
    """Return the change set's paths whose most specific protected-path row is kind C."""
    table = load_protected_paths(root)
    return [path for path in change_set_paths(root) if protected_kind_of(path, table) == "C"]
