"""
Check internal Markdown cross-references (file and optional section anchors).

Scans Markdown files under the repo for same-repo links (e.g. [text](path.md) or
[text](path.md#section)) and verifies that the target file exists and, if an anchor
is present, that the heading exists. For agent-facing docs, it also enforces the
README locale-routing policy: when a target directory has both ``README.md`` and
``README_en.md``, agent-facing sources must link to ``README_en.md``. Broken links
in report files (e.g. under .agents/reports/) are part of the same hygiene story and
feed into the audit (C5 cross-references and C8 reports cleanup).

Link resolution (same-repo targets only):

- Paths starting with ``/`` are resolved from the **repository root** (leading slash
  stripped). Use for top-level files from nested docs, e.g. ``[/AGENTS.md](/AGENTS.md)``.
- Paths starting with ``.agents/``, ``.cursor/``, ``.claude/``, ``.codex/``, ``.gemini/``,
  or ``openspec/`` are resolved from the **repository root** (AIS CR convention for
  cross-tree links, including OpenSpec specs and change artifacts).
- Paths starting with ``./`` or ``../`` are resolved from the **current file's directory**.
- Any other relative path (e.g. ``schemas/README.md``, ``other.plan.md``) is resolved
  from the **current file's directory**, matching usual Markdown behavior for same-folder
  and subdirectory targets.

Usage:
  python .agents/scripts/link_check.py [path ...] [--output json|text]
  If no path given, discovers Markdown under repo root (see doc_discovery patterns).
  Exit 0 = all refs OK, 1 = one or more broken.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


ROOT = _default_root()

# Same as doc_discovery: where to look for markdown when no paths given.
# OpenSpec specs and active change artifacts are included so broken file or heading
# references between OpenSpec docs, `.agents/`, and assistant entry surfaces are
# reported as documentation hygiene findings. The archived change subtree
# (``openspec/changes/archive/``) is excluded from default discovery via
# DEFAULT_EXCLUDE_PREFIXES below: archived changes are immutable historical records
# whose links may have legitimately become stale, so they are not enforced against
# current paths by default. Pass the archive paths explicitly to ``link_check.py`` to
# check them ad hoc; doc_discovery still classifies them as ``openspec_archived_changes``.
DEFAULT_GLOBS = [
    "README*.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CODEX.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    ".cursor/rules/*.mdc",
    ".cursor/**/*.md",
    ".claude/**/*.md",
    ".codex/**/*.md",
    ".gemini/**/*.md",
    ".agents/**/*.md",
    "openspec/specs/**/*.md",
    "openspec/changes/**/*.md",
]
DEFAULT_EXCLUDE_PREFIXES: tuple[str, ...] = ("openspec/changes/archive/",)
AGENT_FACING_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "CODEX.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
}


def get_headings(path: Path) -> set[str]:
    """Return normalized anchor IDs for ## headings (GitHub-style)."""
    anchors: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return anchors
    # Simple: ## Heading -> lowercase, spaces to -, strip punctuation for anchor.
    for m in re.finditer(r"^#{1,6}\s+(.+)$", text, re.MULTILINE):
        raw = m.group(1).strip()
        anchor = raw.lower()
        anchor = re.sub(r"[^\w\s-]", "", anchor)
        anchor = re.sub(r"[-\s]+", "-", anchor).strip("-")
        if anchor:
            anchors.add(anchor)
    return anchors


def find_links(path: Path, root: Path) -> list[tuple[str, str | None]]:
    """Return list of (resolved_target_path, anchor) for same-repo links."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    # [label](url) and [label](url "title")
    pattern = re.compile(r"\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\s*\)")
    try:
        rel_path = path.relative_to(root)
        base_dir = rel_path.parent
    except ValueError:
        base_dir = Path(".")
    out: list[tuple[str, str | None]] = []
    for _label, url in pattern.findall(text):
        url = url.strip()
        if url.startswith("#") or url.startswith("mailto:") or url.startswith("http"):
            continue
        if "#" in url:
            path_part, anchor = url.split("#", 1)
            anchor = anchor.strip().lower()
            anchor = re.sub(r"[^\w\s-]", "", anchor)
            anchor = re.sub(r"[-\s]+", "-", anchor).strip("-") or None
        else:
            path_part, anchor = url, None
        path_part = path_part.strip()
        if not path_part or path_part.startswith("http"):
            continue
        root_prefixed = (
            path_part.startswith(".agents/")
            or path_part.startswith(".cursor/")
            or path_part.startswith(".claude/")
            or path_part.startswith(".codex/")
            or path_part.startswith(".gemini/")
            or path_part.startswith("openspec/")
        )
        if path_part.startswith("/"):
            resolved = (root / path_part.lstrip("/")).resolve()
        elif root_prefixed:
            resolved = (root / path_part).resolve()
        else:
            resolved = (root / base_dir / path_part).resolve()
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            continue
        rel_str = str(rel).replace("\\", "/")
        out.append((rel_str, anchor))
    return out


def _is_default_excluded(root: Path, path: Path) -> bool:
    """Return True when *path* falls under :data:`DEFAULT_EXCLUDE_PREFIXES`.

    Archived OpenSpec change artifacts under ``openspec/changes/archive/`` are
    excluded from default discovery: they are immutable historical records whose
    references may have legitimately become stale as the repo evolved. Callers
    that explicitly pass an archive path will still get it checked.
    """
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return False
    return any(rel.startswith(prefix) for prefix in DEFAULT_EXCLUDE_PREFIXES)


def collect_md_files(root: Path, paths: list[Path] | None) -> list[Path]:
    """Collect Markdown and .mdc files to check, honoring default globs and excludes."""
    if paths:
        result = []
        for p in paths:
            if not p.is_file() or p.suffix.lower() not in (".md", ".mdc"):
                continue
            try:
                p.relative_to(root)
            except ValueError:
                continue
            result.append(p)
        return result
    out: list[Path] = []
    for pattern in DEFAULT_GLOBS:
        for p in root.glob(pattern):
            if p.is_file() and not _is_default_excluded(root, p):
                out.append(p)
    return sorted(set(out))


def is_ignored_by_git(root: Path, rel_path: str) -> bool:
    """Return True if rel_path (relative to root) is ignored by .gitignore."""
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "-q", "--", rel_path],
            check=False,
            cwd=root,
            capture_output=True,
            timeout=5,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_agent_facing_source(source_rel: str) -> bool:
    """Return True when the source doc should prefer English README links."""
    path = Path(source_rel)
    name = path.name
    prefix = source_rel.replace("\\", "/")
    readme_index_names = {"README.md", "README_en.md"}
    return (
        source_rel in AGENT_FACING_FILES
        or prefix.startswith((".claude/", ".codex/", ".cursor/", ".gemini/", ".github/"))
        or (prefix.startswith(".agents/prompts/") and name not in readme_index_names)
        or (prefix.startswith(".agents/plans/") and name.endswith(".plan.md"))
        or prefix.startswith(".agents/canonical_configs/governance_rules/")
        or (prefix.startswith(".agents/canonical_configs/references/") and name not in readme_index_names)
        or (prefix.startswith(".agents/canonical_configs/workflow_skills/") and name not in readme_index_names)
    )


def _is_allowed_counterpart_cross_link(source_str: str, target_rel: str) -> bool:
    """Allow README_en.md -> sibling README.md as the required pair backlink."""
    source_path = Path(source_str)
    target_path = Path(target_rel)
    return (
        source_path.name == "README_en.md"
        and target_path.name == "README.md"
        and source_path.parent == target_path.parent
    )


def check_links(root: Path, md_files: list[Path]) -> list[dict]:
    """Return a list of broken internal links for the given Markdown files."""
    broken: list[dict] = []
    for path in md_files:
        try:
            rel_source = path.relative_to(root)
        except ValueError:
            continue
        source_str = str(rel_source).replace("\\", "/")
        for target_rel, anchor in find_links(path, root):
            target_path = root / target_rel
            if not target_path.exists():
                if is_ignored_by_git(root, target_rel):
                    continue  # local-only file per .gitignore, skip
                broken.append(
                    {
                        "source": source_str,
                        "target": target_rel,
                        "anchor": anchor,
                        "error": "file not found",
                    }
                )
                continue
            if anchor is not None:
                headings = get_headings(target_path)
                if anchor not in headings:
                    broken.append(
                        {
                            "source": source_str,
                            "target": target_rel,
                            "anchor": anchor,
                            "error": "section not found",
                        }
                    )
                    continue
            if is_agent_facing_source(source_str):
                target_name = Path(target_rel).name
                if target_name == "README.md":
                    target_en = target_path.with_name("README_en.md")
                    if target_en.exists() and not _is_allowed_counterpart_cross_link(source_str, target_rel):
                        broken.append(
                            {
                                "source": source_str,
                                "target": target_rel,
                                "anchor": anchor,
                                "error": "prefer README_en.md for agent-facing docs",
                            }
                        )
    return broken


def main() -> None:
    """CLI entry point for checking internal Markdown links."""
    parser = argparse.ArgumentParser(
        description="Check internal Markdown links (file and section anchors).",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Markdown files to check; default: discover from repo.",
    )
    parser.add_argument(
        "--output",
        choices=("json", "text"),
        default="text",
        help="Output format for broken refs (default: text).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repo root (default: derived from script location). Used for testing.",
    )
    args = parser.parse_args()

    root = ROOT if args.root is None else args.root.resolve()
    paths_resolved = [p.resolve() for p in args.paths] if args.paths else None
    md_files = collect_md_files(root, paths_resolved)
    broken = check_links(root, md_files)

    if not broken:
        if args.output == "json":
            print(json.dumps({"broken": [], "checked": len(md_files)}))
        else:
            print(f"Checked {len(md_files)} file(s); all links OK.")
        raise SystemExit(0)

    if args.output == "json":
        print(json.dumps({"broken": broken, "checked": len(md_files)}, indent=2))
    else:
        for b in broken:
            anchor_part = f"#{b['anchor']}" if b.get("anchor") else ""
            print(f"[{b['source']}] -> {b['target']}{anchor_part}: {b['error']}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
