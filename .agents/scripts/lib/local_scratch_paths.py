# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: 083eb1bc1a0c628b2d6d48b806b6568be3f67ac2 2026-11-07T12:31:37+01:00

"""Paths for visible run hand-offs and their bulk staging.

Hand-offs — branch-audit Markdown, operator-patch READMEs, and approval views — live under `.agents/local_scratch/`. The
directory is deliberately Git-visible so new and changed hand-offs appear in normal status and diff review. The
artefact-placement capability owns retention and read-only-in-practice rules. Bulk machine artefacts, including an
operator patch's staged files and manifest, live under the repository cache resolved by ``runtime_env``.

Contract: workflow/artefact-placement
Class: library
Exit codes: Library with no entrypoint; functions resolve, prepare, and retire local hand-offs.
"""

from __future__ import annotations

import re
import stat
from pathlib import Path

from lib import runtime_env

LOCAL_SCRATCH_REL = ".agents/local_scratch"
OPERATOR_PATCHES_REL = runtime_env.OPERATOR_PATCHES_DIRNAME
_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,254}$")
POINTER_NAME = "POINTER.md"


def local_scratch_dir(repo_root: Path) -> Path:
    """Return the resolved local scratch root for hand-offs."""
    return (repo_root / LOCAL_SCRATCH_REL).resolve()


def _segment(value: str) -> str:
    """Return *value* when it is one safe directory segment, else refuse it."""
    if not _SEGMENT_PATTERN.fullmatch(value) or runtime_env.sanitize_label(value) != value:
        raise ValueError(f"hand-off path segment must be a single safe name: {value!r}")
    return value


def _handoff_path(repo_root: Path, *segments: str) -> Path:
    """Return an uncreated hand-off path confined to the local scratch root."""
    path = repo_root.resolve() / LOCAL_SCRATCH_REL
    for segment in segments:
        path = path / _segment(segment)
    return path


def _assert_resolvable_under(path: Path, root: Path) -> None:
    """Refuse a path whose existing ancestors resolve outside *root*.

    Check each existing component before resolving, including dangling links, so an absent hand-off root can be created
    without traversing a redirected ancestor. A component that is absent, or unreachable because an ancestor is a
    regular file, cannot contain a traversable link and is treated as absent.
    """
    root = root.resolve()
    path = path.absolute()
    if ".." in path.parts or not path.is_relative_to(root):
        raise ValueError(f"hand-off path escapes its root: {path}")
    current = root
    for part in path.relative_to(root).parts:
        current /= part
        try:
            metadata = current.lstat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
        ):
            raise ValueError(f"hand-off path contains a link or reparse point: {current}")


def ensure_handoff_dir(repo_root: Path, *segments: str) -> Path:
    """Create and return a hand-off directory under local scratch, idempotently.

    The created path stays confined to the repository through the local scratch root: every segment is a single safe
    name and no existing ancestor may resolve outside the repository. An existing directory is reused without being
    recreated or cleared.
    """
    path = _handoff_path(repo_root, *segments)
    _assert_resolvable_under(path, repo_root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare_run_handoff(repo_root: Path, workflow: str, run: str) -> Path:
    """Create a bounded run directory and its bulk pointer without changing posted bytes."""
    path = ensure_handoff_dir(repo_root, workflow, run)
    bulk = runtime_env.cache_dir(repo_root.resolve(), _segment(workflow), _segment(run))
    _assert_resolvable_under(bulk, repo_root)
    bulk.mkdir(parents=True, exist_ok=True)
    pointer = path / POINTER_NAME
    _assert_resolvable_under(pointer, repo_root)
    expected = f"# Run location\n\nBulk machine artifacts: `{bulk}`\n"
    if pointer.exists() and pointer.read_bytes() != expected.encode("utf-8"):
        raise ValueError(f"hand-off pointer differs; inspect the existing run before reusing it: {pointer}")
    pointer.write_text(expected, encoding="utf-8", newline="\n")
    return path


def checked_handoff_file(repo_root: Path, target: Path) -> Path:
    """Return an absolute file path confined to the checkout without creating anything."""
    root = repo_root.resolve()
    target = target if target.is_absolute() else root / target
    _assert_resolvable_under(target, root)
    return target


def prepare_handoff_file(repo_root: Path, target: Path) -> Path:
    """Validate an output path and create its parents; governed runs also gain a pointer.

    Explicit legacy output paths inside the checkout remain supported. Neither those paths nor the standard workflow/run
    layout may traverse links or escape the checkout.
    """
    root = repo_root.resolve()
    target = checked_handoff_file(root, target)
    parts = target.relative_to(root).parts
    if parts[:2] == (".agents", "local_scratch"):
        if len(parts) != 5:
            raise ValueError("hand-off files must use .agents/local_scratch/<workflow>/<run>/<file>")
        _segment(parts[-1])
        prepare_run_handoff(root, parts[2], parts[3])
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
    return target


def cleanup_run_handoff(repo_root: Path, workflow: str, run: str, allowed: frozenset[str]) -> None:
    """Remove one run's allowlisted ordinary files after validating the complete directory."""
    path = _handoff_path(repo_root, workflow, run)
    _assert_resolvable_under(path, repo_root)
    if not path.exists():
        return
    if not path.is_dir():
        raise ValueError(f"hand-off run is not a directory: {path}")
    entries = list(path.iterdir())
    for entry in entries:
        _assert_resolvable_under(entry, repo_root)
        if entry.name not in allowed or not entry.is_file():
            raise ValueError(f"unexpected hand-off entry; nothing was removed: {entry}")
    for entry in entries:
        entry.unlink()
    path.rmdir()


def operator_patches_dir(repo_root: Path) -> Path:
    """Return the bulk operator-patch staging root under the repository cache."""
    return runtime_env.operator_patch_cache_dir(repo_root)


def operator_patch_handoff_dir(repo_root: Path, label: str) -> Path:
    """Return the visible operator-patch hand-off directory (not created)."""
    return _handoff_path(repo_root, OPERATOR_PATCHES_REL, label)


def ensure_operator_patch_handoff_dir(repo_root: Path, label: str) -> Path:
    """Create and return one operator patch's visible README hand-off directory."""
    return ensure_handoff_dir(repo_root, OPERATOR_PATCHES_REL, label)


def default_branch_audit_report_path(repo_root: Path, report_date: str) -> Path:
    """Default Markdown path for report_sibling_branch_inventory.py when not using --stdout."""
    return local_scratch_dir(repo_root) / f"sibling_branch_inventory_{report_date}.md"
