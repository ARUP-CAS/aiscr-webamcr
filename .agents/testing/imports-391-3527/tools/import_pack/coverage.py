"""Úplnost pokrytí a jednoznačné oddělení přípravy od provedení."""

from .catalog import ARCHIVE_CASES, EFFECTS, RECIPES, SESSION_CASES, VARIANTS
from .common import STATES


def coverage(source):
    """Vytvoří tři operační buňky pro každou třídu a explicitní větve."""
    result = []
    for mapper in source["mappers"]:
        name = mapper["csv"]
        if name not in RECIPES or name not in EFFECTS or name not in VARIANTS:
            raise ValueError(f"Unreviewed class: {name}")
        for operation in ["insert", "update", "delete"]:
            outcome = "reject" if operation == "update" and not mapper["allow_update"] else "apply"
            result.append(
                {
                    "id": f"{name}.{operation}",
                    "class": name,
                    "operation": operation,
                    "outcome": outcome,
                    "variant": "baseline",
                    "state": "prepared",
                    "requirement": (
                        "ARUP-CAS/aiscr-webamcr#3527"
                        if name in ("distribution", "paradata")
                        else "ARUP-CAS/aiscr-webamcr#391"
                    ),
                    "expected": {
                        "domain": outcome,
                        "metadata_targets": EFFECTS[name][0],
                        "history_targets": EFFECTS[name][1],
                        "controls": "unchanged",
                    },
                    "required_evidence": [
                        "input",
                        "db-before",
                        "db-after",
                        "fedora-before",
                        "fedora-after",
                        "report",
                        "human-ux",
                    ],
                }
            )
        for variant in VARIANTS[name]:
            result.append(
                {
                    "id": f"{name}.branch.{variant}",
                    "class": name,
                    "operation": "scenario",
                    "variant": variant,
                    "state": "prepared",
                    "outcome": "scenario-specific",
                    "expected": {"metadata_targets": EFFECTS[name][0], "history_targets": EFFECTS[name][1]},
                    "required_evidence": [
                        "input",
                        "db-before",
                        "db-after",
                        "fedora-before",
                        "fedora-after",
                        "report",
                        "human-ux",
                    ],
                }
            )
    result.extend(
        {
            "id": "session." + case,
            "class": "session",
            "operation": "scenario",
            "variant": case,
            "state": "prepared",
            "outcome": "scenario-specific",
            "expected": {"phase_boundary": case},
            "required_evidence": ["report", "human-ux", "db-before", "db-after", "fedora-before", "fedora-after"],
        }
        for case in SESSION_CASES
    )
    from .negatives import probes

    result.extend(
        {
            "id": "archive." + key,
            "class": "archive",
            "operation": "insert",
            "variant": "archive",
            "state": "prepared",
            "outcome": expected,
            "expected": {"diagnostic": expected},
            "required_evidence": ["input", "report", "db-before", "db-after", "human-ux"],
        }
        for key, expected in ARCHIVE_CASES.items()
    )
    result.extend(
        {
            "id": case["id"],
            "class": case["class"],
            "operation": "insert",
            "variant": case["variant"],
            "state": "prepared",
            "outcome": "reject",
            "expected": {"field": case["field"], "diagnostic": case["expected"]},
            "required_evidence": ["input", "report", "db-before", "db-after", "human-ux"],
        }
        for case in probes(source, "950000", {})
    )
    validate_coverage(source, result)
    return result


def validate_coverage(source, items):
    """Odmítne chybějící, duplicitní a neznámé položky pokrytí."""
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate coverage ID")
    for mapper in source["mappers"]:
        name = mapper["csv"]
        expected = {f"{name}.{op}" for op in ("insert", "update", "delete")}
        expected.update(f"{name}.branch.{variant}" for variant in VARIANTS.get(name, []))
        if not expected.issubset(ids):
            raise ValueError(f"Missing coverage: {sorted(expected - set(ids))}")
    if not {"session." + x for x in SESSION_CASES}.issubset(ids):
        raise ValueError("Session branch coverage is incomplete")
    if not {"archive." + x for x in ARCHIVE_CASES}.issubset(ids):
        raise ValueError("Missing archive coverage")
    from .negatives import probes

    if not {case["id"] for case in probes(source, "950000", {})}.issubset(ids):
        raise ValueError("Missing field boundary coverage")
    for item in items:
        if not item.get("expected") or not item.get("required_evidence"):
            raise ValueError("Coverage has no oracle/evidence contract")


def verdict(items, results, deployment_verified=False):
    """Povolí úplnost pouze s aktuálními důkazy pro všechny povinné kontroly."""
    unknown = set(results) - {item["id"] for item in items}
    if unknown:
        raise ValueError("Results contain unknown coverage IDs")
    states = {}
    for item in items:
        result = results.get(item["id"], {})
        state = result.get("state", "unexecuted")
        if state not in STATES:
            raise ValueError("Unknown result state")
        evidence = result.get("evidence", {})
        if state == "passed" and (
            result.get("mode") != "live" or not all(evidence.get(key) for key in item["required_evidence"])
        ):
            state = "unexecuted"
        if state == "inapplicable" and not result.get("reason"):
            state = "unexecuted"
        states[item["id"]] = state
    return {
        "complete": bool(items) and deployment_verified and all(value == "passed" for value in states.values()),
        "states": states,
    }
