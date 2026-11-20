"""Exact history/control and direct repository checks, independent of counts."""

from .common import digest
from .verify import resource_check


def extract_versions(body):
    """Read Fedora memento URI identifiers from a retained version collection."""
    import re

    text = body.decode("utf-8")
    identifiers = sorted(set(re.findall(r"fcr:versions/([0-9TZ.-]{8,})", text)))
    if not identifiers and not any(name in text for name in ("TimeMap", "hasMemento")):
        raise ValueError("Unrecognized version collection; retain it for inspection")
    return identifiers


def read_responses(root, index):
    """Validate index-to-original hashes before parsing or comparing bodies."""
    from .common import inside

    responses = {}
    for item in index["resources"]:
        data = dict(item)
        if data.get("body_path"):
            body = inside(root, data["body_path"]).read_bytes()
            if data.get("sha256") and digest(body) != data["sha256"]:
                raise ValueError("Direct resource body changed")
            data["body"] = body
        else:
            data["body"] = b""
        if data["url"].endswith("/fcr:versions") and data["status"] == 200:
            data["version_ids"] = extract_versions(data["body"])
        elif data["url"].endswith("/fcr:versions") and data["status"] in (404, 410):
            data["version_ids"] = []
        responses[data["url"]] = data
    return responses


def check_effects(root, before, after, fedora_before, fedora_after, expected):
    """Check explicitly authored target sets; missing plans remain blocked."""
    results = []
    results.extend(orphan_checks(before, after))
    if "history" not in expected or "resources" not in expected:
        raise ValueError("Independent history/resource expectations are required, including empty history lists")
    wanted = expected["history"]
    checked = history(
        before["historie"],
        after["historie"],
        wanted["entries"],
        wanted.get("controls", []),
        wanted.get("deleted_owners", []),
    )
    results.append(
        {
            "id": "history",
            "category": "history",
            "state": "passed" if checked["passed"] else "failed",
            "details": checked,
        }
    )
    old, new = read_responses(root, fedora_before), read_responses(root, fedora_after)
    results.extend(repository(expected["resources"], new))
    if expected.get("unchanged_resources"):
        results.append(
            {
                "id": "unchanged-resources",
                "category": "controls",
                "state": "passed" if unchanged_resources(old, new, expected["unchanged_resources"]) else "failed",
            }
        )
    if expected.get("db_unchanged"):
        results.append(
            {
                "id": "db-unchanged",
                "state": (
                    "passed"
                    if {k: v for k, v in before.items() if not k.startswith("_")}
                    == {k: v for k, v in after.items() if not k.startswith("_")}
                    else "failed"
                ),
            }
        )
    return results


def orphan_checks(before, after):
    """Detect newly orphaned/shared links even when aggregate row counts match."""
    results = []
    for table in ("historie_vazby", "soubor_vazby", "komponenta_vazby"):
        item = {"id": "orphans." + table, "category": "orphans", "state": "blocked"}
        if table in before and table in after and all("_owner_count" in row for row in before[table] + after[table]):
            old = {r["id"] for r in before[table] if r["_owner_count"] != 1}
            new = {r["id"] for r in after[table] if r["_owner_count"] != 1}
            item.update(state="passed" if not new - old else "failed", newly_invalid=sorted(new - old))
        else:
            item["reason"] = "Missing exact link-owner evidence; use the scoped after query with baseline watermarks"
        results.append(item)
    return results


def history(before, after, expected, controls=(), deleted_owners=()):
    """Compare all new history entries as a multiset, including actor and note.

    expected entries have vazba/uzivatel/typ_zmeny/poznamka; one per deduplicated
    target. The agent resolves target link IDs from actual before/after owners.
    """
    old_ids = {r["id"] for r in before}
    added = [r for r in after if r["id"] not in old_ids]
    keys = ("vazba", "uzivatel", "typ_zmeny", "poznamka")
    if any("datum_zmeny" in r for r in expected):
        keys += ("datum_zmeny",)
    from collections import Counter

    actual = Counter(tuple(r.get(k) for k in keys) for r in added)
    wanted = Counter(tuple(r.get(k) for k in keys) for r in expected)
    old_by_id, new_by_id = {r["id"]: r for r in before}, {r["id"]: r for r in after}
    surviving = {i: r for i, r in old_by_id.items() if r.get("vazba") not in deleted_owners}
    return {
        "passed": actual == wanted
        and all(new_by_id.get(i) == r for i, r in surviving.items())
        and not any(r.get("vazba") in deleted_owners for r in after)
        and not any(r.get("vazba") in controls for r in added),
        "expected_entries": sum(wanted.values()),
        "actual_entries": len(added),
        "duplicates": [list(k) for k, n in actual.items() if n > wanted[k]],
    }


def repository(expected, responses):
    """Require every direct resource; index search is only discovery evidence."""
    results = []
    for resource in expected:
        response = responses.get(resource["url"])
        okay = bool(response) and resource_check(response, resource)
        if response and resource.get("mimetype"):
            okay &= (response.get("headers", {}).get("Content-Type") or "").split(";", 1)[0] == resource["mimetype"]
        if response and resource.get("filename"):
            okay &= resource["filename"] in (response.get("headers", {}).get("Content-Disposition") or "")
        if "versions_before" in resource:
            okay &= response is not None and response.get("version_ids") is not None
            if response and response.get("version_ids") is not None:
                added = set(response["version_ids"]) - set(resource["versions_before"])
                okay &= len(added) == resource["expected_new_versions"]
        category = resource.get("category") or (
            "metadata" if "/metadata" in resource["url"] and "/file/" not in resource["url"] else "binaries"
        )
        results.append(
            {
                "id": resource["url"],
                "identity": resource.get("identity", resource["url"]),
                "category": category,
                "semantic_checked": bool(resource.get("xml_assertions") or resource.get("xml_contains")),
                "versions_checked": "versions_before" in resource,
                "state": "passed" if okay else "failed",
            }
        )
    return results


def unchanged_resources(before, after, urls):
    """Paradata-only cases require unchanged domain XML/history and control bytes."""
    return all(
        url in before
        and url in after
        and before[url]["status"] == after[url]["status"]
        and digest(before[url]["body"]) == digest(after[url]["body"])
        for url in urls
    )
