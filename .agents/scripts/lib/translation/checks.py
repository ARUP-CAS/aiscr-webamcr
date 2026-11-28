# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

"""Catalogue verification shared by the PO and ngx command paths.

Checks preserve evidence limits: source-dependent checks are unverified when no source was supplied, rather than
silently passing.

Contract: review/translation-revision
Class: library
Exit codes: Library with no entrypoint.
"""

from __future__ import annotations

import re
from collections import Counter
from html.parser import HTMLParser

from . import ngx_catalogue, po_catalogue

PLACEHOLDER = re.compile(
    r"\{\{\s*(\w+)\s*\}\}|(?<!\{)\{(\w+)(?:![rsa])?(?::[^{}]+)?\}(?!\})"
    r"|%\((\w+)\)[#0 +\-]*\d*(?:\.\d+)?[diouxXeEfFgGcrsa]"
)


def placeholders(text: str | None) -> set[str]:
    """Collect named Angular, brace-format and percent-format placeholders."""
    return {next(name for name in match if name) for match in PLACEHOLDER.findall(text or "")}


class _Markup(HTMLParser):
    """Collect structure and link destinations while ignoring translated text."""

    def __init__(self):
        super().__init__()
        self.items = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        targets = tuple(sorted((key, value) for key, value in attrs if key in ("href", "src")))
        self.items.append(("start", tag, targets, tuple(self.stack)))
        if tag not in (
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        ):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        self.items.append(("end", tag, tuple(self.stack)))
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()


def markup(text: str) -> Counter:
    """Return HTML structure and Markdown link targets, independent of word order."""
    parser = _Markup()
    parser.feed(text)
    links = [("link", target, ()) for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", text)]
    return Counter(parser.items + links)


def catalogue(path: str, format_name: str) -> tuple[dict, list[dict]]:
    """Read texts and format-specific completeness findings; compile without writing."""
    if format_name not in ("po", "ngx"):
        raise ValueError("unsupported catalogue format; use an established native parser and hand over portable checks")
    if format_name == "ngx":
        obj, _ = ngx_catalogue.load(path)
        texts = ngx_catalogue.flatten(obj)
        if any(not isinstance(value, str) for value in texts.values()):
            raise ngx_catalogue.CatalogueError("catalogue leaves must be strings")
        problems = [{"key": key, "kind": "empty"} for key, value in texts.items() if not value.strip()]
        return texts, problems
    po, _ = po_catalogue.load(path)
    texts, problems = {}, []
    for entry in po:
        if not entry.msgid or entry.obsolete:
            continue
        if entry.msgctxt or entry.msgid in texts:
            raise po_catalogue.CatalogueError(
                "context-qualified or duplicate gettext keys require a native context-aware adapter"
            )
        values = list(entry.msgstr_plural.values()) if entry.msgid_plural else [entry.msgstr]
        texts[entry.msgid] = values
        if not values or any(not value.strip() for value in values):
            problems.append({"key": entry.msgid, "kind": "empty"})
        if "fuzzy" in entry.flags:
            problems.append({"key": entry.msgid, "kind": "fuzzy"})
    po.to_binary()
    return texts, problems


def _variants(value):
    return (value or [""]) if isinstance(value, list) else [value]


def _text_problems(key, czech, english, evidence):
    """Compare the rendered text contracts for a single key."""
    names_cs = set().union(*(placeholders(text) for text in czech))
    names_en = set().union(*(placeholders(text) for text in english))
    problems = []
    if names_cs != names_en:
        problems.append({"key": key, "kind": "placeholder-parity"})
    if any(markup(text) != markup(czech[0]) for text in czech[1:] + english):
        problems.append({"key": key, "kind": "markup-parity"})
    unknown = (names_cs | names_en) - set(evidence.get("params", {}).get(key, []))
    if evidence.get("source") and unknown:
        problems.append({"key": key, "kind": "unknown-placeholder", "names": sorted(unknown)})
    return problems


def _scoped_integrity(loaded: dict, keys: set) -> tuple:
    """Separate selected catalogue defects from pre-existing outside-scope findings."""
    problems, outside, uncertain = [], [], []
    for language, (_, rows) in loaded.items():
        for row in rows:
            (problems if row["key"] in keys else outside).append({**row, "language": language})
    for key in sorted(keys):
        variants = []
        for language, (texts, _) in loaded.items():
            if key not in texts:
                problems.append({"key": key, "kind": "missing-translation", "language": language})
                continue
            values = _variants(texts[key])
            variants.extend(values)
            if any(unsupported_placeholders(v) for v in values):
                uncertain.append(f"{key}: unsupported placeholder grammar")
        if variants:
            findings = text_contract_problems(key, variants)
            if any(unsupported_placeholders(v) for v in variants):
                findings = [row for row in findings if row["kind"] != "placeholder-parity"]
            problems.extend(findings)
    return problems, outside, uncertain


def _source_layer(loaded: dict, keys: set, evidence: dict, uncertain: list) -> dict:
    """Evaluate explicitly supplied affected-caller evidence and preserve its limits."""
    source_problems = []
    for site in evidence.get("sites", []):
        if site["key"] not in keys:
            continue
        for language, (texts, _) in loaded.items():
            if site["key"] not in texts:
                source_problems.append({"key": site["key"], "kind": "unresolved-reference", "language": language})
            else:
                required = set().union(*(placeholders(v) for v in _variants(texts[site["key"]])))
                if required - set(site.get("params", [])):
                    source_problems.append({"key": site["key"], "kind": "call-parameters", "language": language})
    source_known = bool(
        evidence.get("source_reviewed")
        and evidence.get("source_method")
        and keys <= set(evidence.get("source_keys", []))
        and not evidence.get("source_limits")
        and not uncertain
    )
    return {
        "status": "failed" if source_problems else "passed" if source_known else "unverified",
        "method": evidence.get("source_method", "affected caller inspection not supplied"),
        "problems": source_problems,
        "unverified": evidence.get("source_limits", []) + uncertain,
    }


# Removal-aware, so the catalogue check carries more local state than its older form.
# pylint: disable-next=too-many-locals
def verify_languages(
    paths: dict, format_name: str, selected: list, evidence: dict | None = None, removals: list | None = None
) -> dict:
    """Check scoped catalogue integrity independently of source/build availability.

    Evidence is explicit caller inspection or native-check results, never an inferred guarantee from a build command.
    All catalogues are parsed; unrelated text findings are reported separately. Unsupported placeholder syntax remains
    unverified. Each removal key is required to be absent from every language.
    """
    evidence = evidence or {}
    loaded = {language: catalogue(path, format_name) for language, path in paths.items()}
    keys = set(selected)
    removal_keys = set(removals or [])
    problems, outside, uncertain = _scoped_integrity(loaded, keys)
    for key in sorted(removal_keys):
        for language, (texts, _) in loaded.items():
            if key in texts:
                problems.append({"key": key, "kind": "removal-not-applied", "language": language})
    source = _source_layer(loaded, keys, evidence, uncertain)
    native = []
    for item in evidence.get("native_checks", []):
        if item.get("status") not in ("passed", "failed", "unverified") or not item.get("method"):
            raise ValueError("native checks require method, coverage and passed/failed/unverified status")
        if not isinstance(item.get("coverage"), list) or not item["coverage"]:
            raise ValueError("native checks require explicit coverage")
        native.append(item)
    layers = {
        "catalogue": {
            "status": "failed" if problems else "unverified" if uncertain else "passed",
            "method": "catalogue parsing, scoped completeness, named placeholders and markup",
            "problems": problems,
            "unverified": uncertain,
        },
        "source": source,
        "build_rendering": {"status": "unverified", "method": "no complete build and rendering evidence"},
    }
    for layer in ("build", "rendering"):
        covering = [item for item in native if layer in item["coverage"]]
        layers[layer] = {
            "status": "failed"
            if any(i["status"] == "failed" for i in covering)
            else "passed"
            if any(i["status"] == "passed" for i in covering)
            else "unverified",
            "method": [i["method"] for i in covering],
        }
    layers["build_rendering"]["status"] = (
        "passed"
        if all(layers[name]["status"] == "passed" for name in ("build", "rendering"))
        else "failed"
        if any(layers[name]["status"] == "failed" for name in ("build", "rendering"))
        else "unverified"
    )
    for layer in layers.values():
        layer["scope"] = sorted(keys | removal_keys)
    return {
        "scope": sorted(keys | removal_keys),
        "layers": layers,
        "native_checks": native,
        "outside_scope": outside,
        "fully_verified": all(layer["status"] == "passed" for layer in layers.values()),
    }


def unsupported_placeholders(text: str | None) -> bool:
    """Keep positional, compound and unfamiliar format fields explicitly unverified.

    Removing supported named forms leaves positional percent widths/precision, dotted or indexed brace fields, nested
    format specs and ICU clauses visible. Escaped percent signs are literals, including an even-length percent run.
    """
    text = text or ""
    remaining = PLACEHOLDER.sub("", text.replace("%%", ""))
    return bool(
        re.search(r"%\(|%[#0 +\-]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]?[diouxXeEfFgGcrsa]", remaining)
        or re.search(r"\{[^{}]*\}", remaining)
        or re.search(r"(?<!\{)\{\d+(?:![rsa])?(?::[^{}]*)?\}(?!\})", text)
    )


def text_contract_problems(key: str, texts: list[str]) -> list[dict]:
    """Compare named placeholders and markup for a proposed multilingual entry."""
    findings = [_text_problems(key, texts[:1], [value], {}) for value in texts[1:] or texts[:1]]
    return [{"key": key, "kind": kind} for kind in sorted({row["kind"] for rows in findings for row in rows})]
