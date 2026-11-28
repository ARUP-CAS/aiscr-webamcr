# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

"""gettext ``.po`` catalogue adapter for the translation-revision engine.

``polib`` is imported lazily, so JSON and Dataspecer subjects never need it. At ``load_preserving`` discovers a
reproducible wrapping profile for scoped writes; the legacy specialised operations retain their established width. Both
refuse source bytes they cannot reproduce before writing.

A written catalogue keeps first-occurrence ordering (path, line), matching the branch catalogue's convention. Plural
entries and tool-owned UI strings are carried unchanged, and the source's line ending is preserved.

Contract: review/translation-revision
Class: library
Exit codes: Library with no entrypoint; raises CatalogueError on a refusal.
"""

from __future__ import annotations

from pathlib import Path

WRAPWIDTH = 78

__all__ = [
    "CatalogueError",
    "assert_roundtrip",
    "dominant_eol",
    "dumps",
    "first_occurrence",
    "is_plural",
    "load",
    "new_entry",
    "sort_by_first_occurrence",
    "write",
]


class CatalogueError(Exception):
    """Raised when a catalogue cannot be read, round-tripped or resolved."""


def _polib():
    """Import polib on first use; JSON and Dataspecer subjects never reach here."""
    try:
        import polib  # pylint: disable=import-outside-toplevel
    except ImportError as exc:  # pragma: no cover -- only when the pin is not installed
        raise CatalogueError("polib is required for gettext catalogues but is not installed") from exc
    return polib


def dominant_eol(raw: bytes) -> str:
    """Return the file's dominant line ending, CRLF unless LF-only outnumbers CRLF."""
    crlf = raw.count(b"\r\n")
    lf_only = raw.count(b"\n") - crlf
    return "\r\n" if crlf and crlf >= lf_only else "\n"


def dumps(po, eol: str = "\n") -> bytes:
    """Render a parsed catalogue to bytes, writing its entries with *eol*."""
    text = str(po)
    if eol == "\r\n":
        text = text.replace("\n", "\r\n")
    return text.encode("utf-8")


def load(path: str | Path, wrapwidth: int = WRAPWIDTH):
    """Read a catalogue and its dominant line ending."""
    try:
        raw = Path(path).read_bytes()
        po = _polib().pofile(str(path), wrapwidth=wrapwidth)
    except (OSError, ValueError) as exc:
        raise CatalogueError(f"cannot read catalogue {path}: {exc}") from exc
    return po, dominant_eol(raw)


def assert_roundtrip(path: str | Path, wrapwidth: int = WRAPWIDTH) -> str:
    """Refuse a source the adapter cannot reproduce byte for byte; return its EOL."""
    raw = Path(path).read_bytes()
    po = _polib().pofile(str(path), wrapwidth=wrapwidth)
    eol = dominant_eol(raw)
    if dumps(po, eol) != raw:
        raise CatalogueError(f"{path} does not round-trip byte for byte at wrapwidth={wrapwidth}")
    return eol


def load_preserving(path: str | Path):
    """Discover a lossless wrapping profile; refuse non-reproducible source bytes."""
    raw = Path(path).read_bytes()
    eol = dominant_eol(raw)
    for width in dict.fromkeys([WRAPWIDTH, 0, *range(10, 201)]):
        po, _ = load(path, width)
        if dumps(po, eol) == raw:
            return po, eol
    raise CatalogueError(f"{path} does not round-trip under a supported wrapping profile")


def write(path: str | Path, po, eol: str = "\n") -> None:
    """Write a parsed catalogue with the given line ending."""
    Path(path).write_bytes(dumps(po, eol))


def new_entry(key: str, value: str):
    """Create a singular entry for a new, approved ledger key."""
    return _polib().POEntry(msgid=key, msgstr=value)


def first_occurrence(entry) -> tuple[str, int]:
    """Return (path, line) of an entry's first occurrence, for ordering."""
    if not entry.occurrences:
        return "", 0
    path, line = entry.occurrences[0]
    try:
        number = int(line)
    except (TypeError, ValueError):
        number = 0
    return path, number


def sort_by_first_occurrence(entries: list) -> list:
    """Order entries by their first occurrence (path, line)."""
    return sorted(entries, key=first_occurrence)


def is_plural(entry) -> bool:
    """Return whether the entry carries plural translations."""
    return bool(entry.msgid_plural)
