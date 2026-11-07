# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: 083eb1bc1a0c628b2d6d48b806b6568be3f67ac2 2026-11-07T12:31:37+01:00

"""Shared command runner for `.agents/scripts/*`.

This module is the single owning home for one decision: how output captured from a child process is decoded. Without an
explicit ``encoding=``, ``subprocess`` decodes with whatever ``locale.getpreferredencoding()`` returns, which is the
workstation code page — ``cp1250`` on a Windows workstation. A byte the code page cannot map kills the reader thread,
leaves ``stdout`` as ``None``, and surfaces in the caller as ``AttributeError: 'NoneType' object has no
attribute 'strip'``. UTF-8 CI cannot reproduce any of it.

The decision lives here rather than at each call site because a policy re-declared per site is satisfied by omission,
and the omission is what CI cannot see.

Pick the entry point by what the caller does with the text:

:func:`run_exact` — the output is parsed or reproduced as content, so an undecodable byte MUST fail loudly rather than
substitute a character. Use it for ``git`` plumbing, ``gh`` bodies, and JSON. Note that this cannot be implemented by
passing ``encoding=`` with strict errors. When both streams are captured, ``subprocess`` decodes on a reader thread; a
``UnicodeDecodeError`` there kills the thread, ``communicate()`` yields ``None`` for that stream, and the caller sees
``AttributeError:
'NoneType' object has no attribute …`` — the original defect's misdirecting signature, reproduced. So the bytes are
captured undecoded and decoded here, in the caller's own stack, where the error surfaces with a traceback that names its
real subject. :func:`run_diagnostic` — the output is replayed as a log or advisory line, so one bad byte MUST NOT
destroy the surrounding run's report. :func:`run_bytes` — the output is not text at all (``git ls-files -z`` and other
NUL-delimited path lists, where the bytes are filesystem names rather than characters). Decode the pieces with
:func:`os.fsdecode` at the call site.

Every entry point captures both streams; these are capture helpers, not a general ``subprocess`` wrapper.

The module also owns the encode-direction pair of the same decision: what a governed CLI emits on its own pipe, and what
a parent pins into a Python child's environment.

:func:`configure_stdout_utf8` — a governed CLI pins its piped stdout/stderr to UTF-8, because consumers decode strictly
and a locale-encoded pipe is a crash or a silent substitution for them. A console-attached stream is left to the host.
:func:`utf8_child_env` — a parent spawning a Python child pins ``PYTHONIOENCODING=utf-8`` so the child's pipes are UTF-8
even before the child's own pin applies.

The two requirements this module implements are *Captured subprocess output SHALL be decoded explicitly rather than by
ambient locale* and *Decode-failure policy SHALL match the consumer's tolerance for substitution*.

Contract: pipeline/script-authoring
Class: library
Exit codes: none; this module is a library with no entrypoint
"""

from __future__ import annotations

# The entry points mirror the `subprocess.run` keywords their call sites actually use
# (cwd, env, input, check, timeout). Collapsing them into an options object would put a
# second shape between the caller and a stdlib signature it already knows.
# pylint: disable=too-many-arguments
import os
import subprocess  # nosec B404 -- this module is the reviewed home for subprocess capture
import sys
from pathlib import Path
from typing import Mapping, Sequence

__all__ = ["run_exact", "run_diagnostic", "run_bytes", "configure_stdout_utf8", "utf8_child_env", "ENCODING"]

ENCODING = "utf-8"


def _capture(
    cmd: Sequence[str],
    *,
    cwd: Path | str | None,
    env: Mapping[str, str] | None,
    input: str | bytes | None,  # pylint: disable=redefined-builtin
    check: bool,
    timeout: float | None,
    encoding: str | None,
    errors: str | None,
) -> subprocess.CompletedProcess:
    """Run *cmd* with both streams captured, decoding per *encoding* / *errors*.

    The ``# nosec`` waiver lives here rather than at every call site, so the security review of "argv list, no shell"
    has one reviewed home. Callers pass a fixed argv sequence and never a shell string; ``shell=False`` is the default
    and is not overridable through this module.
    """
    return subprocess.run(  # nosec B603 -- argv sequence, shell=False, no caller-supplied shell string
        list(cmd),
        cwd=None if cwd is None else str(cwd),
        env=env,
        input=input,
        check=check,
        timeout=timeout,
        capture_output=True,
        encoding=encoding,
        errors=errors,
    )


def _decode_strict(raw: bytes) -> str:
    r"""Decode *raw* as strict UTF-8 with universal-newline translation.

    The newline pass reproduces what ``text=True`` would have done, so routing a call site through this module does not
    silently change ``\\r\\n`` handling on Windows.
    """
    return raw.decode(ENCODING).replace("\r\n", "\n").replace("\r", "\n")


def run_exact(
    cmd: Sequence[str],
    *,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    input: str | None = None,  # pylint: disable=redefined-builtin
    check: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess:
    """Capture *cmd* as strict UTF-8 text, raising in the caller on a bad byte.

    Raises ``UnicodeDecodeError`` when the child emits bytes that are not valid UTF-8. That is the point: this entry
    point is for output whose exactness a consumer depends on, where substituting a replacement character would corrupt
    published content or misparse data.

    Decoding happens here rather than through ``encoding=`` for the reason given in the module docstring: a decode error
    on ``subprocess``'s reader thread is swallowed into a ``None`` stream, which is the failure this module exists to
    prevent rather than an acceptable way to report it.
    """
    proc = _capture(
        cmd,
        cwd=cwd,
        env=env,
        input=None if input is None else input.encode(ENCODING),
        check=False,
        timeout=timeout,
        encoding=None,
        errors=None,
    )
    completed = subprocess.CompletedProcess(
        proc.args,
        proc.returncode,
        _decode_strict(proc.stdout),
        _decode_strict(proc.stderr),
    )
    if check:
        completed.check_returncode()
    return completed


def run_diagnostic(
    cmd: Sequence[str],
    *,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    input: str | None = None,  # pylint: disable=redefined-builtin
    check: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess:
    """Capture *cmd* as UTF-8 text, substituting for undecodable bytes.

    Use for output replayed as a log or advisory line, where one unrepresentable byte in a child's output must not abort
    the surrounding run's report.
    """
    return _capture(
        cmd,
        cwd=cwd,
        env=env,
        input=input,
        check=check,
        timeout=timeout,
        encoding=ENCODING,
        errors="replace",
    )


def run_bytes(
    cmd: Sequence[str],
    *,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    input: bytes | None = None,  # pylint: disable=redefined-builtin
    check: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess:
    """Capture *cmd* without decoding, for output that is not text.

    NUL-delimited path lists (``git ls-files -z``) carry raw filesystem names: git does not apply ``core.quotepath``
    escaping in ``-z`` mode, so the bytes may not be valid UTF-8 and are not characters in the first place. Split the
    result and decode each piece with :func:`os.fsdecode`.
    """
    return _capture(
        cmd,
        cwd=cwd,
        env=env,
        input=input,
        check=check,
        timeout=timeout,
        encoding=None,
        errors=None,
    )


def configure_stdout_utf8() -> None:
    """Pin this process's piped stdout and stderr to UTF-8.

    A governed CLI consumed through a pipe is decoded strictly as UTF-8 by every capture entry point above, while a
    pipe-attached ``sys.stdout`` encodes with the ambient locale by default — ``cp1250`` on a Windows workstation. The
    pair is a crash or a silent substitution, and the CLI cannot know which consumer's shell sits at the other end, so
    the pin is a property of the CLI itself.

    A console-attached stream is left alone: it is not a byte stream, and the host renders it by its own mechanism. A
    stream that cannot be reconfigured (an in-process test harness replacing ``sys.stdout`` with a ``StringIO``) is also
    left alone, because its encoding is the harness's own choice. A stream that exposes neither probe — no ``isatty`` —
    is treated as piped: test doubles and wrapped streams reach the reconfigure path instead of crashing on the probe.
    """
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        isatty = getattr(stream, "isatty", None)
        if isatty is not None and isatty():
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding=ENCODING)
        except (ValueError, OSError):
            # A stream that refuses the pin keeps its ambient encoding; the strict
            # consumer's decode failure then names the real subject.
            continue


def utf8_child_env() -> dict[str, str]:
    """Return the ambient environment with ``PYTHONIOENCODING`` pinned to UTF-8.

    A parent spawning a Python child pins the child's pipe encodings through the environment, so the strict-UTF-8 decode
    above is correct even for a child that does not call :func:`configure_stdout_utf8` itself. The copy is deliberate:
    passing this mapping as ``env=`` replaces the child environment entirely.
    """
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = ENCODING
    return env
