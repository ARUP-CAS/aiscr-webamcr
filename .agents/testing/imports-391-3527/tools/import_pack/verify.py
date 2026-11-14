"""Nezávislé aserce hodnot, změn, historie a obsahu repozitáře."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET


def selected(snapshot, table, selector):
    """Vybere přesně deklarované záznamy; chybějící tabulka je chybějící důkaz."""
    if table not in snapshot:
        raise ValueError(f"Missing table evidence: {table}")
    return [row for row in snapshot[table] if all(row.get(key) == value for key, value in selector.items())]


def expected_value(value, snapshot):
    """Doplní FK pouze ze skutečného exportu jednoznačně určeného rodiče."""
    if isinstance(value, dict) and "$lookup" in value:
        lookup = value["$lookup"]
        rows = selected(snapshot, lookup["table"], lookup["selector"])
        if len(rows) != 1:
            raise ValueError("Expected FK parent is not unique")
        return rows[0][lookup.get("field", "id")]
    return value


def assertions(before, after, checks):
    """Porovná očekávané změny a neovlivněné záznamy bez samopotvrzení reportem."""
    results = []
    for check in checks:
        kind, table = check["kind"], check["table"]
        selector = {k: expected_value(v, after) for k, v in check.get("selector", {}).items()}
        old, new = selected(before, table, selector), selected(after, table, selector)
        if kind == "count":
            passed = len(new) == check["value"]
        elif kind == "count-delta":
            passed = len(new) - len(old) == check["value"]
        elif kind == "unchanged":
            passed = sorted(map(lambda x: json.dumps(x, sort_keys=True), old)) == sorted(
                map(lambda x: json.dumps(x, sort_keys=True), new)
            )
        elif kind == "values":
            passed = len(new) == check.get("count", 1) and all(
                all(row.get(key) == expected_value(value, after) for key, value in check["values"].items())
                for row in new
            )
        elif kind == "preserve-omitted":
            changed = set(check["changed_fields"])
            passed = len(old) == len(new) == 1 and {k: v for k, v in old[0].items() if k not in changed} == {
                k: v for k, v in new[0].items() if k not in changed
            }
        else:
            raise ValueError(f"Unknown assertion kind: {kind}")
        results.append({"id": check["id"], "passed": passed, "kind": kind})
    return results


def resource_check(response, expected):
    """Zkontroluje přímou odpověď, nikoli pouze indexované vyhledávání."""
    if response["status"] != expected["status"]:
        return False
    if expected["status"] != 200:
        return True
    body = response["body"]
    if "sha256" in expected and hashlib.sha256(body).hexdigest() != expected["sha256"]:
        return False
    if "sha512" in expected and hashlib.sha512(body).hexdigest() != expected["sha512"]:
        return False
    if "xml_contains" in expected or "xml_assertions" in expected:
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return False
    if "xml_contains" in expected:
        for name, value in expected["xml_contains"].items():
            if value not in [element.text for element in root.iter() if element.tag.split("}")[-1] == name]:
                return False
    if "xml_assertions" in expected:
        for check in expected["xml_assertions"]:
            found = [node.text for node in root.findall(check["xpath"], check.get("namespaces", {}))]
            wanted = check["texts"]
            if (found if check.get("ordered") else sorted(found, key=str)) != (
                wanted if check.get("ordered") else sorted(wanted, key=str)
            ):
                return False
    return True


def record_urls(ident):
    import re
    from urllib.parse import urlencode

    if not re.fullmatch(r"[A-Za-z0-9-]+", ident):
        raise ValueError("Unsafe record identifier")
    base = "https://fedora-test.aiscr.cz/rest/AMCR/record/" + ident
    return {
        "container": base,
        "metadata": base + "/metadata",
        "versions": base + "/metadata/fcr:versions",
        "search": "https://fedora-test.aiscr.cz/rest/fcr:search?"
        + urlencode({"condition": "fedora_id=" + base + "/*", "offset": 0, "max_results": 100, "format": "json"}),
    }


def fedora_urls(path):
    """Vytvoří credential-free odkazy ze skutečné cesty souboru."""
    import re
    from urllib.parse import urlencode

    path = "/" + path.lstrip("/")
    if not re.fullmatch(r"/rest/AMCR/record/[A-Za-z0-9-]+/file/[a-fA-F0-9-]{36}", path):
        raise ValueError("Not a verified file container path")
    base = "https://fedora-test.aiscr.cz" + path
    record = base.split("/file/")[0]
    return {
        "file": base,
        "orig": base + "/orig",
        "orig_versions": base + "/orig/fcr:versions",
        "metadata": record + "/metadata",
        "metadata_versions": record + "/metadata/fcr:versions",
        "distribution": base + "/atr/alto-xml",
        "paradata": base + "/paradata/atr/alto-xml",
        "search": "https://fedora-test.aiscr.cz/rest/fcr:search?"
        + urlencode({"condition": "fedora_id=" + record + "/*", "max_results": 100, "offset": 0, "format": "json"}),
    }
