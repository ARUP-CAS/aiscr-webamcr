"""Field-level probes with one intended mutation and traceable errors."""

from .datasets import row_for


def probes(source, ns, refs):
    result, index = [], 8000
    for mapper in source["mappers"]:
        if mapper["csv"] in ("distribution", "paradata"):
            continue
        for field, meta in mapper["columns"].items():
            info = (
                source["models"]
                .get(meta.get("model", mapper["model"]), {})
                .get("fields", {})
                .get(meta.get("model_field", field), {})
            )
            variants = []
            if (
                info
                and not info.get("null")
                and "default" not in info
                and field != "id"
                and row_for(mapper, ns, 3, refs).get(field) not in ("", None)
            ):
                variants.append(("missing-required", ""))
            if meta.get("kind") == "lookup":
                variants.append(("missing-lookup", "MISSING-REFERENCE-" + str(index)))
            if info.get("max_length"):
                variants.append(("overflow", "X" * (info["max_length"] + 1)))
            if info.get("type") in (
                "BooleanField",
                "IntegerField",
                "SmallIntegerField",
                "DateField",
                "DateTimeField",
                "TimeField",
            ):
                variants.append(("invalid-type", "INVALID-TYPE"))
            for variant, invalid in variants:
                index += 1
                row = row_for(mapper, ns, index, refs)
                base = row_for(mapper, ns, 3, refs)
                for key in row:
                    if key not in ("ident_cely", "id"):
                        row[key] = base[key]
                row[field] = invalid
                result.append(
                    {
                        "id": f"{mapper['csv']}.field.{field}.{variant}",
                        "class": mapper["csv"],
                        "variant": variant,
                        "field": field,
                        "row": row,
                        "index": index,
                        "expected": "row rejection naming this field/lookup/limit; an unrelated earlier error is not acceptance",
                    }
                )
    return result


def error_checks(report, expectations):
    """Require the intended row AND diagnostic; no rejection-count shortcut."""
    import re

    result = []
    for check in expectations:
        candidates = [row for row in report["Import"] if str(row.get("CSV", "")).removesuffix(".csv") == check["class"]]
        if check.get("csv_row"):
            ordinal = int(check["csv_row"]) - 1
            matched = candidates[ordinal : ordinal + 1] if ordinal >= 0 else []
        else:
            matched = [
                row for row in candidates if str(row.get("ID v CSV", row.get("ID in CSV"))) == str(check["import_id"])
            ]
        regex = check.get("diagnostic_regex")
        column = check.get("diagnostic_column")
        okay = (
            bool(regex)
            and bool(column)
            and len(matched) == 1
            and column in matched[0]
            and re.search(regex, str(matched[0][column]), re.IGNORECASE) is not None
        )
        result.append(
            {
                "id": check["id"],
                "state": "passed" if okay else "blocked",
                "reason": (
                    "Missing intended diagnostic: isolate and repeat this probe after repairing any earlier error"
                    if not okay
                    else "intended row and error matched"
                ),
            }
        )
    return result
