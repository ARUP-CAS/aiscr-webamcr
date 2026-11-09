#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: c35418343fe8896348732bd54f8256de17338f8d 2026-11-07T14:33:16+01:00

"""Gather, render, and post governed GitHub PR reviews.

``gather`` is read-only and acquires the pull-request diff. ``render`` creates a canonical review bundle and an approval
view without contacting GitHub, and refuses when coverage is incomplete or a finding is unplaced. ``post`` accepts only
that bundle, re-verifies the findings ledger, and enforces the selected identity mode and the unchanged interactive
approval file before any GitHub write. ``repair`` posts standalone inline roots and amends a submitted review body under
its own approval digest. Normal reviews and body repairs validate structured advisory observations and their one
rendered section; legacy pending records require regeneration and renewed approval. ``post-summary`` posts the exact
approved PR summary file to the explicitly selected surface.
``cleanup`` removes only the prescribed artifacts from one bounded review run directory in each root after the workflow
reaches a terminal outcome. ``prepare-run`` creates the directories and sidecar pointer before body authoring.

Contract: review/pr-review, workflow/github-write-fidelity
Class: tool
Exit codes: 0 success; 1 findings, refused write, or error; 2 usage error
"""

from __future__ import annotations

# The deterministic CLI intentionally keeps its tightly coupled command boundary
# in one auditable module.
# pylint: disable=too-many-lines
import argparse
import html
import json
import os
import re
import stat
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from lib import local_scratch_paths, runtime_env  # noqa: E402
from lib.log_utils import log_warn  # noqa: E402
from lib.proc_utils import configure_stdout_utf8, run_exact, utf8_child_env  # noqa: E402

from github import github_references, github_utils  # noqa: E402
from github.github_utils import PostingContract  # noqa: E402

REVIEW_MARKER = "<!-- aiscr-review-pr:v1 -->"
SUMMARY_MARKER = "<!-- aiscr-review-pr:summary -->"
INTERACTIVE_REVIEW_DISCLOSURE = (
    "Review conducted with AI assistance through the AIS CR review workflow; "
    "the posting reviewer reviewed and approved these findings."
)
INTERACTIVE_SUMMARY_DISCLOSURE = (
    "This PR summary was prepared with AI assistance through the AIS CR review "
    "workflow; the posting reviewer reviewed and approved it for posting."
)
AUTOMATED_DISCLOSURE = (
    "Automated review conducted with AI assistance through the AIS CR review "
    "workflow; this review is non-blocking and remains subject to human disposition."
)
BUNDLE_SCHEMA = "aiscr-review-pr-bundle-v3"
REPAIR_BUNDLE_SCHEMA = "aiscr-review-pr-repair-bundle-v4"
COVERAGE_SCHEMA = "aiscr-review-pr-coverage-v1"
FINDINGS_LEDGER_SCHEMA = "aiscr-review-pr-findings-ledger-v4"
OBSERVATIONS_OPEN = "<!-- aiscr-review-pr:preexisting-observations -->"
OBSERVATIONS_CLOSE = "<!-- /aiscr-review-pr:preexisting-observations -->"
OBSERVATIONS_HEADING = "## Pre-existing observations"
OBSERVATION_DISPOSITIONS = ("fix-in-pr", "track-separately")
OBSERVATION_TRACKING_STATES = ("pending", "reused", "created")
OBSERVATION_PENDING_REASON_CODES = ("declined", "deferred", "unavailable", "failed", "uncertain")
OBSERVATION_EVIDENCE_TIERS = ("reproduced", "instrumented", "read", "reported", "inferred")
OBSERVATION_ANCHOR_KINDS = ("line", "file")
OBSERVATION_MARKER_PREFIX = "<!-- aiscr-review-pr:observation"
OBSERVATION_MARKER_RE = re.compile(r"<!-- aiscr-review-pr:observation (\S+) (\S+) -->")
FILE_STATE_AVAILABLE = "available"
FILE_STATE_UNAVAILABLE = "unavailable"
PLACEMENT_INLINE_ROOT = "inline-root"
PLACEMENT_REPLY = "reply"
PLACEMENT_BODY_ONLY = "body-only"
PLACEMENTS = (PLACEMENT_INLINE_ROOT, PLACEMENT_REPLY, PLACEMENT_BODY_ONLY)
BODY_ONLY_REASONS = frozenset(
    {
        "off-diff",
        "cross-cutting",
        "process",
        "needs-verification",
    }
)
OUTSTANDING_DISPOSITIONS = frozenset({"resolved", "disputed", "not-addressed"})
COMMUNICATION_REPLY = "reply"
COMMUNICATION_NO_REPLY = "no-reply"
THREAD_COMMUNICATIONS = frozenset({COMMUNICATION_REPLY, COMMUNICATION_NO_REPLY})
SILENCE_RESOLUTION_REASONS = frozenset({"silence", "no-reply", "no-author-reply"})
DIFF_SOURCES = ("local-diff", "pull-files", "compare", "pr-diff", "git-diff")
REVIEW_ONLY_BODY_FINDINGS = {
    "limb": "review-only",
    "holder": "session agent",
    "scope": (
        "Findings that exist only as prose in another reviewer's review body "
        "are supplied by the session agent at reconciliation. Completeness of "
        "that limb is never inferred from an empty outstanding list."
    ),
}
MODES = github_utils.MODES
REVIEW_EVENTS = ("COMMENT", "REQUEST_CHANGES", "APPROVE")
SUMMARY_TARGETS = ("comment", "description")
SUMMARY_TITLE_PATTERN = re.compile(
    r"^# PR summary — \[[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[1-9][0-9]*\](?:\(\S+\)|\[[^\]\r\n]*\])?$"
)
SUMMARY_METADATA_FIELDS = (
    "Title",
    "URL",
    "Referenced items",
    "Author",
    "Base ← head",
    "Head SHA",
    "Size",
    "State",
    "Marked AIS CR review baseline",
    "Prior PR summary",
)
SUMMARY_SECTION_HEADINGS = (
    "## Purpose and scope",
    "## Change map by area",
    "## Change walkthrough",
    "## Attention hints (summary only)",
    "## Validation / test surfaces visible in the PR",
    "## Author context",
    "## Lineage",
)
AUTHOR_CONTEXT_OPEN = "<!-- aiscr-review-pr:author-context -->"
AUTHOR_CONTEXT_CLOSE = "<!-- /aiscr-review-pr:author-context -->"
DESCRIPTION_ARCHIVE_MARKER = "<!-- aiscr-review-pr:description-archive -->"
LEDGER_MARKER = "<!-- aiscr-review-pr:ledger -->"
PROVENANCE_ORIGINAL_OPEN = "<!-- aiscr-review-pr:original -->"
PROVENANCE_ORIGINAL_CLOSE = "<!-- /aiscr-review-pr:original -->"
# The posted marker carries a digest of the body as approved, so a later round can
# tell "nobody touched this since we posted it" from "the author edited it".
SUMMARY_MARKER_PATTERN = re.compile(r"<!-- aiscr-review-pr:summary(?: digest=([0-9a-f]{64}))? -->")
# Reference extraction, one-hop traversal, and the load-bearing set are shared with the
# issue engine: both reconcile GitHub bodies, so the mechanism has one home.
LOAD_BEARING_PATTERNS = github_utils.LOAD_BEARING_PATTERNS
# Single owning definition per class for every name a review run may write. Cleanup
# enforcement and the workflow procedure both resolve these sets; they must not encode
# them independently. ``list-run-artifacts`` prints the union, or one class with --class.
BULK_RUN_ARTIFACTS = frozenset(
    {
        "pr-context.json",
        "review-payload.json",
        "review-replies.json",
        "review-bundle.json",
        "ledger.json",
        "sources.json",
        "findings-ledger.json",
        "pr-diff.patch",
        "repair-payload.json",
        "repair-reopen.json",
        "repair-bundle.json",
    }
)
HANDOFF_RUN_ARTIFACTS = frozenset(
    {
        "POINTER.md",
        "pr-summary.md",
        "review-approval.md",
        "repair-body.md",
        "repair-approval.md",
    }
)
PRESCRIBED_RUN_ARTIFACTS = BULK_RUN_ARTIFACTS | HANDOFF_RUN_ARTIFACTS
ALLOWED_BULK_ARTIFACTS = BULK_RUN_ARTIFACTS
ALLOWED_HANDOFF_ARTIFACTS = HANDOFF_RUN_ARTIFACTS
_DIFF_GIT_RE = re.compile(r"^diff --git a/(.*) b/(.*)$")
_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_THREAD_FINDING_ID_RE = re.compile(r"^thread:([1-9][0-9]*)$")
REVIEW_RUN_DIR_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+-pr-[1-9][0-9]*-[0-9a-fA-F]{7,40}$")
REPO_ROOT = Path(_SCRIPTS_DIR).parents[1]
# The multi-repository acquisition extension is hub-side tooling; a delivered copy may not carry
# it, so the producer checks for it before invoking anything.
_BRIDGE_SCRIPT = Path(_SCRIPTS_DIR) / "sibling" / "sibling_git_read.py"
REVIEW_SCRATCH_ROOT = runtime_env.review_pr_cache_dir(REPO_ROOT)
REVIEW_HANDOFF_ROOT = REPO_ROOT / ".agents" / "local_scratch" / "aiscr-review-pr"


# ---------------------------------------------------------------------------
# General helpers
#
# The process funnel, file helpers, identity gate, approval digest, and
# marker/disclosure contract live in ``github_utils`` so the issue engine shares
# one write model with this one.
# ---------------------------------------------------------------------------

_abort = github_utils.abort
_run = github_utils.run
_gh = github_utils.gh
_resolve_repo = github_utils.resolve_repo
_load_json = github_utils.load_json
_write_json = github_utils.write_json
_write_text = github_utils.write_text
_temporary_json = github_utils.temporary_json
_env_is_set = github_utils.env_is_set
_try_run = github_utils.try_run
_try_run_tolerant = github_utils.try_run_tolerant
_validate_write_environment = github_utils.validate_write_environment
_paginated_rest_items = github_utils.paginated_rest_items
_paginated_graphql_nodes = github_utils.paginated_graphql_nodes
detect_load_bearing = github_utils.detect_load_bearing
_extract_references = github_utils.extract_references
_dedupe_by_target = github_utils.dedupe_by_target


# ---------------------------------------------------------------------------
# Diff acquisition, coverage, and findings-ledger validation
# ---------------------------------------------------------------------------


def _anchors_from_patch(path: str, patch: str) -> list[dict[str, Any]]:
    """Return every diff line a new inline comment may legally target."""
    anchors: list[dict[str, Any]] = []
    old_line = 0
    new_line = 0
    for raw in patch.splitlines():
        hunk = _HUNK_RE.match(raw)
        if hunk:
            old_line = int(hunk.group(1))
            new_line = int(hunk.group(3))
            continue
        if raw.startswith("\\") or raw.startswith("diff ") or raw.startswith("index "):
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            anchors.append({"path": path, "line": new_line, "side": "RIGHT"})
            new_line += 1
        elif raw.startswith("-"):
            anchors.append({"path": path, "line": old_line, "side": "LEFT"})
            old_line += 1
        elif raw.startswith(" "):
            anchors.append({"path": path, "line": new_line, "side": "RIGHT"})
            anchors.append({"path": path, "line": old_line, "side": "LEFT"})
            old_line += 1
            new_line += 1
    return anchors


def _parse_unified_diff(text: str) -> dict[str, str]:
    """Map new-file paths to their unified-diff hunk text."""
    patches: dict[str, str] = {}
    current_path: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_path and current_lines:
            patches[current_path] = "\n".join(current_lines)

    for raw in text.splitlines():
        git_header = _DIFF_GIT_RE.match(raw)
        if git_header:
            flush()
            current_path = git_header.group(2)
            current_lines = [raw]
            continue
        if raw.startswith("+++ "):
            plus_path = raw[4:]
            if plus_path.startswith("b/"):
                plus_path = plus_path[2:]
            if plus_path not in {"/dev/null", "nul"}:
                current_path = plus_path
            if current_path is None:
                current_lines = [raw]
            else:
                current_lines.append(raw)
            continue
        if current_path is None:
            continue
        current_lines.append(raw)
    flush()
    return patches


def _file_record(
    path: str,
    additions: int,
    deletions: int,
    patch: str,
    source: str | None,
) -> dict[str, Any]:
    available = bool(patch.strip())
    changed_lines = additions + deletions
    if not available and changed_lines == 0:
        available = True
    return {
        "path": path,
        "additions": additions,
        "deletions": deletions,
        "changed_lines": changed_lines,
        "state": FILE_STATE_AVAILABLE if available else FILE_STATE_UNAVAILABLE,
        "source": source if available else None,
        "anchors": _anchors_from_patch(path, patch) if available and patch.strip() else [],
    }


def _recompute_coverage(
    files: list[dict[str, Any]],
    *,
    base_sha: str,
    head_sha: str,
    sources_attempted: list[str],
    unreviewable: bool,
) -> dict[str, Any]:
    unread = [item for item in files if item["state"] == FILE_STATE_UNAVAILABLE]
    return {
        "schema": COVERAGE_SCHEMA,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "sources_attempted": sources_attempted,
        "unreviewable": unreviewable,
        "files": files,
        "unread_files": len(unread),
        "unread_changed_lines": sum(int(item["changed_lines"]) for item in unread),
    }


def _github_changed_files(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not items:
        return records
    for item in items:
        if not isinstance(item, dict):
            continue
        path = str(item.get("filename") or "")
        if not path:
            continue
        additions = int(item.get("additions") or 0)
        deletions = int(item.get("deletions") or 0)
        patch = item.get("patch") if isinstance(item.get("patch"), str) else ""
        source = "pull-files" if patch.strip() else None
        records.append(_file_record(path, additions, deletions, patch or "", source))
    return records


def _fill_missing_patches(
    files: list[dict[str, Any]],
    patches: dict[str, str],
    source: str,
) -> None:
    for item in files:
        if item["state"] == FILE_STATE_AVAILABLE:
            continue
        patch = patches.get(item["path"])
        if not patch:
            continue
        filled = _file_record(item["path"], item["additions"], item["deletions"], patch, source)
        item.update(filled)


def _commit_reachable_locally(sha: str) -> bool:
    ok, _stdout = _try_run(["git", "cat-file", "-e", f"{sha}^{{commit}}"])
    return ok


def _commit_reachable_on_platform(owner_repo: str, sha: str) -> bool:
    ok, _stdout = _try_run(["gh", "api", f"repos/{owner_repo}/commits/{sha}", "-q", ".sha"])
    return ok


def _load_local_diff(path: str) -> dict[str, str]:
    """Parse a supplied patch, substituting bytes that are not valid UTF-8.

    A patch is parsed structurally — changed-line coverage and inline anchors, never published text — and the documented
    remedy writes it with ``git diff --output=``, whose bytes are raw, so an undecodable byte must not abort the read.
    """
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        _abort(f"cannot read local diff '{path}': {exc}")
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    return _parse_unified_diff(text)


def _compare_files(owner_repo: str, base_sha: str, head_sha: str) -> list[dict[str, Any]] | None:
    ok, stdout = _try_run(["gh", "api", f"repos/{owner_repo}/compare/{base_sha}...{head_sha}"])
    if not ok:
        return None
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list):
        return None
    return [item for item in files if isinstance(item, dict)]


def _unified_diff_from_pr(owner_repo: str, pr_number: int) -> dict[str, str]:
    ok, stdout = _try_run_tolerant(["gh", "pr", "diff", str(pr_number), "--repo", owner_repo])
    if not ok or not stdout.strip():
        return {}
    return _parse_unified_diff(stdout)


def _unified_diff_from_git(base_sha: str, head_sha: str) -> dict[str, str]:
    ok, stdout = _try_run_tolerant(["git", "diff", f"{base_sha}...{head_sha}"])
    if not ok or not stdout.strip():
        return {}
    return _parse_unified_diff(stdout)


def _declared_files_from_patches(patches: dict[str, str], source: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for path, patch in patches.items():
        additions = sum(1 for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in patch.splitlines() if line.startswith("-") and not line.startswith("---"))
        files.append(_file_record(path, additions, deletions, patch, source))
    return files


def _merge_local_onto_declared(
    declared: list[dict[str, Any]],
    local_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    local_by_path = {item["path"]: item for item in local_files}
    merged: list[dict[str, Any]] = []
    for item in declared:
        local = local_by_path.get(item["path"])
        if local and local["state"] == FILE_STATE_AVAILABLE:
            record = dict(item)
            record["state"] = FILE_STATE_AVAILABLE
            record["source"] = "local-diff"
            record["anchors"] = local["anchors"]
            merged.append(record)
        else:
            merged.append(item)
    return merged


def _patches_from_compare(compared: list[dict[str, Any]]) -> dict[str, str]:
    patches: dict[str, str] = {}
    for item in compared:
        path = item.get("filename")
        patch = item.get("patch")
        if isinstance(path, str) and path and isinstance(patch, str) and patch.strip():
            patches[path] = patch
    return patches


def _fill_from_remaining_sources(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    files: list[dict[str, Any]],
    attempted: list[str],
    owner_repo: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
) -> None:
    if any(item["state"] == FILE_STATE_UNAVAILABLE for item in files):
        attempted.append("compare")
        compared = _compare_files(owner_repo, base_sha, head_sha)
        if compared is not None:
            _fill_missing_patches(files, _patches_from_compare(compared), "compare")
    if any(item["state"] == FILE_STATE_UNAVAILABLE for item in files):
        attempted.append("pr-diff")
        _fill_missing_patches(files, _unified_diff_from_pr(owner_repo, pr_number), "pr-diff")
    if any(item["state"] == FILE_STATE_UNAVAILABLE for item in files):
        attempted.append("git-diff")
        _fill_missing_patches(files, _unified_diff_from_git(base_sha, head_sha), "git-diff")


def _acquire_without_declared_list(
    attempted: list[str],
    owner_repo: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
) -> list[dict[str, Any]]:
    attempted.extend(source for source in DIFF_SOURCES[2:] if source not in attempted)
    compared = _compare_files(owner_repo, base_sha, head_sha)
    if compared is not None:
        files = _github_changed_files(compared)
        for item in files:
            if item["source"] is None and item["state"] == FILE_STATE_AVAILABLE:
                item["source"] = "compare"
        if files:
            return files
    pr_patches = _unified_diff_from_pr(owner_repo, pr_number)
    if pr_patches:
        return _declared_files_from_patches(pr_patches, "pr-diff")
    git_patches = _unified_diff_from_git(base_sha, head_sha)
    if git_patches:
        return _declared_files_from_patches(git_patches, "git-diff")
    return []


def _acquire_coverage(
    owner_repo: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
    local_diff_path: str | None = None,
) -> dict[str, Any]:
    """Acquire declared changed files and fill patches from the fallback chain."""
    attempted: list[str] = []
    local_files: list[dict[str, Any]] = []
    if local_diff_path:
        attempted.append("local-diff")
        local_files = _declared_files_from_patches(_load_local_diff(local_diff_path), "local-diff")

    attempted.append("pull-files")
    listed = _paginated_rest_items(
        f"repos/{owner_repo}/pulls/{pr_number}/files",
        runner=_try_run,
    )
    if listed is not None:
        files = _github_changed_files(listed)
        if local_files:
            files = _merge_local_onto_declared(files, local_files)
        _fill_from_remaining_sources(files, attempted, owner_repo, pr_number, base_sha, head_sha)
    elif local_files:
        files = local_files
        _fill_from_remaining_sources(files, attempted, owner_repo, pr_number, base_sha, head_sha)
    else:
        files = _acquire_without_declared_list(attempted, owner_repo, pr_number, base_sha, head_sha)

    unreviewable = False
    if not files:
        platform_ok = _commit_reachable_on_platform(owner_repo, base_sha) and _commit_reachable_on_platform(
            owner_repo,
            head_sha,
        )
        local_ok = _commit_reachable_locally(base_sha) and _commit_reachable_locally(head_sha)
        unreviewable = not platform_ok and not local_ok

    return _recompute_coverage(
        files,
        base_sha=base_sha,
        head_sha=head_sha,
        sources_attempted=attempted,
        unreviewable=unreviewable,
    )


def _apply_local_diff(coverage: dict[str, Any], local_diff_path: str) -> dict[str, Any]:
    """Fill unavailable files from a locally produced unified diff."""
    patches = _load_local_diff(local_diff_path)
    files = [dict(item) for item in coverage.get("files") or []]
    _fill_missing_patches(files, patches, "local-diff")
    attempted = list(coverage.get("sources_attempted") or [])
    if "local-diff" not in attempted:
        attempted.append("local-diff")
    return _recompute_coverage(
        files,
        base_sha=str(coverage.get("base_sha") or ""),
        head_sha=str(coverage.get("head_sha") or ""),
        sources_attempted=attempted,
        unreviewable=False,
    )


def _coverage_refusal_message(coverage: dict[str, Any]) -> str:
    if coverage.get("unreviewable"):
        return (
            "Pull request is unreviewable: base commit "
            f"{coverage.get('base_sha')} and/or head commit {coverage.get('head_sha')} "
            "are unreachable from the platform and from the local checkout."
        )
    unread_files = int(coverage.get("unread_files") or 0)
    unread_lines = int(coverage.get("unread_changed_lines") or 0)
    base = coverage.get("base_sha")
    head = coverage.get("head_sha")
    return (
        f"Coverage incomplete: {unread_files} unread file(s), "
        f"{unread_lines} unread changed line(s). Content unavailable from the "
        "platform interface is resolved by a local checkout. Supply a locally "
        f"produced diff for base {base} and head {head}: "
        f"`git diff {base}...{head} > pr-diff.patch`, then re-run render with "
        "`--local-diff pr-diff.patch`."
    )


def _refuse_incomplete_coverage(coverage: dict[str, Any]) -> None:
    if coverage.get("unreviewable"):
        _abort(_coverage_refusal_message(coverage))
    if int(coverage.get("unread_files") or 0) or int(coverage.get("unread_changed_lines") or 0):
        _abort(_coverage_refusal_message(coverage))


def _anchor_set(coverage: dict[str, Any]) -> set[tuple[str, int, str]]:
    anchors: set[tuple[str, int, str]] = set()
    for item in coverage.get("files") or []:
        for anchor in item.get("anchors") or []:
            path = anchor.get("path")
            line = anchor.get("line")
            side = anchor.get("side")
            if (
                isinstance(path, str)
                and isinstance(line, int)
                and not isinstance(line, bool)
                and side in {"LEFT", "RIGHT"}
            ):
                anchors.add((path, line, side))
    return anchors


def _coverage_paths(coverage: dict[str, Any]) -> set[str]:
    """Files the acquired coverage reaches, for a file-level anchor."""
    return {
        item["path"]
        for item in coverage.get("files") or []
        if isinstance(item.get("path"), str) and item["path"].strip()
    }


def _is_vendor_bot(login: str | None) -> bool:
    if not login:
        return False
    lowered = login.lower()
    return lowered.endswith("[bot]") or lowered.endswith("-bot")


def _thread_roots_from_conversation(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    roots: list[dict[str, Any]] = []
    for thread in conversation.get("review_threads") or []:
        comments = thread.get("comments") or []
        if not comments:
            continue
        root = comments[0]
        roots.append(
            {
                "id": root.get("id"),
                "node_id": thread.get("node_id") or "",
                "path": thread.get("path"),
                "line": thread.get("line"),
                "body": root.get("body") or "",
                "outdated": bool(thread.get("outdated")),
                "resolved": bool(thread.get("resolved")),
            }
        )
    return roots


def _occupied_thread_locations(existing_threads: list[dict[str, Any]]) -> set[tuple[str, int]]:
    """Path and line pairs that already have a thread root.

    Reply matching uses path and line, not side. A new inline root at one of these locations is a duplicate thread, not
    a new finding.
    """
    occupied: set[tuple[str, int]] = set()
    for thread in existing_threads:
        path = thread.get("path")
        line = thread.get("line")
        if not isinstance(path, str) or not path.strip():
            continue
        if isinstance(line, bool) or not isinstance(line, int):
            continue
        occupied.add((path, line))
    return occupied


def _enumerate_outstanding_findings(  # pylint: disable=too-many-locals
    conversation: dict[str, Any],
    lineage: dict[str, Any],
) -> list[dict[str, Any]]:
    """Enumerate every mechanically visible inline thread with its reviewer history.

    ``prior_review_reply`` records whether the thread already carries a reply from an author of a marked AIS CR review:
    at gather time every such reply is from a prior round, so it is the mechanical basis a standing dispute rests on
    when a later round records the dispute without replying again.
    """
    marked_ids: set[int] = set()
    for comment in lineage.get("last_review_comments") or []:
        comment_id = comment.get("id")
        if isinstance(comment_id, int) and not isinstance(comment_id, bool):
            marked_ids.add(comment_id)
    reviewer_logins = {
        login for login in lineage.get("reviewer_logins") or [] if isinstance(login, str) and login.strip()
    }
    findings: list[dict[str, Any]] = []
    for thread in conversation.get("review_threads") or []:
        comments = thread.get("comments") or []
        if not comments:
            continue
        root = comments[0]
        root_id = root.get("id")
        login = root.get("author")
        if isinstance(root_id, int) and root_id in marked_ids:
            kind = "aiscr"
        elif _is_vendor_bot(login if isinstance(login, str) else None):
            kind = "vendor-bot"
        else:
            kind = "human"
        prior_review_reply = any(comment.get("author") in reviewer_logins for comment in comments[1:])
        root_body = str(root.get("body") or "")
        marker = OBSERVATION_MARKER_RE.search(root_body)
        findings.append(
            {
                "id": f"thread:{root_id}",
                "root_comment_id": root_id,
                "path": thread.get("path"),
                "line": thread.get("line"),
                "author": login,
                "author_kind": kind,
                "platform_resolved": bool(thread.get("resolved")),
                "platform_outdated": bool(thread.get("outdated")),
                "prior_review_reply": prior_review_reply,
                "body": root_body,
                "observation_id": marker.group(1) if marker else None,
            }
        )
    return findings


def _emit_json(payload: Any, output_path: str | None) -> None:
    """Emit JSON to stdout, or to an explicit UTF-8 destination.

    A shell redirect is not a safe substitute: Windows PowerShell 5.1 writes UTF-16 for ``>``, which every UTF-8 reader
    in this workflow rejects. Writing the file here keeps the encoding a property of the producer rather than of the
    operator's shell.
    """
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if output_path is None:
        print(rendered)
        return
    Path(output_path).write_text(rendered + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {output_path}")


def _observation_fields(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    """Check closed record shapes, including fields that would introduce verdict severity."""
    if not isinstance(value, dict) or set(value) != fields:
        _abort(f"{label} must be an object with exactly: {', '.join(sorted(fields))}.")
    return value


def _observation_text(value: Any, label: str) -> str:
    """Accept single-line data, never structural delimiters or control characters."""
    if not isinstance(value, str) or not value.strip():
        _abort(f"{label} must be non-empty text.")
    if any(ord(char) < 32 or ord(char) == 127 for char in value) or "<!--" in value or "-->" in value:
        _abort(f"{label} must be single-line data without control characters or comment delimiters.")
    return value.strip()


def _validate_observation_tracking(value: Any, label: str) -> None:
    """Check disjoint shapes for a pending handoff and a confirmed issue."""
    if not isinstance(value, dict) or value.get("state") not in OBSERVATION_TRACKING_STATES:
        _abort(f"{label} needs a tracking state of pending, reused, or created.")
    if value["state"] == "pending":
        _observation_fields(value, {"state", "reason", "reason_code"}, label)
        _observation_text(value["reason"], f"{label} reason")
        if value["reason_code"] not in OBSERVATION_PENDING_REASON_CODES:
            _abort(f"{label} reason_code must be one of: {', '.join(OBSERVATION_PENDING_REASON_CODES)}.")
        return
    _observation_fields(value, {"state", "issue"}, label)
    issue = _observation_fields(value["issue"], {"repository", "number", "url"}, f"{label} issue")
    repository = _observation_text(issue["repository"], f"{label} issue repository")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        _abort(f"{label} issue repository must be owner/repo.")
    number = issue["number"]
    if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
        _abort(f"{label} issue number must be a positive integer.")
    url = _observation_text(issue["url"], f"{label} issue URL")
    if url != f"https://github.com/{repository}/issues/{number}":
        _abort(f"{label} issue URL must identify the same repository and issue number.")


def _validate_observation_anchor(value: Any, label: str, coverage: dict[str, Any] | None) -> None:
    """Check an anchor's shape and its presence in coverage, not whether its place is the logical one."""
    if not isinstance(value, dict) or value.get("kind") not in OBSERVATION_ANCHOR_KINDS:
        _abort(f"{label} needs an anchor kind of line or file.")
    if value["kind"] == "line":
        _observation_fields(value, {"kind", "path", "line", "side"}, label)
        path = _observation_text(value["path"], f"{label} path")
        if isinstance(value["line"], bool) or not isinstance(value["line"], int):
            _abort(f"{label} line must be an integer.")
        if value["side"] not in {"LEFT", "RIGHT"}:
            _abort(f"{label} side must be LEFT or RIGHT.")
        if coverage is not None and (path, value["line"], value["side"]) not in _anchor_set(coverage):
            _abort(f"{label} is not present in the acquired diff; unverifiable anchors are refused.")
        return
    _observation_fields(value, {"kind", "path"}, label)
    path = _observation_text(value["path"], f"{label} path")
    if coverage is not None and path not in _coverage_paths(coverage):
        _abort(f"{label} names a file outside the acquired coverage.")


def _validate_preexisting_observations(  # pylint: disable=too-many-locals
    value: Any, finding_ids: set[str], coverage: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Verify recorded triage, not the conductor's provenance or repair-scope judgments."""
    if not isinstance(value, list):
        _abort(
            "preexisting_observations must be an explicit JSON array; regenerate the ledger, render, and approve again."
        )
    identities: set[str] = set()
    tracking_keys: set[str] = set()
    common = {"id", "tracking_key", "description", "evidence", "disposition", "rationale"}
    for index, record in enumerate(value, start=1):
        label = f"pre-existing observation {index}"
        if not isinstance(record, dict) or record.get("disposition") not in OBSERVATION_DISPOSITIONS:
            _abort(f"{label} needs exactly one disposition: fix-in-pr or track-separately.")
        fields = common | ({"repair", "anchor"} if record["disposition"] == "fix-in-pr" else {"tracking"})
        _observation_fields(record, fields, label)
        identity = _observation_text(record["id"], f"{label} id")
        key = _observation_text(record["tracking_key"], f"{label} tracking key")
        if identity in identities or identity in finding_ids or key in tracking_keys:
            _abort(f"{label} '{identity}' duplicates an identity, tracking key, or verdict-bearing finding.")
        identities.add(identity)
        tracking_keys.add(key)
        for field in ("description", "rationale"):
            _observation_text(record[field], f"observation '{identity}' {field}")
        evidence = record["evidence"]
        if not isinstance(evidence, list) or not evidence:
            _abort(f"observation '{identity}' needs non-empty provenance evidence references.")
        for reference in evidence:
            entry = _observation_fields(
                reference, {"location", "revision", "tier"}, f"observation '{identity}' evidence"
            )
            for field in ("location", "revision"):
                _observation_text(entry[field], f"observation '{identity}' evidence {field}")
            if entry["tier"] not in OBSERVATION_EVIDENCE_TIERS:
                _abort(
                    f"observation '{identity}' evidence tier must be "
                    "reproduced, instrumented, read, reported, or inferred."
                )
        if record["disposition"] == "fix-in-pr":
            _observation_text(record["repair"], f"observation '{identity}' proposed repair")
            _validate_observation_anchor(record["anchor"], f"observation '{identity}' anchor", coverage)
        else:
            _validate_observation_tracking(record["tracking"], f"observation '{identity}' tracking")
    return value


def _observation_literal(value: str) -> str:
    """Render field content as literal Markdown text rather than headings, links, or HTML."""
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", html.escape(value.strip(), quote=False))


def _render_observations(observations: list[dict[str, Any]]) -> str:
    """Project the approved records once; the machine ledger itself never gets posted."""
    lines = [
        OBSERVATIONS_OPEN,
        OBSERVATIONS_HEADING,
        "",
        "Advisory only: these observations predate the reviewed material and do not contribute to the verdict.",
        "",
    ]
    if not observations:
        lines.extend(["None identified.", ""])
    for record in observations:
        lines.extend(
            [
                f"### Observation: {_observation_literal(record['id'])}",
                "",
                f"- Tracking key: {_observation_literal(record['tracking_key'])}",
                f"- Observation: {_observation_literal(record['description'])}",
                f"- Disposition: `{record['disposition']}`",
            ]
        )
        if record["disposition"] == "fix-in-pr":
            lines.append(f"- Anchor: `{_anchor_place(record['anchor'])}`")
            lines.append("- Full record and proposed repair: the observation anchor on that place.")
        else:
            lines.append(f"- Rationale: {_observation_literal(record['rationale'])}")
            lines.extend(_observation_evidence_lines(record))
            tracking = record["tracking"]
            lines.append(f"- Tracking state: `{tracking['state']}`")
            if tracking["state"] == "pending":
                lines.append(f"- Tracking reason code: `{tracking['reason_code']}`")
                lines.append(f"- Tracking reason: {_observation_literal(tracking['reason'])}")
            else:
                lines.append(f"- Issue: {github_references.reference_link(tracking['issue']['url'].strip())}")
        lines.append("")
    lines.append(OBSERVATIONS_CLOSE)
    return "\n".join(lines)


def _anchor_place(anchor: dict[str, Any]) -> str:
    if anchor["kind"] == "line":
        return f"{anchor['path']}:{anchor['line']} ({anchor['side']})"
    return anchor["path"]


def _observation_evidence_lines(record: dict[str, Any]) -> list[str]:
    lines = ["- Provenance evidence:"]
    for entry in record["evidence"]:
        location = entry["location"].strip()
        display = (
            github_references.reference_link(location)
            if github_references.reference_target(location)
            else _observation_literal(location)
        )
        lines.append(f"  - {display}; revision: {_observation_literal(entry['revision'])}; tier: `{entry['tier']}`")
    return lines


def _observation_marker(record: dict[str, Any]) -> str:
    return f"{OBSERVATION_MARKER_PREFIX} {record['id']} {record['tracking_key']} -->"


def _render_observation_anchor(record: dict[str, Any]) -> str:
    """Render the anchor's canonical record, the only full record for an anchored observation."""
    lines = [
        _observation_marker(record),
        f"### Pre-existing observation: {_observation_literal(record['id'])}",
        "",
        f"- Tracking key: {_observation_literal(record['tracking_key'])}",
        f"- Observation: {_observation_literal(record['description'])}",
        "- Disposition: `fix-in-pr`",
        f"- Rationale: {_observation_literal(record['rationale'])}",
    ]
    lines.extend(_observation_evidence_lines(record))
    lines.extend(
        [
            f"- Proposed repair: {_observation_literal(record['repair'])}",
            f"- Anchor: `{_anchor_place(record['anchor'])}`",
            "",
            "Advisory only: this observation predates the reviewed material and does not contribute to the verdict.",
        ]
    )
    return "\n".join(lines)


def _observation_anchors(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Derive every fix-in-pr anchor from the records; the ledger stays the single home."""
    anchors: list[dict[str, Any]] = []
    for record in records:
        if record.get("disposition") != "fix-in-pr":
            continue
        place = record["anchor"]
        anchor = {
            "observation_id": record["id"],
            "kind": place["kind"],
            "path": place["path"],
            "marker": _observation_marker(record),
            "body": _render_observation_anchor(record),
        }
        if place["kind"] == "line":
            anchor["line"] = place["line"]
            anchor["side"] = place["side"]
        anchors.append(anchor)
    return anchors


def _observation_html_end(line: str) -> str | None:
    """Recognize raw HTML blocks, retaining long-lived blocks across blank lines."""
    for opening, closing in (
        (r"<!--", r"-->"),
        (r"<\?", r"\?>"),
        (r"<!\[CDATA\[", r"\]\]>"),
        (r"<![A-Z]", r">"),
    ):
        if re.match(r" {0,3}" + opening, line):
            return closing
    raw_tag = re.match(r" {0,3}<(script|pre|style|textarea)(?=[ \t>]|$)", line, re.IGNORECASE)
    if raw_tag:
        return rf"</{raw_tag[1]}>"
    if re.match(r" {0,3}</?[A-Za-z][A-Za-z0-9-]*(?=[ \t/>]|$)", line):
        return ""
    return None


def _observation_prefix_is_top_level(prefix: str) -> bool:
    """Fail closed on open fences, raw HTML, and unfinished HTML tokenization.

    Root delimiters cannot inherit list/quote indentation. Balanced fences and blank-ended HTML are supported; an
    ambiguous unclosed container fence is rejected rather than silently closed. The standard-library HTML tokenizer
    keeps an unfinished quoted attribute from appearing to end merely because a Markdown blank line was encountered.
    """
    fence = ""
    html_end: str | None = None
    html_lines: list[str] = []
    markup = HTMLParser(convert_charrefs=False)
    # The standalone opening delimiter follows the final newline immediately; that
    # newline does not supply an additional blank line to terminate an HTML block.
    for line in re.split(r"\r\n|\r|\n", prefix)[:-1]:
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*", line):
                fence = ""
            continue
        if html_end is None:
            opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})(.*)", line)
            if opening and (opening[1][0] != "`" or "`" not in opening[2]):
                fence = opening[1]
                continue
            html_end = _observation_html_end(line)
            if html_end is None:
                continue
            html_lines.clear()
        html_lines.append(line)
        ended = not line.strip() if html_end == "" else re.search(html_end, line, re.IGNORECASE)
        if ended:
            markup.reset()
            try:
                markup.feed("\n".join(html_lines) + "\n")
            except AssertionError:
                return False
            if markup.rawdata:
                return False
            html_end = None
    return not fence and html_end is None


def _with_observations(body: str, observations: list[dict[str, Any]], *, inject: bool = False) -> str:
    """Insert a missing section only at render time; otherwise require its exact projection."""
    expected = _render_observations(observations)
    counts = (body.count(OBSERVATIONS_OPEN), body.count(OBSERVATIONS_CLOSE))
    headings = re.findall(r"(?im)^#{1,6}[ \t]+pre[- ]existing[ -]observations[ \t]*$", body)
    if counts == (0, 0) and not headings and inject:
        body = body.rstrip() + "\n\n" + expected
    elif counts != (1, 1) or len(headings) != 1:
        _abort(
            "review body needs exactly one delimited pre-existing observations section; "
            "regenerate, render, and approve again."
        )
    start = body.index(OBSERVATIONS_OPEN)
    end = body.index(OBSERVATIONS_CLOSE) + len(OBSERVATIONS_CLOSE)
    if body[start:end] != expected:
        _abort("pre-existing observations section disagrees with its structured records; re-render and approve again.")
    if (start and body[start - 1] not in "\r\n") or (end < len(body) and body[end] not in "\r\n"):
        _abort("pre-existing observations delimiters must occupy standalone lines in top-level Markdown context.")
    if not _observation_prefix_is_top_level(body[:start]):
        _abort(
            "pre-existing observations require top-level Markdown context; close preceding code fences or raw HTML "
            "before rendering or posting."
        )
    return body


def _validate_findings_ledger(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    ledger: Any, coverage: dict[str, Any] | None = None
) -> dict[str, Any]:
    if not isinstance(ledger, dict):
        _abort("findings ledger must be a JSON object.")
    if ledger.get("schema") == "aiscr-review-pr-findings-ledger-v3":
        _abort(
            "findings ledger v3 is superseded by v4: every pending observation needs a reason_code "
            f"({', '.join(OBSERVATION_PENDING_REASON_CODES)}); regenerate the ledger, render, and approve again."
        )
    if ledger.get("schema") != FINDINGS_LEDGER_SCHEMA:
        _abort(
            f"findings ledger schema must be '{FINDINGS_LEDGER_SCHEMA}'; "
            "regenerate the ledger, render, and approve again."
        )
    new_findings = ledger.get("new_findings")
    outstanding = ledger.get("outstanding")
    if not isinstance(new_findings, list):
        _abort("findings ledger new_findings must be a JSON array.")
    if not isinstance(outstanding, list):
        _abort("findings ledger outstanding must be a JSON array.")
    seen_ids: set[str] = set()
    for index, finding in enumerate(new_findings, start=1):
        if not isinstance(finding, dict):
            _abort(f"new finding {index} must be a JSON object.")
        finding_id = finding.get("id")
        if not isinstance(finding_id, str) or not finding_id.strip():
            _abort(f"new finding {index} is missing a non-empty id.")
        if finding_id in seen_ids:
            _abort(f"finding '{finding_id}' is placed more than once.")
        seen_ids.add(finding_id)
        placement = finding.get("placement")
        if placement not in PLACEMENTS:
            if placement in {None, ""}:
                _abort(f"finding '{finding_id}' has no declared placement.")
            _abort(f"finding '{finding_id}' placement must be one of: {', '.join(PLACEMENTS)}.")
        # A declared placement is exactly one kind. Carrying another kind's key alongside it
        # is a second placement, so a comment_id outside a reply placement is refused.
        if "comment_id" in finding and placement != PLACEMENT_REPLY:
            _abort(f"finding '{finding_id}' is placed more than once.")
        if placement == PLACEMENT_BODY_ONLY:
            reason = finding.get("reason")
            if reason not in BODY_ONLY_REASONS:
                _abort(
                    f"finding '{finding_id}' body-only reason must be one of: {', '.join(sorted(BODY_ONLY_REASONS))}."
                )
        if placement == PLACEMENT_INLINE_ROOT:
            for key in ("path", "line", "side"):
                if key not in finding:
                    _abort(f"finding '{finding_id}' inline-root placement is missing '{key}'.")
        if placement == PLACEMENT_REPLY:
            comment_id = finding.get("comment_id")
            if isinstance(comment_id, bool) or not isinstance(comment_id, int) or comment_id <= 0:
                _abort(f"finding '{finding_id}' reply placement needs a positive comment_id.")
    outstanding_ids: set[str] = set()
    for index, item in enumerate(outstanding, start=1):
        if not isinstance(item, dict):
            _abort(f"outstanding finding {index} must be a JSON object.")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            _abort(f"outstanding finding {index} is missing a non-empty id.")
        if item_id in outstanding_ids:
            _abort(f"outstanding finding '{item_id}' is listed more than once.")
        outstanding_ids.add(item_id)
        disposition = item.get("disposition")
        if disposition not in OUTSTANDING_DISPOSITIONS:
            if disposition in {None, ""}:
                _abort(f"outstanding finding '{item_id}' has no disposition.")
            _abort(
                f"outstanding finding '{item_id}' disposition must be one of: "
                f"{', '.join(sorted(OUTSTANDING_DISPOSITIONS))}."
            )
        reason = str(item.get("reason") or "").strip()
        if not reason:
            _abort(f"outstanding finding '{item_id}' is missing a non-empty disposition reason.")
        if disposition == "resolved" and reason in SILENCE_RESOLUTION_REASONS:
            _abort(
                f"outstanding finding '{item_id}' cannot be resolved from silence; "
                "absence of an author reply is not resolution."
            )
        if disposition == "resolved" and item.get("platform_resolved") and not item.get("confirmed_against_diff"):
            _abort(
                f"outstanding finding '{item_id}' treats a platform-resolved thread "
                "as a claim; record confirmed_against_diff after checking the current diff."
            )
        if _THREAD_FINDING_ID_RE.fullmatch(item_id):
            _validate_thread_communication(item, item_id, str(disposition))
        else:
            # A review-body finding has no thread, so it has no closure to reverse.
            _validate_reopen_decision(item, item_id, False, "")
    _validate_preexisting_observations(
        ledger.get("preexisting_observations"),
        {identity.strip() for identity in seen_ids | outstanding_ids},
        coverage,
    )
    return ledger


def _no_reply_refusal(item_id: str, disposition: str, platform_resolved: bool) -> str:
    """Explain why this disposition owes a reply, so the refusal names the combination that failed."""
    if disposition == "disputed":
        return (
            f"outstanding inline thread '{item_id}' is disputed on a thread the platform does "
            "not mark resolved; a disputed disposition is always communicated by reply."
        )
    if platform_resolved:
        return (
            f"outstanding inline thread '{item_id}' is {disposition} on a thread the platform marks "
            "resolved; that contradicts a closure the reader can see and must be communicated by reply."
        )
    return (
        f"outstanding inline thread '{item_id}' is resolved on an unresolved thread; confirming a fix "
        "the reader cannot see must be communicated by reply."
    )


def _validate_thread_communication(item: dict[str, Any], item_id: str, disposition: str) -> None:
    """Refuse a mechanically enumerated thread whose disposition is not visibly communicated.

    A reply is owed where the disposition changes what a reader of the thread's current state would conclude. Only
    agreed closure (a platform-resolved thread confirmed resolved), unchanged open work (an unresolved thread left
    not-addressed), and a standing dispute (a platform-resolved thread whose earlier reviewer reply the gathered state
    carries, checked where that state is available) may take no-reply.
    """
    communication = item.get("communication")
    if communication not in THREAD_COMMUNICATIONS:
        _abort(
            f"outstanding inline thread '{item_id}' communication must be one of: "
            f"{', '.join(sorted(THREAD_COMMUNICATIONS))}."
        )
    platform_resolved = item.get("platform_resolved")
    if not isinstance(platform_resolved, bool):
        _abort(f"outstanding inline thread '{item_id}' must declare platform_resolved as a boolean.")
    no_reply_reason = str(item.get("no_reply_reason") or "").strip()
    agreed_closure = platform_resolved and disposition == "resolved"
    unchanged_open_work = not platform_resolved and disposition == "not-addressed"
    standing_dispute = platform_resolved and disposition == "disputed"
    if agreed_closure and communication != COMMUNICATION_NO_REPLY:
        _abort(
            f"outstanding inline thread '{item_id}' confirms a closure the platform already shows; "
            "an agreed closure must use no-reply rather than adding noise to a collapsed thread."
        )
    if communication == COMMUNICATION_NO_REPLY:
        if not agreed_closure and not unchanged_open_work and not standing_dispute:
            _abort(_no_reply_refusal(item_id, disposition, bool(platform_resolved)))
        if not no_reply_reason:
            _abort(f"outstanding inline thread '{item_id}' uses no-reply without a non-empty no_reply_reason.")
    elif no_reply_reason:
        _abort(f"outstanding inline thread '{item_id}' communicates by reply and must not carry no_reply_reason.")
    _validate_reopen_decision(item, item_id, bool(platform_resolved), str(communication))


def _validate_reopen_decision(item: dict[str, Any], item_id: str, platform_resolved: bool, communication: str) -> None:
    """Require an explicit reopen decision wherever a reply would otherwise land out of view.

    Replying to a resolved thread does not reopen it, so the reply stays collapsed. That makes the decision to leave it
    collapsed a real choice, and one that reverses nothing; the decision to reopen reverses a participant's closure.
    Both are recorded per thread and both carry a rationale, so neither happens by default.
    """
    decision_owed = platform_resolved and communication == COMMUNICATION_REPLY
    reopen = item.get("reopen")
    reopen_reason = str(item.get("reopen_reason") or "").strip()
    if not decision_owed:
        if reopen is not None or reopen_reason:
            _abort(
                f"outstanding inline thread '{item_id}' carries a reopen decision, but only a reply "
                "to a platform-resolved thread can reopen one."
            )
        return
    if not isinstance(reopen, bool):
        _abort(
            f"outstanding inline thread '{item_id}' replies to a platform-resolved thread and must "
            "declare reopen as a boolean; a reply to a resolved thread stays collapsed unless it reopens."
        )
    if not reopen_reason:
        _abort(f"outstanding inline thread '{item_id}' declares reopen without a non-empty reopen_reason.")


def _comment_key(comment: dict[str, Any]) -> tuple[str, int, str]:
    return (str(comment["path"]), int(comment["line"]), str(comment["side"]))


def _validate_placements(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches
    ledger: dict[str, Any],
    review: dict[str, Any],
    replies: list[dict[str, Any]],
    coverage: dict[str, Any],
    outstanding: list[dict[str, Any]],
    existing_threads: list[dict[str, Any]],
) -> None:
    comments = review.get("comments") or []
    if not isinstance(comments, list):
        comments = []
    comment_keys = [_comment_key(comment) for comment in comments]
    reply_ids = [int(reply["comment_id"]) for reply in replies]
    used_comments: list[tuple[str, int, str]] = []
    used_replies: set[int] = set()
    anchors = _anchor_set(coverage)
    threads_by_id = {
        int(thread["id"]): thread
        for thread in existing_threads
        if isinstance(thread.get("id"), int) and not isinstance(thread.get("id"), bool)
    }
    occupied_locations = _occupied_thread_locations(existing_threads)

    for finding in ledger["new_findings"]:
        finding_id = finding["id"]
        placement = finding["placement"]
        if placement == PLACEMENT_INLINE_ROOT:
            key = (str(finding["path"]), int(finding["line"]), str(finding["side"]))
            if key not in comment_keys:
                _abort(f"finding '{finding_id}' inline-root placement is not present in the review payload.")
            if key in used_comments:
                _abort(f"finding '{finding_id}' is placed more than once.")
            used_comments.append(key)
            if (key[0], key[1]) in occupied_locations:
                _abort(
                    f"finding '{finding_id}' inline-root placement {key[0]}:{key[1]} "
                    "matches an existing thread; post a reply to that thread instead of a new root."
                )
            if key not in anchors:
                _abort(
                    f"finding '{finding_id}' inline placement {key[0]}:{key[1]} {key[2]} "
                    "is not present in the acquired diff; unverifiable placements are refused."
                )
        elif placement == PLACEMENT_REPLY:
            comment_id = int(finding["comment_id"])
            if comment_id not in reply_ids:
                _abort(f"finding '{finding_id}' reply placement is not present in the replies file.")
            if comment_id in used_replies:
                _abort(f"finding '{finding_id}' is placed more than once.")
            used_replies.add(comment_id)
            thread = threads_by_id.get(comment_id)
            if thread and (thread.get("outdated") or thread.get("resolved")):
                reason = finding.get("stale_thread_reuse_reason")
                if not isinstance(reason, str) or not reason.strip():
                    _abort(
                        f"finding '{finding_id}' reuses an outdated or resolved thread "
                        "without an explicit stale_thread_reuse_reason."
                    )
        elif placement == PLACEMENT_BODY_ONLY and finding.get("reason") not in BODY_ONLY_REASONS:
            _abort(f"finding '{finding_id}' body-only reason is outside the closed set.")

    for key in comment_keys:
        if key not in used_comments:
            _abort(f"inline comment {key[0]}:{key[1]} {key[2]} has no matching findings-ledger placement.")
    _validate_outstanding_communication(ledger, outstanding, reply_ids, used_replies, threads_by_id)
    for comment_id in reply_ids:
        if comment_id not in used_replies:
            _abort(f"reply to comment {comment_id} has no matching findings-ledger placement or disposition.")


def _validate_outstanding_communication(
    ledger: dict[str, Any],
    outstanding: list[dict[str, Any]],
    reply_ids: list[int],
    used_replies: set[int],
    threads_by_id: dict[int, dict[str, Any]] | None = None,
) -> None:
    """Check every enumerated outstanding finding against its recorded disposition and reply decision."""
    threads_by_id = threads_by_id or {}
    outstanding_by_id = {item["id"]: item for item in ledger["outstanding"]}
    for item in outstanding:
        item_id = item["id"]
        if item_id not in outstanding_by_id:
            _abort(f"outstanding finding '{item_id}' has no disposition.")
        recorded = outstanding_by_id[item_id]
        if item.get("platform_resolved") and recorded.get("disposition") == "resolved":
            if not recorded.get("confirmed_against_diff"):
                _abort(
                    f"outstanding finding '{item_id}' treats a platform-resolved thread "
                    "as a claim; record confirmed_against_diff after checking the current diff."
                )
        thread_match = _THREAD_FINDING_ID_RE.fullmatch(item_id)
        if not thread_match:
            continue
        declared_resolved = bool(recorded.get("platform_resolved"))
        gathered_resolved = bool(item.get("platform_resolved"))
        if declared_resolved != gathered_resolved:
            _abort(
                f"outstanding inline thread '{item_id}' declares platform_resolved="
                f"{str(declared_resolved).lower()}, but the gathered thread state is "
                f"{str(gathered_resolved).lower()}; reconcile the ledger against the acquired threads."
            )
        if (
            recorded.get("disposition") == "disputed"
            and recorded.get("communication") == COMMUNICATION_NO_REPLY
            and not item.get("prior_review_reply")
        ):
            _abort(
                f"outstanding inline thread '{item_id}' takes a standing-dispute no-reply, "
                "but the gathered thread state carries no prior reviewer reply; a dispute "
                "raised or changed this round is communicated by reply."
            )
        root_comment_id = int(thread_match.group(1))
        if recorded.get("reopen") is True and not str(threads_by_id.get(root_comment_id, {}).get("node_id") or ""):
            _abort(
                f"outstanding inline thread '{item_id}' declares reopen, but the acquired threads carry "
                "no node id for it; re-gather so the reopen target is resolvable before posting."
            )
        if recorded.get("communication") == COMMUNICATION_REPLY:
            if root_comment_id not in reply_ids:
                _abort(
                    f"outstanding inline thread '{item_id}' requires a reply, "
                    "but its root comment id is absent from the replies file."
                )
            used_replies.add(root_comment_id)
        elif root_comment_id in reply_ids:
            _abort(
                f"outstanding inline thread '{item_id}' declares no-reply, "
                "but the replies file contains that root comment id."
            )


def cmd_list_run_artifacts(artifact_class: str | None = None) -> None:
    """Print one artifact class's prescribed names, or both, one per line, sorted."""
    selected = {"bulk": BULK_RUN_ARTIFACTS, "handoff": HANDOFF_RUN_ARTIFACTS}.get(artifact_class or "")
    for name in sorted(PRESCRIBED_RUN_ARTIFACTS if selected is None else selected):
        print(name)


def cmd_prepare_run(run: str) -> None:
    """Prepare both local run roots before authoring the first summary or approval view."""
    if not REVIEW_RUN_DIR_PATTERN.fullmatch(run):
        _abort("run name must identify repository, PR number, and head SHA.")
    try:
        print(local_scratch_paths.prepare_run_handoff(REPO_ROOT, "aiscr-review-pr", run))
    except (OSError, ValueError) as exc:
        _abort(str(exc))


# ---------------------------------------------------------------------------
# Review bundle validation and rendering
# ---------------------------------------------------------------------------


def _validate_inline_comment(comment: Any, index: int) -> None:
    if not isinstance(comment, dict):
        _abort(f"inline comment {index} must be a JSON object.")
    for key in ("path", "line", "side", "body"):
        if key not in comment:
            _abort(f"inline comment {index} is missing required key '{key}'.")
    if not isinstance(comment["path"], str) or not comment["path"].strip():
        _abort(f"inline comment {index} path must be a non-empty string.")
    if isinstance(comment["line"], bool) or not isinstance(comment["line"], int):
        _abort(f"inline comment {index} line must be an integer.")
    if comment["side"] not in {"LEFT", "RIGHT"}:
        _abort(f"inline comment {index} side must be LEFT or RIGHT.")
    if not isinstance(comment["body"], str) or not comment["body"].strip():
        _abort(f"inline comment {index} body must be a non-empty string.")


def _validate_review_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        _abort("review payload must be a JSON object.")

    required = {"body", "event", "commit_id"}
    missing = sorted(required - payload.keys())
    if missing:
        _abort(f"review payload is missing required keys: {', '.join(missing)}. Required: body, event, commit_id.")

    if not isinstance(payload["body"], str) or not payload["body"].strip():
        _abort("review payload body must be a non-empty string.")
    if payload["event"] not in REVIEW_EVENTS:
        _abort(f"review event must be one of: {', '.join(REVIEW_EVENTS)}.")
    if not isinstance(payload["commit_id"], str) or not payload["commit_id"].strip():
        _abort("review payload commit_id must be a non-empty string.")

    comments = payload.get("comments", [])
    if not isinstance(comments, list):
        _abort("review payload comments must be a JSON array when present.")
    for index, comment in enumerate(comments, start=1):
        _validate_inline_comment(comment, index)

    return payload


def _validate_replies(replies: Any) -> list[dict[str, Any]]:
    if not isinstance(replies, list):
        _abort("replies file must contain a JSON array.")
    seen_comment_ids: set[int] = set()
    for index, reply in enumerate(replies, start=1):
        if not isinstance(reply, dict):
            _abort(f"reply {index} must be a JSON object.")
        comment_id = reply.get("comment_id")
        if isinstance(comment_id, bool) or not isinstance(comment_id, int) or comment_id <= 0:
            _abort(f"reply {index} comment_id must be a positive integer.")
        if comment_id in seen_comment_ids:
            _abort(f"reply target {comment_id} is listed more than once.")
        seen_comment_ids.add(comment_id)
        if not isinstance(reply.get("body"), str) or not reply["body"].strip():
            _abort(f"reply {index} body must be a non-empty string.")
    return replies


REVIEW_CONTRACT = PostingContract(
    marker=REVIEW_MARKER,
    interactive_disclosure=INTERACTIVE_REVIEW_DISCLOSURE,
    automated_disclosure=AUTOMATED_DISCLOSURE,
)


def _inject_review_contract(body: str, mode: str) -> str:
    return github_utils.inject_contract(body, mode, REVIEW_CONTRACT)


def _validate_review_contract(body: str, mode: str) -> None:
    github_utils.validate_contract(body, mode, REVIEW_CONTRACT)


_bundle_digest = github_utils.canonical_digest


def _validate_outgoing_references(
    review: dict[str, Any],
    replies: list[dict[str, Any]],
    label: str,
    anchors: list[dict[str, Any]] | None = None,
) -> None:
    """Preflight the entire review/repair batch, never a lazy sequence of individual posts."""
    fields = []
    if review.get("body") is not None:
        fields.append(github_utils.ReferenceField(f"{label}.body", review["body"]))
    fields.extend(
        github_utils.ReferenceField(f"{label}.comments[{index}].body", item["body"])
        for index, item in enumerate(review.get("comments", []))
    )
    fields.extend(
        github_utils.ReferenceField(f"{label}.replies[{index}].body", item["body"])
        for index, item in enumerate(replies)
    )
    fields.extend(
        github_utils.ReferenceField(f"{label}.observation_anchors[{index}].body", item["body"])
        for index, item in enumerate(anchors or [])
    )
    github_utils.validate_reference_batch(fields)


def _validate_bundle(bundle: Any, mode: str) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        _abort("review bundle must be a JSON object.")
    expected_keys = {"schema", "mode", "review", "replies", "findings_ledger", "coverage", "observation_anchors"}
    if set(bundle) != expected_keys:
        _abort(
            "review bundle must contain exactly: schema, mode, review, replies, findings_ledger, coverage, "
            "observation_anchors."
        )
    if bundle.get("schema") != BUNDLE_SCHEMA:
        _abort(f"review bundle schema must be '{BUNDLE_SCHEMA}'; regenerate the ledger, render, and approve again.")
    if bundle.get("mode") != mode:
        _abort(f"review bundle mode '{bundle.get('mode')}' does not match requested mode '{mode}'.")

    review = _validate_review_payload(bundle.get("review"))
    _validate_replies(bundle.get("replies"))
    _validate_review_contract(review["body"], mode)
    if mode == "automated" and review["event"] != "COMMENT":
        _abort("automated review bundles must use the non-blocking COMMENT event.")
    coverage = bundle.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("schema") != COVERAGE_SCHEMA:
        _abort(f"review bundle coverage schema must be '{COVERAGE_SCHEMA}'.")
    ledger = _validate_findings_ledger(bundle.get("findings_ledger"), coverage)
    anchors = bundle.get("observation_anchors")
    if not isinstance(anchors, list):
        _abort("review bundle observation_anchors must be a JSON array.")
    if not _payloads_match(anchors, _observation_anchors(ledger["preexisting_observations"])):
        _abort(
            "review bundle observation_anchors do not match the validated observation records; "
            "re-render and approve the exact current artefacts."
        )
    _with_observations(review["body"], ledger["preexisting_observations"])
    _validate_outgoing_references(review, bundle["replies"], "review", anchors)
    return bundle


def _enforce_review_gates(
    bundle: dict[str, Any],
    outstanding: list[dict[str, Any]],
    existing_threads: list[dict[str, Any]],
) -> None:
    _refuse_incomplete_coverage(bundle["coverage"])
    _validate_placements(
        bundle["findings_ledger"],
        bundle["review"],
        bundle["replies"],
        bundle["coverage"],
        outstanding,
        existing_threads,
    )


def _outstanding_disposition_lines(item: dict[str, Any]) -> list[str]:
    """Render one outstanding disposition with its reason and communication decision."""
    lines = [
        f"### Outstanding `{item.get('id')}`",
        "",
        f"- Disposition: `{item.get('disposition')}`",
        f"- Reason: {item.get('reason', '')}",
        f"- Author kind: `{item.get('author_kind', '')}`",
    ]
    if _THREAD_FINDING_ID_RE.fullmatch(str(item.get("id") or "")):
        lines.append(f"- Platform resolved: `{bool(item.get('platform_resolved'))}`")
        lines.append(f"- Communication: `{item.get('communication', '')}`")
        if item.get("communication") == COMMUNICATION_NO_REPLY:
            lines.append(f"- No-reply reason: {item.get('no_reply_reason', '')}")
        if isinstance(item.get("reopen"), bool):
            lines.append(f"- Reopen thread: `{item['reopen']}`")
            lines.append(f"- Reopen reason: {item.get('reopen_reason', '')}")
    lines.append("")
    return lines


def _bulk_run_for_handoff(view_path: str) -> Path | None:
    """Return the bulk run directory matching a visible hand-off view, else None.

    The hand-off directory is a direct child of ``REVIEW_HANDOFF_ROOT`` with the same run name as its bulk counterpart,
    so the pointer can be derived without a second argument. A view written anywhere else is left without a pointer
    rather than guessing a target.
    """
    candidate = Path(view_path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    parent = candidate.absolute().parent
    handoff_root = REVIEW_HANDOFF_ROOT.absolute()
    if parent.parent != handoff_root or not REVIEW_RUN_DIR_PATTERN.fullmatch(parent.name):
        return None
    return REVIEW_SCRATCH_ROOT / parent.name


def _handoff_pointer_lines(bulk_run: Path | None) -> list[str]:
    """Return the pointer section naming the bulk run directory, when known."""
    if bulk_run is None:
        return []
    return ["", "## Run location", "", f"Bulk machine artifacts: `{bulk_run}`", ""]


def _write_approval_view(path: str, text: str) -> None:
    """Prepare a confined hand-off before rendering its exact approval bytes."""
    try:
        target = local_scratch_paths.prepare_handoff_file(REPO_ROOT, Path(path))
        _write_text(str(target), text, "approval view")
    except (OSError, ValueError) as exc:
        _abort(str(exc))


def _checked_approval_view(bundle_path: str, explicit: str | None, *, repair: bool = False) -> Path:
    """Resolve the mandatory interactive view, including the split run layout."""
    parent = Path(bundle_path).absolute().parent
    if parent.parent == REVIEW_SCRATCH_ROOT.absolute():
        parent = REVIEW_HANDOFF_ROOT / parent.name
    filename = "repair-approval.md" if repair else "review-approval.md"
    try:
        return local_scratch_paths.checked_handoff_file(REPO_ROOT, Path(explicit) if explicit else parent / filename)
    except ValueError as exc:
        _abort(str(exc))


def _require_approval_view(path: Path, expected: str) -> None:
    """Refuse missing or edited approval presentation before any remote write."""
    try:
        matches = path.read_bytes() == expected.encode("utf-8")
    except OSError as exc:
        _abort(f"cannot read approval view '{path}'; re-render and approve again: {exc}")
    if not matches:
        _abort("approval view was edited; re-render and obtain fresh approval before posting.")


def _approval_view(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    bundle: dict[str, Any], digest: str, bulk_run: Path | None = None
) -> str:
    review = bundle["review"]
    comments = review.get("comments", [])
    replies = bundle["replies"]
    lines = [
        "# AIS CR PR review approval view",
        "",
        f"- Mode: `{bundle['mode']}`",
        f"- Target commit: `{review['commit_id']}`",
        f"- Review event: `{review['event']}`",
        "",
        "## Exact grouped review body",
        "",
        review["body"],
        "",
        "## New inline comments",
        "",
    ]
    if not comments:
        lines.append("None.")
    for index, comment in enumerate(comments, start=1):
        lines.extend(
            [
                f"### Inline comment {index}",
                "",
                f"- Path: `{comment['path']}`",
                f"- Line: `{comment['line']}`",
                f"- Side: `{comment['side']}`",
                "",
                "Exact body:",
                "",
                comment["body"],
                "",
            ]
        )
    anchors = bundle.get("observation_anchors") or []
    lines.extend(
        [
            "",
            "## Observation anchors",
            "",
            "Line anchors join the grouped review; file anchors are posted as standalone review comments after it.",
            "",
        ]
    )
    if not anchors:
        lines.append("None.")
    for index, anchor in enumerate(anchors, start=1):
        lines.extend(
            [
                f"### Anchor {index} — observation `{anchor['observation_id']}` ({anchor['kind']})",
                "",
                f"- Path: `{anchor['path']}`",
            ]
        )
        if anchor["kind"] == "line":
            lines.extend([f"- Line: `{anchor['line']}`", f"- Side: `{anchor['side']}`"])
        lines.extend(["", "Exact body:", "", anchor["body"], ""])
    lines.extend(["", "## Existing-thread replies", ""])
    if not replies:
        lines.append("None.")
    for index, reply in enumerate(replies, start=1):
        lines.extend(
            [
                f"### Reply {index}",
                "",
                f"- Comment ID: `{reply['comment_id']}`",
                "",
                "Exact body:",
                "",
                reply["body"],
                "",
            ]
        )
    ledger = bundle.get("findings_ledger") or {}
    lines.extend(["", "## Capture decisions", ""])
    capture_set = [
        record
        for record in (ledger.get("preexisting_observations") or [])
        if record.get("disposition") == "track-separately"
    ]
    if not capture_set:
        lines.append("(no capture-set observation.)")
    for record in capture_set:
        tracking = record.get("tracking") or {}
        lines.extend(
            [
                f"### Observation `{record.get('id')}`",
                "",
                f"- Tracking key: {record.get('tracking_key')}",
                f"- Disposition: `{record.get('disposition')}`",
                f"- Outcome: `{tracking.get('state')}`",
            ]
        )
        if tracking.get("state") == "pending":
            lines.append(f"- Reason code: `{tracking.get('reason_code')}`")
            lines.append(f"- Detail: {tracking.get('reason')}")
        else:
            issue = tracking.get("issue") or {}
            lines.append(f"- Issue: {github_references.reference_link(str(issue.get('url', '')).strip())}")
        lines.append("")
    lines.extend(["", "## Findings ledger placements", ""])
    new_findings = ledger.get("new_findings") or []
    if not new_findings:
        lines.append("(none declared.)")
    for finding in new_findings:
        placement = finding.get("placement")
        lines.extend([f"### Finding `{finding.get('id')}`", "", f"- Placement: `{placement}`"])
        if placement == PLACEMENT_INLINE_ROOT:
            lines.extend(
                [
                    f"- Path: `{finding.get('path')}`",
                    f"- Line: `{finding.get('line')}`",
                    f"- Side: `{finding.get('side')}`",
                ]
            )
        elif placement == PLACEMENT_REPLY:
            lines.append(f"- Reply to comment: `{finding.get('comment_id')}`")
            if finding.get("stale_thread_reuse_reason"):
                lines.append(f"- Stale-thread reuse reason: `{finding['stale_thread_reuse_reason']}`")
        elif placement == PLACEMENT_BODY_ONLY:
            lines.append(f"- Body-only reason: `{finding.get('reason')}`")
        lines.append("")
    lines.extend(["", "## Outstanding finding dispositions", ""])
    outstanding = ledger.get("outstanding") or []
    if not outstanding:
        lines.append("(none declared.)")
    for item in outstanding:
        lines.extend(_outstanding_disposition_lines(item))
    lines.extend(["", "## Canonical bundle digest", "", f"`{digest}`"])
    lines.extend(_handoff_pointer_lines(bulk_run))
    return "\n".join(lines)


def cmd_render(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    mode: str,
    review_payload_path: str,
    replies_path: str | None,
    bundle_path: str,
    approval_view_path: str,
    pr_context_path: str,
    findings_ledger_path: str,
    local_diff_path: str | None = None,
) -> None:
    """Create the canonical bundle and exact approval presentation."""
    review = _validate_review_payload(_load_json(review_payload_path, "review payload"))
    replies = _validate_replies(_load_json(replies_path, "replies file")) if replies_path else []
    context = _load_json(pr_context_path, "PR context")
    if not isinstance(context, dict):
        _abort("PR context must be a JSON object.")
    coverage = context.get("coverage")
    if not isinstance(coverage, dict):
        _abort("PR context is missing coverage.")
    if local_diff_path:
        coverage = _apply_local_diff(coverage, local_diff_path)
    _refuse_incomplete_coverage(coverage)
    ledger = _validate_findings_ledger(_load_json(findings_ledger_path, "findings ledger"), coverage)
    outstanding = context.get("outstanding_findings") or []
    if not isinstance(outstanding, list):
        _abort("PR context outstanding_findings must be a JSON array when present.")
    existing_threads = context.get("existing_threads") or []
    if not isinstance(existing_threads, list):
        _abort("PR context existing_threads must be a JSON array when present.")
    rendered_review = dict(review)
    rendered_review["body"] = _inject_review_contract(
        _with_observations(review["body"], ledger["preexisting_observations"], inject=True), mode
    )
    if mode == "automated" and rendered_review["event"] != "COMMENT":
        _abort("automated review bundles must use the non-blocking COMMENT event.")
    _validate_placements(ledger, rendered_review, replies, coverage, outstanding, existing_threads)

    bundle = {
        "schema": BUNDLE_SCHEMA,
        "mode": mode,
        "review": rendered_review,
        "replies": replies,
        "findings_ledger": ledger,
        "coverage": coverage,
        "observation_anchors": _observation_anchors(ledger["preexisting_observations"]),
    }
    _validate_bundle(bundle, mode)
    _enforce_review_gates(bundle, outstanding, existing_threads)
    digest = _bundle_digest(bundle)
    _write_approval_view(approval_view_path, _approval_view(bundle, digest, _bulk_run_for_handoff(approval_view_path)))
    _write_json(bundle_path, bundle)
    print(f"Review bundle: {os.path.abspath(bundle_path)}")
    print(f"Approval view: {os.path.abspath(approval_view_path)}")
    print(f"Bundle digest (SHA-256): {digest}")


# ---------------------------------------------------------------------------
# Gather
# ---------------------------------------------------------------------------


def _rest_items(endpoint: str, collection_key: str | None = None) -> list[dict[str, Any]]:
    items = _paginated_rest_items(
        endpoint,
        collection_key=collection_key,
        runner=lambda command: (True, _gh(*command[1:])),
    )
    if items is None:
        _abort(f"cannot read every GitHub REST page for '{endpoint}'.")
    return items


def _fetch_review_details(
    owner_repo: str,
    pr_number: int,
    review_id: int,
) -> tuple[str, list[dict[str, Any]]]:
    body = _gh(
        "api",
        f"repos/{owner_repo}/pulls/{pr_number}/reviews/{review_id}",
        "--jq",
        ".body",
    )
    comments = _rest_items(f"repos/{owner_repo}/pulls/{pr_number}/reviews/{review_id}/comments")
    return body, [
        {
            "id": item.get("id"),
            "path": item.get("path"),
            "line": item.get("line"),
            "side": item.get("side"),
            "body": item.get("body"),
        }
        for item in comments
    ]


def _fetch_issue_comments(owner_repo: str, pr_number: int) -> list[dict[str, Any]]:
    comments = _rest_items(f"repos/{owner_repo}/issues/{pr_number}/comments")
    return [
        {
            "id": item.get("id"),
            "body": item.get("body"),
            "html_url": item.get("html_url"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "user": ((item.get("user") or {}).get("login") if isinstance(item.get("user"), dict) else item.get("user")),
        }
        for item in comments
    ]


def _latest_by(items: list[dict[str, Any]], field: str) -> dict[str, Any] | None:
    if not items:
        return None
    return max(items, key=lambda item: str(item.get(field) or ""))


def _find_summary_comment(
    issue_comments: list[dict[str, Any]],
) -> dict[str, Any] | None:
    marked = [comment for comment in issue_comments if SUMMARY_MARKER_PATTERN.search(str(comment.get("body") or ""))]
    if not marked:
        return None
    return max(
        marked,
        key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""),
    )


def _fetch_pr_identity(pr_number: int, owner_repo: str) -> dict[str, str]:
    raw = _gh(
        "pr",
        "view",
        str(pr_number),
        "--repo",
        owner_repo,
        "--json",
        "headRefOid,baseRefOid,author",
    )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        _abort(f"cannot parse pull request identity: {exc}")
    if not isinstance(payload, dict):
        _abort("pull request identity must be a JSON object.")
    author = payload.get("author") if isinstance(payload.get("author"), dict) else {}
    head_sha = str(payload.get("headRefOid") or "").strip()
    base_sha = str(payload.get("baseRefOid") or "").strip()
    pr_author = str(author.get("login") or "").strip()
    if not head_sha or not base_sha:
        _abort("pull request identity is missing base or head commit SHAs.")
    return {"head_sha": head_sha, "base_sha": base_sha, "pr_author": pr_author}


def _fetch_pr_description(pr_number: int, owner_repo: str) -> str:
    return _gh(
        "pr",
        "view",
        str(pr_number),
        "--repo",
        owner_repo,
        "--json",
        "body",
        "-q",
        ".body",
    )


def _fetch_review_lineage(owner_repo: str, pr_number: int) -> dict[str, Any]:
    reviews = [
        {
            "id": item.get("id"),
            "body": item.get("body"),
            "state": item.get("state"),
            "submitted_at": item.get("submitted_at"),
            "user": ((item.get("user") or {}).get("login") if isinstance(item.get("user"), dict) else item.get("user")),
            "html_url": item.get("html_url"),
        }
        for item in _rest_items(f"repos/{owner_repo}/pulls/{pr_number}/reviews")
        if item.get("state") != "PENDING"
    ]
    marked_reviews = [review for review in reviews if REVIEW_MARKER in str(review.get("body") or "")]
    reviewer_logins = sorted(
        {
            str(review.get("user"))
            for review in marked_reviews
            if isinstance(review.get("user"), str) and review.get("user").strip()
        }
    )
    last_review = _latest_by(marked_reviews, "submitted_at")
    last_review_id = last_review.get("id") if last_review else None
    last_review_body = None
    last_review_comments = None
    if isinstance(last_review_id, int):
        last_review_body, last_review_comments = _fetch_review_details(
            owner_repo,
            pr_number,
            last_review_id,
        )
    return {
        "last_review_id": last_review_id,
        "last_review_body": last_review_body,
        "last_review_comments": last_review_comments,
        "reviewer_logins": reviewer_logins,
        "auxiliary_reviews": [review for review in reviews if review not in marked_reviews],
    }


def _issue_comment_context(
    issue_comments: list[dict[str, Any]],
    pr_author: str,
) -> dict[str, Any]:
    author_comments = [comment for comment in issue_comments if comment.get("user") == pr_author]
    author_comment = _latest_by(author_comments, "created_at")
    return {
        "author_response": author_comment.get("body") if author_comment else None,
        "summary_comment": _find_summary_comment(issue_comments),
    }


PR_COMMENTS_QUERY = """
query($owner:String!, $name:String!, $number:Int!, $endCursor:String) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      comments(first:100, after:$endCursor) {
        nodes { databaseId body createdAt url isMinimized minimizedReason author { login } }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

UNRESOLVE_THREAD_MUTATION = """
mutation($threadId:ID!) {
  unresolveReviewThread(input:{threadId:$threadId}) {
    thread { id isResolved }
  }
}
"""

PR_THREADS_QUERY = """
query($owner:String!, $name:String!, $number:Int!, $endCursor:String) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      reviewThreads(first:100, after:$endCursor) {
        nodes {
          id
          isResolved isOutdated isCollapsed path line
          comments(first:100) {
            nodes { databaseId body createdAt url isMinimized minimizedReason author { login } }
            pageInfo { hasNextPage endCursor }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

THREAD_COMMENTS_QUERY = """
query($thread:ID!, $endCursor:String) {
  node(id:$thread) {
    ... on PullRequestReviewThread {
      comments(first:100, after:$endCursor) {
        nodes { databaseId body createdAt url isMinimized minimizedReason author { login } }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""


def _graphql(query: str, **variables: str) -> dict[str, Any]:
    return github_utils.graphql(query, runner=_gh, **variables)


def _comment_record(node: dict[str, Any], source: str) -> dict[str, Any]:
    """Normalize one comment, carrying where it came from and when."""
    author = node.get("author") or {}
    return {
        "source": source,
        "id": node.get("databaseId"),
        "author": author.get("login"),
        "created_at": node.get("createdAt"),
        "url": node.get("url"),
        "hidden": bool(node.get("isMinimized")),
        "hidden_reason": node.get("minimizedReason"),
        "body": node.get("body") or "",
    }


def _pr_connection(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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
    pull = (((payload.get("data") or {}).get("repository") or {}).get("pullRequest")) or {}
    return pull.get(key) or {}


def _thread_comment_connection(thread_id: str, cursor: str | None) -> dict[str, Any]:
    variables = {"thread": thread_id}
    if cursor is not None:
        variables["endCursor"] = cursor
    payload = _graphql(THREAD_COMMENTS_QUERY, **variables)
    thread = (payload.get("data") or {}).get("node") or {}
    return thread.get("comments") or {}


def _fetch_conversation(owner_repo: str, pr_number: int) -> dict[str, Any]:
    """Gather every comment on the PR, including hidden, resolved, and outdated.

    A resolved thread usually holds the reasoning behind the current state, and a minimized comment is hidden from the
    reader rather than from the record, so neither is skipped. REST exposes neither flag; GraphQL is the only surface
    that does, which is why these connections are read through paginated GraphQL rather than flattened into REST records
    that lose thread state.
    """
    owner, _, name = owner_repo.partition("/")
    discussion_nodes = _paginated_graphql_nodes(
        lambda cursor: _pr_connection(PR_COMMENTS_QUERY, "comments", owner, name, pr_number, cursor)
    )
    thread_nodes = _paginated_graphql_nodes(
        lambda cursor: _pr_connection(PR_THREADS_QUERY, "reviewThreads", owner, name, pr_number, cursor)
    )
    discussion = [_comment_record(node, "pr-comment") for node in discussion_nodes]
    threads: list[dict[str, Any]] = []
    for thread in thread_nodes:
        initial_comments = thread.get("comments") or {}
        thread_id = str(thread.get("id") or "")
        if initial_comments.get("pageInfo", {}).get("hasNextPage") and not thread_id:
            _abort("GitHub review thread has paginated comments but no node id.")
        comment_nodes = _paginated_graphql_nodes(
            lambda cursor, node_id=thread_id: _thread_comment_connection(node_id, cursor),
            initial_comments,
        )
        threads.append(
            {
                "node_id": thread_id,
                "path": thread.get("path"),
                "line": thread.get("line"),
                "resolved": bool(thread.get("isResolved")),
                "outdated": bool(thread.get("isOutdated")),
                "collapsed": bool(thread.get("isCollapsed")),
                "comments": [_comment_record(node, "review-thread") for node in comment_nodes],
            }
        )
    return {"discussion_comments": discussion, "review_threads": threads}


def _conversation_text(conversation: dict[str, Any]) -> list[str]:
    """Every comment body in the conversation, for reference extraction."""
    bodies = [comment["body"] for comment in conversation["discussion_comments"]]
    for thread in conversation["review_threads"]:
        bodies.extend(comment["body"] for comment in thread["comments"])
    return bodies


def _fetch_closing_references(owner_repo: str, pr_number: int) -> list[str]:
    """Issues GitHub itself links to this PR, independent of body text."""
    ok, stdout = _try_run(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            owner_repo,
            "--json",
            "closingIssuesReferences",
            "-q",
            ".closingIssuesReferences[].number",
        ]
    )
    if not ok:
        return []
    return [f"{owner_repo}#{line.strip()}" for line in stdout.splitlines() if line.strip()]


def _fetch_referenced_item(ref: str) -> dict[str, Any] | None:
    """Fetch one referenced issue or pull request with its comment thread."""
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
    issue_comments = _paginated_rest_items(
        f"repos/{target_repo}/issues/{number}/comments",
        runner=_try_run,
    )
    if issue_comments is None:
        return None
    comments = [
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
        for node in issue_comments
    ]
    if item.get("pull_request"):
        review_comments = _paginated_rest_items(
            f"repos/{target_repo}/pulls/{number}/comments",
            runner=_try_run,
        )
        if review_comments is None:
            return None
        comments.extend(
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
        "created_at": item.get("created_at"),
        "body": item.get("body") or "",
        "comments": comments,
    }


def _fetch_check_runs(owner_repo: str, head_sha: str) -> list[dict[str, Any]]:
    """Check runs for the head commit; test evidence often lives here."""
    runs = _paginated_rest_items(
        f"repos/{owner_repo}/commits/{head_sha}/check-runs",
        collection_key="check_runs",
        runner=_try_run,
    )
    if runs is None:
        return []
    return [
        {
            "source": "check-run",
            "name": run.get("name"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "completed_at": run.get("completed_at"),
            "url": run.get("details_url"),
        }
        for run in runs
    ]


def _gather_neighbourhood(
    owner_repo: str,
    pr_number: int,
    texts: list[str],
    seed_refs: list[str],
) -> dict[str, Any]:
    """One hop of referenced issues and pull requests, with their comment threads."""
    return github_utils.gather_neighbourhood(
        owner_repo,
        f"{owner_repo}#{pr_number}",
        texts,
        seed_refs,
        _fetch_referenced_item,
    )


def _produce_sibling_local_diff(sibling: str, base_sha: str, head_sha: str, dest_path: str) -> bool:
    """Produce the local diff for a registered repository through the acquisition bridge.

    The engine is the producer: it invokes the bridge, pins the child's pipe encoding through the environment, and
    writes the patch file itself, so no operator shell redirect can re-encode content this engine later reads back as
    strict UTF-8. The merge-base is resolved first, so the patch carries the same scope as the in-repo three-dot
    comparison.

    Returns ``False`` when the bridge is not part of this copy, or reports an absent or failed outcome; the caller then
    leaves coverage incomplete rather than consuming a destination file left by an earlier round, because a stale patch
    would fabricate complete coverage.
    """
    if not _BRIDGE_SCRIPT.is_file():
        log_warn(
            "a multi-repository local diff needs the acquisition extension, which this copy "
            "does not include; leaving coverage incomplete"
        )
        return False
    bridge = [sys.executable, str(_BRIDGE_SCRIPT)]
    env = utf8_child_env()

    def run_bridge(*git_args: str) -> subprocess.CompletedProcess:
        return run_exact([*bridge, "--repo", sibling, "--", *git_args], env=env)

    merge = run_bridge("merge-base", base_sha, head_sha)
    if merge.returncode != 0:
        log_warn(
            f"repository bridge merge-base failed for {sibling}: "
            f"{merge.stderr.strip() or f'exit {merge.returncode}'}; "
            "leaving coverage incomplete"
        )
        return False
    merge_base = merge.stdout.strip()
    diff = run_bridge("diff", merge_base, head_sha, "--")
    if diff.returncode != 0:
        log_warn(
            f"repository bridge diff failed for {sibling}: "
            f"{diff.stderr.strip() or f'exit {diff.returncode}'}; "
            "leaving coverage incomplete"
        )
        return False
    Path(dest_path).write_text(diff.stdout, encoding="utf-8", newline="\n")
    return True


def cmd_gather(  # pylint: disable=too-many-locals
    pr_number: int,
    repo: str | None,
    local_diff: str | None = None,
    output_path: str | None = None,
    sibling: str | None = None,
) -> None:
    """Fetch PR context and print JSON for use in the review workflow."""
    if sibling and not local_diff:
        _abort("--sibling requires --local-diff naming the patch file the engine writes.")
    owner_repo = _resolve_repo(repo)
    identity = _fetch_pr_identity(pr_number, owner_repo)
    head_sha = identity["head_sha"]
    pr_author = identity["pr_author"]
    pr_description = _fetch_pr_description(pr_number, owner_repo)
    lineage = _fetch_review_lineage(owner_repo, pr_number)
    issue_comments = _fetch_issue_comments(owner_repo, pr_number)
    conversation = _fetch_conversation(owner_repo, pr_number)
    neighbourhood = _gather_neighbourhood(
        owner_repo,
        pr_number,
        [pr_description, *_conversation_text(conversation)],
        _fetch_closing_references(owner_repo, pr_number),
    )
    existing_threads = _thread_roots_from_conversation(conversation)
    outstanding = _enumerate_outstanding_findings(conversation, lineage)
    if sibling:
        if not _produce_sibling_local_diff(sibling, str(identity["base_sha"]), head_sha, local_diff):
            local_diff = None
    coverage = _acquire_coverage(
        owner_repo,
        pr_number,
        identity["base_sha"],
        head_sha,
        local_diff,
    )
    output = {
        "owner_repo": owner_repo,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "base_sha": identity["base_sha"],
        "pr_author": pr_author,
        "pr_description": pr_description,
        "pr_description_has_summary_marker": SUMMARY_MARKER_PATTERN.search(pr_description) is not None,
        "pr_description_state": _description_state(pr_description),
        **lineage,
        **_issue_comment_context(issue_comments, pr_author),
        "existing_threads": existing_threads,
        **conversation,
        **neighbourhood,
        "check_runs": _fetch_check_runs(owner_repo, head_sha),
        "coverage": coverage,
        "outstanding_findings": outstanding,
        "review_only_body_findings": REVIEW_ONLY_BODY_FINDINGS,
    }
    _emit_json(output, output_path)


# ---------------------------------------------------------------------------
# Posting
# ---------------------------------------------------------------------------


def _reopen_threads(targets: list[tuple[str, str]]) -> None:
    """Unresolve each approved thread so the reply it just received is visible.

    Runs after the replies, not before: a reply that lands and then fails to reopen leaves a recoverable collapsed
    comment, while a reopen that lands and then fails to reply leaves a thread reopened with nothing explaining why.
    """
    for item_id, node_id in targets:
        payload = _graphql(UNRESOLVE_THREAD_MUTATION, threadId=node_id)
        thread = ((payload.get("data") or {}).get("unresolveReviewThread") or {}).get("thread") or {}
        if thread.get("isResolved") is False:
            print(f"Thread reopened for {item_id}: {node_id}")
        else:
            print(f"Thread reopen did not take effect for {item_id}: {node_id}")


def _approved_reopen_targets(ledger: dict[str, Any], existing_threads: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Resolve the approved reopen decisions to their thread node ids."""
    nodes = {
        int(thread["id"]): str(thread.get("node_id") or "")
        for thread in existing_threads
        if isinstance(thread.get("id"), int) and not isinstance(thread.get("id"), bool)
    }
    targets: list[tuple[str, str]] = []
    for item in ledger.get("outstanding") or []:
        if item.get("reopen") is not True:
            continue
        match = _THREAD_FINDING_ID_RE.fullmatch(str(item.get("id") or ""))
        if not match:
            continue
        node_id = nodes.get(int(match.group(1)), "")
        if not node_id:
            _abort(f"approved reopen for '{item['id']}' has no thread node id; no thread was reopened.")
        targets.append((str(item["id"]), node_id))
    return targets


def _post_replies(
    owner_repo: str,
    pr_number: int,
    replies: list[dict[str, Any]],
) -> None:
    if not replies:
        return
    existing_comments = _paginated_rest_items(f"repos/{owner_repo}/pulls/{pr_number}/comments?per_page=100")
    if existing_comments is None:
        _abort("cannot verify existing pull-request replies before posting; no reply was written.")
    existing_exact = {
        (int(comment["in_reply_to_id"]), str(comment.get("body") or "").strip()): str(comment.get("html_url") or "")
        for comment in existing_comments
        if isinstance(comment.get("in_reply_to_id"), int) and not isinstance(comment.get("in_reply_to_id"), bool)
    }
    for reply in replies:
        exact_key = (int(reply["comment_id"]), str(reply["body"]).strip())
        if exact_key in existing_exact:
            print(f"Reply already present: {existing_exact[exact_key]}")
            continue
        payload_path = _temporary_json({"body": reply["body"]})
        try:
            reply_url = _gh(
                "api",
                f"repos/{owner_repo}/pulls/{pr_number}/comments/{reply['comment_id']}/replies",
                "--method",
                "POST",
                "--input",
                payload_path,
                "--jq",
                ".html_url",
            )
            print(f"Reply posted: {reply_url}")
            existing_exact[exact_key] = reply_url
        finally:
            os.unlink(payload_path)


def _post_file_anchors(owner_repo: str, pr_number: int, commit_id: str, anchors: list[dict[str, Any]]) -> None:
    """Write approved file anchors as standalone review comments, one per observation."""
    for anchor in anchors:
        payload_path = _temporary_json(
            {
                "body": anchor["body"],
                "commit_id": commit_id,
                "path": anchor["path"],
                "subject_type": "file",
            }
        )
        try:
            anchor_url = _gh(
                "api",
                f"repos/{owner_repo}/pulls/{pr_number}/comments",
                "--method",
                "POST",
                "--input",
                payload_path,
                "--jq",
                ".html_url",
            )
            print(f"Observation anchor posted: {anchor_url}")
        finally:
            os.unlink(payload_path)


def _payloads_match(left: Any, right: Any) -> bool:
    return json.dumps(left, ensure_ascii=False, sort_keys=True, separators=(",", ":")) == json.dumps(
        right,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _new_observation_anchors(
    owner_repo: str, pr_number: int, anchors: list[dict[str, Any]], *, require_existing: bool = False
) -> list[dict[str, Any]]:
    """Reuse only exact live anchors; validate the entire set before any write."""
    if not anchors:
        return []
    existing = _paginated_rest_items(f"repos/{owner_repo}/pulls/{pr_number}/comments?per_page=100")
    if existing is None:
        _abort("cannot verify existing observation anchors before posting; no GitHub write was made.")
    pending: list[dict[str, Any]] = []
    for anchor in anchors:
        matches = [comment for comment in existing if anchor["marker"] in str(comment.get("body") or "")]
        if not matches:
            if require_existing:
                _abort(f"observation anchor '{anchor['observation_id']}' is missing; use a later review round.")
            pending.append(anchor)
            continue
        for comment in matches:
            same = (
                comment.get("body") == anchor["body"]
                and comment.get("path") == anchor["path"]
                and comment.get("subject_type", "line") == anchor["kind"]
            )
            if anchor["kind"] == "line":
                same = same and comment.get("line") == anchor["line"] and comment.get("side") == anchor["side"]
            if not same:
                _abort(
                    f"observation anchor '{anchor['observation_id']}' differs from its approved body or location; "
                    "reconcile it in a later review round before posting."
                )
        print(f"Observation anchor already present: {anchor['observation_id']}")
    return pending


def cmd_post(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches,too-many-statements
    pr_number: int,
    mode: str,
    review_bundle_path: str,
    approved_digest: str | None,
    repo: str | None,
    findings_ledger_path: str,
    pr_context_path: str,
    approval_view_path: str | None = None,
) -> None:
    """Post a validated canonical bundle and its existing-thread replies."""
    bundle = _validate_bundle(
        _load_json(review_bundle_path, "review bundle"),
        mode,
    )
    context = _load_json(pr_context_path, "PR context")
    if not isinstance(context, dict):
        _abort("PR context must be a JSON object.")
    coverage = context.get("coverage")
    if not _payloads_match(coverage, bundle["coverage"]):
        _abort("coverage was altered after approval; re-render and approve the exact current artefacts.")
    ledger = _validate_findings_ledger(_load_json(findings_ledger_path, "findings ledger"), coverage)
    if not _payloads_match(ledger, bundle["findings_ledger"]):
        _abort("findings ledger was altered after approval; re-render and approve the exact current artefacts.")
    outstanding = context.get("outstanding_findings") or []
    existing_threads = context.get("existing_threads") or []
    if not isinstance(outstanding, list) or not isinstance(existing_threads, list):
        _abort("PR context outstanding_findings and existing_threads must be JSON arrays.")
    _enforce_review_gates(bundle, outstanding, existing_threads)
    digest = _bundle_digest(bundle)
    if mode == "interactive":
        if not approved_digest:
            _abort("interactive posting requires --approved-digest from the approval view.")
        if approved_digest != digest:
            _abort(
                "approved digest does not match the review bundle; render and approve "
                "the exact current bundle before posting."
            )

    if mode == "interactive":
        view = _checked_approval_view(review_bundle_path, approval_view_path)
        _require_approval_view(view, _approval_view(bundle, digest, _bulk_run_for_handoff(str(view))))
    _validate_write_environment(mode, "post")
    owner_repo = _resolve_repo(repo)
    new_anchors = _new_observation_anchors(owner_repo, pr_number, bundle["observation_anchors"])
    line_anchors = [anchor for anchor in new_anchors if anchor["kind"] == "line"]
    file_anchors = [anchor for anchor in new_anchors if anchor["kind"] == "file"]
    review_payload = dict(bundle["review"])
    review_payload["comments"] = list(review_payload.get("comments") or []) + [
        {"path": anchor["path"], "line": anchor["line"], "side": anchor["side"], "body": anchor["body"]}
        for anchor in line_anchors
    ]
    review_payload_path = _temporary_json(review_payload)
    try:
        review_url = _gh(
            "api",
            f"repos/{owner_repo}/pulls/{pr_number}/reviews",
            "--method",
            "POST",
            "--input",
            review_payload_path,
            "--jq",
            ".html_url",
        )
        print(f"Review posted: {review_url}")
    finally:
        os.unlink(review_payload_path)
    _post_file_anchors(owner_repo, pr_number, str(bundle["review"]["commit_id"]), file_anchors)

    reopen_targets = _approved_reopen_targets(ledger, existing_threads)
    _post_replies(owner_repo, pr_number, bundle["replies"])
    _reopen_threads(reopen_targets)


def _validate_repair_reopen(reopen: Any, replies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Check reopen targets, which may only accompany a reply that explains the reopening."""
    if reopen is None:
        return []
    if not isinstance(reopen, list):
        _abort("repair bundle reopen must be a JSON array.")
    reply_ids = {int(reply["comment_id"]) for reply in replies}
    seen: set[int] = set()
    for index, entry in enumerate(reopen, start=1):
        if not isinstance(entry, dict) or set(entry) != {"comment_id", "thread_node_id"}:
            _abort(f"repair reopen {index} must contain exactly: comment_id, thread_node_id.")
        comment_id = entry.get("comment_id")
        if isinstance(comment_id, bool) or not isinstance(comment_id, int) or comment_id <= 0:
            _abort(f"repair reopen {index} comment_id must be a positive integer.")
        if not isinstance(entry.get("thread_node_id"), str) or not entry["thread_node_id"].strip():
            _abort(f"repair reopen {index} thread_node_id must be a non-empty string.")
        if comment_id in seen:
            _abort(f"repair reopen target {comment_id} is listed more than once.")
        seen.add(comment_id)
        if comment_id not in reply_ids:
            _abort(
                f"repair reopen target {comment_id} has no reply in this repair; a reopened thread "
                "must carry the reply that explains why it was reopened."
            )
    return reopen


def _validate_repair_source(bundle: dict[str, Any], mode: str, observations: list[dict[str, Any]]) -> None:
    """Bind a body repair to acquired coverage while preserving every anchored record."""
    source = _validate_bundle(bundle["source_review"], mode)
    if source["review"]["commit_id"] != bundle["commit_id"]:
        _abort("body repair commit must match its source review bundle; use a later review round.")
    _refuse_incomplete_coverage(source["coverage"])
    _validate_preexisting_observations(observations, set(), source["coverage"])
    original = {
        record["id"]: record
        for record in source["findings_ledger"]["preexisting_observations"]
        if record["disposition"] == "fix-in-pr"
    }
    replacement = {record["id"]: record for record in observations if record["disposition"] == "fix-in-pr"}
    if not _payloads_match(original, replacement):
        _abort("body repair must preserve every anchored record exactly; use a later review round to change anchors.")


def _validate_repair_bundle(bundle: Any, mode: str) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        _abort("repair bundle must be a JSON object.")
    expected_keys = {
        "schema",
        "mode",
        "review_id",
        "commit_id",
        "comments",
        "replies",
        "reopen",
        "body",
        "preexisting_observations",
        "source_review",
    }
    if set(bundle) != expected_keys:
        _abort(
            "repair bundle must contain exactly: schema, mode, review_id, commit_id, comments, replies, reopen, body, "
            "preexisting_observations, source_review; regenerate, render, and approve again."
        )
    if bundle.get("schema") != REPAIR_BUNDLE_SCHEMA:
        _abort(f"repair bundle schema must be '{REPAIR_BUNDLE_SCHEMA}'; regenerate, render, and approve again.")
    if bundle.get("mode") != mode:
        _abort(f"repair bundle mode '{bundle.get('mode')}' does not match requested mode '{mode}'.")
    review_id = bundle.get("review_id")
    if isinstance(review_id, bool) or not isinstance(review_id, int) or review_id <= 0:
        _abort("repair bundle review_id must be a positive integer.")
    if not isinstance(bundle.get("commit_id"), str) or not bundle["commit_id"].strip():
        _abort("repair bundle commit_id must be a non-empty string.")
    comments = bundle.get("comments")
    if not isinstance(comments, list):
        _abort("repair bundle comments must be a JSON array.")
    for index, comment in enumerate(comments, start=1):
        _validate_inline_comment(comment, index)
    replies = _validate_replies(bundle.get("replies"))
    _validate_repair_reopen(bundle.get("reopen"), replies)
    body = bundle.get("body")
    if body is not None:
        if not isinstance(body, str) or not body.strip():
            _abort("repair bundle body must be a non-empty string when present.")
        _validate_review_contract(body, mode)
        observations = _validate_preexisting_observations(bundle["preexisting_observations"], set())
        _with_observations(body, observations)
        _validate_repair_source(bundle, mode, observations)
    elif bundle["preexisting_observations"] is not None or bundle["source_review"] is not None:
        _abort("a body-unchanged repair must not replace pre-existing observation records.")
    if not comments and not replies and body is None:
        _abort("repair bundle must include at least one standalone inline root, thread reply, or body amendment.")
    _validate_outgoing_references(bundle, replies, "repair")
    return bundle


def _repair_approval_view(bundle: dict[str, Any], digest: str, bulk_run: Path | None = None) -> str:
    lines = [
        "# AIS CR PR review repair approval view",
        "",
        f"- Mode: `{bundle['mode']}`",
        f"- Target review: `{bundle['review_id']}`",
        f"- Target commit: `{bundle['commit_id']}`",
        "",
        "## Standalone inline comment roots",
        "",
    ]
    comments = bundle["comments"]
    if not comments:
        lines.append("(none.)")
    for index, comment in enumerate(comments, start=1):
        lines.extend(
            [
                f"### Repair comment {index}",
                "",
                f"- Path: `{comment['path']}`",
                f"- Line: `{comment['line']}`",
                f"- Side: `{comment['side']}`",
                "",
                "Exact body:",
                "",
                comment["body"],
                "",
            ]
        )
    lines.extend(["", "## Existing-thread replies", ""])
    replies = bundle["replies"]
    if not replies:
        lines.append("(none.)")
    for index, reply in enumerate(replies, start=1):
        lines.extend(
            [
                f"### Repair reply {index}",
                "",
                f"- Reply to comment: `{reply['comment_id']}`",
                "",
                "Exact body:",
                "",
                reply["body"],
                "",
            ]
        )
    lines.extend(["", "## Threads to reopen", ""])
    reopen = bundle["reopen"]
    if not reopen:
        lines.append("(none.)")
    for entry in reopen:
        lines.append(f"- Reply to comment `{entry['comment_id']}` reopens thread `{entry['thread_node_id']}`")
    lines.extend(["", "## Amended review body", ""])
    if bundle["body"] is None:
        lines.append("(unchanged.)")
    else:
        lines.extend([bundle["body"], ""])
        source = bundle["source_review"]
        lines.extend(
            [
                "## Preserved observation anchors",
                "",
                "The source observation section and these exact anchors are checked live before any repair write.",
                "",
            ]
        )
        for anchor in source["observation_anchors"]:
            lines.extend([f"### Observation `{anchor['observation_id']}`", "", anchor["body"], ""])
    lines.extend(["", "## Canonical repair digest", "", f"`{digest}`"])
    lines.extend(_handoff_pointer_lines(bulk_run))
    return "\n".join(lines)


def cmd_repair_render(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    mode: str,
    review_id: int,
    commit_id: str,
    comments_path: str | None,
    body_path: str | None,
    bundle_path: str,
    approval_view_path: str,
    replies_path: str | None = None,
    reopen_path: str | None = None,
    findings_ledger_path: str | None = None,
    source_review_path: str | None = None,
) -> None:
    """Render a repair bundle and its exact approval view (local only)."""
    comments: list[dict[str, Any]] = []
    if comments_path:
        loaded = _load_json(comments_path, "repair comments")
        if not isinstance(loaded, list):
            _abort("repair comments file must contain a JSON array.")
        for index, comment in enumerate(loaded, start=1):
            _validate_inline_comment(comment, index)
        comments = loaded
    replies = _validate_replies(_load_json(replies_path, "repair replies")) if replies_path else []
    reopen = _validate_repair_reopen(_load_json(reopen_path, "repair reopen"), replies) if reopen_path else []
    body: str | None = None
    observations: list[dict[str, Any]] | None = None
    source: dict[str, Any] | None = None
    if body_path:
        try:
            raw_body = Path(body_path).read_text(encoding="utf-8")
        except OSError as exc:
            _abort(f"cannot read repair body '{body_path}': {exc}")
        if not findings_ledger_path:
            _abort("body repair requires --findings-ledger; regenerate the records, render, and approve again.")
        ledger = _validate_findings_ledger(_load_json(findings_ledger_path, "findings ledger"))
        observations = ledger["preexisting_observations"]
        body = _inject_review_contract(_with_observations(raw_body, observations, inject=True), mode)
        if not source_review_path:
            _abort("body repair requires --source-review-bundle naming its existing review bundle.")
        source = _validate_bundle(_load_json(source_review_path, "source review bundle"), mode)
    elif findings_ledger_path or source_review_path:
        _abort("--findings-ledger and --source-review-bundle are only applicable to a body repair.")
    bundle = {
        "schema": REPAIR_BUNDLE_SCHEMA,
        "mode": mode,
        "review_id": review_id,
        "commit_id": commit_id,
        "comments": comments,
        "replies": replies,
        "reopen": reopen,
        "body": body,
        "preexisting_observations": observations,
        "source_review": source,
    }
    _validate_repair_bundle(bundle, mode)
    digest = _bundle_digest(bundle)
    _write_approval_view(
        approval_view_path,
        _repair_approval_view(bundle, digest, _bulk_run_for_handoff(approval_view_path)),
    )
    _write_json(bundle_path, bundle)
    print(f"Repair bundle: {os.path.abspath(bundle_path)}")
    print(f"Repair approval view: {os.path.abspath(approval_view_path)}")
    print(f"Repair digest (SHA-256): {digest}")


def _verify_repair_source(owner_repo: str, pr_number: int, bundle: dict[str, Any]) -> None:
    """Refuse stale source sections or anchors before even the first mutation in a repair batch."""
    source = bundle["source_review"]
    if source is None:
        return
    raw = _gh("api", f"repos/{owner_repo}/pulls/{pr_number}/reviews/{bundle['review_id']}")
    try:
        current = json.loads(raw)
    except json.JSONDecodeError:
        _abort("cannot parse the live source review; no repair write was made.")
    if not isinstance(current, dict) or not isinstance(current.get("body"), str):
        _abort("live source review must contain its body; no repair write was made.")
    if current.get("commit_id") != source["review"]["commit_id"]:
        _abort("live source review commit differs from its bundle; no repair write was made.")
    records = source["findings_ledger"]["preexisting_observations"]
    if _render_observations(bundle["preexisting_observations"]) in current["body"]:
        # A prior attempt may have amended the body before a later write failed.
        records = bundle["preexisting_observations"]
    _with_observations(current["body"], records)
    _new_observation_anchors(owner_repo, pr_number, source["observation_anchors"], require_existing=True)


def cmd_repair_post(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    pr_number: int,
    mode: str,
    repair_bundle_path: str,
    approved_digest: str | None,
    repo: str | None,
    approval_view_path: str | None = None,
) -> None:
    """Post approved standalone inline roots, thread replies, and/or a body amendment."""
    bundle = _validate_repair_bundle(_load_json(repair_bundle_path, "repair bundle"), mode)
    digest = _bundle_digest(bundle)
    if mode == "interactive":
        if not approved_digest:
            _abort("interactive repair posting requires --approved-digest from the repair approval view.")
        if approved_digest != digest:
            _abort(
                "approved digest does not match the repair bundle; render and approve "
                "the exact current repair artefacts before posting."
            )
    if mode == "interactive":
        view = _checked_approval_view(repair_bundle_path, approval_view_path, repair=True)
        _require_approval_view(view, _repair_approval_view(bundle, digest, _bulk_run_for_handoff(str(view))))
    _validate_write_environment(mode, "post")
    owner_repo = _resolve_repo(repo)
    _verify_repair_source(owner_repo, pr_number, bundle)
    for comment in bundle["comments"]:
        payload = {
            "body": comment["body"],
            "commit_id": bundle["commit_id"],
            "path": comment["path"],
            "line": comment["line"],
            "side": comment["side"],
        }
        payload_path = _temporary_json(payload)
        try:
            comment_url = _gh(
                "api",
                f"repos/{owner_repo}/pulls/{pr_number}/comments",
                "--method",
                "POST",
                "--input",
                payload_path,
                "--jq",
                ".html_url",
            )
            print(f"Repair inline comment posted: {comment_url}")
        finally:
            os.unlink(payload_path)
    if bundle["body"] is not None:
        payload_path = _temporary_json({"body": bundle["body"]})
        try:
            review_url = _gh(
                "api",
                f"repos/{owner_repo}/pulls/{pr_number}/reviews/{bundle['review_id']}",
                "--method",
                "PUT",
                "--input",
                payload_path,
                "--jq",
                ".html_url",
            )
            print(f"Repair body amendment posted: {review_url}")
        finally:
            os.unlink(payload_path)
    _post_replies(owner_repo, pr_number, bundle["replies"])
    _reopen_threads([(f"comment {entry['comment_id']}", entry["thread_node_id"]) for entry in bundle["reopen"]])


def _normalized_marker_body(body: str) -> str:
    """Return the body with any stamped digest reduced to the plain marker."""
    return SUMMARY_MARKER_PATTERN.sub(SUMMARY_MARKER, body)


def _generated_portion(body: str) -> str:
    """Return the body outside the delimited author region.

    Scoping the digest here is what lets the two kinds of hand edit resolve without arbitration: an edit to a generated
    section trips the digest and is surfaced as a ``description edit`` source the ledger must account for before the
    write, and only then is that section regenerated, because the surface belongs to the workflow; an edit the author
    makes inside their own region never trips it and is carried forward. Tripping the digest is therefore not a licence
    to overwrite — it is what forces the edit through the dispositions instead of discarding it silently.
    """
    normalized = _normalized_marker_body(body)
    start = normalized.find(AUTHOR_CONTEXT_OPEN)
    end = normalized.find(AUTHOR_CONTEXT_CLOSE)
    if start == -1 or end == -1 or end < start:
        return normalized
    return normalized[:start] + normalized[end + len(AUTHOR_CONTEXT_CLOSE) :]


def _summary_digest(body: str) -> str:
    """Digest the generated portion, independently of the stamp in its marker."""
    return github_utils.text_digest(_generated_portion(body))


def _stamp_summary_digest(body: str) -> str:
    """Replace the plain marker with one carrying the digest of the approved body."""
    digest = _summary_digest(body)
    return SUMMARY_MARKER_PATTERN.sub(f"<!-- aiscr-review-pr:summary digest={digest} -->", body, count=1)


def _posted_digest(body: str) -> str | None:
    match = SUMMARY_MARKER_PATTERN.search(body or "")
    if not match:
        return None
    return match.group(1)


def _author_context_region(body: str) -> str | None:
    """Return the delimited author-context payload, or None when absent."""
    start = body.find(AUTHOR_CONTEXT_OPEN)
    end = body.find(AUTHOR_CONTEXT_CLOSE)
    if start == -1 or end == -1 or end < start:
        return None
    return body[start + len(AUTHOR_CONTEXT_OPEN) : end].strip()


def _description_state(description: str) -> dict[str, Any]:
    """Classify the current description for the reconciliation decision."""
    posted_digest = _posted_digest(description)
    workflow_owned = SUMMARY_MARKER_PATTERN.search(description or "") is not None
    edited_since_post: bool | None = None
    if workflow_owned and posted_digest:
        edited_since_post = _summary_digest(description) != posted_digest
    return {
        "workflow_owned": workflow_owned,
        "posted_digest": posted_digest,
        "edited_since_post": edited_since_post,
        "author_context": _author_context_region(description or ""),
        "load_bearing": detect_load_bearing(description or ""),
        "is_empty": not (description or "").strip(),
    }


def _reconciliation_sources(
    description: str,
    state: dict[str, Any],
    owner_repo: str,
    pr_number: int,
) -> tuple[list[tuple[str, str]], bool]:
    """Return the archived original plus any externally edited hunks, under one vocabulary.

    A first takeover's source is the author's own description, labelled ``description``. On a later round the source is
    this body's carried ``Author context`` region, which is a different thing: carrying it forward verbatim is required,
    where reproducing the author's narrative in that region is not. The labels differ so the shared verifier can tell
    them apart instead of guessing from shape.
    """
    if not state["workflow_owned"]:
        return [("description", description)], False
    original = state["author_context"] or ""
    sources = [(github_utils.CARRIED_REGION_SOURCE, original)] if original else []
    degraded = False
    if state["edited_since_post"] is True:
        prior, degraded = _resolve_pr_comparison_base(state, owner_repo, pr_number)
        base = prior if prior is not None else original
        if description != base:
            sources.extend(github_utils.description_edit_sources(base, description, _generated_portion))
    return sources, degraded


def _resolve_pr_comparison_base(
    state: dict[str, Any],
    owner_repo: str,
    pr_number: int,
) -> tuple[str | None, bool]:
    """Return ``(base, degraded)`` selected by the stamped digest, never by recency."""
    stamped = state["posted_digest"]
    if not stamped:
        return None, True
    bodies = github_utils.fetch_content_edit_bodies(owner_repo, pr_number, subject="pullRequest")
    match = github_utils.select_body_by_digest(bodies, stamped, _summary_digest)
    if match is None:
        archive = _find_description_archive(_fetch_issue_comments(owner_repo, pr_number))
        original = _archived_original(str(archive.get("body") or "")) if archive else ""
        return original, True
    return match, False


def cmd_reconciliation_sources(pr_number: int, repo: str | None, output_path: str | None = None) -> None:
    """Emit the labelled source list verification and the write both consume."""
    owner_repo = _resolve_repo(repo)
    description = _fetch_pr_description(pr_number, owner_repo)
    state = _description_state(description)
    sources, degraded = _reconciliation_sources(description, state, owner_repo, pr_number)
    _emit_json(github_utils.source_list_payload(sources, degraded=degraded, repository=owner_repo), output_path)


def cmd_inspect_description(pr_number: int, repo: str | None, output_path: str | None = None) -> None:
    """Report what a description takeover must carry, without writing anything."""
    owner_repo = _resolve_repo(repo)
    description = _fetch_pr_description(pr_number, owner_repo)
    archive = _find_description_archive(_fetch_issue_comments(owner_repo, pr_number))
    state = _description_state(description)
    state["repo"] = owner_repo
    state["pr_number"] = pr_number
    state["description"] = description
    state["archive_url"] = archive.get("html_url") if archive else None
    _emit_json(state, output_path)


def _find_description_archive(
    issue_comments: list[dict[str, Any]],
) -> dict[str, Any] | None:
    marked = [c for c in issue_comments if DESCRIPTION_ARCHIVE_MARKER in str(c.get("body") or "")]
    if not marked:
        return None
    return marked[0]


def _render_ledger(ledger: dict[str, Any], repository: str = "") -> str:
    """Render the disposition ledger for the provenance comment."""
    return github_utils.render_disposition_ledger(ledger, LEDGER_MARKER, repository=repository)


def _archived_original(body: str) -> str:
    original = github_utils.read_region(body, PROVENANCE_ORIGINAL_OPEN, PROVENANCE_ORIGINAL_CLOSE)
    if original is None:
        _abort("the marked PR provenance comment has no delimited original description.")
    return original


def cmd_archive_description(
    pr_number: int,
    mode: str,
    repo: str | None,
    ledger_path: str | None = None,
) -> None:
    """Keep the provenance record: the verbatim original plus the current ledger.

    The original is written once and never rewritten, so the pre-takeover state stays recoverable and attributed. The
    ledger is replaced each round, so an unattended reconciliation remains auditable by someone who never watched the
    run.
    """
    _validate_write_environment(mode, "archive-description")
    owner_repo = _resolve_repo(repo)
    ledger = _load_json(ledger_path, "disposition ledger") if ledger_path else {}
    existing = _find_description_archive(_fetch_issue_comments(owner_repo, pr_number))

    if existing:
        original = _archived_original(str(existing.get("body") or ""))
        prepared = github_utils.replace_after_region(
            str(existing.get("body") or ""),
            PROVENANCE_ORIGINAL_CLOSE,
            _render_ledger(ledger, owner_repo),
        )
        github_utils.validate_reference_batch(
            [
                github_utils.ReferenceField(
                    "archive.body",
                    prepared,
                    owner_repo,
                    (("description", original),),
                    (PROVENANCE_ORIGINAL_OPEN, PROVENANCE_ORIGINAL_CLOSE),
                    True,
                )
            ]
        )
        url = _post_comment_body(
            f"repos/{owner_repo}/issues/comments/{existing['id']}",
            "PATCH",
            prepared,
        )
        print(f"Provenance record updated: {url}")
        return

    description = _fetch_pr_description(pr_number, owner_repo)
    if not description.strip():
        _abort("refusing to archive an empty PR description; there is nothing to preserve.")
    prepared = _initial_provenance_body(owner_repo, pr_number, description, ledger)
    github_utils.validate_reference_batch(
        [
            github_utils.ReferenceField(
                "archive.body",
                prepared,
                owner_repo,
                (("description", description),),
                (PROVENANCE_ORIGINAL_OPEN, PROVENANCE_ORIGINAL_CLOSE),
                True,
            )
        ]
    )
    archive_url = _post_comment_body(
        f"repos/{owner_repo}/issues/{pr_number}/comments",
        "POST",
        prepared,
    )
    print(f"Original description archived: {archive_url}")


def _post_comment_body(endpoint: str, method: str, body: str) -> str:
    payload_path = _temporary_json({"body": body})
    try:
        return _gh("api", endpoint, "--method", method, "--input", payload_path, "--jq", ".html_url")
    finally:
        os.unlink(payload_path)


def _initial_provenance_body(
    owner_repo: str,
    pr_number: int,
    description: str,
    ledger: dict[str, Any],
) -> str:
    identity = _fetch_pr_identity(pr_number, owner_repo)
    head_sha = identity["head_sha"]
    pr_author = identity["pr_author"]
    source, author = github_utils.provenance_source_and_author(
        github_utils.fetch_issue_payload(owner_repo, pr_number, runner=_gh)
    )
    if not author:
        author = github_utils.github_mention(pr_author)
    return "\n".join(
        [
            DESCRIPTION_ARCHIVE_MARKER,
            "",
            "# Original PR description (archived)",
            "",
            f"- Source: {github_references.reference_link(source)}",
            f"- Author: {author}",
            f"- Head SHA at archive time: `{head_sha}`",
            "",
            "This is the verbatim description as written before the AIS CR review workflow",
            "took over that surface. It is preserved here for attribution and reference.",
            "",
            "---",
            "",
            github_utils.wrap_region(PROVENANCE_ORIGINAL_OPEN, description, PROVENANCE_ORIGINAL_CLOSE),
            "",
            _render_ledger(ledger, owner_repo),
        ]
    )


def cmd_verify_composition(
    sources_path: str, summary_path: str, ledger_path: str | None, output_path: str | None = None
) -> None:
    """Check a composition's accounting locally: no network, no write."""
    summary = _load_summary(summary_path)
    reference_field = github_utils.reference_field_from_sources(
        github_utils.ReferenceField(
            "composition.summary",
            summary,
            region=(AUTHOR_CONTEXT_OPEN, AUTHOR_CONTEXT_CLOSE),
        ),
        sources_path,
    )
    sources = list(reference_field.sources)
    ledger = _load_json(ledger_path, "disposition ledger") if ledger_path else {}
    load_bearing = [item["fragment"] for _, text in sources for item in detect_load_bearing(text)]
    findings = github_utils.verify_composition(
        sources,
        summary,
        ledger,
        load_bearing,
        github_utils.SurfaceVocabulary(declared_section_names(), (AUTHOR_CONTEXT_OPEN, AUTHOR_CONTEXT_CLOSE)),
    )
    github_utils.validate_reference_batch([reference_field])
    _emit_json({"findings": findings}, output_path)
    if findings:
        raise SystemExit(1)


def declared_section_names() -> frozenset[str]:
    """Section names a ledger may route an absorbed segment to on this surface.

    The shared verifier resolves a disposition target against whichever vocabulary the surface declares, so this derives
    from the same heading tuple the shape check uses rather than repeating it.
    """
    return frozenset(heading.removeprefix("## ") for heading in SUMMARY_SECTION_HEADINGS)


def _load_summary(path: str) -> str:
    """Read the authored summary and normalise its line breaks before anything digests it.

    GitHub renders a single newline inside a paragraph as a line break, so a hand-wrapped summary would post with a
    break mid-sentence. Normalising here — the one funnel local verification and the write both read through — keeps the
    approved bytes and the posted bytes identical, and leaves fenced evidence and machine markers untouched.
    """
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return github_utils.normalize_posted_line_breaks(handle.read())
    except OSError as exc:
        _abort(f"cannot read PR summary '{path}': {exc}")


def _single_line_index(lines: list[str], expected: str, label: str) -> int:
    indexes = [index for index, line in enumerate(lines) if line.strip() == expected]
    if len(indexes) != 1:
        _abort(f"PR summary must contain exactly one {label}: '{expected}'.")
    return indexes[0]


def _section_has_content(lines: list[str], start: int, end: int) -> bool:
    return any(line.strip() for line in lines[start + 1 : end])


def _validate_summary_preamble(summary: str) -> tuple[list[str], int, list[int]]:
    if summary.count(SUMMARY_MARKER) != 1:
        _abort("PR summary must contain exactly one AIS CR summary marker.")
    if INTERACTIVE_REVIEW_DISCLOSURE in summary:
        _abort("PR summary contains the formal-review findings disclosure.")
    if summary.count(INTERACTIVE_SUMMARY_DISCLOSURE) != 1:
        _abort("PR summary must contain exactly one summary-specific AI-assistance disclosure.")

    normalized = summary.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()
    marker_index = _single_line_index(lines, SUMMARY_MARKER, "AIS CR summary marker line")
    first_content_index = next(
        (index for index, line in enumerate(lines) if line.strip()),
        None,
    )
    if marker_index != first_content_index:
        _abort("PR summary marker must be the first non-empty line.")

    title_indexes = [index for index, line in enumerate(lines) if SUMMARY_TITLE_PATTERN.fullmatch(line.strip())]
    if len(title_indexes) != 1:
        _abort("PR summary must contain exactly one '# PR summary - [OWNER/REPO#NUMBER](URL)' title.")
    title_index = title_indexes[0]

    section_indexes = [
        _single_line_index(lines, heading, "required section heading") for heading in SUMMARY_SECTION_HEADINGS
    ]
    if section_indexes != sorted(section_indexes):
        _abort("PR summary required section headings are out of order.")
    purpose_index = section_indexes[0]
    if purpose_index <= title_index:
        _abort("PR summary metadata table must appear before 'Purpose and scope'.")
    return lines, title_index, section_indexes


def _validate_summary_metadata(lines: list[str], title_index: int, purpose_index: int) -> None:
    table_header_index = _single_line_index(lines, "| Field | Value |", "metadata table header")
    table_separator_indexes = [
        index for index, line in enumerate(lines) if re.fullmatch(r"\|\s*---\s*\|\s*---\s*\|", line.strip())
    ]
    if len(table_separator_indexes) != 1:
        _abort("PR summary must contain exactly one two-column metadata table separator.")
    table_separator_index = table_separator_indexes[0]
    if not title_index < table_header_index < table_separator_index < purpose_index:
        _abort("PR summary metadata table is not positioned directly after the title.")

    metadata_indexes: list[int] = []
    for field in SUMMARY_METADATA_FIELDS:
        pattern = re.compile(rf"^\|\s*{re.escape(field)}\s*\|\s*(\S.*?)\s*\|$")
        matches = [index for index, line in enumerate(lines) if pattern.fullmatch(line.strip())]
        if len(matches) != 1:
            _abort(f"PR summary metadata must contain exactly one non-empty '{field}' row.")
        metadata_indexes.append(matches[0])
    if metadata_indexes != sorted(metadata_indexes):
        _abort("PR summary metadata rows are out of order.")
    if not all(table_separator_index < index < purpose_index for index in metadata_indexes):
        _abort("PR summary metadata rows must remain inside the metadata table.")


def _validate_summary_mermaid(lines: list[str], section_indexes: list[int]) -> None:
    mermaid_starts = [index for index, line in enumerate(lines) if line.strip().lower() == "```mermaid"]
    if len(mermaid_starts) != 1:
        _abort("PR summary must contain exactly one fenced Mermaid diagram.")
    mermaid_start = mermaid_starts[0]
    mermaid_end = next(
        (index for index in range(mermaid_start + 1, len(lines)) if lines[index].strip() == "```"),
        None,
    )
    if mermaid_end is None:
        _abort("PR summary Mermaid diagram is missing its closing fence.")
    diagram_lines = [line.strip() for line in lines[mermaid_start + 1 : mermaid_end] if line.strip()]
    if not diagram_lines:
        _abort("PR summary Mermaid diagram must not be empty.")
    refusal = github_utils.unsupported_mermaid_family("\n".join(lines[mermaid_start + 1 : mermaid_end]))
    if refusal is not None:
        _abort(refusal)

    walkthrough_index = section_indexes[2]
    attention_index = section_indexes[3]
    if not walkthrough_index < mermaid_start < mermaid_end < attention_index:
        _abort("PR summary Mermaid diagram must follow the walkthrough and precede attention hints.")
    if not _section_has_content(lines, walkthrough_index, mermaid_start):
        _abort("PR summary walkthrough must contain prose before the Mermaid diagram.")


def _validate_summary_section_bodies(lines: list[str], section_indexes: list[int]) -> None:
    section_ranges = (
        (section_indexes[0], section_indexes[1]),
        (section_indexes[1], section_indexes[2]),
        (section_indexes[3], section_indexes[4]),
        (section_indexes[4], section_indexes[5]),
        (section_indexes[5], section_indexes[6]),
    )
    for start, end in section_ranges:
        if not _section_has_content(lines, start, end):
            _abort(f"PR summary section '{lines[start].strip()}' must not be empty.")


def _validate_author_context_region(lines: list[str], section_indexes: list[int]) -> None:
    """Return the carried-fragment region is delimited so regeneration stays deterministic."""
    open_index = _single_line_index(lines, AUTHOR_CONTEXT_OPEN, "author-context opening marker")
    close_index = _single_line_index(lines, AUTHOR_CONTEXT_CLOSE, "author-context closing marker")
    author_index = section_indexes[5]
    lineage_index = section_indexes[6]
    if not author_index < open_index < close_index < lineage_index:
        _abort("PR summary author-context markers must sit inside the 'Author context' section.")
    if not _section_has_content(lines, open_index, close_index):
        _abort(
            "PR summary author-context region must state the carried content, or say so explicitly when there is none."
        )


def _validate_summary_footer(lines: list[str], lineage_index: int) -> None:
    disclosure_index = _single_line_index(
        lines,
        INTERACTIVE_SUMMARY_DISCLOSURE,
        "summary-specific AI-assistance disclosure",
    )
    thematic_breaks = [index for index in range(lineage_index + 1, disclosure_index) if lines[index].strip() == "---"]
    if len(thematic_breaks) != 1:
        _abort("PR summary must contain one thematic break before its disclosure.")
    thematic_break_index = thematic_breaks[0]
    if not _section_has_content(lines, lineage_index, thematic_break_index):
        _abort("PR summary lineage section must not be empty.")
    if any(line.strip() for line in lines[thematic_break_index + 1 : disclosure_index]):
        _abort("PR summary disclosure must immediately follow the thematic break.")
    last_content_index = max(index for index, line in enumerate(lines) if line.strip())
    if disclosure_index != last_content_index:
        _abort("PR summary disclosure must be the final non-empty line.")


def _validate_summary(summary: str) -> None:
    lines, title_index, section_indexes = _validate_summary_preamble(summary)
    _validate_summary_metadata(lines, title_index, section_indexes[0])
    _validate_summary_mermaid(lines, section_indexes)
    _validate_summary_section_bodies(lines, section_indexes)
    _validate_author_context_region(lines, section_indexes)
    _validate_summary_footer(lines, section_indexes[6])


def _post_summary_comment(owner_repo: str, pr_number: int, payload_path: str) -> None:
    existing = _find_summary_comment(_fetch_issue_comments(owner_repo, pr_number))
    if existing:
        summary_url = _gh(
            "api",
            f"repos/{owner_repo}/issues/comments/{existing['id']}",
            "--method",
            "PATCH",
            "--input",
            payload_path,
            "--jq",
            ".html_url",
        )
        print(f"PR summary comment updated: {summary_url}")
    else:
        summary_url = _gh(
            "api",
            f"repos/{owner_repo}/issues/{pr_number}/comments",
            "--method",
            "POST",
            "--input",
            payload_path,
            "--jq",
            ".html_url",
        )
        print(f"PR summary comment posted: {summary_url}")


def _post_summary_description(owner_repo: str, pr_number: int, payload_path: str) -> None:
    summary_url = _gh(
        "api",
        f"repos/{owner_repo}/pulls/{pr_number}",
        "--method",
        "PATCH",
        "--input",
        payload_path,
        "--jq",
        ".html_url",
    )
    print(f"PR description replaced with approved summary: {summary_url}")


def _render_findings(findings: list[dict[str, Any]]) -> str:
    return "\n".join(f"  - {item['kind']}: {item.get('detail', '')}" for item in findings)


def _check_summary_references(
    owner_repo: str,
    pr_number: int,
    summary: str,
    sources: list[tuple[str, str]] | None = None,
) -> None:
    """Obtain source evidence only for a summary that needs a carried-fragment exception."""
    region = (AUTHOR_CONTEXT_OPEN, AUTHOR_CONTEXT_CLOSE)
    carried = github_utils.read_region(summary, *region)
    if sources is None:
        sources = []
        if carried and github_references.check_references(carried):
            description = _fetch_pr_description(pr_number, owner_repo)
            sources, _ = _reconciliation_sources(description, _description_state(description), owner_repo, pr_number)
    github_utils.validate_reference_batch(
        [
            github_utils.ReferenceField(
                "summary.body",
                summary,
                owner_repo,
                tuple(sources),
                region,
            )
        ]
    )


def _prepare_description_takeover(
    owner_repo: str,
    pr_number: int,
    summary: str,
    ledger: dict[str, Any],
) -> str | None:
    """Enforce the takeover preconditions and stamp the posted digest.

    Returns the body to write, or ``None`` when the generated portion is unchanged and there is nothing to post.
    """
    description = _fetch_pr_description(pr_number, owner_repo)
    state = _description_state(description)
    if not state["is_empty"] and not state["workflow_owned"]:
        if _find_description_archive(_fetch_issue_comments(owner_repo, pr_number)) is None:
            _abort(
                "refusing a first description takeover before the original is archived. "
                "Run 'archive-description' first so the author's text is preserved."
            )

    sources, degraded = _reconciliation_sources(description, state, owner_repo, pr_number)
    findings = github_utils.verify_composition(
        sources,
        summary,
        ledger,
        [item["fragment"] for _, text in sources for item in detect_load_bearing(text)],
        github_utils.SurfaceVocabulary(declared_section_names(), (AUTHOR_CONTEXT_OPEN, AUTHOR_CONTEXT_CLOSE)),
    )
    if findings:
        prefix = ""
        if state["edited_since_post"] is True:
            prefix = (
                "refusing to overwrite a pull-request description that has been edited since "
                "the workflow last posted it. Run 'reconciliation-sources' and reconcile the "
                "emitted description-edit sources into the ledger, then verify-composition "
                "against that list. "
            )
        suffix = (
            " operating degraded: content-edit history yielded no body matching the stamped digest." if degraded else ""
        )
        _abort(
            prefix
            + "refusing to write an unverified composition; every finding is repairable"
            + f"{suffix}:\n"
            + _render_findings(findings)
        )

    _check_summary_references(owner_repo, pr_number, summary, sources)
    if state["posted_digest"] and state["posted_digest"] == _summary_digest(summary):
        return None
    return _stamp_summary_digest(summary)


def cmd_post_summary(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    pr_number: int,
    mode: str,
    summary_path: str,
    target: str,
    repo: str | None,
    ledger_path: str | None = None,
) -> None:
    """Post the marked PR summary to the explicitly selected surface.

    Reconciliation runs in both modes; what differs is the supervision. A reviewer reads the dispositions in interactive
    mode, and the same dispositions are verified mechanically here, so an unattended run carries every obligation an
    attended one does.
    """
    if target not in SUMMARY_TARGETS:
        _abort("post-summary requires --target comment or --target description.")
    summary = _load_summary(summary_path)
    _validate_summary(summary)
    _validate_write_environment(mode, "post-summary")

    owner_repo = _resolve_repo(repo)
    if target == "description":
        ledger = _load_json(ledger_path, "disposition ledger") if ledger_path else {}
        prepared = _prepare_description_takeover(owner_repo, pr_number, summary, ledger)
        if prepared is None:
            print("PR description already carries this summary; nothing to post.")
            return
        summary = prepared
    else:
        _check_summary_references(owner_repo, pr_number, summary)

    payload_path = _temporary_json({"body": summary})
    try:
        if target == "comment":
            _post_summary_comment(owner_repo, pr_number, payload_path)
        else:
            _post_summary_description(owner_repo, pr_number, payload_path)
    finally:
        os.unlink(payload_path)


def _is_link_or_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError as exc:
        _abort(f"cannot inspect cleanup path '{path}': {exc}")
    if path.is_symlink():
        return True
    is_junction = getattr(os.path, "isjunction", None)
    if is_junction is not None and is_junction(path):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(metadata, "st_file_attributes", 0) & reparse_flag)


def _cleanup_roots() -> tuple[Path, Path]:
    """Return the bulk and hand-off roots cleanup is confined to."""
    return REVIEW_SCRATCH_ROOT.absolute(), REVIEW_HANDOFF_ROOT.absolute()


def _cleanup_candidate(work_dir: str) -> tuple[Path, Path, Path, Path]:
    """Resolve one run's bulk and hand-off directories from either root's path."""
    scratch_root, handoff_root = _cleanup_roots()
    candidate = Path(work_dir)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    candidate = candidate.absolute()

    if candidate in (scratch_root, handoff_root):
        _abort("cleanup refuses to remove a PR-review root itself.")
    if candidate.parent not in (scratch_root, handoff_root):
        _abort(f"cleanup work directory must be a direct child of '{scratch_root}' or '{handoff_root}'.")
    if not REVIEW_RUN_DIR_PATTERN.fullmatch(candidate.name):
        _abort("cleanup work directory name must identify repository, PR number, and head SHA.")
    return scratch_root, handoff_root, scratch_root / candidate.name, handoff_root / candidate.name


def _validated_cleanup_entries(root: Path, candidate: Path, *, required: bool = True) -> list[Path]:
    """Validate one root's run directory and return its entries.

    An absent hand-off directory is an empty class, not a failure: a run that rendered no hand-off has nothing to leak.
    The bulk directory identifies the run and must exist.
    """
    try:
        local_scratch_paths.checked_handoff_file(REPO_ROOT, candidate)
    except ValueError as exc:
        _abort(str(exc))
    if not root.exists() and not root.is_symlink():
        if required:
            _abort(f"PR-review cleanup root does not exist: '{root}'.")
        return []
    if _is_link_or_reparse(root):
        _abort("cleanup refuses symlink or reparse-point roots and work directories.")
    if not root.is_dir():
        _abort(f"PR-review cleanup root is not a directory: '{root}'.")
    if not candidate.exists() and not candidate.is_symlink():
        if required:
            _abort(f"cleanup work directory does not exist or is not a directory: '{candidate}'.")
        return []
    if _is_link_or_reparse(candidate):
        _abort("cleanup refuses symlink or reparse-point roots and work directories.")
    if not candidate.is_dir():
        _abort(f"cleanup work directory is not a directory: '{candidate}'.")

    root_resolved = root.resolve(strict=True)
    candidate_resolved = candidate.resolve(strict=True)
    if candidate_resolved.parent != root_resolved:
        _abort("cleanup work directory resolves outside its PR-review root.")

    entries = sorted(candidate.iterdir(), key=lambda entry: entry.name)
    return entries


def _preflight_cleanup_entries(entries: list[Path], allowed: frozenset[str]) -> None:
    for entry in entries:
        if entry.name not in allowed:
            _abort(f"cleanup found unexpected entry '{entry.name}'; nothing was removed.")
        if _is_link_or_reparse(entry) or not entry.is_file():
            _abort(f"cleanup entry '{entry.name}' is not an ordinary file; nothing was removed.")


def _remove_cleanup_entries(candidate: Path, entries: list[Path]) -> None:
    if not candidate.exists():
        return
    for entry in entries:
        try:
            entry.unlink()
        except OSError as exc:
            _abort(f"cannot remove review artifact '{entry}': {exc}")
        print(f"Removed review artifact: {entry}")
    try:
        candidate.rmdir()
    except OSError as exc:
        _abort(f"cannot remove empty review work directory '{candidate}': {exc}")
    print(f"Removed review work directory: {candidate}")


def cmd_cleanup(work_dir: str, approve: bool) -> None:
    """Remove allowlisted artifacts from both roots of one bounded PR-review run."""
    if not approve:
        _abort("cleanup requires --approve after the review workflow reaches a terminal outcome.")

    scratch_root, handoff_root, bulk_run, handoff_run = _cleanup_candidate(work_dir)
    bulk_entries = _validated_cleanup_entries(scratch_root, bulk_run)
    handoff_entries = _validated_cleanup_entries(handoff_root, handoff_run, required=False)
    _preflight_cleanup_entries(bulk_entries, ALLOWED_BULK_ARTIFACTS)
    _preflight_cleanup_entries(handoff_entries, ALLOWED_HANDOFF_ARTIFACTS)
    _remove_cleanup_entries(bulk_run, bulk_entries)
    _remove_cleanup_entries(handoff_run, handoff_entries)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:  # pylint: disable=too-many-locals,too-many-statements
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="github_pr_review.py",
        description=(
            "Gather PR context and diff coverage, render exact approval artifacts, "
            "post governed GitHub PR reviews, repair a submitted review, and clean "
            "bounded run artifacts. Summary target, posting mode, and cleanup "
            "approval are always explicit."
        ),
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    gather = subparsers.add_parser(
        "gather",
        help="Fetch marked lineage and PR context (read-only).",
    )
    gather.add_argument("pr_number", type=int, metavar="PR_NUMBER")
    gather.add_argument("--repo", metavar="OWNER/REPO")
    gather.add_argument(
        "--local-diff",
        metavar="FILE",
        help="Locally produced unified diff for the pull request's base and head.",
    )
    gather.add_argument(
        "--sibling",
        metavar="NAME",
        help=(
            "Registered repository name (multi-repository acquisition): produce the local diff "
            "through the acquisition bridge and write it to --local-diff, so no shell "
            "redirect can re-encode it."
        ),
    )
    gather.add_argument(
        "--output-path",
        metavar="FILE",
        help="Write JSON to this UTF-8 file instead of stdout, so a shell redirect cannot re-encode it.",
    )

    render = subparsers.add_parser(
        "render",
        help="Create a canonical bundle and its exact approval view (local only).",
    )
    render.add_argument("--mode", required=True, choices=MODES)
    render.add_argument("--review-payload", required=True, metavar="FILE")
    render.add_argument("--replies", metavar="FILE")
    render.add_argument("--bundle", required=True, metavar="FILE")
    render.add_argument("--approval-view", required=True, metavar="FILE")
    render.add_argument("--pr-context", required=True, metavar="FILE")
    render.add_argument("--findings-ledger", required=True, metavar="FILE")
    render.add_argument("--local-diff", metavar="FILE")

    post = subparsers.add_parser(
        "post",
        help="Post a canonical review bundle using an explicit identity mode.",
    )
    post.add_argument("pr_number", type=int, metavar="PR_NUMBER")
    post.add_argument("--mode", required=True, choices=MODES)
    post.add_argument("--review-bundle", required=True, metavar="FILE")
    post.add_argument("--approved-digest", metavar="SHA256")
    post.add_argument("--approval-view", metavar="FILE", help="Exact rendered view required for interactive posting.")
    post.add_argument("--repo", metavar="OWNER/REPO")
    post.add_argument("--findings-ledger", required=True, metavar="FILE")
    post.add_argument("--pr-context", required=True, metavar="FILE")

    inspect_description = subparsers.add_parser(
        "inspect-description",
        help="Report what a description takeover must carry (read-only).",
    )
    inspect_description.add_argument("pr_number", type=int, metavar="PR_NUMBER")
    inspect_description.add_argument("--repo", metavar="OWNER/REPO")
    inspect_description.add_argument(
        "--output-path",
        metavar="FILE",
        help="Write JSON to this UTF-8 file instead of stdout, so a shell redirect cannot re-encode it.",
    )

    emit_sources = subparsers.add_parser(
        "reconciliation-sources",
        help="Emit the labelled reconciliation source list (read-only).",
    )
    emit_sources.add_argument("pr_number", type=int, metavar="PR_NUMBER")
    emit_sources.add_argument("--repo", metavar="OWNER/REPO")
    emit_sources.add_argument(
        "--output-path",
        metavar="FILE",
        help="Write JSON to this UTF-8 file instead of stdout, so a shell redirect cannot re-encode it.",
    )

    archive_description = subparsers.add_parser(
        "archive-description",
        help="Archive the current PR description once, before a first takeover.",
    )
    archive_description.add_argument("pr_number", type=int, metavar="PR_NUMBER")
    archive_description.add_argument("--mode", required=True, choices=MODES)
    archive_description.add_argument("--repo", metavar="OWNER/REPO")
    archive_description.add_argument("--ledger", metavar="FILE")

    verify_composition = subparsers.add_parser(
        "verify-composition",
        help="Check a composition's accounting against the emitted source list (local only).",
    )
    verify_composition.add_argument("--sources", required=True, metavar="FILE")
    verify_composition.add_argument("--summary", required=True, metavar="FILE")
    verify_composition.add_argument("--ledger", metavar="FILE")
    verify_composition.add_argument(
        "--output-path",
        metavar="FILE",
        help="Write JSON to this UTF-8 file instead of stdout, so a shell redirect cannot re-encode it.",
    )

    post_summary = subparsers.add_parser(
        "post-summary",
        help="Post the exact marked PR summary file to an explicitly selected surface.",
    )
    post_summary.add_argument("pr_number", type=int, metavar="PR_NUMBER")
    post_summary.add_argument("--mode", required=True, choices=MODES)
    post_summary.add_argument("--summary", required=True, metavar="FILE")
    post_summary.add_argument("--target", required=True, choices=SUMMARY_TARGETS)
    post_summary.add_argument("--repo", metavar="OWNER/REPO")
    post_summary.add_argument("--ledger", metavar="FILE")

    repair = subparsers.add_parser(
        "repair",
        help="Render or post an inline, reply, or body repair under the approval digest.",
    )
    repair_sub = repair.add_subparsers(dest="repair_command", required=True)
    repair_render = repair_sub.add_parser(
        "render",
        help="Create an inline, reply, and/or body repair bundle with its exact approval view (local only).",
    )
    repair_render.add_argument("--mode", required=True, choices=MODES)
    repair_render.add_argument("--review-id", required=True, type=int, metavar="ID")
    repair_render.add_argument("--commit-id", required=True, metavar="SHA")
    repair_render.add_argument("--inline-comments", metavar="FILE")
    repair_render.add_argument("--replies", metavar="FILE")
    repair_render.add_argument("--reopen", metavar="FILE")
    repair_render.add_argument("--body", metavar="FILE")
    repair_render.add_argument(
        "--findings-ledger", metavar="FILE", help="Required structured records for a body amendment."
    )
    repair_render.add_argument(
        "--source-review-bundle",
        metavar="FILE",
        help="Required source review bundle for preserving body-repair anchors.",
    )
    repair_render.add_argument("--bundle", required=True, metavar="FILE")
    repair_render.add_argument("--approval-view", required=True, metavar="FILE")
    repair_post = repair_sub.add_parser(
        "post",
        help="Post an approved repair bundle using an explicit identity mode.",
    )
    repair_post.add_argument("pr_number", type=int, metavar="PR_NUMBER")
    repair_post.add_argument("--mode", required=True, choices=MODES)
    repair_post.add_argument("--repair-bundle", required=True, metavar="FILE")
    repair_post.add_argument("--approved-digest", metavar="SHA256")
    repair_post.add_argument("--approval-view", metavar="FILE", help="Exact rendered repair view.")
    repair_post.add_argument("--repo", metavar="OWNER/REPO")

    prepare = subparsers.add_parser("prepare-run", help="Create the local run roots and visible bulk pointer.")
    prepare.add_argument("--run", required=True, metavar="RUN_NAME")

    list_artifacts = subparsers.add_parser(
        "list-run-artifacts",
        help="Print the prescribed review run-artifact names (the cleanup allowlist).",
    )
    list_artifacts.add_argument(
        "--class",
        dest="artifact_class",
        choices=("bulk", "handoff"),
        default=None,
        help="Print only one class's artifacts (default: both).",
    )
    list_artifacts.set_defaults(subcommand="list-run-artifacts")

    cleanup = subparsers.add_parser(
        "cleanup",
        help="Remove allowlisted artifacts from one approved PR-review run directory.",
    )
    cleanup.add_argument(
        "--work-dir",
        required=True,
        metavar="DIR",
        help="Direct-child PR-review run directory beneath either the bulk cache root or the visible hand-off root.",
    )
    cleanup.add_argument(
        "--approve",
        action="store_true",
        help="Confirm removal after all posting decisions reach a terminal outcome.",
    )

    return parser


def main() -> None:  # pylint: disable=too-many-branches
    """Parse CLI arguments and dispatch to the selected subcommand."""
    configure_stdout_utf8()
    args = build_parser().parse_args()
    if args.subcommand == "gather":
        cmd_gather(args.pr_number, args.repo, args.local_diff, args.output_path, args.sibling)
    elif args.subcommand == "render":
        cmd_render(
            args.mode,
            args.review_payload,
            args.replies,
            args.bundle,
            args.approval_view,
            args.pr_context,
            args.findings_ledger,
            args.local_diff,
        )
    elif args.subcommand == "post":
        cmd_post(
            args.pr_number,
            args.mode,
            args.review_bundle,
            args.approved_digest,
            args.repo,
            args.findings_ledger,
            args.pr_context,
            args.approval_view,
        )
    elif args.subcommand == "repair":
        if args.repair_command == "render":
            cmd_repair_render(
                args.mode,
                args.review_id,
                args.commit_id,
                args.inline_comments,
                args.body,
                args.bundle,
                args.approval_view,
                replies_path=args.replies,
                reopen_path=args.reopen,
                findings_ledger_path=args.findings_ledger,
                source_review_path=args.source_review_bundle,
            )
        else:
            cmd_repair_post(
                args.pr_number,
                args.mode,
                args.repair_bundle,
                args.approved_digest,
                args.repo,
                args.approval_view,
            )
    elif args.subcommand == "prepare-run":
        cmd_prepare_run(args.run)
    elif args.subcommand == "list-run-artifacts":
        cmd_list_run_artifacts(args.artifact_class)
    elif args.subcommand == "inspect-description":
        cmd_inspect_description(args.pr_number, args.repo, args.output_path)
    elif args.subcommand == "reconciliation-sources":
        cmd_reconciliation_sources(args.pr_number, args.repo, args.output_path)
    elif args.subcommand == "archive-description":
        cmd_archive_description(args.pr_number, args.mode, args.repo, args.ledger)
    elif args.subcommand == "verify-composition":
        cmd_verify_composition(args.sources, args.summary, args.ledger, args.output_path)
    elif args.subcommand == "post-summary":
        cmd_post_summary(args.pr_number, args.mode, args.summary, args.target, args.repo, args.ledger)
    else:
        cmd_cleanup(args.work_dir, args.approve)


if __name__ == "__main__":  # pragma: no cover -- exercised through main()
    main()
