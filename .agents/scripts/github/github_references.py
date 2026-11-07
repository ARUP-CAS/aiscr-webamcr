# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: c35418343fe8896348732bd54f8256de17338f8d 2026-11-07T14:33:16+01:00

"""Check repository identity in outgoing GitHub issue and pull-request citations.

The checker is portable and pure: it neither acquires source nor changes text. A caller that preserves human text
supplies independently acquired source snapshots and exact, payload-bound spans. Body markers never establish trust.
Ordinary code fences are inspected; a ``github-reference-example`` fence instead holds one JSON input/expected case
whose diagnostic codes are checked before its exact literal input is admitted as an example.

Contract: documentation/github-reference-integrity
Class: library
Exit codes: Library module; returns diagnostics without performing I/O.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections.abc import Mapping, Sequence
from typing import NamedTuple
from urllib.parse import urlsplit

_NAME = r"[A-Za-z0-9_.-]+"
_IDENTITY = re.compile(rf"(?P<repo>{_NAME}/{_NAME})#(?P<number>[1-9][0-9]*)")
_TARGET = re.compile(rf"/(?P<repo>{_NAME}/{_NAME})/(?P<kind>issues|pull)/(?P<number>[1-9][0-9]*)(?P<tail>/.*)?")
_REFERENCE = re.compile(rf"(?<![\w/#])(?:GH-[0-9]+|(?:{_NAME}(?:/{_NAME})?)?#[0-9]+)\b", re.I)
_URL = re.compile(r"https?://[^\s<>\"\]]+")
_GITHUB_ITEM_URL = re.compile(r"https?://(?:www\.)?github\.com/[^/\s]+/[^/\s]+/(?:issues|pull)/", re.I)
_INLINE = re.compile(
    r"(?P<image>!)?\[(?P<label>(?:\\.|[^\]\\\n])*)\]\(\s*"
    r"(?P<url><[^>\n]+>|(?:\\.|[^\s)\\])+)(?:[ \t]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^\)\n]*\)))?\s*\)"
)
_DEFINITION = re.compile(r"^ {0,3}\[(?P<id>(?:\\.|[^\]\\\n])+)\]:[ \t]*(?P<url><[^>\n]+>|\S+)", re.M)
_INDIRECT = re.compile(r"(?P<image>!)?\[(?P<label>(?:\\.|[^\]\\\n])+)\](?:\[(?P<id>(?:\\.|[^\]\\\n])*)\])?")
_EXAMPLE = re.compile(
    r"^ {0,3}(?P<fence>`{3,}|~{3,})github-reference-example[ \t]*\r?\n"
    r"(?P<payload>.*?)\r?\n {0,3}(?P=fence)[ \t]*(?=\r?\n|$)",
    re.M | re.S,
)
_EXAMPLE_OPEN = re.compile(r"^ {0,3}(?:`{3,}|~{3,})github-reference-example\b[^\n]*", re.M)
_ENCODED = re.compile(r"(?:&#0*35;|&#x0*23;|&num;)[0-9]+\b", re.I)
_LOCAL_FRAGMENT = re.compile(r"[\w./-]+\.(?:md|html?)#[0-9]+\b", re.I)
_COLOR_PREFIX = re.compile(r"\b(?:color|background(?:-color)?|fill|stroke)(?:\s*[:=])?\s*['\"]?$", re.I)
_ESCAPE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])")
DIAGNOSTIC_CODES = frozenset(
    {
        "unqualified-reference",
        "unlinked-reference",
        "unlinked-url",
        "reference-target",
        "reference-mismatch",
        "invalid-example",
        "invalid-exemption",
    }
)


class Diagnostic(NamedTuple):
    """One located, actionable violation; syntax checks do not prove remote existence."""

    source: str
    line: int
    column: int
    code: str
    text: str
    message: str

    def render(self) -> str:
        """Render the same diagnostic for payload fields and files."""
        return f"{self.source}:{self.line}:{self.column}: {self.code}: {self.message} [{self.text!r}]"


class SourceSnapshot(NamedTuple):
    """Source acquired by the engine, with its complete preservable machine fragments."""

    repository: str
    text: str
    fragments: tuple[str, ...] = ()


class SourceSpan(NamedTuple):
    """An exact source extent bound to both the source snapshot and outgoing payload."""

    start: int
    end: int
    source_id: str
    source_digest: str
    payload_digest: str
    fragment: str


def text_digest(text: str) -> str:
    """Use the posting engines' payload identity with exactly one terminal LF."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def snapshot_digest(snapshot: SourceSnapshot) -> str:
    """Bind the repository, complete source, and admitted complete fragments together."""
    return text_digest(json.dumps(snapshot, ensure_ascii=False))


def reference_target(destination: str) -> tuple[str, str] | None:
    """Identify supported absolute GitHub item/comment destinations without rewriting them."""
    if re.search(r"[\x00-\x20\x7f]", destination):
        return None
    try:
        parsed = urlsplit(destination)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None
    match = _TARGET.fullmatch(parsed.path)
    if match is None:
        return None
    tail = match["tail"]
    if tail and (match["kind"] != "pull" or not re.fullmatch(r"/(?:files|commits)(?:/[0-9a-fA-F]{7,64})?", tail)):
        return None
    return match["repo"], match["number"]


def reference_link(destination: str) -> str:
    """Give engine-generated source links a visible identity, preserving their exact target."""
    target = reference_target(destination)
    return f"[{target[0]}#{target[1]}]({destination})" if target else destination


def _unescape(text: str) -> str:
    return html.unescape(_ESCAPE.sub(r"\1", text))


def _reference_key(value: str) -> str:
    return " ".join(_unescape(value).split()).casefold()


def _escaped(text: str, position: int) -> bool:
    prefix = text[:position]
    return (len(prefix) - len(prefix.rstrip("\\"))) % 2 == 1


def _inside(span: tuple[int, int], ranges: Sequence[tuple[int, int]]) -> bool:
    return any(start <= span[0] and span[1] <= end for start, end in ranges)


def _source_ranges(
    text: str,
    spans: Sequence[SourceSpan],
    sources: Mapping[str, SourceSnapshot],
) -> tuple[list[tuple[int, int]], list[tuple[int, str, str, str]]]:
    ranges: list[tuple[int, int]] = []
    errors: list[tuple[int, str, str, str]] = []
    for span in spans:
        if not isinstance(span, SourceSpan):
            errors.append((0, "invalid-exemption", "unverified span", "Supply engine-verified source evidence."))
            continue
        snapshot = sources.get(span.source_id)
        valid = (
            isinstance(snapshot, SourceSnapshot)
            and re.fullmatch(rf"{_NAME}/{_NAME}", snapshot.repository) is not None
            and isinstance(span.start, int)
            and not isinstance(span.start, bool)
            and isinstance(span.end, int)
            and not isinstance(span.end, bool)
            and 0 <= span.start < span.end <= len(text)
            and span.source_digest == snapshot_digest(snapshot)
            and span.payload_digest == text_digest(text)
            and span.fragment in (snapshot.text, *snapshot.fragments)
            and text[span.start : span.end] == span.fragment
            and snapshot.repository.lower() in (text[: span.start] + text[span.end :]).lower()
            and not any(span.start < end and start < span.end for start, end in ranges)
        )
        if valid:
            ranges.append((span.start, span.end))
        else:
            errors.append(
                (
                    0,
                    "invalid-exemption",
                    span.source_id,
                    "Reacquire source, retain visible repository context, and verify the exact payload span.",
                )
            )
    return ranges, errors


def _example_ranges(
    text: str,
    protected: Sequence[tuple[int, int]],
    enabled: bool,
) -> tuple[list[tuple[int, int]], list[tuple[int, str, str, str]]]:
    ranges: list[tuple[int, int]] = []
    errors: list[tuple[int, str, str, str]] = []
    for match in _EXAMPLE.finditer(text):
        if _inside(match.span(), protected):
            continue
        ranges.append(match.span())
        valid = False
        if enabled:
            try:
                case = json.loads(match["payload"])
            except ValueError:
                case = None
            if (
                isinstance(case, dict)
                and set(case) == {"input", "expected"}
                and isinstance(case["input"], str)
                and isinstance(case["expected"], list)
                and all(isinstance(code, str) and code in DIAGNOSTIC_CODES for code in case["expected"])
            ):
                valid = [item.code for item in check_references(case["input"], examples=False)] == case["expected"]
        if not valid:
            errors.append(
                (
                    match.start(),
                    "invalid-example",
                    match["payload"],
                    "Use one JSON input/expected case with its exact diagnostic codes.",
                )
            )
    for opener in _EXAMPLE_OPEN.finditer(text):
        if not _inside(opener.span(), [*protected, *ranges]):
            errors.append(
                (opener.start(), "invalid-example", opener.group(), "Close the bounded syntax-example fence.")
            )
    return ranges, errors


def _link_error(label: str, destination: str, image: bool) -> tuple[str, str] | None:  # pylint: disable=too-many-return-statements
    visible = _unescape(label).strip().strip("`")
    identity = _IDENTITY.fullmatch(visible)
    target = reference_target(destination)
    if destination.startswith("#") and identity is None:
        return None  # local document anchor, not a GitHub issue citation
    if target is None:
        if _REFERENCE.search(visible) or _GITHUB_ITEM_URL.match(destination):
            return "reference-target", "Use a supported absolute HTTPS GitHub issue or PR destination."
        return None
    if image:
        return "reference-target", "An image does not display a linked repository-qualified citation."
    if identity is None:
        return "unqualified-reference", "Use a linked owner/repo#N label, including for same-repository items."
    if (identity["repo"].lower(), identity["number"]) != (target[0].lower(), target[1]):
        return "reference-mismatch", "Make the visible repository and number match the destination."
    return None


def _markdown_ranges(
    text: str,
    protected: Sequence[tuple[int, int]],
) -> tuple[list[tuple[int, int]], list[tuple[int, str, str, str]]]:
    ranges = list(protected)
    errors: list[tuple[int, str, str, str]] = []
    definitions = list(_DEFINITION.finditer(text))
    by_id: dict[str, re.Match[str]] = {}
    for definition in definitions:
        if not _inside(definition.span(), protected):
            by_id.setdefault(_reference_key(definition["id"]), definition)
    for match in _INLINE.finditer(text):
        if _inside(match.span(), protected) or _escaped(text, match.start("label") - 1):
            continue
        destination = _unescape(match["url"].strip("<>"))
        error = _link_error(match["label"], destination, bool(match["image"]) and not _escaped(text, match.start()))
        if error:
            errors.append((match.start(), error[0], match.group(), error[1]))
        ranges.extend([match.span("label"), match.span("url")])
    for match in _INDIRECT.finditer(text):
        if (
            _inside(match.span("label"), ranges)
            or _escaped(text, match.start("label") - 1)
            or any(_inside(match.span(), [item.span()]) for item in definitions)
        ):
            continue
        identity = match["id"] if match["id"] else match["label"]
        definition = by_id.get(_reference_key(identity))
        if definition is None:
            continue
        error = _link_error(
            match["label"],
            _unescape(definition["url"].strip("<>")),
            bool(match["image"]) and not _escaped(text, match.start()),
        )
        if error:
            errors.append((match.start(), error[0], match.group(), error[1]))
        ranges.extend([match.span(), definition.span("id"), definition.span("url")])
    return ranges, errors


def _raw_errors(text: str, protected: Sequence[tuple[int, int]]) -> list[tuple[int, str, str, str]]:
    ranges = list(protected)
    errors: list[tuple[int, str, str, str]] = []
    for match in _URL.finditer(text):
        url = match.group().rstrip(".,;:)")
        if not _inside((match.start(), match.start() + len(url)), ranges):
            if _GITHUB_ITEM_URL.match(url):
                code = "unlinked-url" if reference_target(url) else "reference-target"
                errors.append((match.start(), code, url, "Use [owner/repo#N](absolute-item-or-comment-URL)."))
        ranges.append(match.span())
    ranges.extend(match.span() for match in _LOCAL_FRAGMENT.finditer(text))
    for match in _REFERENCE.finditer(text):
        if _inside(match.span(), ranges):
            continue
        token = match.group()
        prefix, suffix = text[: match.start()], text[match.end() :]
        if token.startswith("#") and prefix.endswith("&") and suffix.startswith(";"):
            continue  # an HTML entity, not its decoded text
        if token.startswith("#") and _COLOR_PREFIX.search(prefix) and re.fullmatch(r"#[0-9a-fA-F]{3,8}", token):
            continue
        if _IDENTITY.fullmatch(token) and re.search(
            r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s*$", prefix, re.I
        ):
            continue
        code = "unlinked-reference" if _IDENTITY.fullmatch(token) else "unqualified-reference"
        errors.append((match.start(), code, token, "Use [owner/repo#N](absolute-item-or-comment-URL)."))
    for match in _ENCODED.finditer(text):
        if not _inside(match.span(), ranges):
            errors.append(
                (
                    match.start(),
                    "unqualified-reference",
                    match.group(),
                    "Encoding a hash does not qualify its repository.",
                )
            )
    return errors


def check_references(
    text: str,
    *,
    source: str = "<text>",
    spans: Sequence[SourceSpan] = (),
    sources: Mapping[str, SourceSnapshot] | None = None,
    examples: bool = True,
) -> list[Diagnostic]:
    """Check all narrative citations, admitting only verified bounded exceptions."""
    protected, errors = _source_ranges(text, spans, sources or {})
    example_ranges, example_errors = _example_ranges(text, protected, examples)
    protected.extend(example_ranges)
    ranges, link_errors = _markdown_ranges(text, protected)
    errors.extend([*example_errors, *link_errors, *_raw_errors(text, ranges)])
    diagnostics = [
        Diagnostic(source, text.count("\n", 0, start) + 1, start - text.rfind("\n", 0, start), code, token, message)
        for start, code, token, message in errors
    ]
    return sorted(diagnostics, key=lambda item: (item.line, item.column, item.code))
