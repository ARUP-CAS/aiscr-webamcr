#!/usr/bin/env python3
"""Validate artifacts produced by the AIS CR codebase-review workflow.

The script uses only the Python standard library and works with repositories
that provide an ``.agents/`` tree and ``review_config.toml``. Structured input is
parsed with ``tomllib`` and ``json``; no machine-read field is recovered by matching
Markdown prose. Requires Python 3.11 or newer.

Usage:

    python review_tools.py hash               # check tracked file hashes
    python review_tools.py cross-validate     # cross-validate artifacts
    python review_tools.py coverage-gaps      # identify analysis coverage gaps
    python review_tools.py id-inventory       # inventory IDs across artifacts
    python review_tools.py lint-artifacts     # validate artifact structure
    python review_tools.py prompt-evolution   # inventory workflow-evolution evidence
    python review_tools.py render             # regenerate the Markdown twins
    python review_tools.py render --check     # fail when a Markdown twin is stale
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

try:  # ``tomllib`` is standard library from Python 3.11 onward.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on unsupported interpreters
    tomllib = None  # type: ignore[assignment] # pylint: disable=invalid-name


MIN_PYTHON = (3, 11)

#: Findings-source schema versions this engine understands.
FINDINGS_SCHEMA_VERSIONS = frozenset({"1"})

SEVERITIES = ("Critical", "High", "Medium", "Low")
PRIORITIES = ("High", "Medium", "Low")
EFFORTS = ("S", "M", "L", "XL")

#: A bug of severity X reconciles to backlog priority SEVERITY_TO_PRIORITY[X]
#: unless the bug entry documents a deliberate divergence.
SEVERITY_TO_PRIORITY = {
    "Critical": "High",
    "High": "High",
    "Medium": "Medium",
    "Low": "Low",
}


class ReviewDataError(Exception):
    """A structured review artifact could not be read or is malformed."""


def require_supported_python() -> None:
    """Fail with an explicit version message instead of a ``tomllib`` traceback."""
    if tomllib is None or sys.version_info < MIN_PYTHON:
        current = ".".join(str(part) for part in sys.version_info[:3])
        raise SystemExit(
            f"review_tools.py requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer "
            f"(found {current}); it reads TOML with the standard-library tomllib module."
        )


def _load_toml(path: Path) -> dict:
    """Load a TOML document, returning an empty mapping when the file is absent."""
    require_supported_python()
    if not path.exists():
        return {}
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ReviewDataError(f"Invalid TOML in {path.name}: {exc}") from exc


def _check_schema_version(data: dict, path: Path) -> None:
    """Reject a findings source whose schema version this engine does not know."""
    declared = data.get("schema_version")
    if declared is None:
        raise ReviewDataError(f"{path.name}: missing 'schema_version'")
    if str(declared) not in FINDINGS_SCHEMA_VERSIONS:
        known = ", ".join(sorted(FINDINGS_SCHEMA_VERSIONS))
        raise ReviewDataError(f"{path.name}: unrecognized schema_version '{declared}' (known: {known})")


def _load_findings(path: Path, twin: Path, entry_key: str) -> dict:
    """Load a findings source, refusing to fall back to its generated Markdown twin."""
    if not path.exists():
        if twin.exists():
            raise ReviewDataError(
                f"{path.name} is missing but {twin.name} exists; {twin.name} is a generated "
                f"twin and is not a findings source. Run the migration before validating."
            )
        return {"schema_version": next(iter(FINDINGS_SCHEMA_VERSIONS)), entry_key: []}
    data = _load_toml(path)
    _check_schema_version(data, path)
    entries = data.get(entry_key, [])
    if not isinstance(entries, list):
        raise ReviewDataError(f"{path.name}: '{entry_key}' must be an array of tables")
    return data


def load_bugs(cfg: Config) -> dict:
    """Return the parsed ``bugs.toml`` document."""
    return _load_findings(cfg.bugs_source, cfg.bugs_file, "bug")


def load_backlog(cfg: Config) -> dict:
    """Return the parsed ``refactoring_backlog.toml`` document."""
    return _load_findings(cfg.backlog_source, cfg.backlog_file, "item")


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
    """Review workflow configuration loaded from ``review_config.toml``."""

    def __init__(self, repo_root: Path | None = None, config_path: Path | None = None):
        script_dir = Path(__file__).resolve().parent
        self.repo_root = repo_root or _find_repo_root(script_dir)
        self.agents_dir = self.repo_root / ".agents"
        self.config_dir = self.agents_dir / "config"
        self.reports_dir = self.agents_dir / "reports"
        self.analysis_dir = self.agents_dir / "analysis"
        self.prompts_dir = self.agents_dir / "prompts"

        self.cache_file = self.config_dir / "review_cache.json"
        # Findings sources of truth; the ``*.md`` twins are generated by ``render``.
        self.bugs_source = self.reports_dir / "bugs.toml"
        self.backlog_source = self.reports_dir / "refactoring_backlog.toml"
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

        cfg_path = config_path or self.config_dir / "review_config.toml"
        self._raw = _load_toml(cfg_path)
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
        """Return task IDs defined in ``review_config.toml``."""
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


_BUG_REF_RE = re.compile(r"\bBUG-\d+\b")


def _item_bug_refs(item: dict) -> set[str]:
    """Collect BUG identifiers an item cross-references, from its field and its prose."""
    refs = {str(ref) for ref in item.get("bugs", [])}
    for field in ("description", "recommendation", "title"):
        refs.update(_BUG_REF_RE.findall(str(item.get(field, ""))))
    return refs


def _documents_divergence(bug: dict) -> bool:
    """Return whether a bug entry documents a deliberate severity/priority divergence.

    The rationale lives in the typed ``alignment`` field. Intent is never inferred from
    wording inside ``description`` or ``recommended_fix``.
    """
    return bool(str(bug.get("alignment", "")).strip())


def _task_prefixes(item: dict) -> list[str]:
    """Split an item's task field, which may name two phases as ``T02/T03``."""
    return [part.strip() for part in str(item.get("task", "")).split("/") if part.strip()]


def cmd_cross_validate(cfg: Config, _args: argparse.Namespace) -> int:
    """Cross-validate bugs, backlog entries, reports, and cached metadata."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        bugs_doc = load_bugs(cfg)
        backlog_doc = load_backlog(cfg)
    except ReviewDataError as exc:
        print("[cross-validate] Errors:   1")
        print(f"    ERROR: {exc}")
        return 1

    bugs = bugs_doc.get("bug", [])
    items = backlog_doc.get("item", [])
    final_text = _read_text(cfg.final_audit)

    bug_ids = {str(b.get("id", "")) for b in bugs if b.get("id")}
    bug_sevs = {str(b["id"]): str(b.get("severity", "")) for b in bugs if b.get("id")}
    bugs_by_id = {str(b["id"]): b for b in bugs if b.get("id")}

    for item in items:
        item_id = str(item.get("id", "?"))
        for ref in sorted(_item_bug_refs(item)):
            if ref not in bug_ids:
                errors.append(f"Backlog item {item_id} references {ref} but it does not exist in bugs.toml")

    referenced_bugs: set[str] = set()
    for item in items:
        referenced_bugs.update(_item_bug_refs(item))
    for bug_id in sorted(bug_ids):
        if bug_id not in referenced_bugs and bug_id not in final_text:
            warnings.append(f"{bug_id} is not referenced in backlog or final_audit")

    reports_dir = cfg.review_reports_dir
    for item in items:
        item_id = str(item.get("id", "?"))
        prefixes = _task_prefixes(item)
        if not prefixes:
            errors.append(f"Backlog item {item_id}: missing 'task'")
            continue
        found = False
        for prefix in prefixes:
            report = reports_dir / f"{prefix}.md"
            if report.exists() and item_id in _read_text(report):
                found = True
                break
        if not found:
            names = ", ".join(f"{prefix}.md" for prefix in prefixes)
            warnings.append(f"Backlog item {item_id} [{'/'.join(prefixes)}]: not mentioned in {names}")

    # Severity/priority reconciliation. A bug with no severity is an error, not a skip:
    # this check must never report success because it could not read its own input.
    for bug_id in sorted(bug_ids):
        severity = bug_sevs.get(bug_id, "")
        if not severity:
            errors.append(f"{bug_id}: missing 'severity'; cannot reconcile against backlog priority")
            continue
        if severity not in SEVERITY_TO_PRIORITY:
            errors.append(f"{bug_id}: severity '{severity}' is outside the canonical vocabulary")
            continue
        expected = SEVERITY_TO_PRIORITY[severity]
        for item in items:
            if bug_id not in _item_bug_refs(item):
                continue
            priority = str(item.get("priority", ""))
            if priority and priority != expected and not _documents_divergence(bugs_by_id[bug_id]):
                warnings.append(
                    f"{bug_id}: severity={severity} but backlog item "
                    f"{item.get('id', '?')} has priority '{priority}' "
                    f"(expected '{expected}' or a documented rationale)"
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

    print(f"[cross-validate] BUG entries: {len(bug_ids)}, Backlog items: {len(items)}")
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

    # Scan the findings sources, not their generated twins, so identifiers stay
    # authoritative even when a twin has drifted.
    if cfg.bugs_source.exists():
        _scan_file(cfg.bugs_source, "bugs.toml")
    if cfg.backlog_source.exists():
        _scan_file(cfg.backlog_source, "backlog")
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

    try:
        bugs_doc = load_bugs(cfg)
        for index, bug in enumerate(bugs_doc.get("bug", [])):
            bug_id = str(bug.get("id", "")) or f"bug[{index}]"
            severity = str(bug.get("severity", ""))
            if not severity:
                errors.append(f"{bug_id}: missing 'severity'")
            elif severity not in SEVERITIES:
                errors.append(
                    f"{bug_id}: severity '{severity}' is outside the canonical vocabulary ({', '.join(SEVERITIES)})"
                )
            if not bug.get("files"):
                errors.append(f"{bug_id}: missing file reference")
            if not bug.get("task"):
                warnings.append(f"{bug_id}: missing 'task'")
    except ReviewDataError as exc:
        errors.append(str(exc))

    try:
        backlog_doc = load_backlog(cfg)
        for index, item in enumerate(backlog_doc.get("item", [])):
            item_id = str(item.get("id", "")) or f"item[{index}]"
            priority = str(item.get("priority", ""))
            if not priority:
                errors.append(f"{item_id}: missing 'priority'")
            elif priority not in PRIORITIES:
                errors.append(
                    f"{item_id}: priority '{priority}' is outside the canonical vocabulary ({', '.join(PRIORITIES)})"
                )
            effort = str(item.get("effort", ""))
            if effort and effort not in EFFORTS:
                warnings.append(f"{item_id}: effort '{effort}' is outside {', '.join(EFFORTS)}")
    except ReviewDataError as exc:
        errors.append(str(exc))

    errors.extend(_stale_twin_errors(cfg))

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


_PROMPT_EVOLUTION_FILE_RE = re.compile(r"^(?P<task>[TU]\d{2}[a-z]?)_prompt_update\.md$", re.IGNORECASE)
_PROMPT_EVOLUTION_README_NAMES = {"README.md", "README_en.md"}


def _relative_display_path(root: Path, path: Path) -> str:
    """Return a repository-relative path when possible."""
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def _count_prompt_evolution_bullets(content: str) -> int:
    """Count top-level bullet suggestions in a feedback file."""
    return len(re.findall(r"(?m)^\s*-\s+\S", content))


def cmd_prompt_evolution(cfg: Config, _args: argparse.Namespace) -> int:
    """Inventory workflow-evolution evidence and handoff status."""
    pe_dir = cfg.prompt_evolution_dir
    if not pe_dir.exists():
        print("[prompt-evolution] No workflow-evolution evidence found.")
        return 0

    evidence_files = sorted(path for path in pe_dir.iterdir() if path.is_file())
    feedback_files: list[tuple[str, Path, int, bool]] = []
    malformed: list[tuple[Path, str]] = []

    for evidence_file in evidence_files:
        if evidence_file.name in _PROMPT_EVOLUTION_README_NAMES:
            continue
        match = _PROMPT_EVOLUTION_FILE_RE.match(evidence_file.name)
        if not match:
            malformed.append((evidence_file, "unexpected filename; expected <task_id>_prompt_update.md"))
            continue
        content = _read_text(evidence_file).strip()
        if not content:
            malformed.append((evidence_file, "empty evidence file"))
            continue
        feedback_files.append(
            (
                match.group("task").upper(),
                evidence_file,
                _count_prompt_evolution_bullets(content),
                bool(re.search(r"(?m)^\s*-\s+\S", content)),
            )
        )

    if not feedback_files and not malformed:
        print("[prompt-evolution] No workflow-evolution evidence found.")
        return 0

    total_bullets = sum(count for _, _, count, _ in feedback_files)
    print("[prompt-evolution] Workflow-evolution evidence inventory")
    print(f"  Directory: {_relative_display_path(cfg.repo_root, pe_dir)}")
    print(f"  Evidence files: {len(feedback_files)}")
    print(f"  Bullet suggestions: {total_bullets}")
    print(f"  Pending handoff candidates: {len(feedback_files)}")
    print(f"  Malformed evidence: {len(malformed)}")
    print("  Hub handoff: report-to-backlog-handoff -> /aiscr-note-idea after approval")

    for task, path, bullet_count, has_bullets in feedback_files:
        rel_path = _relative_display_path(cfg.repo_root, path)
        shape = f"{bullet_count} bullet(s)" if has_bullets else "unstructured notes"
        print(f"    [{task}] {rel_path}: {shape}; disposition pending triage")

    for path, reason in malformed:
        rel_path = _relative_display_path(cfg.repo_root, path)
        print(f"    ERROR: {rel_path}: {reason}")

    return len(malformed)


# -- cmd: render ---------------------------------------------------------------


def _inline(text: str) -> str:
    """Collapse a multi-line TOML prose field onto the single line Markdown expects."""
    return re.sub(r"\s*\n\s*", " ", str(text).strip())


def _format_location(entry: dict) -> str:
    """Render one ``[[bug.files]]`` entry as a Markdown code span plus annotations."""
    location = str(entry.get("path", ""))
    if entry.get("line"):
        location = f"{location}:{entry['line']}"
    rendered = f"`{location}`"
    if entry.get("symbol"):
        rendered += f" — `{entry['symbol']}`"
    if entry.get("note"):
        rendered += f" *({entry['note']})*"
    return rendered


def _render_bug(bug: dict) -> str:
    """Render a single bug entry."""
    lines = [f"### {bug.get('id', '?')}: {_inline(bug.get('title', ''))}", ""]
    files = bug.get("files") or []
    # A lone plain location stays inline; anything annotated or multiple becomes a list.
    note = f" {bug['files_note']}" if bug.get("files_note") else ""
    if len(files) == 1 and not files[0].get("symbol") and not files[0].get("note"):
        lines.append(f"- **Files:** {_format_location(files[0])}{note}")
    else:
        lines.append(f"- **Files:**{note}")
        for entry in files:
            lines.append(f"  - {_format_location(entry)}")
    lines.append(f"- **Severity:** {bug.get('severity', '')}")
    if bug.get("github_issue"):
        lines.append(f"- **GitHub Issue:** {bug['github_issue']}")
    if bug.get("description"):
        lines.append(f"- **Description:** {_inline(bug['description'])}")
    if bug.get("recommended_fix"):
        lines.append(f"- **Recommended fix:** {_inline(bug['recommended_fix'])}")
    if bug.get("alignment"):
        lines.append(f"- **Alignment:** {_inline(bug['alignment'])}")
    lines.append(f"- **Task:** {bug.get('task', '')}")
    return "\n".join(lines)


def render_bugs(doc: dict) -> str:
    """Render ``bugs.md`` from the parsed ``bugs.toml`` document."""
    parts: list[str] = []
    preamble = str(doc.get("preamble", "")).strip()
    if preamble:
        parts.append(preamble)
    entries = [_render_bug(bug) for bug in doc.get("bug", [])]
    if entries:
        parts.append("\n\n---\n\n".join(entries))
    return "\n\n".join(parts).rstrip() + "\n"


def _render_backlog_item(item: dict) -> str:
    """Render a single refactoring-backlog item.

    Optional fields are emitted only when present, so a sibling that never records an
    ``impact`` or an ``effort`` does not gain an empty bullet.
    """
    header = f"### [{item.get('task', '')}] {item.get('id', '?')}: {_inline(item.get('title', ''))}"
    lines = [header]
    files = item.get("files") or []
    if files:
        rendered_files = "- **Files:** " + ", ".join(f"`{f}`" for f in files)
        if item.get("files_note"):
            rendered_files += f" {item['files_note']}"
        lines.append(rendered_files)
    applications = item.get("applications") or []
    if applications:
        lines.append("- **Applications:** " + ", ".join(str(a) for a in applications))
    if item.get("description"):
        lines.append(f"- **Description:** {_inline(item['description'])}")
    if item.get("impact"):
        lines.append(f"- **Impact:** {_inline(item['impact'])}")
    if item.get("recommendation"):
        lines.append(f"- **Recommendation:** {_inline(item['recommendation'])}")
    if item.get("effort"):
        lines.append(f"- **Effort:** {item['effort']}")
    if item.get("severity"):
        lines.append(f"- **Severity:** {item['severity']}")
    superseded = item.get("supersedes") or []
    if superseded:
        lines.append("- **Supersedes:** " + "; ".join(str(s) for s in superseded))
    return "\n".join(lines)


def render_backlog(doc: dict) -> str:
    """Render ``refactoring_backlog.md`` from the parsed backlog document."""
    parts: list[str] = []
    preamble = str(doc.get("preamble", "")).strip()
    if preamble:
        parts.append(preamble)

    section_notes = doc.get("section_notes", {})
    items = doc.get("item", [])
    for priority in PRIORITIES:
        in_section = [i for i in items if str(i.get("priority", "")) == priority]
        if not in_section:
            continue
        section = [f"## {priority} Priority"]
        note = str(section_notes.get(priority, "")).strip()
        if note:
            section.append(note)
        section.append("\n\n".join(_render_backlog_item(i) for i in in_section))
        parts.append("\n\n".join(section))
    return "\n\n".join(parts).rstrip() + "\n"


def _twin_targets(cfg: Config) -> list[tuple[Path, str]]:
    """Return each generated twin path paired with the text it should contain."""
    return [
        (cfg.bugs_file, render_bugs(load_bugs(cfg))),
        (cfg.backlog_file, render_backlog(load_backlog(cfg))),
    ]


def _stale_twin_errors(cfg: Config) -> list[str]:
    """Report generated twins whose contents diverge from their TOML source."""
    try:
        targets = _twin_targets(cfg)
    except ReviewDataError as exc:
        return [str(exc)]
    stale: list[str] = []
    for path, expected in targets:
        if not path.exists():
            stale.append(f"{path.name} is missing; run 'review_tools.py render'")
        elif _read_text(path) != expected:
            stale.append(f"{path.name} is stale; run 'review_tools.py render'")
    return stale


def cmd_render(cfg: Config, args: argparse.Namespace) -> int:
    """Regenerate the Markdown twins, or verify they are current under ``--check``."""
    check_only = getattr(args, "check", False)
    try:
        targets = _twin_targets(cfg)
    except ReviewDataError as exc:
        print(f"[render] ERROR: {exc}")
        return 1

    if check_only:
        stale = _stale_twin_errors(cfg)
        print(f"[render --check] Stale twins: {len(stale)}")
        for message in stale:
            print(f"    ERROR: {message}")
        return len(stale)

    written = 0
    for path, expected in targets:
        if not path.exists() or _read_text(path) != expected:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
            written += 1
            print(f"    wrote {path.name}")
    print(f"[render] Twins regenerated: {written}, already current: {len(targets) - written}")
    return 0


def cmd_render_check(cfg: Config, _args: argparse.Namespace) -> int:
    """Run ``render`` in verification mode for the aggregate ``all`` command."""
    return cmd_render(cfg, argparse.Namespace(check=True))


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
    """Print a concise dashboard for the current review workflow state.

    Read-only: this command never writes the generated Markdown twins.
    """
    cache = _load_json(cfg.cache_file)
    try:
        bugs_doc = load_bugs(cfg)
        backlog_doc = load_backlog(cfg)
    except ReviewDataError as exc:
        print("[status] Review System Dashboard")
        print(f"    ERROR: {exc}")
        return 1

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

    bugs = bugs_doc.get("bug", [])
    sev_counts: Counter = Counter(str(b.get("severity", "")) for b in bugs)
    print(f"\n  Bugs: {len(bugs)} total")
    for sev in SEVERITIES:
        if sev_counts[sev]:
            print(f"    {sev}: {sev_counts[sev]}")
    unknown_sev = sorted(set(sev_counts) - set(SEVERITIES))
    for sev in unknown_sev:
        label = sev or "(missing)"
        print(f"    {label}: {sev_counts[sev]} (outside the canonical vocabulary)")

    items = backlog_doc.get("item", [])
    priority_counts: Counter = Counter(str(i.get("priority", "")) for i in items)
    print(f"\n  Backlog items: {len(items)} total")
    for pri in PRIORITIES:
        if priority_counts[pri]:
            print(f"    {pri} priority: {priority_counts[pri]}")
    unknown_pri = sorted(set(priority_counts) - set(PRIORITIES))
    for pri in unknown_pri:
        label = pri or "(missing)"
        print(f"    {label}: {priority_counts[pri]} (outside the canonical vocabulary)")

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
    ("render --check", cmd_render_check),
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
    "prompt-evolution": (cmd_prompt_evolution, "Inventory workflow-evolution evidence"),
    "render": (cmd_render, "Regenerate bugs.md and refactoring_backlog.md from their TOML sources"),
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
        help="Path to review_config.toml (default: .agents/config/review_config.toml)",
    )
    sub = parser.add_subparsers(dest="command")
    for name, (_, help_text) in COMMANDS.items():
        cmd_parser = sub.add_parser(name, help=help_text)
        if name == "render":
            cmd_parser.add_argument(
                "--check",
                action="store_true",
                help="Verify the twins are current without writing them",
            )

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    require_supported_python()
    cfg = Config(repo_root=args.repo_root, config_path=args.config)
    cmd_fn = COMMANDS[args.command][0]
    return cmd_fn(cfg, args)


if __name__ == "__main__":
    sys.exit(main())
