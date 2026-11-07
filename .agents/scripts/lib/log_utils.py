# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: c35418343fe8896348732bd54f8256de17338f8d 2026-11-07T14:33:16+01:00

"""Shared logging utilities for .agents/scripts/*.

All scripts that emit operational status messages should import from here instead of defining their own log_*
functions.  Report output, JSON output, and structured summaries should remain as plain print() calls.

Format: [INFO]  message  (two trailing spaces after INFO) [WARN]  message  (two trailing spaces after WARN) [ERROR]
message  (one trailing space after ERROR), routed to stderr

Contract: pipeline/script-authoring
Class: library
Exit codes: Library with no entrypoint; log_info/log_warn print to stdout, log_error to stderr.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

_LEVEL_LINE_RE = re.compile(r"^[ \t]*\[(INFO|WARN|ERROR)\](?=[ \t]|$)")


@dataclass(frozen=True)
class LogLevelCounts:
    """Captured output volume and strict shared-prefix counts."""

    lines: int
    info: int
    warn: int
    error: int


def count_log_levels(text: str) -> LogLevelCounts:
    """Count output lines and strict shared prefixes, allowing indentation."""
    lines = text.splitlines()
    counts = {"INFO": 0, "WARN": 0, "ERROR": 0}
    for line in lines:
        match = _LEVEL_LINE_RE.match(line)
        if match:
            counts[match.group(1)] += 1
    return LogLevelCounts(len(lines), counts["INFO"], counts["WARN"], counts["ERROR"])


def format_log_error(message: str) -> str:
    """Return one error message with the shared prefix and spacing."""
    return f"[ERROR] {message}"


def log_info(message: str) -> None:
    """Print an informational log message to stdout."""
    print(f"[INFO]  {message}")


def log_warn(message: str) -> None:
    """Print a warning log message to stdout."""
    print(f"[WARN]  {message}")


def log_error(message: str) -> None:
    """Print an error log message to stderr."""
    print(format_log_error(message), file=sys.stderr)


def log_verbose(message: str, *, verbose: bool) -> None:
    """Print message to stdout only when verbose mode is enabled."""
    if verbose:
        print(message)
