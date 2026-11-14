"""Zdrojově potvrzené vady importéru: mechanická klasifikace spouštěcích řádků a odložení dávek."""

from __future__ import annotations

import ast
import re

from .common import PACK, read_json

DEFINITION = "definitions/known-defects.json"


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
    if not defects or operation == "delete":
        return []
    fields = owner_fields(source)
    existing, owned = persisted_state(prerequisites, batches)
    same_batch = (
        {str(r["ident_cely"]) for rows in tables.values() for r in rows if r.get("ident_cely")}
        if operation == "insert"
        else set()
    )
    found = []
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
        section = {key: defect[key] for key in fields}
        section.update(
            {
                "deferred_batches": [b["id"] for b in deferred],
                "deferred_coverage": sorted({c for b in deferred for c in b["coverage_ids"]}),
                "evidence_kind": "source-confirmed",
                "live_outcome": "unexecuted",
            }
        )
        result.append(section)
    return result
