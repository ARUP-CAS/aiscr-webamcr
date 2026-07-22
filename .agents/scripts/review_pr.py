#!/usr/bin/env python3
"""review_pr.py — Gather PR context and post formal GitHub PR reviews.

GH_TOKEN requirement
--------------------
This script interacts with the GitHub API on behalf of a human reviewer.
To prevent reviews from appearing under a personal account, GH_TOKEN **must**
be set to a GitHub Actions installation token or a GitHub App installation
token before running the ``post`` subcommand.  The ``gather`` subcommand is
read-only and does not require GH_TOKEN, though gh CLI must be authenticated.

Subcommands
-----------
gather <PR_NUMBER>
    Fetch PR context and print a JSON object with the fields needed to
    structure review findings (prior review, author response, existing
    inline threads).

post <PR_NUMBER> --review-payload <file> [--replies <file>]
    Post a formal GH PR review (body + new inline comments in one call)
    and, optionally, replies to existing inline comment threads.  Prints
    the posted review URL and reply URLs.

Both subcommands accept ``--repo OWNER/REPO``; when omitted the value is
auto-detected via ``gh repo view``.

Usage examples
--------------
  python .agents/scripts/review_pr.py gather 42
  python .agents/scripts/review_pr.py post 42 \\
      --review-payload /tmp/review_payload.json \\
      --replies /tmp/review_replies.json
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from log_utils import log_error  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], capture: bool = True) -> str:
    """Run a command and return stdout.  Raises SystemExit on failure."""
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = result.stderr.strip() if result.stderr else "(no stderr)"
        log_error(f"command failed: {' '.join(cmd)}\n{msg}")
        sys.exit(1)
    return result.stdout.strip() if capture else ""


def _gh(*args: str) -> str:
    return _run(["gh", *args])


def _resolve_repo(repo_arg: str | None) -> str:
    if repo_arg:
        return repo_arg
    return _gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner")


def _require_gh_token(subcommand: str) -> None:
    """Exit with a clear error if GH_TOKEN is not set.

    All write operations (``post``) must use the GitHub Actions bot identity
    so reviews do not appear under a personal account.
    """
    if not os.environ.get("GH_TOKEN"):
        print(
            f"ERROR: GH_TOKEN is not set.\n"
            f"The '{subcommand}' subcommand posts to the GitHub API on behalf of a\n"
            f"human reviewer and must use the GitHub Actions bot identity.\n"
            f"Export GH_TOKEN with a GitHub Actions installation token or a GitHub\n"
            f"App installation token before running this command.\n"
            f"\n"
            f"  export GH_TOKEN=<github-actions-or-app-installation-token>",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers for gather / post
# ---------------------------------------------------------------------------


def _fetch_review_details(owner_repo: str, pr_number: int, review_id: int):
    """Fetch body and comments for a specific review."""
    body = _gh(
        "api",
        f"repos/{owner_repo}/pulls/{pr_number}/reviews/{review_id}",
        "--jq",
        ".body",
    )
    comments_raw = _gh(
        "api",
        f"repos/{owner_repo}/pulls/{pr_number}/reviews/{review_id}/comments",
        "--jq",
        "[.[].body]",
    )
    try:
        comments = json.loads(comments_raw)
    except json.JSONDecodeError:
        comments = []
    return body, comments


def _post_replies(owner_repo: str, pr_number: int, replies_path: str) -> None:
    """Post replies to existing PR inline comment threads."""
    try:
        with open(replies_path, encoding="utf-8") as f:
            thread_replies = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        log_error(f"cannot read replies file: {exc}")
        sys.exit(1)

    if not isinstance(thread_replies, list):
        log_error("replies file must contain a JSON array.")
        sys.exit(1)

    for reply in thread_replies:
        comment_id = reply.get("comment_id")
        body = reply.get("body", "")
        if not comment_id:
            print(
                f"WARNING: skipping reply with no comment_id: {reply}",
                file=sys.stderr,
            )
            continue

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump({"body": body}, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            reply_url = _gh(
                "api",
                f"repos/{owner_repo}/pulls/{pr_number}/comments/{comment_id}/replies",
                "--method",
                "POST",
                "--input",
                tmp_path,
                "--jq",
                ".html_url",
            )
            print(f"Reply posted: {reply_url}")
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# gather
# ---------------------------------------------------------------------------


def cmd_gather(pr_number: int, repo: str | None) -> None:
    """Fetch PR context and print JSON for use in the review workflow."""
    owner_repo = _resolve_repo(repo)

    head_sha = _gh(
        "pr",
        "view",
        str(pr_number),
        "--json",
        "headRefOid",
        "-q",
        ".headRefOid",
    )
    pr_author = _gh(
        "pr",
        "view",
        str(pr_number),
        "--json",
        "author",
        "-q",
        ".author.login",
    )

    # Most recent submitted review (not PENDING)
    last_review_raw = _gh(
        "api",
        f"repos/{owner_repo}/pulls/{pr_number}/reviews",
        "--jq",
        'map(select(.state != "PENDING")) | sort_by(.submitted_at) | reverse | .[0]',
    )

    last_review_id = None
    last_review_body = None
    last_review_comments = None

    if last_review_raw and last_review_raw != "null":
        try:
            review_obj = json.loads(last_review_raw)
            last_review_id = review_obj.get("id")
        except json.JSONDecodeError:
            pass

    if last_review_id:
        last_review_body, last_review_comments = _fetch_review_details(owner_repo, pr_number, last_review_id)

    # PR author's most recent response comment (posted after the review)
    author_response_raw = _gh(
        "api",
        f"repos/{owner_repo}/issues/{pr_number}/comments",
        "--jq",
        f'[.[] | select(.user.login == "{pr_author}")] | sort_by(.created_at) | reverse | .[0].body',
    )
    author_response = author_response_raw if author_response_raw and author_response_raw != "null" else None

    # Existing root-level inline comment threads
    existing_threads_raw = _gh(
        "api",
        f"repos/{owner_repo}/pulls/{pr_number}/comments",
        "--jq",
        "[.[] | select(.in_reply_to_id == null)] | map({id: .id, path: .path, line: .line, body: .body})",
    )
    try:
        existing_threads = json.loads(existing_threads_raw)
    except json.JSONDecodeError:
        existing_threads = []

    output = {
        "owner_repo": owner_repo,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "pr_author": pr_author,
        "last_review_id": last_review_id,
        "last_review_body": last_review_body,
        "last_review_comments": last_review_comments,
        "author_response": author_response,
        "existing_threads": existing_threads,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# post
# ---------------------------------------------------------------------------


def cmd_post(
    pr_number: int,
    review_payload_path: str,
    replies_path: str | None,
    repo: str | None,
) -> None:
    """Post the main review and, optionally, replies to existing threads.

    GH_TOKEN must be set to a GitHub Actions (or App installation) token so
    the review appears from the bot identity, not a personal account.
    """
    _require_gh_token("post")

    owner_repo = _resolve_repo(repo)

    # Load and validate the review payload
    try:
        with open(review_payload_path, encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        log_error(f"cannot read review payload: {exc}")
        sys.exit(1)

    required_keys = {"body", "event", "commit_id"}
    missing = required_keys - payload.keys()
    if missing:
        print(
            f"ERROR: review payload is missing required keys: {missing}\n"
            f"Required: body, event, commit_id.  Optional: comments (list).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Post main review (body + new inline comments in one call)
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

    # Post replies to existing threads (one call per reply; threads stay open)
    if replies_path:
        _post_replies(owner_repo, pr_number, replies_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="review_pr.py",
        description=(
            "Gather PR context and post formal GitHub PR reviews.\n\n"
            "GH_TOKEN must be set to a GitHub Actions or GitHub App installation\n"
            "token for the 'post' subcommand.  This ensures reviews appear from\n"
            "the bot identity and not a personal account."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # -- gather ---------------------------------------------------------------
    p_gather = sub.add_parser(
        "gather",
        help="Fetch PR context and print JSON (read-only).",
        description=(
            "Fetch PR state, prior review, author response, and existing inline\n"
            "threads.  Prints a JSON object consumed by the review workflow.\n"
            "Read-only; GH_TOKEN is not required (but gh must be authenticated)."
        ),
    )
    p_gather.add_argument("pr_number", type=int, metavar="PR_NUMBER")
    p_gather.add_argument(
        "--repo",
        metavar="OWNER/REPO",
        help="Repository (auto-detected from gh repo view when omitted).",
    )

    # -- post -----------------------------------------------------------------
    p_post = sub.add_parser(
        "post",
        help="Post a formal GH PR review (requires GH_TOKEN).",
        description=(
            "Post the main review (body + new inline comments) in one API call\n"
            "and, optionally, replies to existing comment threads.\n\n"
            "GH_TOKEN must be set to a GitHub Actions installation token or a\n"
            "GitHub App installation token.  Reviews posted without this token\n"
            "will appear under a personal account, which is not allowed."
        ),
    )
    p_post.add_argument("pr_number", type=int, metavar="PR_NUMBER")
    p_post.add_argument(
        "--review-payload",
        required=True,
        metavar="FILE",
        help=(
            "Path to a JSON file with keys: body (str), event (str), "
            "commit_id (str), and optionally comments (list of inline comment dicts)."
        ),
    )
    p_post.add_argument(
        "--replies",
        metavar="FILE",
        help=("Path to a JSON array of {comment_id, body} dicts for replies to existing inline threads.  Optional."),
    )
    p_post.add_argument(
        "--repo",
        metavar="OWNER/REPO",
        help="Repository (auto-detected from gh repo view when omitted).",
    )

    return parser


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate subcommand."""
    parser = build_parser()
    args = parser.parse_args()

    if args.subcommand == "gather":
        cmd_gather(args.pr_number, args.repo)
    elif args.subcommand == "post":
        cmd_post(args.pr_number, args.review_payload, args.replies, args.repo)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
