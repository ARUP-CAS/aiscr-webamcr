#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: 083eb1bc1a0c628b2d6d48b806b6568be3f67ac2 2026-11-07T12:31:37+01:00

"""Shared secret-redacting reader for configuration surfaces.

*Secret and token redaction* in ``agent/security-privacy-ai-usage`` owns the rule that secrets are removed from any AI
context. This module is the **mechanism** for the one path where a wholesale configuration read can place a live key
into an agent context. Redaction is performed by the reading mechanism before content is returned, never left as a
per-caller instruction.

Design rules:

- A key whose name matches a known credential-bearing form has its **value** replaced by a placeholder before the
  content is returned, and the **presence** of the key is still reported, as required by
  ``agent/workspace-safety-config``.
- Redaction applies to every mapping level and to both structured reads and raw-text reads of formats the module does
  not parse.
- Merge-style callers that must preserve values read through their own loaders, not this module; only paths whose
  content can reach an agent context or stdout route through here.
- Known instruction and memory carriers are inventoried **by metadata only**: the module names their paths so reports
  can list them without ever returning their prose. Instruction content remains outside this reader.

Contract: agent/security-privacy-ai-usage
Class: library
Exit codes: none; this module is a library with no entrypoint
"""

from __future__ import annotations

import json
import os
import re
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Tuple

REDACTED_PLACEHOLDER = "<redacted>"

# Credential-bearing key names, matched case-insensitively. A credential word must
# END the key (allowing trailing digits, as in ``token2``): ``api_key``, ``GITHUB_TOKEN``
# and ``oauth_token`` match, while ``model_auto_compact_token_limit`` does not — the
# limit is a setting, not a secret, and redacting it both loses meaning and breaks
# TOML round-tripping. The set is deliberately broad within that anchor: a false
# positive costs a placeholder, a false negative costs the secret that motivated
# this module.
_CREDENTIAL_KEY_RE = re.compile(
    r"(?:^|[_\-\s])(?:api[_\-\s]?key|apikey|token|secret|password|passwd|pwd|"
    r"authorization|auth|bearer|credential|credentials|private[_\-\s]?key|"
    r"access[_\-\s]?key|session[_\-\s]?key|shared[_\-\s]?key|signing[_\-\s]?key)"
    r"\d*$",
    re.IGNORECASE,
)

# Credential-bearing substrings for raw-text redaction of ``key = "value"`` /
# ``"key": "value"`` lines in formats we do not parse structurally.
_TEXT_LINE_RE = re.compile(
    r"^(\s*(?:[\"']?)(?P<key>[A-Za-z0-9_\-\. ]+?)(?:[\"']?)\s*[:=]\s*)(?P<val>\"[^\"]*\"|'[^']*'|[^\s#]+)",
    re.MULTILINE,
)

# Known instruction and memory carriers on a workstation. Metadata only: a
# report may state that these exist; nothing in this module reads their prose.
KNOWN_INSTRUCTION_CARRIERS: Tuple[str, ...] = (
    "~/.codex/memories",
    "~/.codex/history",
    "~/.codex/sessions",
    "~/.codex/goals",
    "~/.codex/threads",
    "~/.claude/CLAUDE.md",
    "~/.claude/projects",
    "~/.claude/todos",
    "~/.claude/shell-snapshots",
    "~/.claude/statsig",
    "~/.gemini/tmp",
    "~/.gemini/collection",
    "~/.cursor/checkpoints",
    "~/.cursor/chat",
    "~/.cursor/globalStorage",
    "~/.config/kilo",
)


def is_credential_key(key: str) -> bool:
    """Return True when a mapping key name matches a known credential-bearing form."""
    return bool(_CREDENTIAL_KEY_RE.search(key))


def redact_mapping(obj: Any) -> Tuple[Any, List[str]]:
    """Deep-copy a structure with credential values replaced; return (copy, redacted keys)."""
    redacted: List[str] = []

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            out: Dict[str, Any] = {}
            for key, value in node.items():
                key_str = str(key)
                if is_credential_key(key_str) and not isinstance(value, (dict, list)):
                    redacted.append(key_str)
                    out[key] = REDACTED_PLACEHOLDER
                else:
                    out[key] = walk(value)
            return out
        if isinstance(node, list):
            return [walk(item) for item in node]
        return node

    return walk(obj), redacted


def redact_text(text: str) -> Tuple[str, List[str]]:
    """Redact credential-bearing ``key = value`` pairs in raw text; return (text, redacted keys)."""
    redacted: List[str] = []

    def replace(match: "re.Match[str]") -> str:
        key = match.group("key").strip()
        if is_credential_key(key):
            redacted.append(key)
            val = match.group("val")
            # Preserve the original quoting so redacted text stays parseable; an
            # unquoted value gets a quoted placeholder, which keeps the line valid
            # TOML/JSON-ish even though the redacted text is a view, never written back.
            if val.startswith(('"', "'")):
                return f"{match.group(1)}{val[0]}{REDACTED_PLACEHOLDER}{val[0]}"
            return f'{match.group(1)}"{REDACTED_PLACEHOLDER}"'
        return match.group(0)

    return _TEXT_LINE_RE.sub(replace, text), redacted


def read_json_redacted(path: Path) -> Tuple[Any, List[str]]:
    """Read a JSON file and return (redacted content, redacted key names)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return redact_mapping(data)


def read_toml_text_redacted(path: Path) -> Tuple[str, List[str]]:
    """Read a TOML file as redacted text (structure-preserving line redaction)."""
    text = path.read_text(encoding="utf-8")
    redacted_text, redacted = redact_text(text)
    # Structural sanity: the redacted text must still parse, which is also what
    # keeps the redaction faithful — the placeholder replaces the value inside
    # the original quoting rather than breaking the line's shape.
    tomllib.loads(redacted_text)
    return redacted_text, redacted


def instruction_carrier_metadata(home: Path | None = None) -> List[Dict[str, Any]]:
    """Return metadata for known instruction/memory carriers; never their content.

    Each entry carries the resolved path, whether it exists, and its size. A report uses this to name carriers by
    metadata only, per the workspace-safety delta: the carriers' prose is never returned.
    """
    base = Path(home) if home is not None else Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or ".")
    entries: List[Dict[str, Any]] = []
    for raw in KNOWN_INSTRUCTION_CARRIERS:
        resolved = base / raw[2:] if raw.startswith("~/") else Path(raw)
        try:
            present = resolved.exists()
            stat = resolved.stat() if present else None
        except OSError:
            present = False
            stat = None
        entries.append(
            {
                "declared_path": raw,
                "resolved_path": str(resolved),
                "present": present,
                "size_bytes": stat.st_size if stat else None,
            }
        )
    return entries
