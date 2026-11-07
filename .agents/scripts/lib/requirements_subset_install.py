# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: 96a1e289289a180161258baa10f7547b8cd9f719 2026-11-07T11:55:51+01:00

"""Install a subset of pinned packages from a requirements file when imports are missing.

Reads full requirement lines (e.g. ``name==version``) from ``requirements-ci.txt``; only listed distributions are
installed.

Contract: agent/workspace-safety-config
Class: library
Exit codes: none; this module is a library with no entrypoint
"""

from __future__ import annotations

import importlib
import re
import subprocess  # nosec B404 -- CalledProcessError only; capture runs through proc_utils
import sys
from pathlib import Path
from typing import Dict, Sequence, Tuple

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:  # pragma: no cover -- direct script startup already supplies this path
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.proc_utils import run_diagnostic  # noqa: E402

# Match a distribution name at the start of a requirement line (before version specifiers).
_NAME_END = re.compile(r"[<>=!~]")


def _normalize_dist_name(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def parse_pinned_requirements(requirements_path: Path) -> Dict[str, str]:
    """Parse a requirements file into ``normalized_dist_name -> full_line``.

    Skips blank lines and full-line comments. Lines use ``name==version`` (or similar); the name is the segment before
    the first version specifier.
    """
    if not requirements_path.is_file():
        raise RuntimeError(f"Requirements file not found: {requirements_path}")
    mapping: Dict[str, str] = {}
    for raw in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = _NAME_END.search(line)
        if m:
            name_part = line[: m.start()].strip()
        else:
            name_part = line.strip()
        if not name_part:
            continue
        key = _normalize_dist_name(name_part)
        mapping[key] = line
    return mapping


def _imports_ok(import_names: Sequence[str]) -> bool:
    for mod in import_names:
        try:
            importlib.import_module(mod)
        except ImportError:
            return False
    return True


def ensure_imports_from_requirements(
    requirements_path: Path,
    needed: Sequence[Tuple[str, str]],
    *,
    quiet: bool = True,
) -> None:
    """Ensure ``import_module_name`` imports succeed, installing from ``requirements_path`` if needed.

    Each entry in ``needed`` is ``(distribution_name_as_in_file, import_module_name)``. Missing distributions in the
    file raise ``RuntimeError`` (no silent drift).
    """
    import_names = [imp for _, imp in needed]
    if _imports_ok(import_names):
        return

    by_dist = parse_pinned_requirements(requirements_path)
    specs: list[str] = []
    for dist_name, imp in needed:
        try:
            importlib.import_module(imp)
        except ImportError:
            key = _normalize_dist_name(dist_name)
            spec = by_dist.get(key)
            if spec is None:
                raise RuntimeError(
                    f"Package {dist_name!r} (normalized {key!r}) not found in {requirements_path}; "
                    "cannot auto-install. Add the pin to that file or install manually."
                ) from None
            specs.append(spec)

    if not specs:
        return

    cmd = [sys.executable, "-m", "pip", "install", *specs]
    if quiet:
        cmd.append("-q")
    try:
        # Diagnostic: pip's output is quoted into a RuntimeError for a human to read,
        # never parsed, so a package's odd byte must not mask the install failure.
        run_diagnostic(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        msg = (exc.stderr or "").strip() or (exc.stdout or "").strip() or "(no output)"
        raise RuntimeError(f"pip install failed for {specs}. Output:\n{msg}") from exc

    if not _imports_ok(import_names):
        raise RuntimeError(
            "Installed requirements subset but imports still fail; check the active Python/venv and retry."
        )
