# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: 96a1e289289a180161258baa10f7547b8cd9f719 2026-11-07T11:55:51+01:00

"""Validate `.github/release.yml` and release-notes report layout.

Runs without an agent or the GitHub API. Optional --check-git-count: sanity check for date-based reports (if there were
commits that day, at least one note). Optional --release-config: validate a recommended report copy instead of
`.github/release.yml`.

Contract: documentation/release-documentation, documentation/docs-language-quality
Class: script
Stable id: validation.release-yml
Exit codes: 0 pass; 1 findings
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- TimeoutExpired only; capture runs through proc_utils
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:  # pragma: no cover -- direct script startup already supplies this path
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.log_utils import log_error  # noqa: E402
from lib.proc_utils import run_exact  # noqa: E402

# Required section headers: Czech (date-range/mimic mode) or English (tag-based).
REQUIRED_SECTIONS_CZECH = (
    "## Zásadní změny",
    "## Nové funkce",
    "## Opravy chyb",
    "## Ostatní",
)
REQUIRED_SECTIONS_ENGLISH = (
    "## Breaking changes",
    "## Features",
    "## Bug fixes",
    "## Other",
)

# Report title must be written in the same language as the section set, so a Czech report
# does not carry an English heading. Owning requirement: release notes are fully Czech
# (headers, boilerplate, bullet text) per
# openspec/specs/documentation/docs-language-quality/spec.md.
REQUIRED_TITLE_CZECH = "# Poznámky k vydání"
REQUIRED_TITLE_ENGLISH = "# Release notes"

# Report file naming: <repo>_YYYY-MM-DD.md (date) or <repo>_<tag>.md (tag).
REPORT_FILENAME_PATTERN = re.compile(r"^[a-z0-9_-]+_(?:\d{4}-\d{2}-\d{2}|[a-zA-Z0-9._-]+)\.md$")
# Date-based report: extract YYYY-MM-DD for git sanity check.
DATE_REPORT_PATTERN = re.compile(r"^[a-z0-9_-]+_(\d{4}-\d{2}-\d{2})\.md$")
# Tag-based publishable companion: <repo>_<tag>.working.md
WORKING_REPORT_SUFFIX = ".working.md"
# Headings allowed only in working companions (forbidden in publishable tag reports).
WORKING_ONLY_HEADINGS = (
    "## Poznámky k sestavení",
    "## Poznámky k sestavení tohoto návrhu",
    "## Assembly notes",
    "## Nasazení (provoz)",
    "## Nasazení",
    "## Working notes",
)


def _is_working_report(name: str) -> bool:
    """Return True when the filename is a tag-based working-notes companion."""
    return name.endswith(WORKING_REPORT_SUFFIX)


def _is_date_report(name: str) -> bool:
    """Return True when the filename is a date-range (mimic) report."""
    return DATE_REPORT_PATTERN.match(name) is not None


def _is_tag_publishable_report(name: str) -> bool:
    """Return True for tag-based publishable notes (not date-range, not .working.md)."""
    if not REPORT_FILENAME_PATTERN.match(name):
        return False
    if _is_working_report(name) or _is_date_report(name):
        return False
    return True


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if "\0" in text:
        raise ValueError("file contains NUL bytes")
    return yaml.safe_load(text)


def validate_release_yml(
    root: Path,
    release_config: Path | None = None,
) -> list[tuple[Path, str]]:
    # pylint: disable=too-many-locals,too-many-return-statements,too-many-branches
    """Validate the selected release config; relative paths resolve from root."""
    errors: list[tuple[Path, str]] = []
    path = root / (release_config if release_config is not None else Path(".github/release.yml"))
    if not path.exists():
        errors.append((path, "file does not exist"))
        return errors
    raw_text = path.read_text(encoding="utf-8")
    if not raw_text.strip():
        errors.append((path, "file is empty"))
        return errors
    first_line = raw_text.strip().split("\n")[0].strip()
    if not first_line.startswith("#"):
        errors.append(
            (
                path,
                (
                    "file must have a top comment (first non-empty line starting with #) "
                    "documenting canonical release notes categories"
                ),
            )
        )
    try:
        data = _load_yaml(path)
    except Exception as e:  # pylint: disable=broad-exception-caught
        errors.append((path, f"invalid YAML: {e}"))
        return errors
    if not isinstance(data, dict):
        errors.append((path, "root must be a mapping"))
        return errors
    changelog = data.get("changelog")
    if changelog is None:
        errors.append((path, "missing top-level key 'changelog'"))
        return errors
    if not isinstance(changelog, dict):
        errors.append((path, "'changelog' must be a mapping"))
        return errors
    categories = changelog.get("categories")
    if categories is None:
        errors.append((path, "missing 'changelog.categories'"))
        return errors
    if not isinstance(categories, list):
        errors.append((path, "'changelog.categories' must be a list"))
        return errors
    if len(categories) == 0:
        errors.append((path, "'changelog.categories' must be non-empty"))
        return errors
    for i, cat in enumerate(categories):
        if not isinstance(cat, dict):
            errors.append((path, f"changelog.categories[{i}] must be a mapping"))
            continue
        title = cat.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append((path, f"changelog.categories[{i}] must have non-empty 'title' (string)"))
        labels = cat.get("labels")
        if not isinstance(labels, list):
            errors.append((path, f"changelog.categories[{i}] must have 'labels' (list)"))
        elif len(labels) == 0:
            errors.append((path, f"changelog.categories[{i}] must have at least one label (populated, not empty)"))
    # Optional changelog.exclude per GitHub Docs (labels, authors).
    exclude = changelog.get("exclude")
    if exclude is not None:
        if not isinstance(exclude, dict):
            errors.append((path, "'changelog.exclude' must be a mapping"))
        else:
            for key in ("labels", "authors"):
                val = exclude.get(key)
                if val is not None and not isinstance(val, list):
                    errors.append((path, f"'changelog.exclude.{key}' must be a list"))
    return errors


def validate_reports_dir(root: Path, skip_reports: bool) -> list[tuple[Path, str]]:
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Check steps 5 & 7: report directory exists; report files naming and required sections."""
    errors: list[tuple[Path, str]] = []
    reports_dir = root / ".agents" / "reports" / "release-notes"
    if skip_reports:
        return errors
    if not reports_dir.exists():
        errors.append((reports_dir, "directory does not exist"))
        return errors
    if not reports_dir.is_dir():
        errors.append((reports_dir, "not a directory"))
        return errors

    tag_publishable: list[Path] = []
    for p in sorted(reports_dir.iterdir()):
        if p.name in ("README.md", "README_en.md") or p.suffix != ".md":
            continue
        if not REPORT_FILENAME_PATTERN.match(p.name):
            errors.append(
                (
                    p,
                    "report file name does not match pattern <repo>_YYYY-MM-DD.md or <repo>_<tag>.md",
                )
            )
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:  # pylint: disable=broad-exception-caught
            errors.append((p, f"failed to read file: {e}"))
            continue
        if "\0" in text:
            errors.append((p, "file contains NUL bytes"))
            continue
        if "#" not in text:
            errors.append((p, "file has no Markdown heading"))
            continue
        # Working companions: light checks only (no four-category requirement).
        if _is_working_report(p.name):
            continue
        if _is_tag_publishable_report(p.name):
            tag_publishable.append(p)
            for heading in WORKING_ONLY_HEADINGS:
                # Match heading at line start (allow trailing text after title).
                if re.search(rf"(?m)^{re.escape(heading)}(?:\s|$)", text):
                    errors.append(
                        (
                            p,
                            (
                                f"publishable tag report must not contain working-only heading "
                                f"'{heading}'; move it to the matching *.working.md companion"
                            ),
                        )
                    )
        # Require all four category sections (Czech or English).
        has_czech = all(s in text for s in REQUIRED_SECTIONS_CZECH)
        has_english = all(s in text for s in REQUIRED_SECTIONS_ENGLISH)
        if not (has_czech or has_english):
            missing_cz = [s for s in REQUIRED_SECTIONS_CZECH if s not in text]
            missing_en = [s for s in REQUIRED_SECTIONS_ENGLISH if s not in text]
            errors.append(
                (
                    p,
                    (
                        "missing required section headers: use either all four Czech headers "
                        "(Zásadní změny, Nové funkce, Opravy chyb, Ostatní) or all four English "
                        "(Breaking changes, Features, Bug fixes, Other). "
                        f"Missing Czech: {missing_cz}; Missing English: {missing_en}."
                    ),
                )
            )
            continue
        # Title language must match the section language (Czech reports keep a Czech title).
        sections = REQUIRED_SECTIONS_CZECH if has_czech else REQUIRED_SECTIONS_ENGLISH
        expected_title = REQUIRED_TITLE_CZECH if has_czech else REQUIRED_TITLE_ENGLISH
        title_line = next((ln for ln in text.splitlines() if ln.startswith("# ")), None)
        if title_line is not None and not title_line.startswith(expected_title):
            errors.append(
                (
                    p,
                    (
                        f"report title must match the section language: expected a title starting "
                        f"'{expected_title}', found '{title_line}'"
                    ),
                )
            )
        # Require each section to be populated: either explicit empty marker or at least one list item.
        empty_markers = ("_(žádné)_", "_(none)_")
        for section_header in sections:
            idx = text.find(section_header)
            start = idx + len(section_header)
            next_h2 = text.find("\n## ", start)
            block = text[start : next_h2 if next_h2 != -1 else len(text)]
            block_stripped = block.strip()
            has_empty = any(m in block for m in empty_markers)
            has_bullet = bool(re.search(r"^\s*-\s+", block_stripped, re.MULTILINE))
            if not (has_empty or has_bullet):
                errors.append(
                    (
                        p,
                        (
                            f"section '{section_header}' must be populated: use "
                            "_(žádné)_/_(none)_ or at least one list item (- ...)"
                        ),
                    )
                )
    # Tag-based publishable reports require a matching *.working.md companion.
    for p in tag_publishable:
        companion = p.with_name(p.name[: -len(".md")] + WORKING_REPORT_SUFFIX)
        if not companion.exists():
            errors.append(
                (
                    p,
                    (f"tag-based publishable report requires working companion {companion.name}"),
                )
            )
    return errors


def _count_bullets_in_report(text: str) -> int:
    """Count list items (lines starting with - ) in report body; excludes empty markers."""
    count = 0
    for m in re.finditer(r"^\s*-\s+(.+)$", text, re.MULTILINE):
        rest = m.group(1).strip()
        if rest in ("_(žádné)_", "_(none)_"):
            continue
        count += 1
    return count


def validate_reports_git_sanity(root: Path, skip_reports: bool) -> list[tuple[Path, str]]:
    """Run the optional sanity check: for date-based reports, if there were commits that day, at least one note."""
    errors: list[tuple[Path, str]] = []
    if skip_reports:
        return errors
    reports_dir = root / ".agents" / "reports" / "release-notes"
    if not reports_dir.exists():
        return errors
    for p in sorted(reports_dir.iterdir()):
        if p.suffix != ".md" or p.name in ("README.md", "README_en.md"):
            continue
        match = DATE_REPORT_PATTERN.match(p.name)
        if not match:
            continue
        date_str = match.group(1)
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        bullet_count = _count_bullets_in_report(text)
        since = f"{date_str} 00:00:00"
        # --until is exclusive; use next day 00:00 to include full day.
        try:
            d = date(int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10]))
            next_d = d + timedelta(days=1)
            until = f"{next_d.isoformat()} 00:00:00"
        except (ValueError, IndexError):
            continue
        try:
            out = run_exact(
                ["git", "rev-list", "--count", f"--since={since}", f"--until={until}", "HEAD"],
                cwd=root,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        if out.returncode != 0:
            continue
        try:
            commit_count = int(out.stdout.strip())
        except ValueError:
            continue
        if commit_count > 0 and bullet_count == 0:
            errors.append(
                (
                    p,
                    (
                        "report has no notes but git log shows "
                        f"{commit_count} commit(s) for this day; expected at least one note"
                    ),
                )
            )
    return errors


def validate_report_copy_yml(root: Path) -> list[tuple[Path, str]]:
    """Step 6: if *_release.yml exists in reports, validate structure."""
    errors: list[tuple[Path, str]] = []
    reports_dir = root / ".agents" / "reports" / "release-notes"
    if not reports_dir.exists():
        return errors
    for p in sorted(reports_dir.glob("*_release.yml")):
        try:
            data = _load_yaml(p)
        except Exception as e:  # pylint: disable=broad-exception-caught
            errors.append((p, f"invalid YAML: {e}"))
            continue
        if not isinstance(data, dict):
            errors.append((p, "root must be a mapping"))
            continue
        changelog = data.get("changelog")
        if not isinstance(changelog, dict):
            errors.append((p, "missing or invalid 'changelog' mapping"))
            continue
        categories = changelog.get("categories")
        if not isinstance(categories, list) or len(categories) == 0:
            errors.append((p, "'changelog.categories' must be a non-empty list"))
            continue
        for i, cat in enumerate(categories):
            if not isinstance(cat, dict):
                errors.append((p, f"changelog.categories[{i}] must be a mapping"))
                continue
            if not isinstance(cat.get("title"), str) or not str(cat.get("title", "")).strip():
                errors.append((p, f"changelog.categories[{i}] must have non-empty 'title'"))
            labels = cat.get("labels")
            if not isinstance(labels, list):
                errors.append((p, f"changelog.categories[{i}] must have 'labels' list"))
            elif len(labels) == 0:
                errors.append((p, f"changelog.categories[{i}] must have at least one label (populated, not empty)"))
    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for release config and report layout validation."""
    parser = argparse.ArgumentParser(
        description="Validate .github/release.yml and release-notes report layout (no agent/API)."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repo root (default: derived from script location).",
    )
    parser.add_argument(
        "--release-config",
        type=Path,
        default=None,
        help="Release config to validate instead of .github/release.yml; relative to --root, or absolute.",
    )
    parser.add_argument(
        "--skip-reports",
        action="store_true",
        help="Validate only the selected release config and report copy YAML; skip report dir and .md checks.",
    )
    parser.add_argument(
        "--check-git-count",
        action="store_true",
        help="Sanity check: for date-based reports, if there were commits that day, require at least one note.",
    )
    args = parser.parse_args(argv)
    root = (args.root or _default_root()).resolve()

    all_errors: list[tuple[Path, str]] = []
    all_errors.extend(validate_release_yml(root, args.release_config))
    all_errors.extend(validate_report_copy_yml(root))
    all_errors.extend(validate_reports_dir(root, args.skip_reports))
    if args.check_git_count:
        all_errors.extend(validate_reports_git_sanity(root, args.skip_reports))

    if not all_errors:
        print("Release config and report layout passed validation.")
        return 0

    for path, msg in all_errors:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        log_error(f"{rel}: {msg}")
    return 1


if __name__ == "__main__":  # pragma: no cover -- exercised through main(argv)
    raise SystemExit(main())
