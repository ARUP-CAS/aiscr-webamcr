#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00

"""Shared GitHub write machinery for posting engines.

Holds exactly what more than one posting engine needs: the ``gh`` process funnel and its file helpers, the posting
identity-mode gate, the canonical approval digest, the machine-marker plus AI-assistance disclosure contract, and the
shared provenance helpers (paired regions, disposition-ledger rendering, and content-edit-history lookup).
Engine-specific payload shapes, validation rules, and command surfaces stay in the engine that owns them.

Every function here is reachable from an enrolled sibling, so the module carries no hub-only assumption. The shared
reference checker, ``log_utils``, and ``proc_utils`` travel with it in the same explicitly declared bundle.

Contract: workflow/github-write-fidelity
Class: library
Exit codes: Library module with no entrypoint; imported by the posting engines (abort raises SystemExit 1)
"""

from __future__ import annotations

# The shared write contract stays one auditable module because it is one delivery unit:
# both engines name it in their `bundled_scripts`, so splitting it would change what every
# enrolled sibling receives rather than only how this file reads.
# pylint: disable=too-many-lines
import difflib
import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Callable, Collection
from typing import Any, NamedTuple, NoReturn

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from lib.log_utils import log_error  # noqa: E402
from lib.proc_utils import run_diagnostic, run_exact  # noqa: E402

from github import github_references  # noqa: E402

MODES = ("interactive", "automated")
CI_ENV_VARS = ("CI", "GITHUB_ACTIONS")

# GitHub renders the core Mermaid build only; families that need a third-party
# plugin cannot render there and are refused. `zenuml` is the only such family.
PLUGIN_ONLY_MERMAID_FAMILIES = frozenset({"zenuml"})


def unsupported_mermaid_family(diagram_text: str) -> str | None:
    """Return a refusal when a Mermaid block's family needs a third-party plugin.

    Skip Mermaid front matter, comments, and initialization directives before reading the declared family. Inspecting
    only the first content line lets a preamble hide a plugin family; searching every token would reject core diagrams
    that merely use a plugin's name in a label or configuration value.
    """
    content = re.sub(r"%%\{.*?\}%%", "", diagram_text.removeprefix("\ufeff"), flags=re.DOTALL).lstrip()
    content = re.sub(r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|$)", "", content, flags=re.DOTALL)
    first_line = next(
        (line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("%%")), ""
    )
    tokens = first_line.split()
    family = tokens[0].lower() if tokens else ""
    if family in PLUGIN_ONLY_MERMAID_FAMILIES:
        return f"Mermaid family '{family}' renders only through a third-party plugin; GitHub does not render it."
    return None


class PostingContract(NamedTuple):
    """Machine marker and per-mode disclosure that a posted body must carry.

    The automated slot is optional so a surface can state that it has no unattended mode. A required slot forced every
    surface to invent a disclosure it never uses, which is how an unrequested automated path reaches a command surface.
    """

    marker: str
    interactive_disclosure: str
    automated_disclosure: str | None = None


class ReferenceField(NamedTuple):
    """One prospective outgoing field and its engine-acquired preservation context."""

    label: str
    text: str
    repository: str = ""
    sources: tuple[tuple[str, str], ...] = ()
    region: tuple[str, str] | None = None
    original: bool = False


def reference_snapshots(field: ReferenceField) -> dict[str, github_references.SourceSnapshot]:
    """Construct source snapshots, admitting existing newline equivalence only for a complete original."""
    original = read_region(field.text, *field.region) if field.original and field.region else None
    snapshots = {}
    for index, (label, text) in enumerate(field.sources):
        if original is not None and text_digest(original) == text_digest(text):
            text = original
        snapshots[f"{index}:{label}"] = github_references.SourceSnapshot(
            field.repository, text, tuple(item["fragment"] for item in detect_load_bearing(text))
        )
    return snapshots


def preserved_reference_spans(
    field: ReferenceField,
    snapshots: dict[str, github_references.SourceSnapshot],
) -> list[github_references.SourceSpan]:
    """Admit one exact original or one occurrence of each required complete carried fragment.

    Regions locate the output; their markers provide no source evidence. The snapshot supplies that evidence, and the
    pure checker independently verifies each complete fragment, source digest, and payload-bound output span.
    """
    if field.region is None:
        return []
    opening, closing = field.region
    content = read_region(field.text, opening, closing)
    if content is None:
        return []
    offset = field.text.index(opening) + len(opening)
    if field.text[offset:].startswith("\r\n"):
        offset += 2
    elif field.text[offset:].startswith("\n"):
        offset += 1
    spans: list[github_references.SourceSpan] = []
    used: set[str] = set()
    for source_id, snapshot in snapshots.items():
        fragments = (snapshot.text,) if field.original else snapshot.fragments
        for fragment in fragments:
            if not fragment or fragment in used or not github_references.check_references(fragment):
                continue
            position = 0 if field.original and content == fragment else content.find(fragment)
            if position < 0 or (field.original and content != fragment):
                continue
            used.add(fragment)
            start = offset + position
            spans.append(
                github_references.SourceSpan(
                    start,
                    start + len(fragment),
                    source_id,
                    github_references.snapshot_digest(snapshot),
                    github_references.text_digest(field.text),
                    fragment,
                )
            )
    return spans


def validate_reference_batch(fields: list[ReferenceField]) -> dict[str, dict[str, str]]:
    """Preflight every outgoing field before any part of its batch mutates GitHub.

    Return source fingerprints for the approval envelope when a field used preservation evidence. A fresh source
    snapshot therefore changes approval even when the particular carried fragment stayed the same.
    """
    findings: list[github_references.Diagnostic] = []
    evidence: dict[str, dict[str, str]] = {}
    for field in fields:
        snapshots = reference_snapshots(field)
        spans = preserved_reference_spans(field, snapshots)
        findings.extend(
            github_references.check_references(
                field.text,
                source=field.label,
                spans=spans,
                sources=snapshots,
            )
        )
        if spans:
            evidence[field.label] = {
                source_id: github_references.snapshot_digest(snapshots[source_id])
                for source_id in sorted({span.source_id for span in spans})
            }
    if findings:
        abort(
            "GitHub reference validation failed; repair the cited fields without guessing:\n"
            + "\n".join(item.render() for item in findings)
        )
    return evidence


def abort(message: str) -> NoReturn:
    """Print an error to stderr and exit non-zero."""
    log_error(message)
    raise SystemExit(1)


def run(cmd: list[str]) -> str:
    """Run a command and return stripped stdout. Raise SystemExit on failure.

    Strict decoding: this funnel carries every ``gh`` call, including review and summary bodies that are posted verbatim
    and digest-checked, so a substituted character would corrupt published content.
    """
    result = run_exact(cmd)
    if result.returncode != 0:
        message = result.stderr.strip() if result.stderr else "(no stderr)"
        log_error(f"command failed: {' '.join(cmd)}\n{message}")
        raise SystemExit(1)
    return result.stdout.strip()


def gh(*args: str) -> str:
    """Run a ``gh`` subcommand through the strict funnel."""
    return run(["gh", *args])


def graphql(
    query: str,
    *,
    runner: Callable[..., str] | None = None,
    **variables: str,
) -> dict[str, Any]:
    """Run a GraphQL query through ``gh`` and return the parsed payload."""
    invoke = runner or gh
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args.extend(["-F", f"{key}={value}"])
    try:
        return json.loads(invoke(*args))
    except json.JSONDecodeError as exc:
        abort(f"cannot parse GraphQL response: {exc}")


def try_run(cmd: list[str]) -> tuple[bool, str]:
    """Run a command and report success with its stdout, never exiting.

    Used where a failure is information rather than a reason to stop: a reference that cannot be read is recorded as
    unfollowed so the boundary of what was read stays visible, which a fatal funnel could not express.
    """
    result = run_exact(cmd)
    if result.returncode != 0:
        return False, ""
    return True, result.stdout


def try_run_tolerant(cmd: list[str]) -> tuple[bool, str]:
    """Run a command and report success with its stdout, substituting bad bytes.

    Use only where the caller parses the output structurally and never publishes it, as with a unified diff: the engine
    derives changed-line counts and line positions from a patch and posts none of its text. A patch copies bytes from
    the changed files, so a strict decode would abort the acquisition on a target that carries non-UTF-8 content.
    Failure reporting is unchanged: a non-zero exit still returns ``(False, "")``.
    """
    result = run_diagnostic(cmd)
    if result.returncode != 0:
        return False, ""
    return True, result.stdout


def paginated_rest_items(
    endpoint: str,
    *,
    collection_key: str | None = None,
    runner: Callable[[list[str]], tuple[bool, str]] = try_run,
) -> list[dict[str, Any]] | None:
    """Read every REST page and flatten its collection.

    ``gh api --paginate --slurp`` always returns an array of page payloads. Plain collection endpoints therefore produce
    ``[[...], [...]]`` while envelope endpoints such as check runs produce ``[{"check_runs": [...]}, ...]``. Returning
    ``None`` distinguishes an unreadable endpoint from a readable empty collection.
    """
    ok, stdout = runner(["gh", "api", endpoint, "--paginate", "--slurp"])
    if not ok:
        return None
    try:
        pages = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if collection_key and isinstance(pages, dict):
        pages = [pages]
    if not isinstance(pages, list):
        return None
    if collection_key is None and all(isinstance(item, dict) for item in pages):
        return pages

    items: list[dict[str, Any]] = []
    for page in pages:
        collection = page.get(collection_key) if collection_key and isinstance(page, dict) else page
        if not isinstance(collection, list) or not all(isinstance(item, dict) for item in collection):
            return None
        items.extend(collection)
    return items


def paginated_graphql_nodes(
    fetch_page: Callable[[str | None], dict[str, Any]],
    initial: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Follow one GraphQL connection until ``hasNextPage`` is false.

    The caller owns the query and returns the connection object for each cursor. This keeps API-specific paths in their
    engines while the fail-closed cursor discipline has one implementation.
    """
    nodes: list[dict[str, Any]] = []
    connection = initial if initial is not None else fetch_page(None)
    while True:
        page_nodes = connection.get("nodes") or []
        if not isinstance(page_nodes, list) or not all(isinstance(node, dict) or node is None for node in page_nodes):
            abort("GitHub GraphQL connection returned an invalid nodes collection.")
        nodes.extend(node for node in page_nodes if node is not None)
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            return nodes
        cursor = page_info.get("endCursor")
        if not isinstance(cursor, str) or not cursor:
            abort("GitHub GraphQL connection has another page but no end cursor.")
        connection = fetch_page(cursor)


CONTENT_EDIT_SUBJECTS = frozenset({"issue", "pullRequest"})
_ISSUE_CONTENT_EDITS_QUERY = """
query($owner:String!, $name:String!, $number:Int!, $endCursor:String) {
  repository(owner:$owner, name:$name) {
    issue(number:$number) {
      userContentEdits(first:100, after:$endCursor) {
        nodes { diff }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""
_PULL_CONTENT_EDITS_QUERY = """
query($owner:String!, $name:String!, $number:Int!, $endCursor:String) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      userContentEdits(first:100, after:$endCursor) {
        nodes { diff }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""


def fetch_content_edit_bodies(owner_repo: str, number: int, *, subject: str) -> list[str]:
    """Return every prior body GitHub recorded for an issue or pull-request description.

    ``diff`` is documented as a summary and observably carries the complete body as of that edit. Callers select by
    digest rather than by recency; an unusable history is an empty list, not a nearest-neighbour guess.
    """
    if subject not in CONTENT_EDIT_SUBJECTS:
        abort(f"unsupported content-edit subject '{subject}'; expected issue or pullRequest.")
    query = _ISSUE_CONTENT_EDITS_QUERY if subject == "issue" else _PULL_CONTENT_EDITS_QUERY
    field = "issue" if subject == "issue" else "pullRequest"
    owner, _, name = owner_repo.partition("/")

    def fetch_page(cursor: str | None) -> dict[str, Any]:
        variables = {"owner": owner, "name": name, "number": str(number)}
        if cursor is not None:
            variables["endCursor"] = cursor
        payload = graphql(query, **variables)
        node = (((payload.get("data") or {}).get("repository") or {}).get(field)) or {}
        return node.get("userContentEdits") or {}

    return [str(node.get("diff") or "") for node in paginated_graphql_nodes(fetch_page)]


def select_body_by_digest(
    bodies: Collection[str],
    digest: str,
    digest_fn: Callable[[str], str],
) -> str | None:
    """Return the body whose digest matches, or ``None`` when none does.

    Matching the digest, not the newest entry and not the posting account, is what identifies the workflow's own post
    after a later human edit. A digest that appears only as a leftover marker in a subsequent edit is not a match.
    """
    for body in bodies:
        if body and digest_fn(body) == digest:
            return body
    return None


def resolve_repo(repo_arg: str | None) -> str:
    """Return the explicit ``owner/repo`` when given, else the checkout's own."""
    if repo_arg:
        return repo_arg
    return gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner")


def load_json(path: str, label: str) -> Any:
    """Read a JSON file, aborting with the caller's label on failure."""
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        abort(f"cannot read {label} '{path}': {exc}")


def write_json(path: str, value: Any) -> None:
    """Write pretty JSON with LF endings."""
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except OSError as exc:
        abort(f"cannot write JSON file '{path}': {exc}")


def write_text(path: str, value: str, label: str = "text file") -> None:
    """Write text with LF endings, aborting with the caller's label on failure."""
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(value)
    except OSError as exc:
        abort(f"cannot write {label} '{path}': {exc}")


def temporary_json(value: Any) -> str:
    """Write a value to a temp JSON file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
        newline="\n",
    ) as handle:
        json.dump(value, handle, ensure_ascii=False)
        handle.write("\n")
        return handle.name


def env_is_set(name: str) -> bool:
    """Report whether an environment variable is set to a truthy value."""
    value = os.environ.get(name)
    if value is None:
        return False
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


def validate_write_environment(mode: str, subcommand: str) -> None:
    """Enforce the explicit posting identity mode before any GitHub write."""
    if mode not in MODES:
        abort(f"unsupported mode '{mode}'; expected interactive or automated.")

    ci_variables = [name for name in CI_ENV_VARS if env_is_set(name)]
    token_present = bool(os.environ.get("GH_TOKEN"))

    if mode == "interactive":
        if ci_variables:
            abort(
                f"'{subcommand}' in interactive mode is not allowed in a recognized "
                f"CI environment ({', '.join(ci_variables)})."
            )
        if token_present:
            abort(
                "interactive posting refuses ambient GH_TOKEN because its identity "
                "cannot be verified. Unset GH_TOKEN for this invocation and retry "
                "using stored gh authentication."
            )
        return

    if not ci_variables:
        abort(f"'{subcommand}' in automated mode requires a recognized CI environment ({', '.join(CI_ENV_VARS)}).")
    if not token_present:
        abort(
            f"'{subcommand}' in automated mode requires GH_TOKEN containing a "
            "GitHub Actions or GitHub App installation token."
        )


def canonical_digest(payload: dict[str, Any]) -> str:
    """Return the SHA-256 of a payload's canonical JSON encoding.

    Approval binds to this digest, so the encoding is fixed: sorted keys, no whitespace padding, and no ASCII escaping.
    """
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def text_digest(text: str) -> str:
    """Return the SHA-256 of a posted body, insensitive to newline style.

    A posted body round-trips through GitHub, which may normalise line endings, so the digest that proves "nobody edited
    this since we posted it" must not change when only the newline style does.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def wrap_region(opening: str, payload: str, closing: str) -> str:
    """Bound a payload with an opening and closing marker, each on its own line."""
    return f"{opening}\n{payload}\n{closing}"


def read_region(body: str, opening: str, closing: str) -> str | None:
    """Return the payload between the first opening and last closing marker.

    Using the last closer is what lets a payload that quotes the closing marker round-trip: the wrapper closer is
    written after the payload, so it is the last occurrence. Reversed markers, or a closer that sits before the opener,
    yield ``None`` rather than a truncated slice.
    """
    start = body.find(opening)
    if start == -1:
        return None
    content_start = start + len(opening)
    end = body.rfind(closing)
    if end == -1 or end < content_start:
        return None
    value = body[content_start:end]
    if value.startswith("\r\n"):
        value = value[2:]
    elif value.startswith("\n"):
        value = value[1:]
    if value.endswith("\r\n"):
        value = value[:-2]
    elif value.endswith("\n"):
        value = value[:-1]
    return value


def replace_after_region(body: str, closing: str, tail: str) -> str:
    """Keep the prefix through the last closer and replace everything after it.

    The original sits inside the paired region; later rounds replace only the tail, so a quoted closer inside the
    original cannot truncate the prefix.
    """
    end = body.rfind(closing)
    if end == -1:
        abort(f"cannot replace after missing region closer '{closing}'.")
    prefix = body[: end + len(closing)].rstrip()
    return f"{prefix}\n\n{tail.rstrip()}\n"


def github_mention(login: str | None) -> str:
    """Return a GitHub mention so the name is actionable in a posted comment."""
    name = str(login or "").strip().lstrip("@")
    return f"@{name}" if name else ""


def description_comment_url(html_url: str | None, issue_id: object) -> str:
    """Permalink the issue or pull-request body as its timeline comment.

    ``owner/repo#N`` names the thread. The ``#issue-{id}`` fragment is the description item itself, which is what a
    provenance record is quoting.
    """
    base = str(html_url or "").split("#", 1)[0].rstrip("/")
    if base and issue_id is not None and str(issue_id) != "":
        return f"{base}#issue-{issue_id}"
    return base


def provenance_source_and_author(issue: dict[str, Any]) -> tuple[str, str]:
    """Return the description permalink and author mention for a provenance header."""
    pull = issue.get("pull_request")
    pull_url = pull.get("html_url") if isinstance(pull, dict) else None
    html_url = str(pull_url or issue.get("html_url") or issue.get("url") or "")
    issue_id = issue.get("id")
    if issue_id is None:
        issue_id = issue.get("databaseId")
    login = None
    user = issue.get("user")
    if isinstance(user, dict):
        login = user.get("login")
    elif isinstance(user, str):
        login = user
    author = issue.get("author")
    if not login and isinstance(author, dict):
        login = author.get("login")
    elif not login and isinstance(author, str):
        login = author
    return description_comment_url(html_url, issue_id), github_mention(login)


def fetch_issue_payload(
    owner_repo: str,
    number: int,
    runner: Callable[..., str] | None = None,
) -> dict[str, Any]:
    """Return the issues-API object for an issue or pull request."""
    invoke = runner or gh
    try:
        payload = json.loads(invoke("api", f"repos/{owner_repo}/issues/{number}"))
    except json.JSONDecodeError as exc:
        abort(f"cannot parse issue '{owner_repo}#{number}': {exc}")
    if not isinstance(payload, dict):
        abort(f"issue '{owner_repo}#{number}' did not return an object.")
    return payload


GITHUB_HOSTS = frozenset({"github.com", "www.github.com"})
GITHUB_URL_REF_PATTERN = re.compile(
    r"https://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/(?:issues|pull)/([0-9]+)"
)
GITHUB_SHORT_REF_PATTERN = re.compile(r"(?<![A-Za-z0-9_/#-])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#([0-9]+)\b")
URL_PATTERN = re.compile(r"https?://[^\s)>\]\"']+")
# Fragments another system reads. Absorbing one into prose breaks it silently and the
# failure surfaces long after a reviewer approved a body that read perfectly well, so
# these are carried verbatim instead. The set is deliberately small and universal: it
# needs no per-repository declaration.
LOAD_BEARING_PATTERNS = (
    (
        "closing-keyword",
        re.compile(
            r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#[0-9]+\b",
            re.IGNORECASE,
        ),
    ),
    ("task-list-item", re.compile(r"^[ \t]*[-*+][ \t]+\[[ xX]\][ \t]+\S.*$", re.MULTILINE)),
    ("trailer", re.compile(r"^(?:Signed-off-by|Co-authored-by):[ \t]*\S.*$", re.IGNORECASE | re.MULTILINE)),
)


def detect_load_bearing(text: str) -> list[dict[str, str]]:
    """Return the machine-read fragments a reconciliation must carry unchanged."""
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for kind, pattern in LOAD_BEARING_PATTERNS:
        for match in pattern.finditer(text or ""):
            fragment = match.group(0).strip()
            key = (kind, fragment)
            if key in seen:
                continue
            seen.add(key)
            found.append({"kind": kind, "fragment": fragment})
    return found


def extract_references(owner_repo: str, texts: list[str]) -> tuple[list[str], list[str]]:
    """Split link-like content into same-host GitHub refs and everything else."""
    refs: list[str] = []
    external: list[str] = []
    for text in texts:
        for match in GITHUB_URL_REF_PATTERN.finditer(text):
            ref = f"{match.group(1)}/{match.group(2)}#{match.group(3)}"
            if ref not in refs:
                refs.append(ref)
        for match in GITHUB_SHORT_REF_PATTERN.finditer(text):
            ref = f"{match.group(1) or owner_repo}#{match.group(2)}"
            if ref not in refs:
                refs.append(ref)
        for match in URL_PATTERN.finditer(text):
            url = match.group(0).rstrip(".,);")
            host = url.split("/")[2].lower() if url.count("/") >= 2 else ""
            if host in GITHUB_HOSTS or url in external:
                continue
            external.append(url)
    return refs, external


def dedupe_by_target(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep the first report per target, so one link is not reported twice."""
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for entry in entries:
        if entry["target"] in seen:
            continue
        seen.add(entry["target"])
        deduped.append(entry)
    return deduped


def gather_neighbourhood(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    owner_repo: str,
    self_ref: str,
    texts: list[str],
    seed_refs: list[str],
    fetch: Callable[[str], dict[str, Any] | None],
    unbounded_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Read one hop of referenced issues and pull requests, and report the rest.

    The traversal stops at a single hop. References discovered inside those items, links off GitHub, references past the
    bound, and references that could not be read are all reported rather than silently omitted, so the boundary of what
    was read stays visible. ``fetch`` belongs to the calling engine, which knows how much of a referenced item it needs.

    ``unbounded_refs`` are typed edges — a parent, a sub-issue — rather than mentions. They are placed first, while
    every direct mention is still followed. The only bound is depth: references discovered inside those first-hop items
    are reported rather than fetched. A flat model applied to a structured graph weights an incidental mention the same
    as the work item a sub-issue belongs to.
    """
    refs, external = extract_references(owner_repo, texts)
    for ref in seed_refs:
        if ref not in refs:
            refs.insert(0, ref)
    refs = [ref for ref in refs if ref != self_ref]
    typed = [ref for ref in unbounded_refs or [] if ref != self_ref]

    followed, unfollowed = _follow_first_hop(refs, external, fetch, typed)
    unfollowed.extend(_second_hop_reports(owner_repo, self_ref, followed))
    return {"referenced_items": followed, "unfollowed_references": dedupe_by_target(unfollowed)}


def _follow_first_hop(
    refs: list[str],
    external: list[str],
    fetch: Callable[[str], dict[str, Any] | None],
    typed: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    followed: list[dict[str, Any]] = []
    unfollowed: list[dict[str, str]] = [{"target": url, "reason": "link is not on GitHub"} for url in external]
    ordinary = [ref for ref in refs if ref not in typed]
    for ref in typed + ordinary:
        item = fetch(ref)
        if item is None:
            unfollowed.append({"target": ref, "reason": "reference could not be read"})
            continue
        followed.append(item)
    return followed, unfollowed


def _second_hop_reports(owner_repo: str, self_ref: str, followed: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Report what the followed items point at, without following it."""
    followed_refs = {item["ref"] for item in followed}
    texts = [item.get("body") or "" for item in followed]
    texts.extend(comment["body"] for item in followed for comment in item.get("comments") or [])
    refs, external = extract_references(owner_repo, texts)
    reports = [
        {"target": ref, "reason": "second hop; traversal stops after one"}
        for ref in refs
        if ref not in followed_refs and ref != self_ref
    ]
    reports.extend({"target": url, "reason": "link is not on GitHub"} for url in external)
    return reports


DISPOSITION_ACTIONS = frozenset(
    {"absorbed", "carried", "quoted", "superseded", "dropped", "degraded-carry", "extracted"}
)
# Source label for a body's own carried-region content on a later round, as distinct from
# the human original. Both are reconciliation input, but only one may legitimately sit in
# the region verbatim: continuity is not the appended draft the absorption check looks for.
# Defined here because the engine that emits the label and the verifier that exempts it must
# read one definition rather than agree by convention.
CARRIED_REGION_SOURCE = "carried region"


class SurfaceVocabulary(NamedTuple):
    """What a surface declares for the shared verifier to resolve against.

    One type rather than two loose arguments, because these travel together and mean one thing: the mechanism is shared,
    the vocabulary is the surface's. ``sections`` are the names a disposition may target; ``region`` is the marker pair
    bounding the carried-fragment region. Both default to unset so a surface that declares no shape is checked on
    completeness and retention alone.
    """

    sections: Collection[str] | None = None
    region: tuple[str, str] | None = None


# A lossy action must say why; an extraction must say where the content went, because
# "no content leaves without a trace" is the property that makes moving it out safe.
REASON_REQUIRED_ACTIONS = frozenset({"superseded", "dropped", "degraded-carry"})
ANCHOR_PATTERNS = (
    re.compile(r"`[^`\n]+`"),
    re.compile(r"https?://[^\s)>\]\"']+"),
    re.compile(r"(?<![A-Za-z0-9_/#-])(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#[0-9]+\b"),
)


_STRUCTURAL_LINE_PATTERNS = (
    re.compile(r"^\s*#{1,6}\s"),  # heading
    re.compile(r"^\s*\|"),  # table row
    re.compile(r"^\s*<!--"),  # HTML or machine marker
    re.compile(r"^\s*>"),  # blockquote
)
_LIST_ITEM_LINE = re.compile(r"^\s*(?:[-*+]\s+(?:\[[ xX]\]\s+)?|\d+[.)]\s+)\S")
_FENCE_LINE = re.compile(r"^\s*```")


def normalize_posted_line_breaks(text: str) -> str:
    """Join soft-wrapped prose so a posted body renders as it was written.

    GitHub renders a single newline inside a paragraph as a line break in issue, pull-request, and comment bodies, so a
    hand-wrapped paragraph posts with a break mid-sentence at every wrap. Joining continuation lines before the approval
    digest is computed means the approver sees what will render and the approved bytes are the posted bytes; normalising
    after approval would change content nobody agreed to.

    Structure whose line break is deliberate keeps its own line: headings, table rows, list items, blockquotes, HTML and
    machine markers, and everything inside a fenced block. Quoted evidence therefore survives byte-for-byte, which is
    why a reflow can never misrepresent a diff or a code suggestion.

    Line structure is the only thing that changes; wording and ordering do not.
    """
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    buffer: list[str] = []
    in_fence = False

    def flush() -> None:
        if buffer:
            # The first line's indentation is structure: it nests a list item or a
            # continuation paragraph under its parent, so it survives the join.
            first = buffer[0]
            indent = first[: len(first) - len(first.lstrip())]
            out.append(indent + " ".join(part.strip() for part in buffer).strip())
            buffer.clear()

    for line in lines:
        if _FENCE_LINE.match(line):
            flush()
            out.append(line)
            in_fence = not in_fence
            continue
        if in_fence:
            out.append(line)
            continue
        if not line.strip():
            flush()
            out.append("")
            continue
        if any(pattern.match(line) for pattern in _STRUCTURAL_LINE_PATTERNS):
            flush()
            out.append(line.rstrip())
            continue
        if _LIST_ITEM_LINE.match(line):
            # A new item ends whatever was open; its own wrapped lines join into it.
            flush()
            buffer.append(line.rstrip())
            continue
        buffer.append(line.rstrip())
    flush()

    collapsed: list[str] = []
    for entry in out:
        if entry == "" and collapsed and collapsed[-1] == "":
            continue
        collapsed.append(entry)
    return "\n".join(collapsed).strip("\n") + "\n"


def segment_body(text: str) -> list[str]:
    """Split a body into the units a reconciliation must account for.

    Segmentation is deterministic so the same original always yields the same units: a heading or list item is one
    segment, and other runs of non-blank lines form a paragraph segment. Verification compares dispositions against
    these units, so a segmenter that drifted would silently change what "complete" means.
    """
    segments: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            segments.append("\n".join(paragraph).strip())
            paragraph.clear()

    for raw_line in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if (
            stripped.startswith("#")
            or re.match(r"^[-*+][ \t]+\S", stripped)
            or re.match(r"^[0-9]+[.)][ \t]+\S", stripped)
        ):
            flush()
            segments.append(stripped)
            continue
        paragraph.append(line)
    flush()
    return [segment for segment in segments if segment]


def description_edit_sources(
    previous: str,
    current: str,
    normalize: Callable[[str], str] | None = None,
) -> list[tuple[str, str]]:
    """Return only externally changed hunks, never the unchanged generated body."""
    transform = normalize or (lambda text: text)
    old = segment_body(transform(previous))
    new = segment_body(transform(current))
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    edits: list[tuple[str, str]] = []
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            text = "External editor removed these previously generated segments:\n" + "\n\n".join(
                old[old_start:old_end]
            )
        else:
            text = "\n\n".join(new[new_start:new_end])
        edits.append((f"description edit {len(edits) + 1} ({tag})", text))
    return edits


def extract_anchors(text: str) -> list[str]:
    """Return the concrete facts a reconciliation must retain or declare dropped.

    Narrative may be reworded freely; an inline code span, URL, or issue reference is a fact whose silent loss is the
    failure a reviewer's reading was there to catch.
    """
    anchors: list[str] = []
    for pattern in ANCHOR_PATTERNS:
        for match in pattern.finditer(text or ""):
            anchor = match.group(0).strip()
            if anchor and anchor not in anchors:
                anchors.append(anchor)
    return anchors


def segment_sources(sources: list[tuple[str, str]]) -> list[dict[str, str]]:
    """Segment several labelled bodies into one indexed list carrying provenance.

    A pull-request description is a single source; an issue reconciliation draws on the description *and* its thread,
    and a disposition has to be able to say which comment a segment came from. Flattening to one index keeps the ledger
    simple while the label keeps the citation honest.
    """
    segments: list[dict[str, str]] = []
    for label, text in sources:
        segments.extend({"source": label, "text": unit} for unit in segment_body(text))
    return segments


def verify_composition(
    sources: list[tuple[str, str]],
    composed: str,
    ledger: dict[str, Any],
    load_bearing: list[str] | None = None,
    vocabulary: SurfaceVocabulary | None = None,
) -> list[dict[str, Any]]:
    """Check that a reconciliation declared everything it did with the original.

    Establishes completeness (every segment carries a disposition) and retention (every anchor is present, explicitly
    dropped with a reason, or declared preserved in the provenance record), plus load-bearing carry and absorption. It
    cannot establish that a disposition is *true* — no mechanism can — but it makes silent loss impossible, which is the
    property a human reading supplied.

    ``vocabulary`` is what the target surface declares, passed in rather than assumed, so one verifier serves every
    surface instead of hardcoding one surface's shape.

    Returns findings; an empty list means the composition may be written.
    """
    declared = vocabulary or SurfaceVocabulary()
    segments = segment_sources(sources)
    findings, dispositioned = _check_dispositions(ledger.get("dispositions") or [], segments, declared.sections)
    findings.extend(_check_completeness(segments, dispositioned))
    findings.extend(_check_anchor_retention(sources, composed, ledger))
    findings.extend(_check_absorption(segments, composed, load_bearing, declared.region))
    findings.extend(
        {"kind": "load-bearing-dropped", "detail": fragment}
        for fragment in load_bearing or []
        if fragment not in composed
    )
    return findings


def _rstripped_lines(text: str) -> str:
    """Return ``text`` with per-line trailing whitespace removed.

    Containment tests run against this form because reporter and author input routinely arrives as a blockquote whose
    lines carry trailing spaces. Segmentation already rstrips, so an exact-substring test would miss a blockquote copied
    verbatim — the very shape the absorption check exists to catch.
    """
    return "\n".join(line.rstrip() for line in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"))


def delimited_region(composed: str, region: tuple[str, str] | None) -> str | None:
    """Return the text between a surface's region markers, or ``None`` when absent."""
    if not region:
        return None
    open_marker, close_marker = region
    lines = (composed or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    start = next((index for index, line in enumerate(lines) if line.strip() == open_marker), None)
    end = next((index for index, line in enumerate(lines) if line.strip() == close_marker), None)
    if start is None or end is None or end <= start:
        return None
    return "\n".join(lines[start + 1 : end])


def _check_absorption(
    segments: list[dict[str, str]],
    composed: str,
    load_bearing: list[str] | None,
    region: tuple[str, str] | None,
) -> list[dict[str, Any]]:
    """Return a non-load-bearing segment sitting verbatim in the carried region is an appended draft.

    Every governed surface requires narrative to be absorbed into its structured sections and machine-read fragments to
    be carried unchanged. Only the second belongs in the region, so a segment found there that is not load-bearing is
    the append this contract forbids. The check examines the region rather than the whole body, because quoting a phrase
    of the original inside an analytical section is legitimate reconciliation.

    A segment labelled ``CARRIED_REGION_SOURCE`` is exempt. On a later round a surface's own region content is
    reconciliation input, and carrying it forward verbatim is required rather than forbidden — the two cases are
    indistinguishable by shape, which is why the emitted source list names them differently.
    """
    carried = delimited_region(composed, region)
    if carried is None:
        return []
    haystack = _rstripped_lines(carried)
    exempt = {_rstripped_lines(fragment).strip() for fragment in load_bearing or []}
    findings: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        if segment["source"] == CARRIED_REGION_SOURCE:
            continue
        needle = _rstripped_lines(segment["text"]).strip()
        if not needle or needle in exempt:
            continue
        if needle in haystack:
            findings.append(
                {
                    "kind": "segment-copied-into-region",
                    "segment": index,
                    "source": segment["source"],
                    "detail": needle[:120],
                }
            )
    return findings


def _check_dispositions(
    dispositions: list[dict[str, Any]],
    segments: list[dict[str, str]],
    sections: Collection[str] | None = None,
) -> tuple[list[dict[str, Any]], set[int]]:
    """Validate each declared disposition and report which segments it covers."""
    findings: list[dict[str, Any]] = []
    dispositioned: set[int] = set()
    for entry in dispositions:
        index = entry.get("segment")
        action = entry.get("action")
        if not isinstance(index, int) or index < 0 or index >= len(segments):
            findings.append({"kind": "segment-out-of-range", "detail": repr(index)})
            continue
        if action not in DISPOSITION_ACTIONS:
            findings.append({"kind": "unknown-action", "segment": index, "detail": repr(action)})
            continue
        if action in REASON_REQUIRED_ACTIONS and not str(entry.get("reason") or "").strip():
            findings.append({"kind": "missing-reason", "segment": index, "detail": action})
            continue
        if action == "extracted" and not str(entry.get("issue") or "").strip():
            findings.append({"kind": "missing-extraction-target", "segment": index, "detail": action})
            continue
        target = entry.get("target")
        if sections is not None and target is not None and str(target) not in sections:
            findings.append({"kind": "target-out-of-shape", "segment": index, "detail": repr(target)})
            continue
        cited = entry.get("source")
        if cited is not None and cited != segments[index]["source"]:
            findings.append(
                {
                    "kind": "source-mismatch",
                    "segment": index,
                    "source": segments[index]["source"],
                    "detail": f"ledger cites {cited!r}",
                }
            )
            continue
        dispositioned.add(index)
    return findings, dispositioned


def _check_completeness(segments: list[dict[str, str]], dispositioned: set[int]) -> list[dict[str, Any]]:
    """Return a segment nobody declared is the silent omission the reading caught."""
    return [
        {
            "kind": "segment-undispositioned",
            "segment": index,
            "source": segment["source"],
            "detail": segment["text"][:120],
        }
        for index, segment in enumerate(segments)
        if index not in dispositioned
    ]


def _check_anchor_retention(
    sources: list[tuple[str, str]],
    composed: str,
    ledger: dict[str, Any],
) -> list[dict[str, Any]]:
    """Every concrete fact is present in the result, explicitly dropped, or preserved.

    ``preserved_anchors`` exists because retention would otherwise penalise the behaviour absorption demands:
    reproducing the original in the body satisfies every anchor at once, while absorbing prose properly leaves an author
    declaring anchors *dropped* that remain verbatim in the provenance record. A gate whose compliant path costs more
    than its non-compliant path gets satisfied the wrong way. ``dropped_anchors`` keeps its meaning for an anchor absent
    from the body and the preserved original alike, so a reader of the rendered ledger can still tell the two apart.
    """
    declared = {
        str(item.get("anchor") or "")
        for key in ("dropped_anchors", "preserved_anchors")
        for item in ledger.get(key) or []
        if str(item.get("reason") or "").strip()
    }
    return [
        {"kind": "anchor-unretained", "source": label, "detail": anchor}
        for label, text in sources
        for anchor in extract_anchors(text)
        if anchor not in composed and anchor not in declared
    ]


def render_disposition_ledger(ledger: dict[str, Any], marker: str, *, repository: str = "") -> str:
    """Render the disposition ledger both provenance records carry."""
    lines = [marker, "", "## Reconciliation ledger (current round)", ""]
    if repository:
        lines.extend([f"Source repository: `{repository}`.", ""])
    dispositions = ledger.get("dispositions") or []
    if not dispositions:
        lines.append("No dispositions recorded for this round.")
    for entry in dispositions:
        target = f" → {entry['target']}" if entry.get("target") else ""
        issue = f" → {entry['issue']}" if entry.get("issue") else ""
        reason = f" — {entry['reason']}" if entry.get("reason") else ""
        lines.append(f"- segment {entry.get('segment')}: **{entry.get('action')}**{target}{issue}{reason}")
    dropped = ledger.get("dropped_anchors") or []
    if dropped:
        lines.extend(["", "Anchors dropped by declaration:", ""])
        lines.extend(f"- {item.get('anchor')} — {item.get('reason')}" for item in dropped)
    preserved = ledger.get("preserved_anchors") or []
    if preserved:
        lines.extend(["", "Anchors preserved in this record:", ""])
        lines.extend(f"- {item.get('anchor')} — {item.get('reason')}" for item in preserved)
    lines.append("")
    return "\n".join(lines)


def _source_items(payload: Any) -> list[tuple[str, str]]:
    """Parse the shared labelled-source shape from one already acquired JSON snapshot."""
    items = payload.get("sources") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        abort("sources must be a JSON list or an object with a 'sources' list.")
    return [(str(item.get("source")), str(item.get("text") or "")) for item in items]


def load_source_list(path: str) -> list[tuple[str, str]]:
    """Read a labelled source list from a JSON array or ``{"sources": [...]}`` object."""
    return _source_items(load_json(path, "sources"))


def reference_field_from_sources(field: ReferenceField, path: str) -> ReferenceField:
    """Read one atomic source snapshot with an explicit repository; never infer it from the write target."""
    payload = load_json(path, "sources")
    repository = str(payload.get("repository") or "") if isinstance(payload, dict) else ""
    return field._replace(repository=repository, sources=tuple(_source_items(payload)))


def source_list_payload(
    sources: list[tuple[str, str]],
    *,
    degraded: bool = False,
    repository: str = "",
) -> dict[str, Any]:
    """Shape the labelled source list both verification and the write consume."""
    payload: dict[str, Any] = {
        "degraded": degraded,
        "sources": [{"source": label, "text": text} for label, text in sources],
    }
    if repository:
        payload["repository"] = repository
    if degraded:
        payload["degraded_reason"] = (
            "content-edit history yielded no body matching the stamped digest; "
            "the preserved original is the comparison base"
        )
    return payload


def disclosure_for_mode(contract: PostingContract, mode: str) -> str:
    """Return the AI-assistance disclosure required for a posting mode.

    A mode the contract does not declare is refused rather than defaulted, so a surface that supports only supervised
    posting says so through its contract.
    """
    if mode == "interactive":
        return contract.interactive_disclosure
    if mode == "automated":
        if contract.automated_disclosure is None:
            abort("this surface declares no automated mode; automated posting is unsupported for it.")
        return contract.automated_disclosure
    abort(f"unsupported mode '{mode}'; expected interactive or automated.")


def inject_contract(body: str, mode: str, contract: PostingContract, label: str = "review") -> str:
    """Append the mode disclosure and machine marker unless already present."""
    disclosure = disclosure_for_mode(contract, mode)
    opposite_disclosure = contract.automated_disclosure if mode == "interactive" else contract.interactive_disclosure
    if opposite_disclosure is not None and opposite_disclosure in body:
        abort(f"{label} body contains the disclosure for the wrong mode ({mode}).")
    if body.count(contract.marker) > 1:
        abort(f"{label} body contains the AIS CR {label} marker more than once.")

    rendered = body.rstrip()
    if disclosure not in rendered:
        rendered = f"{rendered}\n\n{disclosure}"
    if contract.marker not in rendered:
        rendered = f"{rendered}\n\n{contract.marker}"
    return rendered


def validate_contract(body: str, mode: str, contract: PostingContract, label: str = "review") -> None:
    """Fail closed when a body lacks its required disclosure or marker."""
    disclosure = disclosure_for_mode(contract, mode)
    if disclosure not in body:
        abort(f"{label} body is missing the required {mode} AI-assistance disclosure.")
    if body.count(contract.marker) != 1:
        abort(f"{label} body must contain exactly one AIS CR {label} marker.")
