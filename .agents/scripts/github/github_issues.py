#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00

"""Gather, verify, and write governed GitHub issue bodies.

``gather`` is read-only: it returns the issue's whole conversation, including resolved and hidden comments, plus one hop
of referenced issues and pull requests and every hierarchy edge. ``reconciliation-sources`` emits the labelled source
list local verification and the write consume. ``verify-composition`` checks a developed body locally, with no network
and no write: its shape and its reconciliation accounting. ``post-body`` writes the description only after that same
check passes. ``extract`` files the issue for content that belongs elsewhere, before a ledger can reference it.
``post-comment`` posts a live-acceptance run's verification comment on the driving issue, in the issue's own language
and under exact-content approval.

Posting is supervised only. The command surface declares ``interactive`` as its one mode rather than accepting one it
does not implement. ``prepare-handoff`` creates a confined visible run directory and its bulk pointer before body
authoring; ``cleanup-handoff --approve`` retires its allowlisted files after a successful terminal outcome. Approval
views can still print to stdout, but posting also reads their rendered file and refuses missing or edited bytes.

The write model — identity mode, machine marker, approval digest, and the accounting rules — is shared through
``github_utils`` rather than reimplemented here.

Contract: workflow/github-issue-lifecycle, workflow/github-write-fidelity, review/live-acceptance-verification
Class: tool
Exit codes: 0 success; 1 not-ready/composition findings or refused write; 2 usage error
"""

# pylint: disable=too-many-lines

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from lib import local_scratch_paths  # noqa: E402
from lib.proc_utils import configure_stdout_utf8  # noqa: E402

from github import github_references, github_utils  # noqa: E402

ISSUE_MARKER = "<!-- aiscr-plan-issue:body -->"
REPO_ROOT = Path(_SCRIPTS_DIR).parents[1]
HANDOFF_ARTIFACTS = {
    "issue": frozenset(
        {
            "POINTER.md",
            "original-description.md",
            "archive-approval.json",
            "stub.md",
            "extract-approval.json",
            "body.md",
            "post-body-approval.json",
            "create-approval.json",
        }
    ),
    "draft-pr": frozenset({"POINTER.md", "pr-body.md", "draft-pr-approval.json"}),
    "comment": frozenset({"POINTER.md", "comment.md", "comment-approval.json"}),
}
ISSUE_MARKER_PATTERN = re.compile(r"<!-- aiscr-plan-issue:body(?: digest=([0-9a-f]{64}))? -->")
# One owning home for "what counts as the title": the shape check enforces exactly one
# such heading and ``issue_title`` derives the GitHub title from the same pattern.
TITLE_PATTERN = re.compile(r"#\s+(\S.*)")
REPORTER_CONTEXT_OPEN = "<!-- aiscr-plan-issue:reporter-context -->"
REPORTER_CONTEXT_CLOSE = "<!-- /aiscr-plan-issue:reporter-context -->"
PROVENANCE_MARKER = "<!-- aiscr-plan-issue:provenance -->"
LEDGER_MARKER = "<!-- aiscr-plan-issue:ledger -->"
PROVENANCE_ORIGINAL_OPEN = "<!-- aiscr-plan-issue:original -->"
PROVENANCE_ORIGINAL_CLOSE = "<!-- /aiscr-plan-issue:original -->"
INTERACTIVE_DISCLOSURE = (
    "This issue description was developed with AI assistance through the AIS CR issue "
    "workflow; the posting maintainer reviewed and approved it."
)
# Supervised posting only, declared rather than guarded: the contract carries no
# automated disclosure, so the shared lookup refuses that mode for this surface.
ISSUE_MODES = ("interactive",)
ISSUE_CONTRACT = github_utils.PostingContract(
    marker=ISSUE_MARKER,
    interactive_disclosure=INTERACTIVE_DISCLOSURE,
)
EXTRACTION_LINKS = ("sub-issue", "cross-reference")

PROMOTION_MARKER = "<!-- aiscr-plan-from-issue:promotion -->"
PROMOTION_DISCLOSURE = (
    "This pull request was opened by the AIS CR issue-promotion workflow with AI "
    "assistance; the promoting maintainer reviewed and approved its content."
)
PROMOTION_CONTRACT = github_utils.PostingContract(
    marker=PROMOTION_MARKER,
    interactive_disclosure=PROMOTION_DISCLOSURE,
)
# The live-acceptance comment surface: a run's findings posted on the driving
# issue, in that issue's language. Supervised posting only, like every surface
# here; the shared lookup refuses an automated mode the contract does not declare.
COMMENT_MARKER = "<!-- aiscr-review-live:comment -->"
COMMENT_INTERACTIVE_DISCLOSURE = (
    "This acceptance-verification comment was posted by the AIS CR live-acceptance "
    "workflow with AI assistance; the posting maintainer reviewed and approved it."
)
COMMENT_CONTRACT = github_utils.PostingContract(
    marker=COMMENT_MARKER,
    interactive_disclosure=COMMENT_INTERACTIVE_DISCLOSURE,
)
_abort = github_utils.abort
_gh = github_utils.gh
_try_run = github_utils.try_run
_resolve_repo = github_utils.resolve_repo
_load_json = github_utils.load_json
_temporary_json = github_utils.temporary_json
_validate_write_environment = github_utils.validate_write_environment
_canonical_digest = github_utils.canonical_digest
_paginated_rest_items = github_utils.paginated_rest_items
_paginated_graphql_nodes = github_utils.paginated_graphql_nodes
detect_load_bearing = github_utils.detect_load_bearing
APPROVAL_OPERATIONS = ("archive-description", "create", "post-body", "post-comment", "extract", "open-draft-pr")

ISSUE_QUERY = """
query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    issue(number:$number) {
      title state body createdAt url
      author { login }
      parent { number repository { nameWithOwner } }
    }
  }
}
"""

ISSUE_COMMENTS_QUERY = """
query($owner:String!, $name:String!, $number:Int!, $endCursor:String) {
  repository(owner:$owner, name:$name) {
    issue(number:$number) {
      comments(first:100, after:$endCursor) {
        nodes { databaseId body createdAt url isMinimized minimizedReason author { login } }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

ISSUE_SUB_ISSUES_QUERY = """
query($owner:String!, $name:String!, $number:Int!, $endCursor:String) {
  repository(owner:$owner, name:$name) {
    issue(number:$number) {
      subIssues(first:50, after:$endCursor) {
        nodes { number repository { nameWithOwner } }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

# ---------------------------------------------------------------------------
# The developed issue shape
#
# Derived backwards from what promotion consumes: `Problem` seeds an OpenSpec
# proposal's *Why*, `Scope` its scope and impact, `Acceptance criteria` the spec
# scenarios, and `Open questions` the design record. One universal shape was
# rejected because a bug and a feature need materially different evidence and
# forcing one shape produces empty sections, so the core stays uniform while a
# single type block carries the differing part.
#
# Every heading and metadata label declares its accepted per-language forms in
# this one place. Localising a heading must not require a validator change, and an
# undeclared form must fail rather than pass silently. Metadata *values* that a
# machine selects on — the `Type` token — stay fixed, like a domain entity name.
# ---------------------------------------------------------------------------

TABLE_HEADER_FORMS = ("| Field | Value |", "| Pole | Hodnota |")
METADATA_FORMS: dict[str, tuple[str, ...]] = {
    "Type": ("Type", "Typ"),
    "Affects": ("Affects", "Dotčená oblast"),
    "Reported by": ("Reported by", "Nahlásil"),
    "Reproducibility": ("Reproducibility", "Reprodukovatelnost"),
}
REQUIRED_METADATA = ("Type", "Affects", "Reported by")
BUG_METADATA = "Reproducibility"
SECTION_FORMS: dict[str, tuple[str, ...]] = {
    "Problem": ("Problem", "Problém"),
    "Scope": ("Scope", "Rozsah"),
    "Acceptance criteria": ("Acceptance criteria", "Akceptační kritéria"),
    "Open questions": ("Open questions", "Otevřené otázky"),
    "Reporter context": ("Reporter context", "Kontext ohlašovatele"),
}
TYPE_BLOCK_FORMS: dict[str, tuple[str, ...]] = {
    "bug": ("Reproduction", "Reprodukce"),
    "feature": ("Motivation and alternatives", "Motivace a alternativy"),
    "task": ("Work outline", "Plánovaný postup"),
}
ISSUE_TYPES = tuple(TYPE_BLOCK_FORMS)

# The acceptance comment's heading forms, declared per language in the same place
# as the issue shape it answers. The comment follows the driving issue's language,
# so every heading exists in each supported language and a body mixing languages
# is refused rather than posted half-translated. Domain entity names stay verbatim
# in both, like the fixed `Type` token above.
COMMENT_SECTION_FORMS: dict[str, tuple[str, ...]] = {
    "Summary": ("Summary", "Souhrn"),
    "Verified behaviour": ("Verified behaviour", "Ověřené chování"),
    "Findings": ("Findings", "Zjištění"),
    "Maintainer-assisted checks": ("Maintainer-assisted checks", "Kontroly vyžadující správce"),
    "Unverified": ("Unverified", "Neověřeno"),
}
COMMENT_REQUIRED_SECTIONS = ("Summary", "Verified behaviour")
# Per-section list-form rules, in both directions: sections carrying only what a
# maintainer still has to act on render task lists; settled sections render plain
# lists, so a completed statement never displays as an open obligation.
COMMENT_TASK_LIST_SECTIONS = ("Findings", "Maintainer-assisted checks")
COMMENT_PLAIN_LIST_SECTIONS = ("Verified behaviour", "Unverified")
_TASK_LIST_PATTERN = re.compile(r"^\s*[-*] \[[ xX]\](?:\s|$)")
# CommonMark renders a marker with zero to three leading spaces as a top-level
# list item; deeper indentation is structural (a child of an earlier item or
# code content). The outstanding-section task rule binds those top-level items.
_LIST_ITEM_PATTERN = re.compile(r"^( {0,3})[-*] ")
_TOP_LEVEL_TASK_PATTERN = re.compile(r"^ {0,3}[-*] \[[ xX]\](?:\s|$)")
# The core sections in order. The type block sits between `Problem` and `Scope`:
# the observation comes first, then the evidence its type calls for.
CORE_SECTIONS = ("Problem", "Scope", "Acceptance criteria", "Open questions", "Reporter context")
TYPE_BLOCK_AFTER = "Problem"


def declared_section_names() -> frozenset[str]:
    """Every accepted section name, in every declared language.

    A ledger routes an absorbed segment to a section by name, so the checker needs the same declaration the validator
    uses rather than a second copy of it.
    """
    names = {form for forms in SECTION_FORMS.values() for form in forms}
    names.update(form for forms in TYPE_BLOCK_FORMS.values() for form in forms)
    return frozenset(names)


class _ShapeError(Exception):
    """A structural defect in a developed issue body."""


def _read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return handle.read().replace("\r\n", "\n").replace("\r", "\n")
    except OSError as exc:
        _abort(f"cannot read '{path}': {exc}")


def _normalized_marker_body(body: str) -> str:
    return ISSUE_MARKER_PATTERN.sub(ISSUE_MARKER, body)


def body_digest(body: str) -> str:
    """Digest the whole body, independently of the stamp in its marker."""
    return github_utils.text_digest(_normalized_marker_body(body))


def stamp_digest(body: str) -> str:
    return ISSUE_MARKER_PATTERN.sub(f"<!-- aiscr-plan-issue:body digest={body_digest(body)} -->", body, count=1)


def posted_digest(body: str) -> str | None:
    match = ISSUE_MARKER_PATTERN.search(body or "")
    return match.group(1) if match else None


def body_state(body: str) -> dict[str, Any]:
    """Classify an issue description for the reconciliation decision."""
    workflow_owned = ISSUE_MARKER_PATTERN.search(body or "") is not None
    stamped = posted_digest(body)
    edited_since_post: bool | None = None
    if workflow_owned and stamped:
        edited_since_post = body_digest(body) != stamped
    return {
        "workflow_owned": workflow_owned,
        "posted_digest": stamped,
        "edited_since_post": edited_since_post,
        "load_bearing": detect_load_bearing(body or ""),
        "is_empty": not (body or "").strip(),
    }


def _find_provenance_comment(comments: list[dict[str, Any]]) -> dict[str, Any] | None:
    marked = [comment for comment in comments if PROVENANCE_MARKER in str(comment.get("body") or "")]
    if not marked:
        return None
    return marked[0]


def _provenance_original(comment: dict[str, Any]) -> str:
    original = github_utils.read_region(
        str(comment.get("body") or ""), PROVENANCE_ORIGINAL_OPEN, PROVENANCE_ORIGINAL_CLOSE
    )
    if original is None:
        _abort("the marked issue provenance comment has no delimited original description.")
    return original


def _render_provenance(
    original: str,
    ledger: dict[str, Any] | None = None,
    *,
    source: str = "",
    author: str = "",
) -> str:
    """Keep the reporter original immutable and the current ledger replaceable."""
    header = [
        PROVENANCE_MARKER,
        "",
        "# Issue description provenance",
        "",
    ]
    if source:
        header.append(f"- Source: {github_references.reference_link(source)}")
    if author:
        header.append(f"- Author: {author}")
    if source or author:
        header.append("")
    return (
        "\n".join(
            [
                *header,
                "## Original reporter description (verbatim)",
                "",
                github_utils.wrap_region(PROVENANCE_ORIGINAL_OPEN, original, PROVENANCE_ORIGINAL_CLOSE),
                "",
                github_utils.render_disposition_ledger(ledger or {}, LEDGER_MARKER),
            ]
        ).rstrip()
        + "\n"
    )


def _description_edit_sources(previous: str, current: str) -> list[tuple[str, str]]:
    """Return only externally changed hunks, never the unchanged generated body."""
    return github_utils.description_edit_sources(previous, current, _normalized_marker_body)


# ---------------------------------------------------------------------------
# Structural validation
#
# At pull-request parity, and for the same reason: the accounting checks verify
# that nothing was lost from the original, which a faithfully preserved two-line
# issue satisfies. Conservation is not construction, so the shape is checked too.
# ---------------------------------------------------------------------------


def _section_has_content(lines: list[str], start: int, end: int) -> bool:
    return any(line.strip() for line in lines[start + 1 : end])


def _heading_index(lines: list[str], section: str, forms: tuple[str, ...]) -> int:
    accepted = {f"## {form}" for form in forms}
    indexes = [index for index, line in enumerate(lines) if line.strip() in accepted]
    if len(indexes) != 1:
        raise _ShapeError(f"issue body must contain exactly one '{section}' heading; accepted: {', '.join(accepted)}.")
    return indexes[0]


def _metadata_rows(lines: list[str]) -> dict[str, tuple[int, str]]:
    """Locate each declared metadata field, in any of its declared languages."""
    found: dict[str, tuple[int, str]] = {}
    for field, forms in METADATA_FORMS.items():
        matches = [
            (index, match.group(1))
            for index, line in enumerate(lines)
            for form in forms
            if (match := re.fullmatch(rf"\|\s*{re.escape(form)}\s*\|\s*(\S.*?)\s*\|", line.strip()))
        ]
        if len(matches) > 1:
            raise _ShapeError(f"issue metadata declares the '{field}' row more than once.")
        if matches:
            found[field] = matches[0]
    return found


def _validate_preamble(body: str) -> tuple[list[str], int]:
    """Exactly one marker, first; exactly one title; the disclosure exactly once."""
    if len(ISSUE_MARKER_PATTERN.findall(body)) != 1:
        raise _ShapeError("issue body must contain exactly one AIS CR issue marker.")
    if body.count(INTERACTIVE_DISCLOSURE) != 1:
        raise _ShapeError("issue body must contain exactly one AI-assistance disclosure.")

    lines = body.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    marker_indexes = [index for index, line in enumerate(lines) if ISSUE_MARKER_PATTERN.fullmatch(line.strip())]
    if len(marker_indexes) != 1:
        raise _ShapeError("issue body marker must stand alone on its own line.")
    first_content_index = next((index for index, line in enumerate(lines) if line.strip()), None)
    if marker_indexes[0] != first_content_index:
        raise _ShapeError("issue body marker must be the first non-empty line.")

    title_indexes = [index for index, line in enumerate(lines) if TITLE_PATTERN.fullmatch(line.strip())]
    if len(title_indexes) != 1:
        raise _ShapeError("issue body must contain exactly one '# ' title stating the symptom or outcome.")
    return lines, title_indexes[0]


def issue_title(body: str) -> str:
    """Derive the GitHub title from the body's single ``# `` heading.

    The title is not a separate field to set by hand. The shape contract already declares that heading to be "the text a
    person would search for", so a GitHub title that differs from it is a defect rather than a choice: the body renders
    on the issue page while the title is what search, lists and cross-references show. Deriving it here — from the same
    pattern the shape check enforces — removes the divergence instead of adding a flag to remember. Returns "" when no
    heading is present, which the shape check reports on its own.
    """
    for line in (body or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        match = TITLE_PATTERN.fullmatch(line.strip())
        if match:
            return match.group(1).strip()
    return ""


def _validate_metadata(lines: list[str], title_index: int, problem_index: int) -> str:
    """Return the declared metadata table, and the `Type` row that selects the block."""
    header_indexes = [index for index, line in enumerate(lines) if line.strip() in TABLE_HEADER_FORMS]
    if len(header_indexes) != 1:
        raise _ShapeError(f"issue body must contain exactly one metadata table header; accepted: {TABLE_HEADER_FORMS}.")
    separator_indexes = [
        index for index, line in enumerate(lines) if re.fullmatch(r"\|\s*---\s*\|\s*---\s*\|", line.strip())
    ]
    if len(separator_indexes) != 1:
        raise _ShapeError("issue body must contain exactly one two-column metadata table separator.")
    if not title_index < header_indexes[0] < separator_indexes[0] < problem_index:
        raise _ShapeError("issue metadata table must sit between the title and the first section.")

    rows = _metadata_rows(lines)
    missing = [field for field in REQUIRED_METADATA if field not in rows]
    if missing:
        raise _ShapeError(f"issue metadata is missing a non-empty row for: {', '.join(missing)}.")

    issue_type = rows["Type"][1].strip().strip("`")
    if issue_type not in ISSUE_TYPES:
        raise _ShapeError(f"issue metadata 'Type' must be one of: {', '.join(ISSUE_TYPES)}; found {issue_type!r}.")
    if issue_type == "bug" and BUG_METADATA not in rows:
        raise _ShapeError(f"an issue of type 'bug' must declare a non-empty '{BUG_METADATA}' row.")

    row_indexes = [index for index, _ in rows.values()]
    if row_indexes != sorted(row_indexes):
        raise _ShapeError("issue metadata rows are out of order.")
    if not all(separator_indexes[0] < index < problem_index for index in row_indexes):
        raise _ShapeError("issue metadata rows must remain inside the metadata table.")
    return issue_type


def _validate_sections(lines: list[str], issue_type: str) -> list[int]:
    """Return the core sections in order, with the block the declared `Type` selects."""
    for other, forms in TYPE_BLOCK_FORMS.items():
        if other == issue_type:
            continue
        accepted = {f"## {form}" for form in forms}
        if any(line.strip() in accepted for line in lines):
            raise _ShapeError(
                f"issue declares 'Type: {issue_type}' but carries the '{other}' block; "
                f"a block belonging to another type does not satisfy the requirement."
            )

    ordered: list[tuple[str, tuple[str, ...]]] = []
    for section in CORE_SECTIONS:
        ordered.append((section, SECTION_FORMS[section]))
        if section == TYPE_BLOCK_AFTER:
            ordered.append((f"{issue_type} block", TYPE_BLOCK_FORMS[issue_type]))
    indexes = [_heading_index(lines, section, forms) for section, forms in ordered]
    if indexes != sorted(indexes):
        raise _ShapeError("issue core sections are out of order.")
    return indexes


def _validate_section_bodies(lines: list[str], section_indexes: list[int], end_index: int) -> None:
    """Return a section with nothing to record says so; none may be silently blank."""
    bounds = section_indexes + [end_index]
    for position, start in enumerate(section_indexes):
        if not _section_has_content(lines, start, bounds[position + 1]):
            raise _ShapeError(
                f"issue section '{lines[start].strip()}' must not be empty; "
                "state explicitly that there is nothing to record."
            )


def _validate_reporter_region(lines: list[str], reporter_index: int, end_index: int) -> None:
    """Return the carried-fragment region is delimited so regeneration stays deterministic."""
    open_indexes = [index for index, line in enumerate(lines) if line.strip() == REPORTER_CONTEXT_OPEN]
    close_indexes = [index for index, line in enumerate(lines) if line.strip() == REPORTER_CONTEXT_CLOSE]
    if len(open_indexes) != 1 or len(close_indexes) != 1:
        raise _ShapeError("issue body must delimit the reporter-context region exactly once.")
    if not reporter_index < open_indexes[0] < close_indexes[0] < end_index:
        raise _ShapeError("issue reporter-context markers must sit inside the reporter-context section.")
    if not _section_has_content(lines, open_indexes[0], close_indexes[0]):
        raise _ShapeError(
            "issue reporter-context region must state the carried content, or say so explicitly when there is none."
        )


def _validate_mermaid(lines: list[str]) -> None:
    """Whichever diagrams are present use a GitHub-renderable family.

    Any core Mermaid family GitHub renders is accepted; only a plugin-only family is refused. Whether a diagram is
    *warranted* is not decidable, so nothing here counts them: an issue may carry several, of the same or different
    types, or none.
    """
    for start, line in enumerate(lines):
        if line.strip().lower() != "```mermaid":
            continue
        end = next((index for index in range(start + 1, len(lines)) if lines[index].strip() == "```"), None)
        if end is None:
            raise _ShapeError("issue Mermaid diagram is missing its closing fence.")
        diagram = [entry.strip() for entry in lines[start + 1 : end] if entry.strip()]
        if not diagram:
            raise _ShapeError("issue Mermaid diagram is empty.")
        refusal = github_utils.unsupported_mermaid_family("\n".join(lines[start + 1 : end]))
        if refusal is not None:
            raise _ShapeError(refusal)


def _validate_footer(lines: list[str]) -> int:
    """Return the disclosure is the final non-empty line; return its index."""
    disclosure_indexes = [index for index, line in enumerate(lines) if line.strip() == INTERACTIVE_DISCLOSURE]
    if len(disclosure_indexes) != 1:
        raise _ShapeError("issue AI-assistance disclosure must stand alone on its own line.")
    last_content_index = max(index for index, line in enumerate(lines) if line.strip())
    if disclosure_indexes[0] != last_content_index:
        raise _ShapeError("issue AI-assistance disclosure must be the final non-empty line.")
    return disclosure_indexes[0]


def _validate_shape(body: str) -> None:
    lines, title_index = _validate_preamble(body)
    problem_index = _heading_index(lines, "Problem", SECTION_FORMS["Problem"])
    issue_type = _validate_metadata(lines, title_index, problem_index)
    section_indexes = _validate_sections(lines, issue_type)
    disclosure_index = _validate_footer(lines)
    _validate_section_bodies(lines, section_indexes, disclosure_index)
    _validate_reporter_region(lines, section_indexes[-1], disclosure_index)
    _validate_mermaid(lines)


def shape_findings(body: str) -> list[dict[str, str]]:
    """Structural findings for a developed description; empty means the shape holds."""
    try:
        _validate_shape(body)
    except _ShapeError as exc:
        return [{"kind": "body-out-of-shape", "detail": str(exc)}]
    return []


def _comment_heading_section(heading: str) -> str | None:
    """Map a declared comment heading to its canonical section name."""
    for section, forms in COMMENT_SECTION_FORMS.items():
        if heading in {f"## {form}" for form in forms}:
            return section
    return None


def _comment_headings_share_one_language(headings: list[str]) -> bool:
    """Return True when every heading is a form of the same language position.

    The comment answers one issue, so it is written in one language; a body whose headings mix the declared languages is
    refused rather than posted half-translated.
    """
    positions: set[int] = set()
    for heading in headings:
        for forms in COMMENT_SECTION_FORMS.values():
            for position, form in enumerate(forms):
                if heading == f"## {form}":
                    positions.add(position)
    return len(positions) <= 1


def _validate_comment_shape(body: str) -> None:
    """Return the declared acceptance-comment shape: one language, one marker, ordered sections.

    The comment is a summary a maintainer reads on the issue it answers, so its shape is lighter than a description's:
    no metadata table, no title. What it must carry is the run's verification result — at minimum what was checked and
    what was found — with every heading a declared form in the issue's own language.
    """
    lines = (body or "").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    stripped = [line.strip() for line in lines]

    marker_indexes = [index for index, line in enumerate(stripped) if line == COMMENT_MARKER]
    if len(marker_indexes) != 1:
        raise _ShapeError("comment body must contain exactly one AIS CR comment marker on its own line.")
    if marker_indexes[0] != next((index for index, line in enumerate(stripped) if line), None):
        raise _ShapeError("comment body marker must be the first non-empty line.")

    disclosure_indexes = [index for index, line in enumerate(stripped) if line == COMMENT_INTERACTIVE_DISCLOSURE]
    if len(disclosure_indexes) != 1:
        raise _ShapeError("comment AI-assistance disclosure must stand alone on its own line.")
    if disclosure_indexes[0] != max(index for index, line in enumerate(stripped) if line):
        raise _ShapeError("comment AI-assistance disclosure must be the final non-empty line.")

    headings = [line for line in stripped if line.startswith("## ")]
    if not headings:
        raise _ShapeError("comment body must carry its declared section headings.")
    unknown = [heading for heading in headings if _comment_heading_section(heading) is None]
    if unknown:
        accepted = sorted(f"## {form}" for forms in COMMENT_SECTION_FORMS.values() for form in forms)
        raise _ShapeError(
            f"comment heading is not a declared form: {', '.join(unknown)}; accepted: {', '.join(accepted)}."
        )
    if not _comment_headings_share_one_language(headings):
        raise _ShapeError("comment headings must use one language, matching the issue they answer.")

    order = {section: index for index, section in enumerate(COMMENT_SECTION_FORMS)}
    section_sequence = [order[_comment_heading_section(heading)] for heading in headings]  # type: ignore[arg-type]
    if section_sequence != sorted(section_sequence):
        raise _ShapeError("comment sections are out of order.")
    for section in COMMENT_REQUIRED_SECTIONS:
        if section_sequence.count(order[section]) != 1:
            raise _ShapeError(f"comment body must contain exactly one '{section}' section.")

    bounds = [index for index, line in enumerate(stripped) if line.startswith("## ")] + [disclosure_indexes[0]]
    for position, start in enumerate(bounds[:-1]):
        if not any(lines[start + 1 : bounds[position + 1]]):
            raise _ShapeError(f"comment section '{stripped[start]}' must not be empty; state explicitly what it holds.")
    _validate_comment_list_forms(lines, stripped, bounds)


def _validate_comment_list_forms(lines: list[str], stripped: list[str], bounds: list[int]) -> None:
    """Per-section list-form rules, enforced in both directions.

    The outstanding sections render every top-level list item as a GitHub task-list entry so it can be ticked off in
    place; the settled sections carry no task-list entries, so a completed statement never displays as an open
    obligation. Lines inside fenced code blocks are judged by neither rule — an evidence excerpt is not a list item.
    Nesting follows the list structure: an item more indented than the item it immediately follows is its child, and
    top-level means zero to three leading spaces per CommonMark.
    """
    for position, start in enumerate(bounds[:-1]):
        section = _comment_heading_section(stripped[start])
        if section not in COMMENT_TASK_LIST_SECTIONS + COMMENT_PLAIN_LIST_SECTIONS:
            continue
        in_fence = False
        prev_item_indent: int | None = None
        for line in lines[start + 1 : bounds[position + 1]]:
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                prev_item_indent = None
                continue
            if in_fence:
                continue
            item_match = _LIST_ITEM_PATTERN.match(line)
            if item_match is None:
                if line.strip() and not line.startswith((" ", "\t")):
                    prev_item_indent = None
                continue
            indent = len(item_match.group(1))
            nested = prev_item_indent is not None and indent > prev_item_indent
            prev_item_indent = indent
            is_task = _TOP_LEVEL_TASK_PATTERN.match(line) is not None
            if section in COMMENT_TASK_LIST_SECTIONS:
                if not nested and not is_task:
                    raise _ShapeError(
                        f"comment section '{section}' must render every top-level list item "
                        f"as a task-list entry; offending item: {line.strip()!r}."
                    )
            elif _TASK_LIST_PATTERN.match(line):
                raise _ShapeError(
                    f"comment section '{section}' must not contain task-list entries; offending item: {line.strip()!r}."
                )


def comment_shape_findings(body: str) -> list[dict[str, str]]:
    """Structural findings for an acceptance comment; empty means the shape holds."""
    try:
        _validate_comment_shape(body)
    except _ShapeError as exc:
        return [{"kind": "comment-out-of-shape", "detail": str(exc)}]
    return []


def _heading_span(lines: list[str], forms: tuple[str, ...]) -> tuple[int, int] | None:
    """Locate a section by any declared form, and the extent of its content."""
    accepted = {f"## {form}" for form in forms}
    for index, line in enumerate(lines):
        if line.strip() not in accepted:
            continue
        end = next(
            (later for later in range(index + 1, len(lines)) if lines[later].strip().startswith("## ")),
            len(lines),
        )
        return index, end
    return None


def section_status(body: str) -> dict[str, list[str]]:
    """Report every declared section as present, missing, or empty.

    The shape validator stops at the first defect, which is right for a write gate and wrong for a readiness report:
    someone told to go back deserves the whole list, not one item at a time.
    """
    lines = (body or "").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    rows = {}
    with contextlib.suppress(_ShapeError):
        rows = _metadata_rows(lines)
    issue_type = rows["Type"][1].strip().strip("`") if "Type" in rows else None

    expected = dict(SECTION_FORMS)
    if issue_type in TYPE_BLOCK_FORMS:
        expected[TYPE_BLOCK_FORMS[issue_type][0]] = TYPE_BLOCK_FORMS[issue_type]

    present, missing, empty = [], [], []
    for section, forms in expected.items():
        span = _heading_span(lines, forms)
        if span is None:
            missing.append(section)
        elif _section_has_content(lines, span[0], span[1]):
            present.append(section)
        else:
            empty.append(section)
    return {
        "present": present,
        "missing": missing,
        "empty": empty,
        "missing_metadata": [field for field in REQUIRED_METADATA if field not in rows],
    }


def readiness(body: str, thread: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Assess whether a description can seed a change, and why not when it cannot.

    Readiness is the declared shape, not a judgement: an issue that satisfies it already holds what promotion consumes.
    The thread is reported alongside because a gap the conversation already covers is one shaping run away, not new work
    — and being told "go back" without that distinction reads as an instruction to go and think harder.
    """
    findings = shape_findings(body)
    sections = section_status(body)
    comments = [item for item in thread or [] if str(item.get("body") or "").strip()]
    return {
        "ready": not findings,
        "shape_findings": findings,
        **sections,
        "thread": {
            "comments": len(comments),
            "characters": sum(len(str(item.get("body") or "")) for item in comments),
        },
        "thread_has_content": bool(comments),
    }


def _comment_record(node: dict[str, Any]) -> dict[str, Any]:
    author = node.get("author") or {}
    return {
        "source": f"comment {node.get('databaseId')}",
        "id": node.get("databaseId"),
        "author": author.get("login"),
        "created_at": node.get("createdAt"),
        "url": node.get("url"),
        "hidden": bool(node.get("isMinimized")),
        "hidden_reason": node.get("minimizedReason"),
        "body": node.get("body") or "",
    }


def _graphql(query: str, **variables: str) -> dict[str, Any]:
    return github_utils.graphql(query, runner=_gh, **variables)


def _hierarchy_edges(
    issue: dict[str, Any],
    owner_repo: str,
    sub_issues: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Return the issue's parent and sub-issues, as typed edges rather than mentions.

    A sub-issue's parent states the work it belongs to and a parent's sub-issues state how that work is decomposed, so
    both are decisive far more often than an incidental mention — and neither is subject to the bound that governs
    mentions.
    """

    def ref(node: dict[str, Any]) -> str:
        repository = (node.get("repository") or {}).get("nameWithOwner") or owner_repo
        return f"{repository}#{node.get('number')}"

    edges: list[dict[str, str]] = []
    parent = issue.get("parent")
    if parent:
        edges.append({"relation": "parent", "ref": ref(parent)})
    edges.extend({"relation": "sub-issue", "ref": ref(node)} for node in sub_issues if node)
    return edges


def _issue_connection(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    query: str,
    key: str,
    owner: str,
    name: str,
    number: int,
    cursor: str | None,
) -> dict[str, Any]:
    variables = {"owner": owner, "name": name, "number": str(number)}
    if cursor is not None:
        variables["endCursor"] = cursor
    payload = _graphql(query, **variables)
    issue = (((payload.get("data") or {}).get("repository") or {}).get("issue")) or {}
    return issue.get(key) or {}


def fetch_conversation(owner_repo: str, number: int) -> dict[str, Any]:
    """Return the issue with every comment, including those hidden or in resolved threads.

    An issue's real content routinely accumulates in its thread while the body stays a thin draft, so the thread is
    gathered as reconciliation input rather than as background.
    """
    owner, _, name = owner_repo.partition("/")
    payload = _graphql(ISSUE_QUERY, owner=owner, name=name, number=str(number))
    issue = (((payload.get("data") or {}).get("repository") or {}).get("issue")) or {}
    comment_nodes = _paginated_graphql_nodes(
        lambda cursor: _issue_connection(ISSUE_COMMENTS_QUERY, "comments", owner, name, number, cursor)
    )
    sub_issues = _paginated_graphql_nodes(
        lambda cursor: _issue_connection(ISSUE_SUB_ISSUES_QUERY, "subIssues", owner, name, number, cursor)
    )
    comments = [_comment_record(node) for node in comment_nodes]
    return {
        "title": issue.get("title"),
        "state": issue.get("state"),
        "url": issue.get("url"),
        "created_at": issue.get("createdAt"),
        "author": (issue.get("author") or {}).get("login"),
        "body": issue.get("body") or "",
        "comments": comments,
        "hierarchy": _hierarchy_edges(issue, owner_repo, sub_issues),
    }


def _fetch_referenced_item(ref: str) -> dict[str, Any] | None:
    target_repo, _, number = ref.partition("#")
    ok, stdout = _try_run(["gh", "api", f"repos/{target_repo}/issues/{number}"])
    if not ok:
        return None
    try:
        item = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(item, dict):
        return None
    comments = _paginated_rest_items(
        f"repos/{target_repo}/issues/{number}/comments",
        runner=_try_run,
    )
    if comments is None:
        return None
    normalized_comments = [
        {
            "source": f"{ref} comment",
            "id": node.get("id"),
            "author": (node.get("user") or {}).get("login"),
            "created_at": node.get("created_at"),
            "url": node.get("html_url"),
            "hidden": False,
            "hidden_reason": None,
            "body": node.get("body") or "",
        }
        for node in comments
    ]
    if item.get("pull_request"):
        review_comments = _paginated_rest_items(
            f"repos/{target_repo}/pulls/{number}/comments",
            runner=_try_run,
        )
        if review_comments is None:
            return None
        normalized_comments.extend(
            {
                "source": f"{ref} review comment",
                "id": node.get("id"),
                "author": (node.get("user") or {}).get("login"),
                "created_at": node.get("created_at"),
                "url": node.get("html_url"),
                "hidden": False,
                "hidden_reason": None,
                "body": node.get("body") or "",
            }
            for node in review_comments
        )
    return {
        "ref": ref,
        "title": item.get("title"),
        "state": item.get("state"),
        "url": item.get("html_url"),
        "body": item.get("body") or "",
        "comments": normalized_comments,
    }


def gather_neighbourhood(
    owner_repo: str,
    number: int,
    texts: list[str],
    hierarchy: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """One hop of mentions plus every hierarchy edge; the rest is reported."""
    return github_utils.gather_neighbourhood(
        owner_repo,
        f"{owner_repo}#{number}",
        texts,
        [],
        _fetch_referenced_item,
        [edge["ref"] for edge in hierarchy or []],
    )


def reconciliation_sources(
    conversation: dict[str, Any],
    *,
    comparison_base: str | None = None,
) -> list[tuple[str, str]]:
    """Return the reporter original, external edits, and thread as reconciliation input.

    Once the workflow owns the body, its unchanged generated text is deliberately absent. The comparison base — the last
    workflow-posted body — isolates later human edits without feeding the generated body back into itself. The
    provenance comment is internal state and is not thread evidence. The original is always labelled ``description``, so
    a ledger citation does not shift when a record appears.
    """
    provenance = _find_provenance_comment(conversation["comments"])
    if provenance is None:
        sources = [("description", conversation["body"])]
    else:
        original = _provenance_original(provenance)
        sources = [("description", original)] if original else []
        base = original if comparison_base is None else comparison_base
        state = body_state(conversation["body"])
        body_is_current_workflow_post = state["workflow_owned"] and state["edited_since_post"] is False
        if not body_is_current_workflow_post and conversation["body"] != base:
            sources.extend(_description_edit_sources(base, conversation["body"]))
    sources.extend(
        (comment["source"], comment["body"])
        for comment in conversation["comments"]
        if PROVENANCE_MARKER not in str(comment.get("body") or "")
    )
    return sources


def _resolve_comparison_base(
    conversation: dict[str, Any],
    *,
    owner_repo: str,
    number: int,
) -> tuple[str | None, bool]:
    """Return ``(base, degraded)`` for a later round, fetching content-edit history.

    ``degraded`` is true when history yields no body matching the stamped digest; the preserved original is then the
    base. The current generated body is never the base.
    """
    provenance = _find_provenance_comment(conversation["comments"])
    if provenance is None:
        return None, False
    original = _provenance_original(provenance)
    state = body_state(conversation["body"])
    if state["workflow_owned"] and state["edited_since_post"] is False:
        return conversation["body"], False
    stamped = state["posted_digest"]
    if not stamped:
        return original, True
    bodies = github_utils.fetch_content_edit_bodies(owner_repo, number, subject="issue")
    match = github_utils.select_body_by_digest(bodies, stamped, body_digest)
    if match is None:
        return original, True
    return match, False


def _composition_findings(
    sources: list[tuple[str, str]],
    body: str,
    ledger: dict[str, Any],
    load_bearing: list[str],
) -> list[dict[str, Any]]:
    """Shape plus accounting: what a body must satisfy before it is written."""
    return shape_findings(body) + github_utils.verify_composition(
        sources,
        body,
        ledger,
        load_bearing,
        github_utils.SurfaceVocabulary(declared_section_names(), (REPORTER_CONTEXT_OPEN, REPORTER_CONTEXT_CLOSE)),
    )


def composed_body(path: str) -> str:
    """Read a drafted body and normalise its line breaks before anything digests it.

    This is the issue surface's single entry point for a body it authored, so the text local verification checks and the
    text the write digests are the same string. The preserved reporter original does not come through here: it is read
    as gathered.
    """
    return github_utils.normalize_posted_line_breaks(_read_text(path))


def cmd_gather(number: int, repo: str | None) -> None:
    """Print the issue's whole conversation and one hop of references."""
    owner_repo = _resolve_repo(repo)
    conversation = fetch_conversation(owner_repo, number)
    texts = [conversation["body"]] + [comment["body"] for comment in conversation["comments"]]
    output = {
        "owner_repo": owner_repo,
        "number": number,
        **conversation,
        "body_state": body_state(conversation["body"]),
        **gather_neighbourhood(owner_repo, number, texts, conversation["hierarchy"]),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def _resolve_promotion_repo(repo_arg: str | None) -> str:
    """Resolve the target, refusing an issue this checkout does not own.

    Promotion produces an OpenSpec change, a branch, and a pull request, and all three belong to the repository the
    issue lives in, because that is where the implementation happens. Accepting a foreign ``--repo`` would put the
    change in a repository the work never reaches, which reads as success until someone goes looking for it.
    """
    local = _resolve_repo(None)
    if repo_arg and repo_arg != local:
        _abort(
            f"refusing to promote '{repo_arg}' from a checkout of '{local}'. "
            "The change, its branch, and its pull request live where the issue does; "
            f"run this in a checkout of '{repo_arg}'."
        )
    return local


def cmd_assess_readiness(number: int, repo: str | None) -> None:
    """Report whether an issue can seed a change. Read-only; exits 1 when it cannot."""
    owner_repo = _resolve_promotion_repo(repo)
    conversation = fetch_conversation(owner_repo, number)
    report = readiness(conversation["body"], conversation["comments"])
    print(json.dumps({"owner_repo": owner_repo, "number": number, **report}, ensure_ascii=False, indent=2))
    if not report["ready"]:
        raise SystemExit(1)


def cmd_verify_composition(sources_path: str, body_path: str, ledger_path: str | None) -> None:
    """Check a developed body locally — shape and accounting: no network, no write."""
    body = composed_body(body_path)
    reference_field = github_utils.reference_field_from_sources(
        github_utils.ReferenceField(
            "composition.body",
            body,
            region=(REPORTER_CONTEXT_OPEN, REPORTER_CONTEXT_CLOSE),
        ),
        sources_path,
    )
    sources = list(reference_field.sources)
    ledger = _load_json(ledger_path, "disposition ledger") if ledger_path else {}
    load_bearing = [item["fragment"] for _, text in sources for item in detect_load_bearing(text)]
    findings = _composition_findings(sources, body, ledger, load_bearing)
    github_utils.validate_reference_batch([reference_field])
    print(json.dumps({"findings": findings}, ensure_ascii=False, indent=2))
    if findings:
        raise SystemExit(1)


def _approval_envelope(
    operation: str,
    owner_repo: str,
    endpoint: str,
    method: str,
    payload: dict[str, Any],
    **context: Any,
) -> dict[str, Any]:
    """Bind approval to the exact target, operation, and GitHub request body."""
    return {
        "operation": operation,
        "repository": owner_repo,
        **context,
        "request": {
            "endpoint": endpoint,
            "method": method,
            "payload": payload,
        },
    }


def _check_approval_references(
    approval: dict[str, Any],
    contexts: dict[str, github_utils.ReferenceField] | None = None,
) -> None:
    """Check the complete prepared batch, including generated provenance, before approval or mutation."""
    fields = []
    for name in ("request", "provenance_request"):
        request = approval.get(name)
        if request is None:
            continue
        for key in ("title", "body"):
            text = request["payload"].get(key)
            if isinstance(text, str):
                label = f"{name}.{key}"
                context = (contexts or {}).get(label, github_utils.ReferenceField(label, text))
                fields.append(context._replace(label=label, text=text))
    evidence = github_utils.validate_reference_batch(fields)
    if evidence:
        approval["reference_sources"] = evidence


def _prepare_archive_description(number: int, body_path: str, repo: str | None) -> tuple[str, str, dict[str, Any]]:
    current = _read_text(body_path)
    if not current.strip():
        _abort("refusing to archive an empty issue description; there is no reporter input or baseline to preserve.")
    owner_repo = _resolve_repo(repo)
    state = body_state(current)
    original = "" if state["workflow_owned"] else current
    acquired = github_utils.fetch_issue_payload(owner_repo, number, runner=_gh)
    source, author = github_utils.provenance_source_and_author(acquired)
    approval = _approval_envelope(
        "archive-description",
        owner_repo,
        f"repos/{owner_repo}/issues/{number}/comments",
        "POST",
        {"body": _render_provenance(original, {}, source=source, author=author)},
        issue=number,
    )
    _check_approval_references(
        approval,
        {
            "request.body": github_utils.ReferenceField(
                "request.body",
                "",
                owner_repo,
                (("description", str(acquired.get("body") or "")),),
                (PROVENANCE_ORIGINAL_OPEN, PROVENANCE_ORIGINAL_CLOSE),
                True,
            )
        },
    )
    return owner_repo, current, approval


def _post_body_reference_contexts(
    body: str,
    conversation: dict[str, Any],
    owner_repo: str,
    number: int,
    provenance: dict[str, Any] | None,
) -> dict[str, github_utils.ReferenceField]:
    """Build preservation evidence from the same acquired conversation used by the write."""
    sources = ()
    if github_references.check_references(body):
        comparison_base, _ = _resolve_comparison_base(conversation, owner_repo=owner_repo, number=number)
        sources = tuple(reconciliation_sources(conversation, comparison_base=comparison_base))
    contexts = {
        "request.body": github_utils.ReferenceField(
            "request.body",
            "",
            owner_repo,
            sources,
            (REPORTER_CONTEXT_OPEN, REPORTER_CONTEXT_CLOSE),
        )
    }
    if provenance is not None:
        contexts["provenance_request.body"] = github_utils.ReferenceField(
            "provenance_request.body",
            "",
            owner_repo,
            (("description", _provenance_original(provenance)),),
            (PROVENANCE_ORIGINAL_OPEN, PROVENANCE_ORIGINAL_CLOSE),
            True,
        )
    return contexts


def _prepare_post_body(
    number: int,
    body_path: str,
    repo: str | None,
    ledger: dict[str, Any] | None = None,
) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    body = composed_body(body_path)
    github_utils.validate_contract(body, "interactive", ISSUE_CONTRACT, "issue")
    owner_repo = _resolve_repo(repo)
    conversation = fetch_conversation(owner_repo, number)
    provenance = _find_provenance_comment(conversation["comments"])
    if conversation["body"].strip() and provenance is None:
        _abort(
            "refusing to replace a non-empty issue description without a marked provenance comment; "
            "run 'archive-description' first so the reporter original or workflow baseline is durable."
        )
    stamped = stamp_digest(body)
    payload: dict[str, Any] = {"body": stamped}
    context: dict[str, Any] = {"issue": number}
    derived_title = issue_title(body)
    current_title = str(conversation.get("title") or "")
    if derived_title:
        payload["title"] = derived_title
        if derived_title != current_title:
            # A rename is outward-facing, so it is surfaced as its own envelope field
            # rather than hidden inside the payload: the operator sees what the title
            # becomes before approving, and the digest binds it like the body.
            context["title_change"] = {"from": current_title, "to": derived_title}
    approval = _approval_envelope(
        "post-body",
        owner_repo,
        f"repos/{owner_repo}/issues/{number}",
        "PATCH",
        payload,
        **context,
    )
    if provenance is not None:
        # Bind the exact comment that will be written, not just the tail that replaces the
        # ledger. The original stays immutable because `replace_after_region` keeps the
        # prefix; carrying the resolved body means the approved digest also covers that
        # prefix, so an original edited between the approval view and the write is refused
        # instead of silently preserved and then read back as reconciliation input.
        approval["provenance_request"] = {
            "endpoint": f"repos/{owner_repo}/issues/comments/{provenance['id']}",
            "method": "PATCH",
            "payload": {
                "body": github_utils.replace_after_region(
                    str(provenance.get("body") or ""),
                    PROVENANCE_ORIGINAL_CLOSE,
                    github_utils.render_disposition_ledger(
                        ledger or {},
                        LEDGER_MARKER,
                        repository=owner_repo
                        if github_references.check_references(_provenance_original(provenance))
                        else "",
                    ),
                )
            },
        }
    _check_approval_references(
        approval, _post_body_reference_contexts(body, conversation, owner_repo, number, provenance)
    )
    return owner_repo, body, approval, conversation


def _prepare_issue_creation(
    title: str,
    body_path: str,
    repo: str | None,
    sources_path: str | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """Prepare a structured new issue without coupling the engine to its input source."""
    body = composed_body(body_path)
    github_utils.validate_contract(body, "interactive", ISSUE_CONTRACT, "issue")
    owner_repo = _resolve_repo(repo)
    approval = _approval_envelope(
        "create",
        owner_repo,
        f"repos/{owner_repo}/issues",
        "POST",
        {"title": title, "body": stamp_digest(body)},
    )
    contexts = {}
    if sources_path:
        contexts["request.body"] = github_utils.reference_field_from_sources(
            github_utils.ReferenceField(
                "request.body",
                "",
                region=(REPORTER_CONTEXT_OPEN, REPORTER_CONTEXT_CLOSE),
            ),
            sources_path,
        )
    _check_approval_references(approval, contexts)
    return owner_repo, body, approval


def _append_to_reporter_region(body: str, fragment: str) -> str:
    """Return ``body`` with ``fragment`` as the last paragraph of the reporter-context region.

    A body without a delimited region is returned unchanged, so the shape check that follows reports the missing region
    instead of this helper inventing one.
    """
    lines = body.split("\n")
    close = next((index for index, line in enumerate(lines) if line.strip() == REPORTER_CONTEXT_CLOSE), None)
    if close is None:
        return body
    return "\n".join(lines[:close] + ["", fragment] + lines[close:])


def _prepare_extraction(
    parent: int,
    link: str,
    title: str,
    body_path: str,
    repo: str | None,
) -> tuple[str, str, dict[str, Any]]:
    filed = composed_body(body_path).rstrip()
    if not filed:
        _abort("refusing to file an empty extraction stub; it must carry the extracted content.")

    owner_repo = _resolve_repo(repo)
    parent_url = f"https://github.com/{owner_repo}/issues/{parent}"
    back_link = f"Extracted from {github_references.reference_link(parent_url)} by the AIS CR issue workflow."
    # Extraction files either a short stub or a fully developed child. A body carrying
    # the marker is claiming to be the latter, so it is held to the issue contract and
    # the issue shape, and stamped — without the stamp the child is not workflow-owned,
    # and a later post-body would read its generated body back as though it were
    # reporter input. Its back-link goes inside the reporter-context region, because the
    # shape requires the disclosure last and the region is where carried provenance
    # lives. A stub carries no marker and gets the back-link appended, as before.
    if ISSUE_MARKER_PATTERN.search(filed):
        github_utils.validate_contract(filed, "interactive", ISSUE_CONTRACT, "issue")
        if back_link not in filed:
            filed = _append_to_reporter_region(filed, back_link)
        findings = shape_findings(filed)
        if findings:
            _abort(f"refusing to file an extracted body out of shape: {findings[0]['detail']}")
        filed = stamp_digest(filed)
    elif back_link not in filed:
        filed = f"{filed}\n\n{back_link}"
    approval = _approval_envelope(
        "extract",
        owner_repo,
        f"repos/{owner_repo}/issues",
        "POST",
        {"title": title, "body": filed},
        parent=parent,
        link=link,
    )
    _check_approval_references(approval)
    return owner_repo, filed, approval


def _prepare_draft_pr(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    number: int,
    head: str,
    base: str,
    title: str,
    body_path: str,
    repo: str | None,
) -> tuple[str, str, dict[str, Any]]:
    body = composed_body(body_path)
    github_utils.validate_contract(body, "interactive", PROMOTION_CONTRACT, "pull request")
    if f"#{number}" not in body:
        _abort(f"promotion pull-request body must reference the issue it promotes (#{number}).")
    closing = [item["fragment"] for item in detect_load_bearing(body) if item["kind"] == "closing-keyword"]
    if closing:
        _abort(
            "refusing a promotion pull request that carries an issue-closing keyword "
            f"({', '.join(closing)}); promotion plans the work, it does not resolve the issue."
        )

    owner_repo = _resolve_promotion_repo(repo)
    if f"{owner_repo}#{number}" not in github_utils.extract_references(owner_repo, [body])[0]:
        _abort("promotion pull-request body must reference the issue in the selected repository.")
    approval = _approval_envelope(
        "open-draft-pr",
        owner_repo,
        f"repos/{owner_repo}/pulls",
        "POST",
        {"title": title, "head": head, "base": base, "body": body, "draft": True},
        issue=number,
    )
    _check_approval_references(approval)
    return owner_repo, body, approval


def _prepare_issue_comment(
    number: int,
    body_path: str,
    repo: str | None,
) -> tuple[str, str, dict[str, Any]]:
    """Validate an acceptance comment and bind its exact write envelope."""
    body = composed_body(body_path)
    github_utils.validate_contract(body, "interactive", COMMENT_CONTRACT, "comment")
    findings = comment_shape_findings(body)
    if findings:
        _abort(
            "refusing an out-of-shape acceptance comment:\n"
            + "\n".join(f"  - {item['kind']}: {item.get('detail', '')}" for item in findings)
        )
    owner_repo = _resolve_repo(repo)
    approval = _approval_envelope(
        "post-comment",
        owner_repo,
        f"repos/{owner_repo}/issues/{number}/comments",
        "POST",
        {"body": body},
        issue=number,
    )
    _check_approval_references(approval)
    return owner_repo, body, approval


def _render_approval(approval: dict[str, Any]) -> str:
    """Render exactly the file an operator approves, with deterministic LF endings."""
    return (
        json.dumps({"approval_digest": _canonical_digest(approval), "write": approval}, ensure_ascii=False, indent=2)
        + "\n"
    )


def _require_approved_digest(
    approval: dict[str, Any], approved_digest: str | None, body_path: str, approval_view_path: str | None
) -> None:
    digest = _canonical_digest(approval)
    if not approved_digest:
        _abort("interactive GitHub writes require --approved-digest from the approval-view output.")
    if approved_digest != digest:
        _abort(
            "approved digest does not match the exact GitHub payload; regenerate and approve "
            "the current approval view before writing."
        )
    target = Path(approval_view_path) if approval_view_path else Path(body_path).parent / "approval.json"
    try:
        target = local_scratch_paths.checked_handoff_file(REPO_ROOT, target)
        matches = target.read_bytes() == _render_approval(approval).encode("utf-8")
    except (OSError, ValueError) as exc:
        _abort(f"cannot read approval view '{target}'; re-render and approve again: {exc}")
    if not matches:
        _abort("approval view was edited; re-render and obtain fresh approval before writing.")


def cmd_run_handoff(action: str, workflow: str, run: str, approve: bool = False, *, kind: str = "issue") -> None:
    """Prepare a visible pointer before body authoring, or clean a completed run safely."""
    if kind not in HANDOFF_ARTIFACTS:
        _abort("unsupported hand-off artifact class")
    if action not in ("prepare-handoff", "cleanup-handoff"):
        _abort("unsupported hand-off action")
    if action == "cleanup-handoff" and not approve:
        _abort("hand-off cleanup requires --approve after every posting decision is terminal.")
    try:
        if action == "prepare-handoff":
            print(local_scratch_paths.prepare_run_handoff(REPO_ROOT, workflow, run))
        else:
            local_scratch_paths.cleanup_run_handoff(REPO_ROOT, workflow, run, HANDOFF_ARTIFACTS[kind])
    except (OSError, ValueError) as exc:
        _abort(str(exc))


def cmd_approval_view(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-branches,too-many-locals
    operation: str,
    number: int | None,
    body_path: str,
    repo: str | None,
    link: str | None,
    title: str | None,
    head: str | None,
    base: str | None,
    ledger_path: str | None = None,
    output_path: str | None = None,
    sources_path: str | None = None,
) -> None:
    """Render the exact canonical write envelope and its approval digest; never write GitHub."""
    if sources_path and operation != "create":
        _abort("--sources is supported only for a create approval view.")
    if operation == "create":
        if number is not None or not title or any((link, head, base, ledger_path)):
            _abort("create approval-view requires --title and no issue number, --link, --head, --base, or --ledger.")
        approval = _prepare_issue_creation(title, body_path, repo, sources_path)[2]
    elif number is None:
        _abort(f"{operation} approval-view requires ISSUE_NUMBER.")
    elif operation == "archive-description":
        if any((link, title, head, base, ledger_path)):
            _abort("archive-description approval-view accepts only ISSUE_NUMBER, --body, and optional --repo.")
        approval = _prepare_archive_description(number, body_path, repo)[2]
    elif operation == "post-body":
        if any((link, title, head, base)):
            _abort("post-body approval-view accepts only ISSUE_NUMBER, --body, --ledger, and optional --repo.")
        if not ledger_path:
            # The ledger renders into the provenance record this operation also writes, and
            # the digest binds that record. Substituting an empty one would emit a digest no
            # write supplying a ledger can reproduce, and the operator would meet the mismatch
            # refusal — which everywhere else means the payload was altered after approval.
            # Refusing here keeps that refusal meaning one thing.
            _abort("post-body approval-view requires --ledger; it is bound by the digest the write must match.")
        ledger = _load_json(ledger_path, "disposition ledger")
        approval = _prepare_post_body(number, body_path, repo, ledger)[2]
    elif operation == "post-comment":
        if any((link, title, head, base, ledger_path)):
            _abort("post-comment approval-view accepts only ISSUE_NUMBER, --body, and optional --repo.")
        approval = _prepare_issue_comment(number, body_path, repo)[2]
    elif operation == "extract":
        if not link or not title or head or base or ledger_path:
            _abort(
                "extract approval-view requires --link and --title, and does not accept --head, --base, or --ledger."
            )
        approval = _prepare_extraction(number, link, title, body_path, repo)[2]
    else:
        if not all((title, head, base)) or link or ledger_path:
            _abort(
                "open-draft-pr approval-view requires --title, --head, and --base, "
                "and does not accept --link or --ledger."
            )
        approval = _prepare_draft_pr(number, head, base, title, body_path, repo)[2]
    rendered = _render_approval(approval)
    if output_path is None:
        print(rendered, end="")
        return
    try:
        target = local_scratch_paths.prepare_handoff_file(REPO_ROOT, Path(output_path))
        target.write_text(rendered, encoding="utf-8", newline="\n")
    except (OSError, ValueError) as exc:
        _abort(str(exc))
    print(os.path.abspath(target))


def cmd_archive_description(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    number: int,
    body_path: str,
    mode: str,
    approved_digest: str | None,
    repo: str | None,
    approval_view_path: str | None = None,
) -> None:
    """Preserve the reporter original or establish a workflow-owned baseline once."""
    _validate_write_environment(mode, "archive-description")
    owner_repo, current, approval = _prepare_archive_description(number, body_path, repo)
    _require_approved_digest(approval, approved_digest, body_path, approval_view_path)
    conversation = fetch_conversation(owner_repo, number)
    existing = _find_provenance_comment(conversation["comments"])
    if existing is not None:
        print(f"Issue description provenance already exists: {existing.get('url') or existing.get('id')}")
        return
    if conversation["body"] != current:
        _abort(
            "the issue description changed after the provenance view was rendered; gather it again and approve "
            "the current exact body before archiving."
        )
    request = approval["request"]
    url = _gh_with_payload(request["endpoint"], request["method"], request["payload"], ".html_url")
    print(f"Issue description provenance archived: {url}")


def cmd_create(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    title: str,
    body_path: str,
    sources_path: str,
    ledger_path: str,
    mode: str,
    approved_digest: str | None,
    repo: str | None,
    approval_view_path: str | None = None,
) -> None:
    """Create one structured issue after re-verifying its source accounting."""
    _validate_write_environment(mode, "create")
    _, body, approval = _prepare_issue_creation(title, body_path, repo, sources_path)
    _require_approved_digest(approval, approved_digest, body_path, approval_view_path)
    sources = github_utils.load_source_list(sources_path)
    ledger = _load_json(ledger_path, "disposition ledger")
    findings = _composition_findings(
        sources, body, ledger, [item["fragment"] for _, text in sources for item in detect_load_bearing(text)]
    )
    if findings:
        _abort(
            "refusing to create an unverified issue composition; every finding is repairable:\n"
            + "\n".join(f"  - {item['kind']}: {item.get('detail', '')}" for item in findings)
        )
    request = approval["request"]
    url = _gh_with_payload(
        request["endpoint"],
        request["method"],
        request["payload"],
        ".html_url",
    )
    print(f"Issue created: {url}")


def cmd_extract(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    parent: int,
    link: str,
    title: str,
    body_path: str,
    mode: str,
    approved_digest: str | None,
    repo: str | None,
    approval_view_path: str | None = None,
) -> None:
    """File the issue for extracted content, before a ledger can reference it.

    The link type states the relationship rather than assuming one: content that is part of the same work becomes a
    sub-issue, while a different problem that merely surfaced in the thread becomes an independent issue with a
    cross-reference.

    What is filed may be a short stub or a fully developed body; this is the only surface that establishes the parent
    link, so a child of a program belongs here rather than in ``create``, which files a standalone issue. Extraction
    still does not recurse: developing a stub further is a separate invocation.
    """
    _validate_write_environment(mode, "extract")
    owner_repo, _, approval = _prepare_extraction(parent, link, title, body_path, repo)
    _require_approved_digest(approval, approved_digest, body_path, approval_view_path)
    request = approval["request"]

    created = _gh_with_payload(
        request["endpoint"],
        request["method"],
        request["payload"],
        "[.number, .id, .html_url] | @tsv",
    )
    number, database_id, url = created.split("\t")
    if link == "sub-issue":
        _gh_with_payload(
            f"repos/{owner_repo}/issues/{parent}/sub_issues",
            "POST",
            {"sub_issue_id": int(database_id)},
            ".html_url",
        )
    print(f"Extracted issue created as a {link}: {owner_repo}#{number} — {url}")


def cmd_open_draft_pr(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    number: int,
    head: str,
    base: str,
    title: str,
    body_path: str,
    mode: str,
    approved_digest: str | None,
    repo: str | None,
    approval_view_path: str | None = None,
) -> None:
    """Open the draft pull request the promoted change will be implemented on.

    Draft is not a formality: the change is planned, not done, and a ready pull request would invite review of an
    implementation that has not happened. Re-running cites the existing pull request rather than opening a second one,
    so a resumed promotion is idempotent.
    """
    _validate_write_environment(mode, "open-draft-pr")
    owner_repo, _, approval = _prepare_draft_pr(number, head, base, title, body_path, repo)
    _require_approved_digest(approval, approved_digest, body_path, approval_view_path)
    owner, _, _ = owner_repo.partition("/")
    existing = _gh(
        "api",
        f"repos/{owner_repo}/pulls",
        "--method",
        "GET",
        "-f",
        f"head={owner}:{head}",
        "--jq",
        ".[0].html_url // empty",
    )
    if existing:
        print(f"Branch '{head}' already carries a pull request: {existing}")
        return

    request = approval["request"]
    url = _gh_with_payload(
        request["endpoint"],
        request["method"],
        request["payload"],
        ".html_url",
    )
    print(f"Draft pull request opened: {url}")


def cmd_post_comment(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    number: int,
    body_path: str,
    mode: str,
    approved_digest: str | None,
    repo: str | None,
    approval_view_path: str | None = None,
) -> None:
    """Post the acceptance-verification comment under exact-content approval."""
    _validate_write_environment(mode, "post-comment")
    _, _, approval = _prepare_issue_comment(number, body_path, repo)
    _require_approved_digest(approval, approved_digest, body_path, approval_view_path)
    request = approval["request"]
    url = _gh_with_payload(request["endpoint"], request["method"], request["payload"], ".html_url")
    print(f"Issue comment posted: {url}")


def _gh_with_payload(endpoint: str, method: str, payload: dict[str, Any], jq: str) -> str:
    payload_path = _temporary_json(payload)
    try:
        return _gh("api", endpoint, "--method", method, "--input", payload_path, "--jq", jq)
    finally:
        os.unlink(payload_path)


def cmd_post_body(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    number: int,
    mode: str,
    body_path: str,
    approved_digest: str | None,
    repo: str | None,
    ledger_path: str | None,
    approval_view_path: str | None = None,
) -> None:
    """Write the developed description after its shape and accounting verify."""
    _validate_write_environment(mode, "post-body")
    ledger = _load_json(ledger_path, "disposition ledger") if ledger_path else {}
    owner_repo, body, approval, conversation = _prepare_post_body(number, body_path, repo, ledger)
    _require_approved_digest(approval, approved_digest, body_path, approval_view_path)
    state = body_state(conversation["body"])
    comparison_base, degraded = _resolve_comparison_base(conversation, owner_repo=owner_repo, number=number)
    sources = reconciliation_sources(conversation, comparison_base=comparison_base)
    load_bearing = [item["fragment"] for _, text in sources for item in detect_load_bearing(text)]
    findings = _composition_findings(sources, body, ledger, load_bearing)
    if findings:
        suffix = (
            " operating degraded: content-edit history yielded no body matching the stamped digest." if degraded else ""
        )
        _abort(
            "refusing to write an unverified composition; every finding is repairable"
            f"{suffix}:\n" + "\n".join(f"  - {item['kind']}: {item.get('detail', '')}" for item in findings)
        )

    body_already_current = bool(state["posted_digest"] and state["posted_digest"] == body_digest(body))
    provenance_request = approval.get("provenance_request")
    existing_provenance = _find_provenance_comment(conversation["comments"])
    next_provenance = provenance_request["payload"]["body"] if provenance_request else None
    provenance_already_current = next_provenance is None or next_provenance == existing_provenance["body"]
    if body_already_current and provenance_already_current:
        print("Issue description and provenance already carry this composition; nothing to post.")
        return

    url = conversation.get("url") or f"https://github.com/{owner_repo}/issues/{number}"
    if not body_already_current:
        request = approval["request"]
        url = _gh_with_payload(
            request["endpoint"],
            request["method"],
            request["payload"],
            ".html_url",
        )
    if next_provenance is not None and not provenance_already_current:
        _gh_with_payload(
            provenance_request["endpoint"],
            provenance_request["method"],
            provenance_request["payload"],
            ".html_url",
        )
    print(f"Issue description updated: {url}")


def cmd_reconciliation_sources(number: int, repo: str | None) -> None:
    """Emit the labelled source list verification and the write both consume."""
    owner_repo = _resolve_repo(repo)
    conversation = fetch_conversation(owner_repo, number)
    comparison_base, degraded = _resolve_comparison_base(conversation, owner_repo=owner_repo, number=number)
    sources = reconciliation_sources(conversation, comparison_base=comparison_base)
    print(
        json.dumps(
            github_utils.source_list_payload(sources, degraded=degraded, repository=owner_repo),
            ensure_ascii=False,
            indent=2,
        )
    )


def _add_handoff_commands(subparsers) -> None:
    """Declare generic local lifecycle commands without requiring an optional workflow asset."""
    for action in ("prepare-handoff", "cleanup-handoff"):
        handoff = subparsers.add_parser(action, help="Prepare or safely clean a local run's visible hand-off.")
        handoff.add_argument("--workflow", required=True, metavar="NAMESPACE")
        handoff.add_argument("--run", required=True, metavar="RUN_NAME")
        if action == "cleanup-handoff":
            handoff.add_argument("--kind", required=True, choices=tuple(HANDOFF_ARTIFACTS))
            handoff.add_argument("--approve", action="store_true")


def build_parser() -> argparse.ArgumentParser:  # pylint: disable=too-many-statements
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="github_issues.py",
        description=(
            "Gather an issue's whole conversation, verify a developed body's shape and "
            "accounting, extract content that belongs elsewhere, and write the description "
            "under an explicit identity mode."
        ),
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    gather = subparsers.add_parser("gather", help="Fetch the issue conversation and one hop (read-only).")
    gather.add_argument("number", type=int, metavar="ISSUE_NUMBER")
    gather.add_argument("--repo", metavar="OWNER/REPO")

    assess = subparsers.add_parser("assess-readiness", help="Report whether an issue can seed a change (read-only).")
    assess.add_argument("number", type=int, metavar="ISSUE_NUMBER")
    assess.add_argument("--repo", metavar="OWNER/REPO")

    verify = subparsers.add_parser("verify-composition", help="Check a body's shape and accounting (local only).")
    verify.add_argument("--sources", required=True, metavar="FILE")
    verify.add_argument("--body", required=True, metavar="FILE")
    verify.add_argument("--ledger", metavar="FILE")

    emit_sources = subparsers.add_parser(
        "reconciliation-sources",
        help="Emit the labelled reconciliation source list (read-only).",
    )
    emit_sources.add_argument("number", type=int, metavar="ISSUE_NUMBER")
    emit_sources.add_argument("--repo", metavar="OWNER/REPO")

    approval = subparsers.add_parser(
        "approval-view",
        help="Print the exact canonical GitHub write envelope and approval digest (read-only).",
    )
    approval.add_argument("operation", choices=APPROVAL_OPERATIONS)
    approval.add_argument("number", type=int, nargs="?", metavar="ISSUE_NUMBER")
    approval.add_argument("--body", required=True, metavar="FILE")
    approval.add_argument("--repo", metavar="OWNER/REPO")
    approval.add_argument("--link", choices=EXTRACTION_LINKS)
    approval.add_argument("--title", metavar="TITLE")
    approval.add_argument("--head", metavar="BRANCH")
    approval.add_argument("--base", metavar="BRANCH")
    approval.add_argument("--ledger", metavar="FILE")
    approval.add_argument(
        "--sources", metavar="FILE", help="Explicit source snapshots for creation preservation checks."
    )
    approval.add_argument(
        "--approval-view",
        dest="approval_view",
        metavar="FILE",
        default=None,
        help="Write the approval view to this file instead of stdout (visible hand-off).",
    )

    archive = subparsers.add_parser(
        "archive-description",
        help="Preserve the reporter original or workflow baseline in a marked comment.",
    )
    archive.add_argument("number", type=int, metavar="ISSUE_NUMBER")
    archive.add_argument("--body", required=True, metavar="FILE")
    archive.add_argument("--mode", required=True, choices=ISSUE_MODES)
    archive.add_argument("--approved-digest", required=True, metavar="SHA256")
    archive.add_argument("--repo", metavar="OWNER/REPO")

    create = subparsers.add_parser("create", help="Create a structured issue from external input.")
    create.add_argument("--title", required=True, metavar="TITLE")
    create.add_argument("--body", required=True, metavar="FILE")
    create.add_argument("--sources", required=True, metavar="FILE")
    create.add_argument("--ledger", required=True, metavar="FILE")
    create.add_argument("--mode", required=True, choices=ISSUE_MODES)
    create.add_argument("--approved-digest", required=True, metavar="SHA256")
    create.add_argument("--repo", metavar="OWNER/REPO")

    extract = subparsers.add_parser("extract", help="File extracted content as its own issue.")
    extract.add_argument("parent", type=int, metavar="PARENT_ISSUE_NUMBER")
    extract.add_argument("--link", required=True, choices=EXTRACTION_LINKS)
    extract.add_argument("--title", required=True, metavar="TITLE")
    extract.add_argument("--body", required=True, metavar="FILE")
    extract.add_argument("--mode", required=True, choices=ISSUE_MODES)
    extract.add_argument("--approved-digest", required=True, metavar="SHA256")
    extract.add_argument("--repo", metavar="OWNER/REPO")

    draft = subparsers.add_parser("open-draft-pr", help="Open the draft PR for a promoted change.")
    draft.add_argument("number", type=int, metavar="ISSUE_NUMBER")
    draft.add_argument("--head", required=True, metavar="BRANCH")
    draft.add_argument("--base", required=True, metavar="BRANCH")
    draft.add_argument("--title", required=True, metavar="TITLE")
    draft.add_argument("--body", required=True, metavar="FILE")
    draft.add_argument("--mode", required=True, choices=ISSUE_MODES)
    draft.add_argument("--approved-digest", required=True, metavar="SHA256")
    draft.add_argument("--repo", metavar="OWNER/REPO")

    post = subparsers.add_parser("post-body", help="Write the developed issue description.")
    post.add_argument("number", type=int, metavar="ISSUE_NUMBER")
    post.add_argument("--mode", required=True, choices=ISSUE_MODES)
    post.add_argument("--body", required=True, metavar="FILE")
    post.add_argument("--approved-digest", required=True, metavar="SHA256")
    post.add_argument("--repo", metavar="OWNER/REPO")
    post.add_argument("--ledger", required=True, metavar="FILE")

    comment = subparsers.add_parser(
        "post-comment",
        help="Post the live-acceptance verification comment on an issue.",
    )
    comment.add_argument("number", type=int, metavar="ISSUE_NUMBER")
    comment.add_argument("--body", required=True, metavar="FILE")
    comment.add_argument("--mode", required=True, choices=ISSUE_MODES)
    comment.add_argument("--approved-digest", required=True, metavar="SHA256")
    comment.add_argument("--repo", metavar="OWNER/REPO")

    for writer in (archive, create, extract, draft, post, comment):
        writer.add_argument("--approval-view", metavar="FILE", help="Exact rendered file to validate before writing.")
    _add_handoff_commands(subparsers)

    return parser


def main() -> None:
    """Parse CLI arguments and dispatch to the selected subcommand."""
    configure_stdout_utf8()
    args = build_parser().parse_args()
    if args.subcommand in ("prepare-handoff", "cleanup-handoff"):
        cmd_run_handoff(
            args.subcommand,
            args.workflow,
            args.run,
            getattr(args, "approve", False),
            kind=getattr(args, "kind", "issue"),
        )
    elif args.subcommand == "gather":
        cmd_gather(args.number, args.repo)
    elif args.subcommand == "assess-readiness":
        cmd_assess_readiness(args.number, args.repo)
    elif args.subcommand == "verify-composition":
        cmd_verify_composition(args.sources, args.body, args.ledger)
    elif args.subcommand == "reconciliation-sources":
        cmd_reconciliation_sources(args.number, args.repo)
    elif args.subcommand == "approval-view":
        cmd_approval_view(
            args.operation,
            args.number,
            args.body,
            args.repo,
            args.link,
            args.title,
            args.head,
            args.base,
            args.ledger,
            args.approval_view,
            **({"sources_path": args.sources} if args.sources else {}),
        )
    elif args.subcommand == "archive-description":
        cmd_archive_description(args.number, args.body, args.mode, args.approved_digest, args.repo, args.approval_view)
    elif args.subcommand == "create":
        cmd_create(
            args.title,
            args.body,
            args.sources,
            args.ledger,
            args.mode,
            args.approved_digest,
            args.repo,
            args.approval_view,
        )
    elif args.subcommand == "extract":
        cmd_extract(
            args.parent,
            args.link,
            args.title,
            args.body,
            args.mode,
            args.approved_digest,
            args.repo,
            args.approval_view,
        )
    elif args.subcommand == "open-draft-pr":
        cmd_open_draft_pr(
            args.number,
            args.head,
            args.base,
            args.title,
            args.body,
            args.mode,
            args.approved_digest,
            args.repo,
            args.approval_view,
        )
    elif args.subcommand == "post-comment":
        cmd_post_comment(args.number, args.body, args.mode, args.approved_digest, args.repo, args.approval_view)
    else:
        cmd_post_body(
            args.number, args.mode, args.body, args.approved_digest, args.repo, args.ledger, args.approval_view
        )


if __name__ == "__main__":  # pragma: no cover -- exercised through main()
    main()
