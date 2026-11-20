"""Zdrojově potvrzené vady importéru: mechanická klasifikace spouštěcích řádků a odložení dávek."""

from __future__ import annotations

import ast
import re

from .common import PACK, read_json

DEFINITION = "definitions/known-defects.json"
# Defects decided by the row's own values; a branch case triggering one is moved to a deferred companion.
# ``delete-history-target`` defers the whole batch (no split): its dependants delete what the deferred rows still reference.
ROW_LEVEL_KINDS = (
    "prefixed-key",
    "lookup-format",
    "empty-cell",
    "single-system-geometry",
    "case",
    "delete-history-target",
)
SPLIT_KINDS = ("lookup-format", "empty-cell", "single-system-geometry", "case")
# Kinds that only reject the row itself: harmless (an intended diagnostic) in a batch expected to reject.
REJECTING_KINDS = ("single-system-geometry",)


def case_triggers(coverage_ids, defects):
    """
    Najde pokrytí, které podle definice vady druhu ``case`` vadu spouští.

    Vada druhu ``case`` závisí na stavu databáze (např. změna rodiče, který je zároveň primárním klíčem), takže
    ji nelze poznat z hodnot řádku; definice proto jmenuje pokrytí, které ji vyvolává.

    :param coverage_ids: Pokrytí dávky nebo případu.
    :param defects: Aktivní definice vad.
    :return: Seznam ``{"defect", "class", "row", "value", "condition"}``.
    """
    return [
        {"defect": d["id"], "class": c.split(".", 1)[0], "row": None, "value": c, "condition": "case"}
        for d in defects or ()
        if d.get("kind") == "case"
        for c in coverage_ids
        if c in d["coverage"]
    ]


def defects_for(expected, defects):
    """
    Vybere vady, které dávce s daným očekávaným výsledkem skutečně brání.

    Vada, která jen zamítne vlastní řádek (``REJECTING_KINDS``), je v zamítací dávce zamýšlenou diagnostikou;
    brání jen dávce, která se má provést.

    :param expected: Očekávaný výsledek dávky (``apply``, ``reject…``).
    :param defects: Aktivní definice vad.
    :return: Seznam vad relevantních pro dávku.
    """
    if str(expected).startswith("reject"):
        return [d for d in defects or () if d.get("kind") not in REJECTING_KINDS]
    return list(defects or ())


def resolver_table(repo):
    """
    Vytáhne z ``get_record_from_ident`` uspořádanou tabulku vzor -> model bez spuštění Django.

    :param repo: Kořen zdrojového checkoutu.
    :return: Seznam ``{"patterns": [...], "model": ..., "strip_suffix": n}`` v pořadí vyhodnocení.
    """
    tree = ast.parse((repo / "webclient/core/ident_cely.py").read_text(encoding="utf-8"))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_record_from_ident")
    table = []
    for statement in function.body:
        if not isinstance(statement, ast.If):
            continue
        patterns = [
            n.args[0].value
            for n in ast.walk(statement.test)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "fullmatch"
            and isinstance(n.args[0], ast.Constant)
        ]
        returned = next((n.value for n in statement.body if isinstance(n, ast.Return)), None)
        if not patterns or not isinstance(returned, ast.Call) or ast.unparse(returned.func) != "get_object_or_404":
            continue
        lookup = next(k.value for k in returned.keywords if k.arg == "ident_cely")
        strip = 0
        if isinstance(lookup, ast.Subscript):
            upper = ast.literal_eval(lookup.slice.upper)
            if lookup.slice.lower is not None or upper >= 0:
                raise ValueError("Unsupported resolver identifier slice: " + ast.unparse(lookup))
            strip = -upper
        table.append({"patterns": patterns, "model": returned.args[0].id, "strip_suffix": strip})
    return table


def load_definitions(source, definitions=None):
    """
    Vrátí vady platné pro pinovaný zdroj; neověřitelnou vadu odmítne místo tichého vynechání.

    :param source: Inventář s ``source_hashes``.
    :param definitions: Obsah definice vad; ``None`` načte zmrazený ``definitions/known-defects.json``.
    :return: Seznam aktivních (neopravených) definic vad.
    :raises ValueError: Zdroj vady se změnil a definice neříká, zda byla opravena.
    """
    if definitions is None:
        path = PACK / DEFINITION
        if not path.is_file():
            return []
        definitions = read_json(path)
    active = []
    for defect in definitions["defects"]:
        pinned = source["source_hashes"].get(defect["source"])
        resolution = defect.get("resolved_in")
        if resolution and resolution.get("source_sha256") == pinned:
            continue
        if pinned != defect["source_sha256"]:
            raise ValueError(
                f"Known defect {defect['id']} is stale for this source; review whether it is fixed "
                "and record resolved_in or a refreshed source_sha256"
            )
        active.append(defect)
    return active


def owner_fields(source):
    """
    Najde CSV třídy, jejichž vlastník se načítá přes ``VazbaLookupImportField``.

    :param source: Inventář s definicemi sloupců mapperů.
    :return: Slovník ``csv -> {"column", "read_field", "classes"}``.
    """
    result = {}
    for mapper in source["mappers"]:
        for column, info in mapper["columns"].items():
            definition = info.get("definition") or ""
            if not definition.startswith("VazbaLookupImportField("):
                continue
            call = ast.parse(definition, mode="eval").body
            classes = (
                [ast.unparse(e) for e in call.args[0].elts] if call.args and isinstance(call.args[0], ast.Tuple) else []
            )
            read = next((k.value.value for k in call.keywords if k.arg == "read_field_name"), None)
            result[mapper["csv"]] = {"column": column, "read_field": read, "classes": classes}
    return result


def closure(batch_ids, batches):
    """Vrátí tranzitivní prerekvizity, tj. dávky zaručeně provedené dříve."""
    by_id = {b["id"]: b for b in batches}
    seen, stack = set(), list(batch_ids)
    while stack:
        current = stack.pop()
        if current in seen or current not in by_id:
            continue
        seen.add(current)
        stack.extend(by_id[current].get("prerequisites", []))
    return seen


def persisted_state(prerequisites, batches):
    """
    Vrátí identifikátory, které po zaručeně dřívějších dávkách existují, a všechny identifikátory běhu.

    :param prerequisites: Přímé prerekvizity posuzované dávky.
    :param batches: Dosud sestavené dávky manifestu.
    :return: Dvojice (existující identifikátory běhu, všechny identifikátory vytvářené kdekoli v manifestu).
    """
    earlier = closure(prerequisites, batches)
    created, deleted, owned = set(), set(), set()
    for batch in batches:
        idents = {str(r["ident_cely"]) for rows in batch["tables"].values() for r in rows if r.get("ident_cely")}
        if batch["operation"] == "insert" and not str(batch.get("expected", "apply")).startswith("reject"):
            owned |= idents
            if batch["id"] in earlier:
                created |= idents
        if batch["operation"] == "delete" and batch["id"] in earlier:
            deleted |= idents
    return created - deleted, owned


def condition(value, field, defect, source, existing, owned, extra_owned=()):
    """
    Zrcadlí větve ``VazbaLookupImportField._process_value`` a vrátí spouštěcí podmínku vady, nebo ``None``.

    :param value: Hodnota vlastníka z CSV.
    :param field: Popis pole z :func:`owner_fields`.
    :param defect: Definice vady s tabulkou resolveru.
    :param source: Inventář s poli modelů.
    :param existing: Identifikátory běhu existující před dávkou.
    :param owned: Všechny identifikátory vytvářené během.
    :param extra_owned: Identifikátory vytvářené v téže dávce (nejsou dosud uložené).
    :return: Název podmínky z definice vady, nebo ``None`` pro bezpečný řádek.
    """
    if value is None or str(value).strip() == "" or str(value).lower() == "nan":
        return None
    value = str(value)

    def exists(ident):
        return ident in existing or (ident not in owned and ident not in extra_owned)

    entry = next((e for e in defect["resolver"] if any(re.fullmatch(p, value) for p in e["patterns"])), None)
    if entry is None:
        return "no-identifier-pattern"
    lookup = value[: -entry["strip_suffix"]] if entry["strip_suffix"] else value
    if not exists(lookup):
        return "owner-not-persisted"
    model = entry["model"]
    if field["classes"] and model == "Dokument" and "Dokument" not in field["classes"]:
        if "DokumentCast" in field["classes"]:
            return None if exists(value) else "document-part-missing"
        if "DokumentacniJednotka" in field["classes"]:
            return "document-part-missing"
    if field["read_field"] in source["models"].get(model, {}).get("fields", {}):
        return None
    return "owner-lacks-read-attribute"


def triggering_rows(tables, operation, prerequisites, batches, source, defects):
    """
    Najde řádky dávky, které při validaci spustí některou aktivní vadu.

    :param tables: Tabulky dávky ``csv -> řádky``.
    :param operation: Operace dávky.
    :param prerequisites: Přímé prerekvizity dávky.
    :param batches: Dosud sestavené dávky.
    :param source: Inventář.
    :param defects: Aktivní definice vad.
    :return: Seznam ``{"defect", "class", "row", "value", "condition"}`` s pořadím řádku od 1.
    """
    found = []
    if operation in ("update", "delete"):
        for defect in defects:
            if defect.get("kind") != "prefixed-key":
                continue
            for name, rows in tables.items():
                if name in defect["classes"]:
                    found += [
                        {
                            "defect": defect["id"],
                            "class": name,
                            "row": index,
                            "value": row.get("id"),
                            "condition": "prefixed-key-update-delete",
                        }
                        for index, row in enumerate(rows, 1)
                    ]
    for defect in defects or ():
        if defect.get("kind") != "lookup-format":
            continue
        for name, rows in tables.items():
            if name not in defect["classes"]:
                continue
            mapper = next((m for m in source.get("mappers", []) if m["csv"].removesuffix(".csv") == name), None)
            models = source.get("models", {})
            # A field is either declared explicitly or derived by the importer from the model field type
            # (e.g. every Point/GeometryField becomes GeomImportField).
            columns = [
                c
                for c, info in (mapper or {}).get("columns", {}).items()
                if (info.get("definition") or "").startswith(defect["field_type"] + "(")
                or (
                    info.get("kind") == "model"
                    and models.get(info.get("model"), {}).get("fields", {}).get(info.get("model_field"), {}).get("type")
                    in defect.get("model_field_types", ())
                )
            ]
            for index, row in enumerate(rows, 1):
                for column in columns:
                    value = row.get(column)
                    if (
                        isinstance(value, str)
                        and value.strip()
                        and not value.startswith("$")
                        and not re.match(defect["accepted_pattern"], value)
                    ):
                        found.append(
                            {
                                "defect": defect["id"],
                                "class": name,
                                "row": index,
                                "value": value,
                                "condition": "lookup-format",
                            }
                        )
    for defect in defects or ():
        if defect.get("kind") != "empty-cell":
            continue
        # The importer reads CSV with pandas, so an empty cell arrives as NaN and crashes a ``(value or "").strip()``.
        for name, rows in tables.items():
            for index, row in enumerate(rows, 1):
                for column in defect["columns"].get(name, ()):
                    if column in row and (row[column] is None or str(row[column]).strip() == ""):
                        found.append(
                            {
                                "defect": defect["id"],
                                "class": name,
                                "row": index,
                                "value": "",
                                "condition": "empty-cell",
                            }
                        )
    for defect in defects or ():
        if defect.get("kind") != "single-system-geometry" or operation == "delete":
            continue
        # Both columns are required before the importer derives one from the other (F1).
        for name, rows in tables.items():
            columns = defect["columns"].get(name, ())
            for index, row in enumerate(rows, 1):
                if not all(c in row for c in columns):
                    continue
                empty = [c for c in columns if row[c] is None or str(row[c]).strip() == ""]
                if len(empty) == 1:
                    found.append(
                        {
                            "defect": defect["id"],
                            "class": name,
                            "row": index,
                            "value": empty[0],
                            "condition": "single-system-geometry",
                        }
                    )
    for defect in defects or ():
        if defect.get("kind") != "delete-history-target" or operation != "delete":
            continue
        # The row deletes the record its own history target belongs to (F42).
        for name, rows in tables.items():
            if name in defect["classes"]:
                found += [
                    {
                        "defect": defect["id"],
                        "class": name,
                        "row": index,
                        "value": row.get("ident_cely"),
                        "condition": "delete-history-target",
                    }
                    for index, row in enumerate(rows, 1)
                ]
    defects = [d for d in defects or () if d.get("kind") not in ROW_LEVEL_KINDS]
    if not defects or operation == "delete":
        return found
    fields = owner_fields(source)
    existing, owned = persisted_state(prerequisites, batches)
    same_batch = (
        {str(r["ident_cely"]) for rows in tables.values() for r in rows if r.get("ident_cely")}
        if operation == "insert"
        else set()
    )
    for defect in defects:
        for name, rows in tables.items():
            if name not in fields or name not in defect["classes"]:
                continue
            for index, row in enumerate(rows, 1):
                if fields[name]["column"] not in row:
                    continue
                reason = condition(
                    row[fields[name]["column"]], fields[name], defect, source, existing, owned, same_batch
                )
                if reason:
                    found.append(
                        {
                            "defect": defect["id"],
                            "class": name,
                            "row": index,
                            "value": row[fields[name]["column"]],
                            "condition": reason,
                        }
                    )
    return found


def summary(defects, batches):
    """
    Sestaví sekci známých vad pro manifest a report, oddělenou od živých výsledků.

    :param defects: Aktivní definice vad.
    :param batches: Dávky manifestu včetně odložených.
    :return: Seznam vad s odloženými dávkami a pokrytím; důkaz je pouze zdrojově potvrzený.
    """
    fields = (
        "id",
        "title",
        "source",
        "source_sha256",
        "symbol",
        "lines",
        "defects",
        "conditions",
        "effect",
        "prerequisite",
        "evidence",
    )
    result = []
    for defect in defects:
        deferred = [b for b in batches if defect["id"] in b.get("deferred", {}).get("defects", [])]
        coverage = set()
        for batch in deferred:
            rows = batch["deferred"].get("rows") or []
            classes = {r["class"] for r in rows if r["defect"] == defect["id"]}
            # A batch deferred only through a deferred prerequisite carries the defect for all its coverage.
            coverage |= {c for c in batch["coverage_ids"] if not rows or c.split(".", 1)[0] in classes}
        section = {key: defect[key] for key in fields}
        section.update(
            {
                "deferred_batches": [b["id"] for b in deferred],
                "deferred_coverage": sorted(coverage),
                "evidence_kind": defect.get("evidence", {}).get("kind", "source-confirmed"),
                "live_outcome": "unexecuted",
            }
        )
        result.append(section)
    return result
