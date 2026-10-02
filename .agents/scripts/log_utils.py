"""
Shared logging utilities for .agents/scripts/*.

All scripts that emit operational status messages should import from here
instead of defining their own log_* functions.  Report output, JSON output,
and structured summaries should remain as plain print() calls.

Format:
  [INFO]  message  (two trailing spaces after INFO)
  [WARN]  message  (two trailing spaces after WARN)
  [ERROR] message  (one trailing space after ERROR), routed to stderr
"""

from __future__ import annotations

import sys


def log_info(message: str) -> None:
    """Print an informational log message to stdout."""
    print(f"[INFO]  {message}")


def log_warn(message: str) -> None:
    """Print a warning log message to stdout."""
    print(f"[WARN]  {message}")


def log_error(message: str) -> None:
    """Print an error log message to stderr."""
    print(f"[ERROR] {message}", file=sys.stderr)


def log_verbose(message: str, *, verbose: bool) -> None:
    """Print message to stdout only when verbose mode is enabled."""
    if verbose:
        print(message)
