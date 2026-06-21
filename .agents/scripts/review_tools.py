#!/usr/bin/env python3
"""Validate artifacts produced by the AIS CR codebase-review workflow.

The script uses only the Python standard library and works with repositories
that provide an ``.agents/`` tree and ``review_config.yaml``.

Usage:

    python review_tools.py hash               # check tracked file hashes
    python review_tools.py cross-validate     # cross-validate artifacts
    python review_tools.py coverage-gaps      # identify analysis coverage gaps
    python review_tools.py id-inventory       # inventory IDs across artifacts
    python review_tools.py lint-artifacts     # validate artifact structure
    python review_tools.py prompt-evolution   # find unapplied prompt proposals
    python review_tools.py repo-structure     # report repository statistics
    python review_tools.py status             # show review workflow status
    python review_tools.py all                # run every check
"""

# The canonical engine is intentionally a single-file, standard-library bundle
# so enrolled repositories can execute it without importing hub modules.
# pylint: disable=too-many-lines,too-many-return-statements,too-many-branches
# pylint: disable=too-many-statements,too-many-locals,too-many-nested-blocks
# pylint: disable=too-many-instance-attributes

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def _yaml_scalar(s: str):
    """Convert a simple YAML scalar to its Python value."""
    s = s.strip()
    if not s or s in ("~", "null", "Null"):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if len(s) >= 2 and s[0] in ('"', "'") and s[-1] == s[0]:
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        return [_yaml_scalar(x) for x in s[1:-1].split(",") if x.strip()]
    try:
        return int(s)
    except ValueError:
        return s


def _yaml_strip_comment(s: str) -> str:
    """Remove an unquoted trailing comment from a YAML line."""
    in_quote = None
    for i, c in enumerate(s):
        if c in ('"', "'"):
            if in_quote == c:
                in_quote = None
            elif in_quote is None:
                in_quote = c
        elif c == "#" and in_quote is None and (i == 0 or s[i - 1] == " "):
            return s[:i].rstrip()
    return s


def _yaml_indent(line: str) -> int:
    """Return the leading-space indentation of a YAML line."""
    return len(line) - len(line.lstrip())


def _load_yaml(path: Path) -> dict:
    """Load the supported YAML subset without third-party dependencies."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    result, _ = _yaml_map(lines, 0, -1)
    return result


def _yaml_map(lines: list[str], pos: int, parent_indent: int) -> tuple[dict, int]:
    """Parse a YAML mapping block and return its data and next position."""
    result: dict = {}
    block_indent: int | None = None
    while pos < len(lines):
        raw = lines[pos]
        stripped = raw.lstrip()
        if not stripped or stripped.startswith("#"):
            pos += 1
            continue
        indent = _yaml_indent(raw)
        if block_indent is None:
            if indent <= parent_indent:
                break
            block_indent = indent
        if indent < block_indent:
            break
        if indent > block_indent or stripped.startswith("- "):
            pos += 1
            continue
        if ":" not in stripped:
            pos += 1
            continue
        ci = stripped.index(":")
        key = stripped[:ci].strip()
        rest = _yaml_strip_comment(stripped[ci + 1 :]).strip()
        if rest in ("", ">", "|"):
            npos = pos + 1
            while npos < len(lines):
                ns = lines[npos].lstrip()
                if ns and not ns.startswith("#"):
                    break
                npos += 1
            if npos >= len(lines) or _yaml_indent(lines[npos]) <= indent:
                result[key] = "" if rest != ">" else ""
                pos = npos
            elif rest == ">":
                mlines: list[str] = []
                while npos < len(lines):
                    ns = lines[npos].lstrip()
                    if not ns:
                        npos += 1
                        continue
                    if _yaml_indent(lines[npos]) <= indent:
                        break
                    mlines.append(ns)
                    npos += 1
                result[key] = " ".join(mlines)
                pos = npos
            else:
                ns = lines[npos].lstrip()
                if ns.startswith("- "):
                    val, pos = _yaml_seq(lines, npos, indent)
                else:
                    val, pos = _yaml_map(lines, npos, indent)
                result[key] = val
        elif rest.startswith("[") and rest.endswith("]"):
            result[key] = [_yaml_scalar(x) for x in rest[1:-1].split(",") if x.strip()]
            pos += 1
        else:
            result[key] = _yaml_scalar(rest)
            pos += 1
    return result, pos


def _yaml_seq(lines: list[str], pos: int, _parent_indent: int) -> tuple[list, int]:
    """Parse a YAML sequence block and return its data and next position."""
    result: list = []
    block_indent: int | None = None
    while pos < len(lines):
        raw = lines[pos]
        stripped = raw.lstrip()
        if not stripped or stripped.startswith("#"):
            pos += 1
            continue
        indent = _yaml_indent(raw)
        if block_indent is None:
            block_indent = indent
        if indent < block_indent:
            break
        if not stripped.startswith("- "):
            if indent > block_indent:
                pos += 1
                continue
            break
        content = _yaml_strip_comment(stripped[2:]).strip()
        if ":" in content and not content.startswith("{"):
            ci = content.index(":")
            k = content[:ci].strip()
            v = _yaml_strip_comment(content[ci + 1 :]).strip()
            item: dict = {}
            if v in ("", ">", "|"):
                npos = pos + 1
                while npos < len(lines):
                    ns = lines[npos].lstrip()
                    if ns and not ns.startswith("#"):
                        break
                    npos += 1
                if npos < len(lines) and _yaml_indent(lines[npos]) > indent + 2:
                    ns = lines[npos].lstrip()
                    if ns.startswith("- "):
                        sv, npos = _yaml_seq(lines, npos, indent + 2)
                    else:
                        sv, npos = _yaml_map(lines, npos, indent + 2)
                    item[k] = sv
                else:
                    item[k] = None
                pos = npos
            else:
                item[k] = _yaml_scalar(v)
                pos += 1
            while pos < len(lines):
                r2 = lines[pos]
                s2 = r2.lstrip()
                if not s2 or s2.startswith("#"):
                    pos += 1
                    continue
                i2 = _yaml_indent(r2)
                if i2 <= indent:
                    break
                if s2.startswith("- "):
                    break
                if ":" in s2:
                    c2 = s2.index(":")
                    k2 = s2[:c2].strip()
                    v2 = _yaml_strip_comment(s2[c2 + 1 :]).strip()
                    if v2 in ("", ">", "|"):
                        npos = pos + 1
                        while npos < len(lines):
                            ns = lines[npos].lstrip()
                            if ns and not ns.startswith("#"):
                                break
                            npos += 1
                        if npos < len(lines) and _yaml_indent(lines[npos]) > i2:
                            ns = lines[npos].lstrip()
                            if ns.startswith("- "):
                                sv, npos = _yaml_seq(lines, npos, i2)
                            else:
                                sv, npos = _yaml_map(lines, npos, i2)
                            item[k2] = sv
                        else:
                            item[k2] = None
                        pos = npos
                    elif v2.startswith("[") and v2.endswith("]"):
                        item[k2] = [_yaml_scalar(x) for x in v2[1:-1].split(",") if x.strip()]
                        pos += 1
                    else:
                        item[k2] = _yaml_scalar(v2)
                        pos += 1
                else:
                    pos += 1
            result.append(item)
        else:
            result.append(_yaml_scalar(content))
            pos += 1
    return result, pos


def _find_repo_root(start: Path) -> Path:
    """Find the nearest repository root, falling back to the start path."""
    current = start.resolve()
    for _ in range(20):
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return start.resolve()


class Config:
    """Review workflow configuration loaded from ``review_config.yaml``."""

    def __init__(self, repo_root: Path | None = None, config_path: Path | None = None):
        script_dir = Path(__file__).resolve().parent
        self.repo_root = repo_root or _find_repo_root(script_dir)
        self.agents_dir = self.repo_root / ".agents"
        self.config_dir = self.agents_dir / "config"
        self.reports_dir = self.agents_dir / "reports"
        self.analysis_dir = self.agents_dir / "analysis"
        self.prompts_dir = self.agents_dir / "prompts"

        self.cache_file = self.config_dir / "review_cache.json"
        self.bugs_file = self.reports_dir / "bugs.md"
        self.backlog_file = self.reports_dir / "refactoring_backlog.md"
        self.final_audit = self.reports_dir / "review_reports" / "final_audit.md"
        self.review_reports_dir = self.reports_dir / "review_reports"
        self.review_codebase = self.prompts_dir / "review_codebase.md"
        self.prompt_evolution_dir = self.prompts_dir / "prompt_evolution"

        self.ignored_dirs = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            "build",
            "dist",
            "media",
            "staticfiles",
            ".pytest_cache",
            ".mypy_cache",
            "coverage",
            ".agents",
        }
        self.vendored_dirs: set[str] = {"vendor", "vendors", "lib", "libs", "dist", "node_modules"}
        self.vendored_file_patterns: set[str] = {"*.min.js", "*.min.css"}
        self.vendored_headers: tuple[str, ...] = ("/*!", "* @license", "* jQuery", "* Bootstrap")
        self.vendored_filenames: set[str] = set()
        self.source_extensions: tuple[str, ...] = (
            ".py",
            ".js",
            ".ts",
            ".html",
            ".css",
            ".scss",
            ".md",
            ".yaml",
            ".yml",
            ".sh",
        )
        self.tasks: list[dict] = []
        self.django_project_root: Path | None = None

        cfg_path = config_path or self.config_dir / "review_config.yaml"
        self._raw = _load_yaml(cfg_path)
        self._apply_config()

    def _apply_config(self):
        """Apply repository configuration to this instance."""
        cfg = self._raw
        if not cfg:
            self._detect_django_root()
            return
        ign = cfg.get("ignored_directories", [])
        if isinstance(ign, list):
            self.ignored_dirs.update(str(d) for d in ign)
        ve = cfg.get("vendored_exclusions", {})
        if isinstance(ve, dict):
            for d in ve.get("directories", []):
                self.vendored_dirs.add(str(d).rstrip("/"))
            for h in ve.get("copyright_headers", []):
                self.vendored_headers = tuple(list(self.vendored_headers) + [str(h)])
            for p in ve.get("file_patterns", []):
                self.vendored_file_patterns.add(str(p))
            for fn in ve.get("filenames", []):
                self.vendored_filenames.add(str(fn))
        tasks = cfg.get("tasks", [])
        if isinstance(tasks, list):
            self.tasks = [t for t in tasks if isinstance(t, dict)]
        source_extensions = cfg.get("source_extensions", [])
        if isinstance(source_extensions, list) and source_extensions:
            self.source_extensions = tuple(
                ext if ext.startswith(".") else f".{ext}" for ext in map(str, source_extensions)
            )
        self._detect_django_root()

    def _detect_django_root(self):
        """Infer the Django project root from configuration or layout."""
        key_apps = self._raw.get("key_django_apps", [])
        if isinstance(key_apps, list) and key_apps:
            first_dir = key_apps[0].get("dir", "") if isinstance(key_apps[0], dict) else ""
            if first_dir:
                parts = Path(first_dir).parts
                if parts:
                    candidate = self.repo_root / parts[0]
                    if (candidate / "manage.py").exists():
                        self.django_project_root = candidate
                        return
        for name in ("webclient", "src", "app", "backend", ""):
            candidate = self.repo_root / name if name else self.repo_root
            if (candidate / "manage.py").exists():
                self.django_project_root = candidate
                return

    def get_task_ids(self) -> list[str]:
        """Return task IDs defined in ``review_config.yaml``."""
        return [t.get("id", "") for t in self.tasks if t.get("id")]

    def get_analysis_files(self) -> dict[str, Path]:
        """Map task IDs to their analysis JSON paths."""
        result: dict[str, Path] = {}
        for t in self.tasks:
            tid = t.get("id", "")
            tf = t.get("target_file", "")
            if tid and tf:
                result[tid] = self.repo_root / tf
        return result


def _read_text(path: Path) -> str:
    """Read a UTF-8 text file, returning an empty string when absent."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    """Load a JSON object, returning an empty mapping for invalid input."""
    text = _read_text(path)
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _is_vendored_js(filename: str, content: str, cfg: Config) -> bool:
    """Heuristically determine whether a JavaScript file is vendored."""
    if filename in cfg.vendored_filenames:
        return True
    for pat in cfg.vendored_file_patterns:
        if pat.startswith("*") and filename.endswith(pat[1:]):
            return True
    stripped = content.lstrip()[:200] if content else ""
    if any(stripped.startswith(h) for h in cfg.vendored_headers):
        return True
    head = content[:3000] if content else ""
    if re.search(r"\bL\.\w+\s*=\s*L\.\w+\.extend\s*\(", head):
        return True
    if re.search(r"\bL\.\w+\s*=\s*\(?\s*function", head):
        return True
    first_line = content.split("\n", 1)[0] if content else ""
    if len(first_line) > 1000:
        return True
    return False


ID_PATTERNS = [
    re.compile(r"\bBUG-\d+\b"),
    re.compile(r"\b[A-Z]{2,}(?:-[A-Z]+)*-\d+\b"),
]


def _extract_all_ids(text: str) -> set[str]:
    """Extract every structured artifact identifier from text."""
    ids: set[str] = set()
    for pat in ID_PATTERNS:
        ids.update(pat.findall(text))
    return ids


def _section_header(name: str) -> str:
    """Create a section separator for the ``all`` command."""
    return f"\n{'=' * 60}\n {name}\n{'=' * 60}"


# -- cmd: hash -----------------------------------------------------------------


def cmd_hash(cfg: Config, _args: argparse.Namespace) -> int:
    """Compare cached file hashes with the working tree."""
    cache = _load_json(cfg.cache_file)
    file_hashes = cache.get("file_hashes", {})
    changed: list[tuple[str, str, str, str]] = []
    missing: list[str] = []
    unchanged = 0

    for rel_path, info in file_hashes.items():
        fp = cfg.repo_root / rel_path
        if not fp.exists():
            missing.append(rel_path)
            continue
        current = hashlib.sha256(fp.read_bytes()).hexdigest()
        stored = info.get("sha256", "")
        if current != stored:
            task = info.get("task_id", "?")
            changed.append((rel_path, stored[:12], current[:12], task))
        else:
            unchanged += 1

    total = len(file_hashes)
    print(f"[hash] Tracked files: {total}")
    print(f"  Unchanged: {unchanged}")
    print(f"  Changed:   {len(changed)}")
    print(f"  Missing:   {len(missing)}")
    if changed:
        print("\n  Changed files:")
        for path, old, new, task in changed:
            print(f"    {path} [{task}]: {old} -> {new}")
    if missing:
        print("\n  Missing files:")
        for p in missing:
            print(f"    {p}")
    return len(changed) + len(missing)


# -- cmd: cross-validate -------------------------------------------------------


def _extract_bug_severities(text: str) -> dict[str, str]:
    """Extract ``BUG-XXX`` to severity mappings from ``bugs.md``."""
    result: dict[str, str] = {}
    for m in re.finditer(r"### (BUG-\d+).*?\n.*?\*\*Závažnost:\*\*\s*(\S+)", text, re.DOTALL):
        result[m.group(1)] = m.group(2)
    return result


def _extract_backlog_items(text: str) -> dict[str, str]:
    """Extract backlog item identifiers and their task prefixes."""
    result: dict[str, str] = {}
    for m in re.finditer(r"### \[(T\d+[a-z]?(?:/T\d+[a-z]?)?)\]\s+([A-Z][\w-]*\d+)", text):
        result[m.group(2)] = m.group(1)
    return result


def _get_backlog_priority_section(text: str, item_id: str) -> str | None:
    """Return the backlog priority section containing an item."""
    sections = list(re.finditer(r"^## (Vysoká|Střední|Nízká) priorita", text, re.MULTILINE))
    item_pos = text.find(item_id)
    if item_pos == -1:
        return None
    for i, sec in enumerate(sections):
        start = sec.start()
        end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
        if start <= item_pos < end:
            return sec.group(1)
    return None


def cmd_cross_validate(cfg: Config, _args: argparse.Namespace) -> int:
    """Cross-validate bugs, backlog entries, reports, and cached metadata."""
    errors: list[str] = []
    warnings: list[str] = []

    bugs_text = _read_text(cfg.bugs_file)
    backlog_text = _read_text(cfg.backlog_file)
    final_text = _read_text(cfg.final_audit)

    bug_ids = set(re.findall(r"### (BUG-\d+)", bugs_text))
    bug_sevs = _extract_bug_severities(bugs_text)
    backlog_items = _extract_backlog_items(backlog_text)

    backlog_bug_refs = set(re.findall(r"BUG-\d+", backlog_text))
    for ref in sorted(backlog_bug_refs):
        if ref not in bug_ids:
            errors.append(f"Backlog references {ref} but it does not exist in bugs.md")

    for bug in sorted(bug_ids):
        if bug not in backlog_text and bug not in final_text:
            warnings.append(f"{bug} is not referenced in backlog or final_audit")

    reports_dir = cfg.review_reports_dir
    for item_id, prefix in sorted(backlog_items.items()):
        prefixes = [p.strip() for p in prefix.split("/")]
        found = False
        for p in prefixes:
            report = reports_dir / f"{p}.md"
            if report.exists():
                rt = _read_text(report)
                if item_id in rt:
                    found = True
                    break
        if not found:
            names = ", ".join(f"{p}.md" for p in prefixes)
            warnings.append(f"Backlog item {item_id} [{prefix}]: not mentioned in {names}")

    sev_map = {"Kritická": "Vysoká", "Vysoká": "Vysoká", "Střední": "Střední", "Nízká": "Nízká"}
    for bug in sorted(bug_ids):
        sev = bug_sevs.get(bug)
        if not sev or bug not in backlog_text:
            continue
        bs = _get_backlog_priority_section(backlog_text, bug)
        if bs and sev in sev_map and bs != sev_map[sev]:
            bug_block = bugs_text.split(bug)[1].split("###")[0] if bug in bugs_text else ""
            if "Sjednocení" not in bug_block and "reconcil" not in bug_block.lower():
                warnings.append(
                    f"{bug}: severity={sev} but in backlog '{bs} priorita' "
                    f"(expected '{sev_map[sev]} priorita' or documented rationale)"
                )

    cache = _load_json(cfg.cache_file)
    for task_id, info in cache.get("tasks", {}).items():
        rp = info.get("report_path")
        if rp and not (cfg.repo_root / rp).exists():
            errors.append(f"Cache task {task_id}: report_path '{rp}' does not exist")
        for sub_id, sub_info in info.get("sub_tasks", {}).items():
            srp = sub_info.get("report_path")
            if srp and not (cfg.repo_root / srp).exists():
                errors.append(f"Cache sub-task {sub_id}: report_path '{srp}' does not exist")

    print(f"[cross-validate] BUG entries: {len(bug_ids)}, Backlog items: {len(backlog_items)}")
    print(f"  Errors:   {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    for e in errors:
        print(f"    ERROR: {e}")
    for w in warnings:
        print(f"    WARN:  {w}")
    return len(errors)


# -- cmd: coverage-gaps --------------------------------------------------------


def cmd_coverage_gaps(cfg: Config, _args: argparse.Namespace) -> int:
    """Find source areas not represented in existing analysis artifacts."""
    gaps: list[tuple[str, str, str]] = []
    info_lines: list[str] = []

    # T03: Django ORM coverage
    if cfg.django_project_root:
        orm = _load_json(cfg.analysis_dir / "orm_analysis.json")
        analyzed_apps: set[str] = set()
        for model_key in orm.get("models", {}):
            analyzed_apps.add(model_key.split(".")[0])

        for mf in sorted(cfg.django_project_root.glob("*/models.py")):
            app = mf.parent.name
            if app == cfg.django_project_root.name:
                continue
            content = _read_text(mf)
            lines = len(content.splitlines())
            has_models = "models.Model" in content or "(models." in content
            if app not in analyzed_apps and has_models and lines > 5:
                mc = len(re.findall(r"class\s+\w+\(.*models\.", content))
                gaps.append(("T03", app, f"models.py ({lines} lines, ~{mc} models) not in orm_analysis.json"))

    # T07: Frontend JS coverage
    frontend = _load_json(cfg.analysis_dir / "frontend_analysis.json")
    analyzed_js: set[str] = set()
    for f in frontend.get("custom_javascript", {}).get("files_analyzed", []):
        analyzed_js.add(Path(f).name)

    if cfg.django_project_root:
        js_dir = cfg.django_project_root / "static" / "js"
        if js_dir.exists():
            for js_file in sorted(js_dir.glob("*.js")):
                if js_file.name not in analyzed_js:
                    content = _read_text(js_file)
                    lines = len(content.splitlines())
                    if _is_vendored_js(js_file.name, content, cfg):
                        info_lines.append(f"    [T07] {js_file.name} ({lines} lines) — likely vendored, skipped")
                    else:
                        gaps.append(("T07", js_file.name, f"JS file ({lines} lines) not in frontend_analysis.json"))

    # T10: Scripts coverage
    scripts = _load_json(cfg.analysis_dir / "scripts_analysis.json")
    analyzed_scripts: set[str] = set()
    for entry in scripts.get("all_scripts", scripts.get("scripts", [])):
        p = entry.get("path", "") if isinstance(entry, dict) else str(entry)
        analyzed_scripts.add(p)
        analyzed_scripts.add(Path(p).name)

    scripts_dir = cfg.repo_root / "scripts"
    if scripts_dir.exists():
        for sf in sorted(scripts_dir.rglob("*")):
            if sf.is_dir():
                continue
            rel = str(sf.relative_to(cfg.repo_root)).replace("\\", "/")
            if rel not in analyzed_scripts and sf.name not in analyzed_scripts:
                gaps.append(("T10", rel, "script not in scripts_analysis.json"))

    print(f"[coverage-gaps] Gaps found: {len(gaps)}")
    for task, item, desc in gaps:
        print(f"    [{task}] {item}: {desc}")
    if info_lines:
        print(f"  Vendored (skipped): {len(info_lines)}")
        for line in info_lines:
            print(line)
    return len(gaps)


# -- cmd: id-inventory ---------------------------------------------------------


def cmd_id_inventory(cfg: Config, _args: argparse.Namespace) -> int:
    """Inventory structured identifiers across review artifacts."""
    id_locations: dict[str, set[str]] = defaultdict(set)
    trivial_ids = {"UTF-8", "ISO-8601"}

    def _scan_file(path: Path, label: str):
        text = _read_text(path)
        for found_id in _extract_all_ids(text):
            if found_id in trivial_ids or len(found_id) < 4:
                continue
            id_locations[found_id].add(label)

    if cfg.bugs_file.exists():
        _scan_file(cfg.bugs_file, "bugs.md")
    if cfg.backlog_file.exists():
        _scan_file(cfg.backlog_file, "backlog")
    if cfg.final_audit.exists():
        _scan_file(cfg.final_audit, "final_audit")

    for rpt in sorted(cfg.review_reports_dir.glob("*.md")):
        if rpt.name in ("README.md", "final_audit.md"):
            continue
        _scan_file(rpt, rpt.stem)

    for jf in sorted(cfg.analysis_dir.glob("*.json")):
        _scan_file(jf, jf.stem)

    bug_ids = {i for i in id_locations if i.startswith("BUG-")}
    sec_ids = {i for i in id_locations if i.startswith("SEC-")}
    all_ids = sorted(id_locations.keys())

    orphan_bugs = [i for i in sorted(bug_ids) if len(id_locations[i]) == 1]
    orphan_sec = [i for i in sorted(sec_ids) if "final_audit" not in id_locations[i]]
    single_ref = [i for i in all_ids if len(id_locations[i]) == 1 and i not in bug_ids]

    issues = 0
    print(f"[id-inventory] Total unique IDs: {len(all_ids)}")
    print(f"  BUG IDs: {len(bug_ids)}, SEC IDs: {len(sec_ids)}")

    if orphan_bugs:
        print("\n  Orphan BUG IDs (only in one artifact):")
        for i in orphan_bugs:
            print(f"    {i}: only in {', '.join(id_locations[i])}")
        issues += len(orphan_bugs)

    if orphan_sec:
        print("\n  SEC IDs not in final_audit:")
        for i in orphan_sec:
            print(f"    {i}: found in {', '.join(id_locations[i])}")

    if single_ref and len(single_ref) <= 20:
        print(f"\n  Single-reference IDs (informational): {len(single_ref)}")
        for i in single_ref[:10]:
            print(f"    {i}: only in {', '.join(id_locations[i])}")
        if len(single_ref) > 10:
            print(f"    ... and {len(single_ref) - 10} more")

    return issues


# -- cmd: lint-artifacts -------------------------------------------------------


def cmd_lint_artifacts(cfg: Config, _args: argparse.Namespace) -> int:
    """Validate the structure and consistency of ``.agents/`` artifacts."""
    errors: list[str] = []
    warnings: list[str] = []

    if not cfg.agents_dir.exists():
        errors.append(f".agents/ directory not found at {cfg.agents_dir}")
        print(f"[lint-artifacts] Errors: {len(errors)}")
        for e in errors:
            print(f"    ERROR: {e}")
        return len(errors)

    for jf in sorted(cfg.analysis_dir.glob("*.json")):
        text = _read_text(jf)
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON: {jf.name}: {exc}")

    cache_file = cfg.cache_file
    if cache_file.exists():
        text = _read_text(cache_file)
        try:
            cache = json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid cache JSON: {exc}")
            cache = {}

        if "file_hashes" not in cache:
            warnings.append("review_cache.json missing 'file_hashes' key")
        if "tasks" not in cache:
            warnings.append("review_cache.json missing 'tasks' key")

        for task_id, info in cache.get("tasks", {}).items():
            rp = info.get("report_path")
            if rp and not (cfg.repo_root / rp).exists():
                errors.append(f"Cache {task_id}: report_path '{rp}' not found")
            ca = info.get("completed_at")
            if ca and isinstance(ca, str) and ca > "2099":
                warnings.append(f"Cache {task_id}: completed_at '{ca}' looks implausible")
    else:
        warnings.append("review_cache.json not found")

    bugs_text = _read_text(cfg.bugs_file)
    if bugs_text:
        bug_entries = re.findall(r"### (BUG-\d+)", bugs_text)
        for bug in bug_entries:
            block = bugs_text.split(bug)[1].split("###")[0] if bug in bugs_text else ""
            if "**Závažnost:**" not in block and "**Severity:**" not in block:
                warnings.append(f"{bug}: missing severity field")
            has_file_ref = any(marker in block for marker in ("**Soubor:**", "**Soubory:**", "**File:**", "**Files:**"))
            if not has_file_ref:
                warnings.append(f"{bug}: missing file reference")

    for tf in cfg.get_analysis_files().values():
        if tf.suffix == ".json" and not tf.exists():
            warnings.append(f"Analysis file missing: {tf.relative_to(cfg.repo_root)}")

    expected_dirs = ["config", "analysis", "reports", "prompts"]
    for d in expected_dirs:
        if not (cfg.agents_dir / d).exists():
            warnings.append(f".agents/{d}/ directory missing")

    print(f"[lint-artifacts] Errors: {len(errors)}, Warnings: {len(warnings)}")
    for e in errors:
        print(f"    ERROR: {e}")
    for w in warnings:
        print(f"    WARN:  {w}")
    return len(errors)


# -- cmd: prompt-evolution -----------------------------------------------------


def cmd_prompt_evolution(cfg: Config, _args: argparse.Namespace) -> int:
    """Report prompt-evolution proposals not reflected in the active prompt."""
    pe_dir = cfg.prompt_evolution_dir
    if not pe_dir.exists():
        print("[prompt-evolution] No prompt_evolution/ directory found.")
        return 0

    codebase_text = _read_text(cfg.review_codebase)
    if not codebase_text:
        print("[prompt-evolution] review_codebase.md not found; cannot check integration.")
        return 0

    pe_files = sorted(pe_dir.glob("*_prompt_update.md"))
    if not pe_files:
        print("[prompt-evolution] No prompt evolution files found.")
        return 0

    pending: list[tuple[str, str]] = []
    integrated = 0
    total_suggestions = 0

    for pf in pe_files:
        task = pf.stem.replace("_prompt_update", "")
        content = _read_text(pf)
        suggestions = re.split(r"\n-\s+", content)
        for suggestion in suggestions:
            suggestion = suggestion.strip()
            if not suggestion or len(suggestion) < 20:
                continue
            total_suggestions += 1
            keywords = re.findall(r"\b[A-Za-z_]{4,}\b", suggestion)
            significant = [
                k
                for k in keywords
                if k.lower()
                not in {
                    "should",
                    "could",
                    "would",
                    "this",
                    "that",
                    "with",
                    "from",
                    "have",
                    "been",
                    "they",
                    "were",
                    "into",
                    "more",
                    "when",
                    "also",
                    "each",
                    "does",
                    "what",
                    "make",
                    "will",
                    "than",
                    "only",
                    "just",
                    "very",
                    "note",
                    "such",
                    "must",
                }
            ]
            match_count = sum(1 for k in significant[:6] if k.lower() in codebase_text.lower())
            if match_count >= 2:
                integrated += 1
            else:
                short = suggestion[:80].replace("\n", " ")
                pending.append((task.upper(), short))

    print(f"[prompt-evolution] Files: {len(pe_files)}, Suggestions: {total_suggestions}")
    print(f"  Integrated:  {integrated}")
    print(f"  Pending:     {len(pending)}")
    if pending:
        for task, desc in pending[:10]:
            print(f"    [{task}] {desc}...")
        if len(pending) > 10:
            print(f"    ... and {len(pending) - 10} more")
    return len(pending)


# -- cmd: repo-structure -------------------------------------------------------


def cmd_repo_structure(cfg: Config, _args: argparse.Namespace) -> int:
    """Report repository file, extension, line-count, and layout statistics."""
    ext_counts: Counter = Counter()
    ext_lines: Counter = Counter()
    large_files: list[tuple[str, int]] = []
    dir_file_counts: Counter = Counter()
    total_files = 0

    for root, dirs, files in os.walk(cfg.repo_root):
        dirs[:] = [d for d in dirs if d not in cfg.ignored_dirs]
        rel_root = Path(root).relative_to(cfg.repo_root)
        top_dir = str(rel_root).split(os.sep, maxsplit=1)[0] if str(rel_root) != "." else "."

        for f in files:
            fp = Path(root) / f
            ext = fp.suffix.lower() or "(no ext)"
            ext_counts[ext] += 1
            dir_file_counts[top_dir] += 1
            total_files += 1

            if ext in cfg.source_extensions:
                try:
                    lines = len(fp.read_text(encoding="utf-8", errors="replace").splitlines())
                    ext_lines[ext] += lines
                    if lines > 1000:
                        rel = str(fp.relative_to(cfg.repo_root)).replace("\\", "/")
                        large_files.append((rel, lines))
                except (OSError, UnicodeDecodeError) as e:
                    # File could not be read or decoded; skip it but report for transparency.
                    print(f"[repo-structure] Warning: failed to read {fp}: {e}", file=sys.stderr)

    print(f"[repo-structure] Total files: {total_files}")
    print("\n  Files by extension (top 15):")
    for ext, count in ext_counts.most_common(15):
        line_info = f" ({ext_lines[ext]:,} lines)" if ext in ext_lines else ""
        print(f"    {ext:12s} {count:5d}{line_info}")

    print("\n  Files by top-level directory (top 10):")
    for d, count in dir_file_counts.most_common(10):
        print(f"    {d:20s} {count:5d}")

    if large_files:
        large_files.sort(key=lambda x: -x[1])
        print("\n  Large files (>1000 lines, top 15):")
        for path, lines in large_files[:15]:
            print(f"    {path}: {lines:,} lines")

    repo_map = _load_json(cfg.analysis_dir / "repository_map.json")
    if repo_map:
        mapped_dirs = set()
        for key in repo_map.get("directories", {}):
            mapped_dirs.add(key)
        actual_dirs = set()
        for d in sorted(cfg.repo_root.iterdir()):
            if d.is_dir() and d.name not in cfg.ignored_dirs:
                actual_dirs.add(d.name)
        new_dirs = actual_dirs - mapped_dirs - cfg.ignored_dirs
        if new_dirs:
            print("\n  New directories not in repository_map.json:")
            for d in sorted(new_dirs):
                print(f"    {d}/")

    return 0


# -- cmd: status ---------------------------------------------------------------


def cmd_status(cfg: Config, _args: argparse.Namespace) -> int:
    """Print a concise dashboard for the current review workflow state."""
    cache = _load_json(cfg.cache_file)
    bugs_text = _read_text(cfg.bugs_file)
    backlog_text = _read_text(cfg.backlog_file)

    print("[status] Review System Dashboard")
    print(f"  Repository: {cfg.repo_root.name}")

    tasks = cache.get("tasks", {})
    done = sum(1 for t in tasks.values() if t.get("status") == "done")
    split = sum(1 for t in tasks.values() if t.get("status") == "split")
    pending = sum(1 for t in tasks.values() if t.get("status") == "pending")
    total_tasks = len(tasks)
    print(f"\n  Tasks: {total_tasks} total — {done} done, {split} split, {pending} pending")
    for tid, info in sorted(tasks.items()):
        status = info.get("status", "?")
        completed = info.get("completed_at", "")
        subs = info.get("sub_tasks", {})
        sub_info = f" ({len(subs)} sub-tasks)" if subs else ""
        date_info = f" [{completed[:10]}]" if completed else ""
        print(f"    {tid:6s} {status:8s}{date_info}{sub_info}")

    bug_ids = re.findall(r"### (BUG-\d+)", bugs_text)
    bug_sevs = _extract_bug_severities(bugs_text)
    sev_counts: Counter = Counter()
    for sev in bug_sevs.values():
        sev_counts[sev] += 1
    print(f"\n  Bugs: {len(bug_ids)} total")
    for sev in ["Kritická", "Vysoká", "Střední", "Nízká"]:
        if sev_counts[sev]:
            print(f"    {sev}: {sev_counts[sev]}")

    backlog_items = _extract_backlog_items(backlog_text)
    priority_counts: Counter = Counter()
    for item_id in backlog_items:
        sec = _get_backlog_priority_section(backlog_text, item_id)
        if sec:
            priority_counts[sec] += 1
    print(f"\n  Backlog items: {len(backlog_items)} total")
    for pri in ["Vysoká", "Střední", "Nízká"]:
        if priority_counts[pri]:
            print(f"    {pri} priorita: {priority_counts[pri]}")

    file_hashes = cache.get("file_hashes", {})
    print(f"\n  Tracked files: {len(file_hashes)}")
    last_updated = cache.get("last_updated", "unknown")
    print(f"  Last updated: {last_updated}")

    analysis_files = cfg.get_analysis_files()
    existing = sum(1 for p in analysis_files.values() if p.exists())
    print(f"\n  Analysis files: {existing}/{len(analysis_files)} present")

    return 0


# -- cmd: all ------------------------------------------------------------------

ALL_CHECKS = [
    ("hash", cmd_hash),
    ("cross-validate", cmd_cross_validate),
    ("coverage-gaps", cmd_coverage_gaps),
    ("id-inventory", cmd_id_inventory),
    ("lint-artifacts", cmd_lint_artifacts),
    ("prompt-evolution", cmd_prompt_evolution),
]


def cmd_all(cfg: Config, args: argparse.Namespace) -> int:
    """Run all checks and return the bounded aggregate issue count."""
    total = 0
    for name, cmd in ALL_CHECKS:
        print(_section_header(name))
        result = cmd(cfg, args)
        total += result
        print(f"  => {result} issue(s)\n")
    print(f"Total issues: {total}")
    return min(total, 125)


# -- main ----------------------------------------------------------------------

COMMANDS: dict[str, tuple] = {
    "hash": (cmd_hash, "Compare file hashes against review_cache.json"),
    "cross-validate": (cmd_cross_validate, "Cross-validate BUG/backlog/final_audit consistency"),
    "coverage-gaps": (cmd_coverage_gaps, "Detect uncovered source files"),
    "id-inventory": (cmd_id_inventory, "Cross-reference all IDs across artifacts"),
    "lint-artifacts": (cmd_lint_artifacts, "Validate .agents/ artifact structure"),
    "prompt-evolution": (cmd_prompt_evolution, "Check prompt evolution integration status"),
    "repo-structure": (cmd_repo_structure, "Scan and summarize repository structure"),
    "status": (cmd_status, "Print review system status dashboard"),
    "all": (cmd_all, "Run all validation checks"),
}


def main() -> int:
    """Run the command-line interface and return its exit status."""
    parser = argparse.ArgumentParser(
        description="Validate artifacts produced by the AIS CR codebase-review workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (auto-detected from .git if omitted)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to review_config.yaml (default: .agents/config/review_config.yaml)",
    )
    sub = parser.add_subparsers(dest="command")
    for name, (_, help_text) in COMMANDS.items():
        sub.add_parser(name, help=help_text)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    cfg = Config(repo_root=args.repo_root, config_path=args.config)
    cmd_fn = COMMANDS[args.command][0]
    return cmd_fn(cfg, args)


if __name__ == "__main__":
    sys.exit(main())
