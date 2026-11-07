# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00

"""Shared repo-local runtime paths.

Label-scoped temp and cache directories under the gitignored ``.venv/.cache/`` tree for validation runners and their
child processes, not the system temp directory or divergent per-runner layouts.

On POSIX, ``temp_dir`` may shorten a label path to ``.venv/.cache/t/<8-hex>`` so ``unittest_parallel`` multiprocessing
Managers can bind AF_UNIX sockets within the ``sun_path`` byte budget.

Contract: pipeline/testing-pipeline-maintenance
Class: library
Exit codes: Library with no entrypoint; functions return Path values or mutated env dicts.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, Union

DEFAULT_LABEL = "shared"
_TEMP_ENV_VARS = ("TMPDIR", "TEMP", "TMP")
# multiprocessing places sockets at ``{TMPDIR}/pymp-XXXXXXXX/listener-XXXXXXXX``.
_AF_UNIX_SOCKET_OVERHEAD = len("/pymp-XXXXXXXX/listener-XXXXXXXX")
# Linux ``sun_path`` is 108 bytes including NUL; macOS is 104. Usable length excludes NUL.
_AF_UNIX_PATH_MAX = 103 if sys.platform == "darwin" else 107

PathLike = Union[Path, str]


def sanitize_label(value: str) -> str:
    """Sanitise *value* for safe use as a single filesystem path segment."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "default"


def resolve_venv_dir(root: Path) -> Optional[Path]:
    """Return the repository-local virtualenv directory when present."""
    for candidate in (root / ".venv", root / "venv"):
        if candidate.exists():
            return candidate
    return None


def resolve_venv_python(root: Path) -> Optional[str]:
    """Return the repository-local virtualenv interpreter path, or None if absent.

    Git-installed pre-commit hooks and IDE terminals invoke ``python`` from the caller's PATH, which on Windows is
    routinely a system interpreter carrying different tool versions than ``requirements-ci.txt`` pins. Hook shims
    resolve the interpreter through this helper so a check cannot silently report against an unpinned instrument.
    """
    for candidate in (
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
        root / "venv" / "Scripts" / "python.exe",
        root / "venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return os.fspath(candidate)
    return None


def cache_root(root: Path) -> Path:
    """Return the canonical repo-local cache root ``<venv>/.cache``.

    Prefers an existing virtualenv directory (``.venv`` or ``venv``) and falls back to ``<root>/.venv`` so the layout is
    stable for documentation and gitignore even before the virtualenv is created.
    """
    venv_dir = resolve_venv_dir(root) or (root / ".venv")
    return venv_dir / ".cache"


def cache_dir(
    root: Path,
    kind: str,
    label: Optional[str] = None,
    *,
    create: bool = False,
) -> Path:
    """Return a cache directory ``<venv>/.cache/<kind>[/<label>]``."""
    path = cache_root(root) / kind
    if label is not None:
        path = path / sanitize_label(label)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def short_temp_label(label: str) -> str:
    """Return a stable 8-hex label for AF_UNIX-safe short temp directories."""
    return hashlib.sha256(sanitize_label(label).encode("utf-8")).hexdigest()[:8]


def prose_pass_dir(root: Path, change_slug: Optional[str] = None, *, create: bool = False) -> Path:
    """Return the prose-optimisation ledger directory ``<venv>/.cache/prose-pass[/<slug>]``."""
    return cache_dir(root, "prose-pass", change_slug, create=create)


def openspec_corpus_dir(root: Path, *, create: bool = False) -> Path:
    """Return the OpenSpec corpus index directory ``<venv>/.cache/openspec-corpus``."""
    return cache_dir(root, "openspec-corpus", create=create)


# The operator-patch staging directory name, shared by the cache stage here and the visible
# hand-off under ``.agents/local_scratch/`` (``local_scratch_paths`` imports this module).
OPERATOR_PATCHES_DIRNAME = "operator-patches"


def operator_patch_cache_dir(root: Path, label: Optional[str] = None, *, create: bool = False) -> Path:
    """Return the operator-patch bulk stage ``<venv>/.cache/operator-patches[/<label>]``."""
    return cache_dir(root, OPERATOR_PATCHES_DIRNAME, label, create=create)


def review_pr_cache_dir(root: Path, run: Optional[str] = None, *, create: bool = False) -> Path:
    """Return the PR-review bulk run directory ``<venv>/.cache/aiscr-review-pr[/<run>]``."""
    return cache_dir(root, "aiscr-review-pr", run, create=create)


def af_unix_temp_budget() -> int:
    """Return the max TMPDIR length that still leaves room for Manager sockets."""
    return _AF_UNIX_PATH_MAX - _AF_UNIX_SOCKET_OVERHEAD


def temp_dir(root: Path, label: str = DEFAULT_LABEL, *, create: bool = False) -> Path:
    """Return the label-scoped temp directory under ``<venv>/.cache/``.

    Prefers ``tmp/<label>``. On POSIX, when that path would leave too little room for multiprocessing AF_UNIX sockets,
    falls back to ``t/<8-hex>`` so runners such as ``unittest_parallel`` can still bind their Manager listener.
    """
    canonical = cache_dir(root, "tmp", label, create=False)
    if os.name != "nt" and len(str(canonical)) > af_unix_temp_budget():
        path = cache_dir(root, "t", short_temp_label(label), create=False)
    else:
        path = canonical
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def pylint_home(root: Path, label: str = DEFAULT_LABEL, *, create: bool = False) -> Path:
    """Return the label-scoped pylint home ``<venv>/.cache/pylint/<label>``."""
    return cache_dir(root, "pylint", label, create=create)


def apply_temp_env(env: Dict[str, str], temp_path: Path) -> Dict[str, str]:
    """Point the standard temp env vars at *temp_path* (mutates and returns env)."""
    value = str(temp_path)
    for name in _TEMP_ENV_VARS:
        env[name] = value
    return env


def prepend_pythonpath(env: Dict[str, str], entries: Iterable[PathLike]) -> Dict[str, str]:
    """Prepend *entries* to ``PYTHONPATH`` (mutates and returns env)."""
    parts = [str(entry) for entry in entries]
    if not parts:
        return env
    existing = env.get("PYTHONPATH")
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def prepend_venv_bin_to_path(env: Dict[str, str], root: Path) -> Dict[str, str]:
    """Prepend the venv ``Scripts``/``bin`` directory to ``PATH`` when present."""
    venv_dir = resolve_venv_dir(root)
    if venv_dir is None:
        return env
    bindir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    if not bindir.is_dir():
        return env
    prefix = str(bindir)
    old_path = env.get("PATH", "")
    env["PATH"] = f"{prefix}{os.pathsep}{old_path}" if old_path else prefix
    return env


def build_runtime_env(  # pylint: disable=too-many-arguments
    root: Path,
    *,
    label: str = DEFAULT_LABEL,
    base_env: Optional[Mapping[str, str]] = None,
    pylint: bool = False,
    pythonpath: Iterable[PathLike] = (),
    prepend_venv_bin: bool = False,
    create: bool = True,
) -> Dict[str, str]:
    """Build a child-process environment with repo-local temp/cache paths.

    Always redirects the standard temp env vars under the label-scoped ``temp_dir`` path (``tmp/<label>``, or
    ``t/<8-hex>`` when that path would overflow the POSIX AF_UNIX socket budget). Optionally sets ``PYLINTHOME`` under
    the same label, prepends ``PYTHONPATH`` entries, and prepends the venv ``Scripts``/``bin`` directory to ``PATH``.
    """
    env: Dict[str, str] = dict(os.environ if base_env is None else base_env)
    apply_temp_env(env, temp_dir(root, label, create=create))
    if pylint:
        env["PYLINTHOME"] = str(pylint_home(root, label, create=create))
    prepend_pythonpath(env, pythonpath)
    if prepend_venv_bin:
        prepend_venv_bin_to_path(env, root)
    return env
