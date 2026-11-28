# SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
# SPDX-License-Identifier: MIT
# delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00

"""ngx-translate JSON catalogue adapter for the translation-revision engine.

A catalogue (for example ``src/assets/i18n/{en,de}.json``) is nested JSON: two-space indent, ``ensure_ascii=False``, LF
or CRLF, keys joined by dots. A node name may itself contain a dot (a dotted leaf), so a key is resolved by greedy
longest-match from the current node rather than by a plain split.

Scoped writes detect repository indentation, escaping, spacing and line endings and refuse bytes they cannot reproduce.
Legacy specialised operations retain their established rendering. Insert and merge keep declaration order, and a merge
whose values differ is refused rather than silently overwriting one of them - the failure the session hit when a nested
merge dropped values.

Contract: review/translation-revision
Class: library
Exit codes: Library with no entrypoint; raises CatalogueError on a refusal.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

INDENT = 2

__all__ = [
    "CatalogueError",
    "assert_roundtrip",
    "dominant_eol",
    "dump",
    "flatten",
    "get",
    "insert_after",
    "load",
    "put_after",
    "rename_in",
    "resolve",
    "set_value",
    "remove",
    "write",
]


class CatalogueError(Exception):
    """Raised when a catalogue cannot be read, resolved, round-tripped or merged."""


def render_like(path: str | Path, obj: dict) -> bytes:
    """Preserve the source's indentation, escaping, spacing, EOL and final newline."""
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8")
    matched = re.search(r'\n([ \t]+)"', text)
    indent = matched[1] if matched else None
    colon = ": " if re.search(r'": +', text) else ":"
    comma = ", " if not indent and ", " in text else ","
    rendered = json.dumps(
        obj, ensure_ascii=bool(re.search(r"\\u[0-9a-fA-F]{4}", text)), indent=indent, separators=(comma, colon)
    )
    if text.endswith("\n"):
        rendered += "\n"
    return rendered.replace("\n", dominant_eol(raw)).encode("utf-8")


def assert_preserving(path: str | Path) -> tuple[dict, str]:
    """Load only when the detected formatting profile reproduces all original bytes."""
    obj, eol = load(path)
    if render_like(path, obj) != Path(path).read_bytes():
        raise CatalogueError(f"{path} does not round-trip with its formatting profile")
    return obj, eol


def flatten(obj: dict, prefix: str = "") -> dict:
    """Return dotted leaves in declaration order, refusing ambiguous physical paths."""
    out: dict = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            leaves = flatten(value, f"{prefix}.{key}" if prefix else key)
            collisions = out.keys() & leaves.keys()
            if collisions:
                raise CatalogueError(f"ambiguous dotted catalogue paths: {', '.join(sorted(collisions))}")
            out.update(leaves)
    else:
        out[prefix] = obj
    return out


def dominant_eol(raw: bytes) -> str:
    """Return the file's dominant line ending, CRLF unless LF-only outnumbers CRLF."""
    crlf = raw.count(b"\r\n")
    lf_only = raw.count(b"\n") - crlf
    return "\r\n" if crlf and crlf >= lf_only else "\n"


def dump(obj: dict, eol: str = "\n") -> bytes:
    """Render the object in the catalogue's canonical form, using *eol*."""
    text = json.dumps(obj, ensure_ascii=False, indent=INDENT)
    if eol == "\r\n":
        text = text.replace("\n", "\r\n")
    return (text + eol).encode("utf-8")


def load(path: str | Path) -> tuple[dict, str]:
    """Read a catalogue and its dominant line ending."""
    raw = Path(path).read_bytes()
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CatalogueError(f"cannot read catalogue {path}: {exc}") from exc
    if not isinstance(obj, dict):
        raise CatalogueError(f"{path} is not a nested JSON object")
    return obj, dominant_eol(raw)


def assert_roundtrip(path: str | Path) -> str:
    """Refuse a source the adapter cannot reproduce byte for byte; return its EOL."""
    raw = Path(path).read_bytes()
    obj, eol = load(path)
    if dump(obj, eol) != raw:
        raise CatalogueError(f"{path} does not round-trip byte for byte")
    return eol


def write(path: str | Path, obj: dict, eol: str) -> None:
    """Write the object with the given line ending."""
    Path(path).write_bytes(dump(obj, eol))


def resolve(obj: dict, key: str) -> list[str]:
    """Resolve a dotted key to its node path, greedy longest-match per segment.

    A node name may contain dots, so ``card.desc.a.b`` may be ``card`` -> ``desc`` -> ``a`` -> ``b`` or ``card`` ->
    ``desc.a`` -> ``b``; the longest matching node is tried first and a dead end backtracks, which is how the session's
    catalogue mixed flat and nested nodes.
    """
    parts = key.split(".")

    def walk(node, index: int, path: list[str]) -> list[str] | None:
        if index == len(parts):
            return path
        for end in range(len(parts), index, -1):
            candidate = ".".join(parts[index:end])
            if isinstance(node, dict) and candidate in node:
                found = walk(node[candidate], end, path + [candidate])
                if found is not None:
                    return found
        return None

    result = walk(obj, 0, [])
    if result is None:
        raise CatalogueError(f"unresolvable catalogue key: {key}")
    return result


def get(obj: dict, key: str):
    """Return the value at a dotted key."""
    node = obj
    for part in resolve(obj, key):
        node = node[part]
    return node


def set_value(obj: dict, key: str, value, *, refuse_conflict: bool = False) -> None:
    """Update the actual dotted leaf, or insert a new path without losing siblings."""
    try:
        path = resolve(obj, key)
    except CatalogueError:
        path = []
    if path:
        parent = obj
        for part in path[:-1]:
            parent = parent[part]
        if refuse_conflict and parent[path[-1]] != value:
            raise CatalogueError(f"refused: {key} already carries a different value")
        parent[path[-1]] = value
        return
    parts = key.split(".")
    node = obj
    while len(parts) > 1:
        # Existing node names may themselves contain dots.
        size = next((n for n in range(len(parts) - 1, 0, -1) if ".".join(parts[:n]) in node), 1)
        name = ".".join(parts[:size])
        node = node.setdefault(name, {})
        if not isinstance(node, dict):
            raise CatalogueError(f"a leaf is in the way of {key}")
        parts = parts[size:]
    node[parts[0]] = value


def remove(obj: dict, key: str) -> None:
    """Remove one resolved leaf, pruning only ancestors made empty by that removal."""
    path = resolve(obj, key)
    parents = [obj]
    for part in path[:-1]:
        parents.append(parents[-1][part])
    del parents[-1][path[-1]]
    for index in range(len(path) - 2, -1, -1):
        if parents[index + 1]:
            break
        del parents[index][path[index]]


def insert_after(parent: dict, after: str, key: str, value) -> None:
    """Insert *key* immediately after *after* in *parent*, preserving order."""
    items = list(parent.items())
    index = next((i for i, (name, _) in enumerate(items) if name == after), len(items) - 1)
    items.insert(index + 1, (key, value))
    parent.clear()
    parent.update(items)


def rename_in(parent: dict, old_leaf: str, new_leaf: str) -> None:
    """Rename *old_leaf* in place keeping order; a dotted *new_leaf* becomes nested."""
    items = list(parent.items())
    parent.clear()
    for name, value in items:
        if name != old_leaf:
            if name in parent and isinstance(parent[name], dict) and isinstance(value, dict):
                parent[name].update(value)
            else:
                parent[name] = value
            continue
        if "." in new_leaf:
            head, tail = new_leaf.split(".", 1)
            parent.setdefault(head, {})[tail] = value
        else:
            parent[new_leaf] = value


def put_after(parent: dict, after: str, rel: str, value) -> None:
    """Insert or merge *rel* (relative, may be nested) after *after*, refusing a conflict.

    Existing sibling nodes are preserved: only the named leaf is written. A leaf that already carries a different value
    is refused, not overwritten.
    """
    head = rel.split(".")[0]
    if "." in rel:
        if head not in parent:
            insert_after(parent, after, head, {})
        node = parent[head]
        if not isinstance(node, dict):
            raise CatalogueError(f"a leaf is in the way of {rel}")
        for part in rel.split(".")[1:-1]:
            node = node.setdefault(part, {})
            if not isinstance(node, dict):
                raise CatalogueError(f"a leaf is in the way of {rel}")
        leaf = rel.rsplit(".", 1)[1]
        if leaf in node and node[leaf] != value:
            raise CatalogueError(f"refused: {rel} already carries a different value")
        node[leaf] = value
    elif head in parent:
        if parent[head] != value:
            raise CatalogueError(f"refused: {head} already carries a different value")
    else:
        insert_after(parent, after, head, value)
