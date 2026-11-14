"""Vytvoření oddělených sad vstupů s přehledem závislostí a nevyřešených údajů."""

from __future__ import annotations

import io
import json

from .catalog import RECIPES
from .common import digest, generator_hashes, inside, json_bytes, save_json, write_new
from .coverage import coverage
from .datasets import csv_bytes, graph, ident, missing_tokens, resolve, row_for, zip_bytes
from .sql import reference_sql, schema_sql, snapshot_sql


def binary_files(tag):
    """Vytvoří platný PDF/JPEG se syntetickými GPS a známé XML/JSON obsahy."""
    from PIL import Image, ImageDraw

    pdf = io.BytesIO()
    page = Image.new("RGB", (64, 64), (int(digest(tag.encode())[:2], 16), 200, 120))
    ImageDraw.Draw(page).text((2, 2), tag[-10:], fill="black")
    page.save(
        pdf,
        format="PDF",
        title=tag,
        creator="AISCR synthetic test",
        creationDate="D:20200101000000Z",
        modDate="D:20200101000000Z",
    )
    jpg = io.BytesIO()
    exif = Image.Exif()
    from PIL.TiffImagePlugin import IFDRational

    exif[0x8825] = {
        1: "N",
        2: (IFDRational(50), IFDRational(0), IFDRational(0)),
        3: "E",
        4: (IFDRational(14), IFDRational(30), IFDRational(0)),
    }
    photo = Image.new("RGB", (64, 64), (80, 100, int(digest(tag.encode())[:2], 16)))
    label = tag.removesuffix("-replacement")[-6:] + ("R" if tag.endswith("-replacement") else "")
    ImageDraw.Draw(photo).text((1, 1), label, fill="white")
    photo.save(jpg, format="JPEG", exif=exif)
    return {
        f"test-{tag}.pdf": pdf.getvalue(),
        f"gps-{tag}.jpg": jpg.getvalue(),
        f"alto-{tag}.xml": f'<?xml version="1.0" encoding="UTF-8"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Description><sourceImageInformation><fileName>{tag}.pdf</fileName></sourceImageInformation></Description><Layout/></alto>'.encode(),
        f"paradata-{tag}.json": json_bytes(
            {
                "@context": "https://w3id.org/ro/crate/1.1/context",
                "@graph": [{"@id": "./", "@type": "Dataset", "name": "Synthetic " + tag}],
            }
        ),
        f"replacement-{tag}.txt": ("TEST REPLACEMENT " + tag + "\n").encode(),
    }


def key_rows(mapper, rows, operation):
    """Vybere klíče pro DELETE; pro UPDATE ponechá úplný vstup s ověřeným PK."""
    result = []
    for i, original in enumerate(rows, 1):
        row = dict(original)
        if mapper["key"] == "id" and mapper["csv"] != "distribution":
            row["id"] = f"$bind:{mapper['csv']}:{i}.id"
        if operation == "delete":
            keys = list(mapper["key"]) if isinstance(mapper["key"], (list, tuple)) else [mapper["key"]]
            if mapper["csv"] in ("distribution", "paradata"):
                keys += ["distribution"]
            row = {key: row[key] for key in keys}
        result.append(row)
    return result


def add_batch(out, manifest, batch_id, operation, tables, coverage_ids, prerequisites=(), expected="apply", data=None):
    """Zapíše vstup a kartu; nevyřešené vstupy jsou jednoznačně šablony."""
    from .datasets import late_bind

    for name, inputs in tables.items():
        for row in inputs:
            for key, value in row.items():
                if isinstance(value, str) and value.startswith("$bind:") and value[6:] in manifest.get("bindings", {}):
                    late_bind({name: [{key: value}]}, manifest["bindings"])
    tables = {
        name: [
            {
                key: (
                    manifest.get("bindings", {}).get(value[6:], value)
                    if isinstance(value, str) and value.startswith("$bind:")
                    else value
                )
                for key, value in row.items()
            }
            for row in rows
        ]
        for name, rows in tables.items()
    }
    if not missing_tokens([row for rows in tables.values() for row in rows]):
        # Validate supplied key/path values through the same strict binder.
        for name, originals in tables.items():
            for row in originals:
                if name in ("distribution",) and not __import__("re").fullmatch(r"soub-\d+", str(row.get("id"))):
                    raise ValueError("Invalid prefixed file key")
    unresolved = missing_tokens([row for rows in tables.values() for row in rows])
    if expected == "apply" and manifest.get("identifier_patterns"):
        import re

        for inputs in tables.values():
            for row in inputs:
                value = row.get("ident_cely")
                if (
                    value
                    and not str(value).startswith("$")
                    and not any(re.fullmatch(pattern, str(value)) for pattern in manifest["identifier_patterns"])
                ):
                    raise ValueError("Invalid positive fixture identifier: " + str(value))
    content = data if data is not None else zip_bytes({name + ".csv": csv_bytes(rows) for name, rows in tables.items()})
    suffix = ".template.zip" if unresolved else ".zip"
    path = inside(out, "inputs/" + batch_id + suffix)
    write_new(path, content)
    batch = {
        "id": batch_id,
        "suite": manifest["suite"],
        "operation": operation,
        "input": path.relative_to(out).as_posix(),
        "input_sha256": digest(content),
        "rows": sum(map(len, tables.values())),
        "tables": tables,
        "coverage_ids": coverage_ids,
        "prerequisites": list(prerequisites),
        "unresolved": unresolved,
        "ready": not unresolved,
        "expected": expected,
        "state": "prepared",
    }
    defer_if_known_defect(manifest, batch)
    manifest["batches"].append(batch)


def defer_if_known_defect(manifest, batch):
    """
    Odloží dávku, jejíž řádek by spustil známou vadu, nebo jejíž prerekvizita je odložená.

    Odložená dávka má vstup připravený pro opakování po opravě, ale nedostane kartu ani nesmí být
    označena jako provedená; její pokrytí je ``blocked`` s opravou jako prerekvizitou.

    :param manifest: Rozpracovaný manifest; kontext vad je v klíči ``_defect_context``.
    :param batch: Nově sestavovaná dávka (ještě není v manifestu).
    :return: Funkce nevrací hodnotu; při odložení doplní ``batch["deferred"]`` a stav ``blocked``.
    """
    context = manifest.get("_defect_context")
    triggers = []
    if context:
        from .known_defects import triggering_rows

        triggers = triggering_rows(
            batch["tables"],
            batch["operation"],
            batch["prerequisites"],
            manifest["batches"],
            context["source"],
            context["defects"],
        )
    # A dependent of a deferred batch cannot run either, with or without a classification context.
    deferred_parents = [b for b in manifest["batches"] if b["id"] in batch["prerequisites"] and b.get("deferred")]
    if not triggers and not deferred_parents:
        return
    defect_ids = sorted(
        {t["defect"] for t in triggers} | {d for b in deferred_parents for d in b["deferred"]["defects"]}
    )
    inherited = [p for b in deferred_parents for p in b["deferred"]["prerequisite"]]
    known = [d["prerequisite"] for d in (context or {}).get("defects", []) if d["id"] in defect_ids]
    batch["deferred"] = {
        "defects": defect_ids,
        "rows": triggers,
        "deferred_prerequisites": [b["id"] for b in deferred_parents],
        "prerequisite": sorted(set(known + inherited)),
    }
    batch["state"] = "blocked"


def finish_known_defects(manifest):
    """
    Označí pokrytí odložených dávek jako ``blocked`` a připojí sekci známých vad; odstraní pracovní kontext.

    :param manifest: Sestavený manifest s pracovním klíčem ``_defect_context``.
    :return: Funkce nevrací hodnotu.
    """
    from .known_defects import summary

    context = manifest.pop("_defect_context", None) or {"defects": []}
    deferred = {}
    for batch in manifest["batches"]:
        if batch.get("deferred"):
            for coverage_id in batch["coverage_ids"]:
                deferred.setdefault(coverage_id, {"batches": [], "defects": set()})
                deferred[coverage_id]["batches"].append(batch["id"])
                deferred[coverage_id]["defects"].update(batch["deferred"]["defects"])
    for item in manifest.get("coverage", []):
        if item["id"] in deferred:
            item["state"] = "blocked"
            item["blocked_by"] = {
                "batches": deferred[item["id"]]["batches"],
                "defects": sorted(deferred[item["id"]]["defects"]),
                "reason": "Deferred: a source-confirmed importer defect would abort this batch; rerun after the fix",
            }
    manifest["known_defects"] = summary(context["defects"], manifest["batches"])


def add_procedure(out, manifest, batch_id, case, recipe, prerequisites):
    """Keep a management procedure distinct from a browser CSV import."""
    content = json_bytes(recipe)
    path = inside(out, "inputs/" + batch_id + ".procedure.json")
    write_new(path, content)
    manifest["batches"].append(
        {
            "id": batch_id,
            "suite": manifest["suite"],
            "operation": "update",
            "execution_kind": "controlled-procedure",
            "input": path.relative_to(out).as_posix(),
            "input_sha256": digest(content),
            "rows": 0,
            "tables": {},
            "coverage_ids": [case["id"]],
            "prerequisites": prerequisites,
            "unresolved": [],
            "ready": True,
            "expected": "apply",
            "state": "prepared",
            "execution_gate": "Isolated fixture/approved scan scope, exact setup and restoration required",
            "controlled_setup": case["notes"],
        }
    )


def build_behaviour(out, source, ns, refs, repo, bindings=None):
    """Vytvoří kompletní operační základ, negativní vstupy a SQL kontrolní body."""
    source = json.loads(json_bytes(source))
    tables = graph(source, ns, refs, bindings)
    manifest = {
        "schema_version": 1,
        "suite": "behaviour",
        "namespace": ns,
        "generator_hashes": generator_hashes(),
        "identifier_patterns": source["identifier_patterns"],
        "source_hash_mode": source.get("source_hash_mode"),
        "source_hashes": source["source_hashes"],
        "source_commit": source.get("source_commit"),
        "deployment": None,
        "batches": [],
        "coverage": coverage(source),
        "bindings": bindings or {},
        "class_tables": {m["csv"]: source["models"].get(m["model"], {}).get("table") for m in source["mappers"]},
    }
    from .known_defects import load_definitions

    manifest["_defect_context"] = {"source": source, "defects": load_definitions(source)}
    stages = {
        "B01-foundations": ["heslar", "organizace", "osoby"],
        "B02-domain-graph": [
            m["csv"]
            for m in source["mappers"]
            if m["csv"]
            not in (
                "heslar",
                "organizace",
                "osoby",
                "soubory",
                "distribution",
                "paradata",
                "historie",
                "komponenty",
                "komponenty_aktivity",
                "komponenty_nalezy_objekty",
                "komponenty_nalezy_predmety",
                "uzivatele_opravneni",
                "uzivatele_notifikace",
            )
        ],
        "B02b-components": [
            "komponenty",
            "komponenty_aktivity",
            "komponenty_nalezy_objekty",
            "komponenty_nalezy_predmety",
        ],
        "B02c-user-relations": ["uzivatele_opravneni", "uzivatele_notifikace"],
        "B03-files": ["soubory"],
        "B04-distributions-paradata": ["distribution", "paradata"],
        "B05-explicit-history": ["historie"],
    }
    previous = []
    for batch_id, names in stages.items():
        add_batch(
            out,
            manifest,
            batch_id,
            "insert",
            {name: tables[name] for name in names},
            [name + ".insert" for name in names],
            previous,
        )
        previous = [batch_id]
    allowed = [m for m in source["mappers"] if m["allow_update"]]
    updates = {m["csv"]: key_rows(m, tables[m["csv"]], "update") for m in allowed}
    changes = {
        "heslar": ("popis", "TEST UPDATED {tag}"),
        "heslar_datace": ("rok_do_max", 250),
        "heslar_dokument_typ_material": ("dokument_material", "$ref:synthetic_document_material_2"),
        "heslar_hierarchie": ("typ", "uplatnění"),
        "heslar_odkazy": ("kod", "UPD-{tag}"),
        "organizace": ("nazev", "TEST UPDATED {tag}"),
        "osoby": ("prijmeni", "Updated{tag}"),
        "projekty": ("lokalizace", "TEST UPDATED {tag}"),
        "projekty_oznamovatele": ("poznamka", "TEST UPDATED {tag}"),
        "samostatne_nalezy": ("poznamka", "TEST UPDATED {tag}"),
        "az_akce": ("uzivatelske_oznaceni", "TEST UPDATED {tag}"),
        "az_lokality": ("poznamka", "TEST UPDATED {tag}"),
        "az_akce_vedouci": ("organizace", "$row:organizace:2"),
        "az_pian": ("geom", "POINT(14.50002 50.00002)"),
        "az_dokumentacni_jednotky": ("nazev", "TEST UPDATED {tag}"),
        "az_adb": ("trat", "TEST UPDATED {tag}"),
        "az_adb_vyskove_body": ("geom", "$ref:elevation_point_5514_updated"),
        "dokumenty_lety": ("pilot", "TEST UPDATED {tag}"),
        "dokumenty": ("poznamka", "TEST UPDATED {tag}"),
        "dokumenty_tvary": ("poznamka", "TEST UPDATED {tag}"),
        "dokumenty_casti": ("poznamka", "TEST UPDATED {tag}"),
        "dokumenty_neident_akce": ("poznamka", "TEST UPDATED {tag}"),
        "komponenty": ("poznamka", "TEST UPDATED {tag}"),
        "komponenty_nalezy_objekty": ("pocet", 3),
        "komponenty_nalezy_predmety": ("pocet", 4),
        "externi_zdroje": ("poznamka", "TEST UPDATED {tag}"),
        "externi_odkazy": ("paginace", "3-4"),
        "uzivatele": ("first_name", "Updated{tag}"),
        "uzivatele_spoluprace": ("stav", 2),
        "soubory": ("nazev", "replacement-{tag}.pdf"),
        "distribution": ("nazev", "alto-v2-{tag}.xml"),
        "paradata": ("nazev", "paradata-v2-{tag}.json"),
        "historie": ("poznamka", "TEST UPDATED {tag}"),
    }
    if set(changes) != {m["csv"] for m in allowed}:
        raise ValueError("UPDATE change recipes do not match permitted classes")
    for name, rows in updates.items():
        field, value = changes[name]
        for i, row in enumerate(rows, 1):
            row[field] = resolve(value, name, i, ns, refs, bindings or {})
    add_batch(out, manifest, "B06-full-update", "update", updates, [m["csv"] + ".update" for m in allowed], previous)
    partial = {}
    for m in allowed:
        keys = list(m["key"]) if isinstance(m["key"], (list, tuple)) else [m["key"]]
        field = changes[m["csv"]][0]
        partial[m["csv"]] = []
        for i, row in enumerate(updates[m["csv"]]):
            # Revert the changed field, so omission checks cannot pass a no-op.
            columns = list(row) if m["csv"] in ("distribution", "paradata") else [*keys, field]
            value = {k: row[k] for k in columns}
            value[field] = tables[m["csv"]][i][field]
            partial[m["csv"]].append(value)
    add_batch(out, manifest, "B07-partial-update", "update", partial, [], ["B06-full-update"])
    denied = [m for m in source["mappers"] if not m["allow_update"]]
    add_batch(
        out,
        manifest,
        "N01-prohibited-updates",
        "update",
        {m["csv"]: tables[m["csv"]] for m in denied},
        [m["csv"] + ".update" for m in denied],
        ["B02-domain-graph"],
        "reject unsupported CSV list",
    )
    # Separate structural failures cannot conceal another parser/filename check.
    for batch_id, members, expected in [
        ("N02-unknown-file", {"unknown.csv": b'"unknown"\r\n"1"\r\n'}, "unsupported file"),
        ("N03-malformed-csv", {"osoby.csv": b'"ident_cely","jmeno"\r\n"unterminated'}, "CSV parser error"),
        ("N04-empty-zip", {}, "empty import"),
        ("N05-wrong-headers", {"osoby.csv": b'"wrong"\r\n"1"\r\n'}, "incorrect column structure"),
        (
            "N08-wrong-encoding",
            {"osoby.csv": "ident_cely,jmeno,prijmeni\r\nOS-959997,Příliš,Žluťoučký\r\n".encode("cp1250")},
            "encoding error",
        ),
        (
            "N09-duplicate-headers",
            {"osoby.csv": b"ident_cely,jmeno,jmeno\r\nOS-959996,one,two\r\n"},
            "incorrect column structure",
        ),
        (
            "N10-semicolon",
            {"osoby.csv": b"ident_cely;jmeno;prijmeni\r\nOS-959995;one;two\r\n"},
            "incorrect column structure",
        ),
    ]:
        add_batch(
            out, manifest, batch_id, "insert", {}, ["archive." + batch_id], expected=expected, data=zip_bytes(members)
        )
    add_batch(
        out,
        manifest,
        "N06-not-a-zip",
        "insert",
        {},
        ["archive.N06-not-a-zip"],
        expected="invalid ZIP",
        data=b"NOT A ZIP\n",
    )
    import struct

    # The central directory declares >1 GiB while the body remains tiny. The size
    # guard must reject before CSV extraction; no multi-GiB file is created locally.
    oversized = bytearray(zip_bytes({"osoby.csv": b"x\n1\n"}))
    central = oversized.index(b"PK\x01\x02")
    struct.pack_into("<I", oversized, central + 24, 1024**3 + 1)
    add_batch(
        out,
        manifest,
        "N11-expansion-limit",
        "insert",
        {},
        ["archive.N11-expansion-limit"],
        expected="zip_too_large",
        data=bytes(oversized),
    )
    person_mapper = next(m for m in source["mappers"] if m["csv"] == "osoby")
    bom_rows = [row_for(person_mapper, ns, 7950, refs)]
    add_batch(
        out,
        manifest,
        "P01-utf8-bom",
        "insert",
        {"osoby": bom_rows},
        ["archive.P01-utf8-bom"],
        ["B01-foundations"],
        data=zip_bytes({"osoby.csv": b"\xef\xbb\xbf" + csv_bytes(bom_rows)}),
    )
    from collections import defaultdict

    from .negatives import probes

    negative_rows = defaultdict(list)
    negative_cases = probes(source, ns, refs)
    ordering_probes = []
    row_probes = []
    from .known_defects import triggering_rows

    deferred_probes = []
    for case in negative_cases:
        if case["variant"] == "missing-lookup" and (
            case["class"] == "heslar_hierarchie" or (case["class"] == "organizace" and case["field"] == "soucast")
        ):
            ordering_probes.append(case)
        elif triggering_rows(
            {case["class"]: [case["row"]]},
            "insert",
            ["B05-explicit-history"],
            manifest["batches"],
            source,
            manifest["_defect_context"]["defects"],
        ):
            # A known defect would abort the whole N07 job; keep these probes for a rerun after the fix.
            deferred_probes.append(case)
        else:
            negative_rows[case["class"]].append(case["row"])
            row_probes.append(case)
    add_batch(
        out,
        manifest,
        "N07-field-boundaries",
        "insert",
        dict(negative_rows),
        [c["id"] for c in row_probes],
        ["B05-explicit-history"],
        "reject intended row diagnostics",
    )
    if deferred_probes:
        deferred_rows = defaultdict(list)
        for case in deferred_probes:
            deferred_rows[case["class"]].append(case["row"])
        add_batch(
            out,
            manifest,
            "N07x-deferred-known-defects",
            "insert",
            dict(deferred_rows),
            [c["id"] for c in deferred_probes],
            ["B05-explicit-history"],
            "reject intended row diagnostics",
        )
    for index, case in enumerate(ordering_probes, 1):
        add_batch(
            out,
            manifest,
            f"N07-{index}-ordering-boundary",
            "insert",
            {case["class"]: [case["row"]]},
            [case["id"]],
            ["B05-explicit-history"],
            "reject intended ordering lookup",
        )
    manifest["negative_probes"] = negative_cases
    from .branches import branch_contexts

    setup, cases, groups = branch_contexts(source, ns, refs)
    manifest["branch_scenarios"] = cases
    component_names = ("komponenty", "komponenty_aktivity", "komponenty_nalezy_objekty", "komponenty_nalezy_predmety")
    relation_names = ("uzivatele_opravneni", "uzivatele_notifikace")
    roots = {
        name: rows
        for name, rows in setup.items()
        if name not in ("soubory", "historie", *component_names, *relation_names)
    }
    add_batch(out, manifest, "V00-isolated-contexts", "insert", roots, [], ["B05-explicit-history"])
    add_batch(
        out,
        manifest,
        "V00b-isolated-components",
        "insert",
        {name: setup[name] for name in component_names if name in setup},
        [],
        ["V00-isolated-contexts"],
    )
    add_batch(
        out,
        manifest,
        "V00c-isolated-user-relations",
        "insert",
        {name: setup[name] for name in relation_names if name in setup},
        [],
        ["V00b-isolated-components"],
    )
    add_batch(
        out,
        manifest,
        "V00d-isolated-history",
        "insert",
        {"historie": setup["historie"]},
        [],
        ["V00c-isolated-user-relations"],
    )
    if setup.get("soubory"):
        add_batch(
            out, manifest, "V01-isolated-files", "insert", {"soubory": setup["soubory"]}, [], ["V00-isolated-contexts"]
        )
    existing_dist, existing_para = [], []
    for case in cases:
        name, index = case["class"], case["index"]
        if name not in ("distribution", "paradata"):
            continue
        special_existing = case["variant"] in (
            "existing-distribution",
            "existing-ancestor-conflict",
            "existing-descendant-conflict",
        ) or (name == "paradata" and case["variant"] == "duplicate-in-batch")
        if not special_existing and (case["operation"] == "insert" or case["outcome"] == "reject"):
            continue
        dist = row_for(next(m for m in source["mappers"] if m["csv"] == "distribution"), ns, index, refs)
        dist["id"] = f"$bind:file:{index}.id"
        dist["distribution"] = case["row"]["distribution"]
        if case["variant"] in ("existing-ancestor-conflict", "existing-descendant-conflict"):
            dist["distribution"] = "ocr" if case["variant"] == "existing-ancestor-conflict" else "ocr/alto-xml"
        if dist["distribution"] not in ("orig", "thumb"):
            existing_dist.append(dist)
        if case["variant"] == "same-record-multiple-files":
            existing_dist.append({**dist, "id": f"$bind:file:{index + 1}.id"})
        if name == "paradata" and case["operation"] != "insert":
            para = row_for(next(m for m in source["mappers"] if m["csv"] == "paradata"), ns, index, refs)
            para["path"] = f"$bind:file:{index}.path"
            para["distribution"] = case["row"]["distribution"]
            existing_para.append(para)
    add_batch(
        out,
        manifest,
        "V02-existing-distributions",
        "insert",
        {"distribution": existing_dist},
        [],
        ["V01-isolated-files"],
    )
    add_batch(
        out,
        manifest,
        "V03-existing-paradata",
        "insert",
        {"paradata": existing_para},
        [],
        ["V02-existing-distributions"],
    )
    for index, group in enumerate(groups, 1):
        tables_group = group["tables"]
        if group["operation"] == "delete":
            by_name = {m["csv"]: m for m in source["mappers"]}
            tables_group = {
                name: [
                    {
                        key: row[key]
                        for key in (
                            (
                                [*by_name[name]["key"]]
                                if isinstance(by_name[name]["key"], (list, tuple))
                                else [by_name[name]["key"]]
                            )
                            + (["distribution"] if name in ("distribution", "paradata") else [])
                        )
                    }
                    for row in rows
                ]
                for name, rows in tables_group.items()
            }
        prerequisites = (
            ["V03-existing-paradata"] if set(tables_group) & {"distribution", "paradata"} else ["V00d-isolated-history"]
        )
        add_batch(
            out,
            manifest,
            f"V{index + 3:02}-branches-{group['operation']}",
            group["operation"],
            tables_group,
            group["cases"],
            prerequisites,
            group["outcome"],
        )
    from .branches import FILE_LIFECYCLES, LIFECYCLES, RUNTIME

    file_cases = [case for case in cases if case["id"] in FILE_LIFECYCLES]
    for batch in manifest["batches"]:
        if batch["id"] == "V01-isolated-files":
            batch["coverage_ids"].extend(case["id"] for case in file_cases)
    add_batch(
        out,
        manifest,
        "F01-replace-all-file-owners",
        "update",
        {"soubory": [case["row"] for case in file_cases]},
        [case["id"] for case in file_cases],
        ["V01-isolated-files"],
    )
    add_batch(
        out,
        manifest,
        "F02-delete-all-file-owners",
        "delete",
        {"soubory": [{"id": case["row"]["id"]} for case in file_cases]},
        [case["id"] for case in file_cases],
        ["F01-replace-all-file-owners"],
    )
    for index, case in enumerate((c for c in cases if c["variant"] in LIFECYCLES), 1):
        if case["variant"] == "relation-add-remove":
            previous_step = "V00c-isolated-user-relations"
            for step, operation in enumerate(("insert", "delete"), 1):
                batch_id = f"J{index:02}-{step}-{operation}"
                add_batch(
                    out, manifest, batch_id, operation, {case["class"]: case["rows"]}, [case["id"]], [previous_step]
                )
                previous_step = batch_id
            continue
        previous_step = "V03-existing-paradata" if case["class"] == "paradata" else "V02-existing-distributions"
        for batch in manifest["batches"]:
            if batch["id"] == previous_step:
                batch["coverage_ids"].append(case["id"])
        for step, operation in enumerate(("update", "delete", "insert"), 1):
            rows = case["rows"]
            if operation == "delete":
                keys = ("path", "distribution") if case["class"] == "paradata" else ("id", "distribution")
                rows = [{key: row[key] for key in keys} for row in rows]
            batch_id = f"T{index:02}-{step}-{operation}"
            add_batch(out, manifest, batch_id, operation, {case["class"]: rows}, [case["id"]], [previous_step])
            previous_step = batch_id
    for index, case in enumerate(
        (case for case in cases if case["variant"] in RUNTIME or case["outcome"] == "acceptance-unresolved"), 1
    ):
        if case["variant"] in ("thumb-backfill", "backfill-idempotence"):
            from .controlled import recipe

            file_row = {
                "id": f"$bind:file:{case['index']}.id",
                "vazba": ident("dokumenty", ns, case["index"], refs),
                "nazev": f"replacement-{ns}-{case['index']}.pdf",
            }
            prerequisite = f"Q{index:02}-prepare-thumbnail-versions"
            add_batch(out, manifest, prerequisite, "update", {"soubory": [file_row]}, [], ["V01-isolated-files"])
            add_procedure(
                out, manifest, f"R{index:02}-controlled-procedure", case, recipe(case, ns, refs), [prerequisite]
            )
            if case["variant"] == "thumb-backfill":
                manifest["batches"][-1]["coverage_ids"].append("session.thumbnail-backfill")
            continue
        rows = case["rows"]
        if case["operation"] == "delete":
            mapper = next(m for m in source["mappers"] if m["csv"] == case["class"])
            keys = list(mapper["key"]) if isinstance(mapper["key"], (list, tuple)) else [mapper["key"]]
            rows = [{key: row[key] for key in keys} for row in rows]
        add_batch(
            out,
            manifest,
            f"R{index:02}-controlled-scenario",
            case["operation"],
            {case["class"]: rows},
            [case["id"]],
            ["V00-isolated-contexts"],
            case["outcome"],
        )
        manifest["batches"][-1]["controlled_setup"] = case["notes"]
        manifest["batches"][-1]["execution_gate"] = "resolve acceptance/setup and obtain target-specific authorization"
    # Explicit child DELETEs precede parent DELETEs; each class must be visited.
    previous = ["B07-partial-update"]
    dependencies = {
        m["csv"]: {
            v.split(":")[1]
            for v in RECIPES[m["csv"]].values()
            if isinstance(v, str) and v.startswith("$row:") and v.split(":")[1] != m["csv"]
        }
        for m in source["mappers"]
    }
    for name in ["heslar_datace", "heslar_dokument_typ_material", "heslar_hierarchie", "heslar_odkazy"]:
        dependencies[name].add("heslar")
    dependencies["distribution"].add("soubory")
    dependencies["paradata"].add("distribution")
    dependencies["dokumenty_neident_akce_vedouci"].add("dokumenty_neident_akce")
    # Root deletion may cascade. Children are in strictly earlier delete batches.
    remaining = set(dependencies)
    index = 0
    while remaining:
        names = sorted(name for name in remaining if not any(name in dependencies[other] for other in remaining))
        if not names:
            raise ValueError("Delete dependency cycle; explicit scenario setup required")
        index += 1
        batch_id = f"D{index:02}-dependency-layer"
        by_name = {m["csv"]: m for m in source["mappers"]}
        add_batch(
            out,
            manifest,
            batch_id,
            "delete",
            {
                name: key_rows(by_name[name], tables[name][:1] if name == "heslar" else tables[name], "delete")
                for name in names
            },
            [name + ".delete" for name in names],
            previous,
        )
        previous = [batch_id]
        remaining.difference_update(names)
    identifiers = [
        row["ident_cely"]
        for batch in manifest["batches"]
        for rows in batch["tables"].values()
        for row in rows
        if row.get("ident_cely")
    ]
    write_new(inside(out, "sql/references.sql"), reference_sql(repo or source).encode())
    write_new(inside(out, "sql/schema.sql"), schema_sql().encode())
    write_new(inside(out, "sql/snapshot.sql"), snapshot_sql(source, identifiers).encode())
    for name, content in binary_files(ns + "-1").items():
        write_new(inside(out, "binaries/" + name), content)
    import re

    binary_indices = {case["index"] for case in cases if case["class"] in ("soubory", "distribution", "paradata")}
    binary_indices.update(
        int(match.group(1))
        for row in setup.get("soubory", [])
        if (match := re.fullmatch("test-" + ns + r"-(\d+)\.pdf", row["nazev"]))
    )
    for index in sorted(binary_indices):
        for name, content in binary_files(ns + "-" + str(index)).items():
            write_new(inside(out, "binaries/" + name), content)
        replacements = binary_files(ns + "-" + str(index) + "-replacement")
        replacement_pdf = replacements[f"test-{ns}-{index}-replacement.pdf"]
        write_new(inside(out, f"binaries/replacement-{ns}-{index}.pdf"), replacement_pdf)
        write_new(inside(out, f"binaries/pdf-disguised-{ns}-{index}.jpg"), replacement_pdf)
        write_new(
            inside(out, f"binaries/replacement-{ns}-{index}.jpg"), replacements[f"gps-{ns}-{index}-replacement.jpg"]
        )
    replacement = binary_files(ns + "-2")
    for name, content in [
        ("replacement-" + ns + "-1.pdf", replacement["test-" + ns + "-2.pdf"]),
        ("alto-v2-" + ns + "-1.xml", replacement["alto-" + ns + "-2.xml"]),
        ("paradata-v2-" + ns + "-1.json", replacement["paradata-" + ns + "-2.json"]),
    ]:
        write_new(inside(out, "binaries/" + name), content)
    case_map = {case["id"]: case for case in cases}
    for batch in manifest["batches"]:
        batch["case_details"] = [
            {key: case_map[case_id][key] for key in ("id", "class", "variant", "index", "notes", "outcome")}
            for case_id in batch["coverage_ids"]
            if case_id in case_map
        ]
        for detail in batch["case_details"]:
            detail["target"] = case_map[detail["id"]]["row"].get("ident_cely")
    finish_known_defects(manifest)
    from .planning import complete

    manifest["preparation"] = complete(out, manifest, source)
    save_json(inside(out, "manifest.json"), manifest)
    return manifest


def build_load(out, source, ns, refs, workload, bindings=None):
    """Vygeneruje plnou velikost zátěže bez odeslání do služby."""
    source = json.loads(json_bytes(source))
    by_name = {m["csv"]: m for m in source["mappers"]}
    manifest = {
        "schema_version": 1,
        "suite": "load",
        "namespace": ns,
        "workload": workload,
        "generator_hashes": generator_hashes(),
        "identifier_patterns": source["identifier_patterns"],
        "source_hash_mode": source.get("source_hash_mode"),
        "source_hashes": source["source_hashes"],
        "source_commit": source.get("source_commit"),
        "deployment": None,
        "batches": [],
        "coverage": [],
        "bindings": bindings or {},
        "class_tables": {m["csv"]: source["models"].get(m["model"], {}).get("table") for m in source["mappers"]},
    }
    from .known_defects import load_definitions

    manifest["_defect_context"] = {"source": source, "defects": load_definitions(source)}
    if workload == "relational":
        names = ["projekty", "az_akce", "az_dokumentacni_jednotky", "komponenty", "komponenty_nalezy_predmety"]
        rows = {name: [row_for(by_name[name], ns, i, refs, bindings) for i in range(1, 10001)] for name in names}
        # Independent setup is explicit, never borrowed from a behaviour run.
        setup = {name: [row_for(by_name[name], ns, 1, refs, bindings)] for name in ["organizace", "osoby", "az_pian"]}
        for row in rows["projekty"]:
            row["organizace"], row["vedouci_projektu"] = ident("organizace", ns, 1, refs), ident("osoby", ns, 1, refs)
        for row in rows["az_akce"]:
            row["organizace"], row["hlavni_vedouci"] = ident("organizace", ns, 1, refs), ident("osoby", ns, 1, refs)
        for row in rows["az_dokumentacni_jednotky"]:
            row["pian"] = ident("az_pian", ns, 1, refs)
        add_batch(out, manifest, "L00-setup", "insert", setup, [])
        add_batch(out, manifest, "L01-relational-50000", "insert", rows, [], ["L00-setup"])
        manifest["workload_counts"] = {
            "measured_rows": 50000,
            "projects": 10000,
            "fieldwork_events": 10000,
            "documentation_units": 10000,
            "components": 10000,
            "finds": 10000,
        }
        events = [r["ident_cely"] for name in ("projekty", "az_akce") for r in rows[name]]
        combined = manifest["batches"][-1]
        manifest["measured_batches"] = [
            {
                "id": combined["id"],
                "label": "combined",
                "counts": manifest["workload_counts"],
                "metadata_targets": events,
                "expected_deduplicated_import_history": 20000,
            }
        ]
        if combined.get("deferred"):
            # Known defect: components cannot reference documentation units created in the same import.
            # Measure the same rows as two imports instead; the combined import stays prepared and blocked.
            owners = {r["ident_cely"]: r["archeologicky_zaznam"] for r in rows["az_dokumentacni_jednotky"]}
            parents = ("projekty", "az_akce", "az_dokumentacni_jednotky")
            children = ("komponenty", "komponenty_nalezy_predmety")
            add_batch(
                out,
                manifest,
                "L01a-relational-parents-30000",
                "insert",
                {n: rows[n] for n in parents},
                [],
                ["L00-setup"],
            )
            add_batch(
                out,
                manifest,
                "L01b-relational-components-20000",
                "insert",
                {n: rows[n] for n in children},
                [],
                ["L01a-relational-parents-30000"],
            )
            if any(b.get("deferred") for b in manifest["batches"][-2:]):
                raise ValueError("The relational substitute still triggers a known defect")
            manifest["measured_batches"] = [
                {
                    "id": "L01a-relational-parents-30000",
                    "label": "substitute",
                    "counts": {
                        "measured_rows": 30000,
                        "projects": 10000,
                        "fieldwork_events": 10000,
                        "documentation_units": 10000,
                    },
                    "metadata_targets": events,
                    "expected_deduplicated_import_history": 20000,
                },
                {
                    "id": "L01b-relational-components-20000",
                    "label": "substitute",
                    "counts": {"measured_rows": 20000, "components": 10000, "finds": 10000},
                    "metadata_targets": sorted({owners[r["vazba"]] for r in rows["komponenty"]}),
                    "expected_deduplicated_import_history": 10000,
                },
            ]
            manifest["substitute"] = {
                "label": "two-import substitute",
                "replaces": combined["id"],
                "batches": [m["id"] for m in manifest["measured_batches"]],
                "reason": "The combined import is deferred by a known importer defect; the same 50,000 rows are measured "
                "as two sequential imports. Its figures are not the combined-import figure.",
            }
    elif workload == "distributions":
        documents = [row_for(by_name["dokumenty"], ns, i, refs, bindings) for i in range(1, 5001)]
        for row in documents:
            row["let"] = ""
            row["organizace"] = ident("organizace", ns, 1, refs)
        setup = {"organizace": [row_for(by_name["organizace"], ns, 1, refs)], "dokumenty": documents}
        files, distributions, paradata = [], [], []
        for i in range(1, 10001):
            tag = ns + "-" + str(i)
            files.append(
                {
                    "id": f"soub-{int(ns) + i}",
                    "vazba": ident("dokumenty", ns, (i + 1) // 2, refs),
                    "nazev": f"test-{tag}.pdf",
                }
            )
            for distribution, suffix, mime in [
                ("atr/alto-xml", "xml", "application/xml"),
                ("atrium/document-json", "json", "application/json"),
            ]:
                file_id = (bindings or {}).get(f"file:{i}.id", f"$bind:file:{i}.id")
                path = (bindings or {}).get(f"file:{i}.path", f"$bind:file:{i}.path")
                distributions.append(
                    {
                        "id": file_id,
                        "nazev": f"distribution-{tag}.{suffix}",
                        "mimetype": mime,
                        "distribution": distribution,
                    }
                )
                paradata.append(
                    {
                        "path": path,
                        "nazev": f"paradata-{tag}.json",
                        "mimetype": "application/ld+json",
                        "distribution": distribution,
                    }
                )
        add_batch(out, manifest, "L00-parents", "insert", setup, [])
        add_batch(out, manifest, "L01-files", "insert", {"soubory": files}, [], ["L00-parents"])
        add_batch(
            out,
            manifest,
            "L02-distributions-40000",
            "insert",
            {"distribution": distributions, "paradata": paradata},
            [],
            ["L01-files"],
        )
        manifest["workload_counts"] = {
            "measured_rows": 40000,
            "parent_records": 5000,
            "files": 10000,
            "distributions": 20000,
            "paradata": 20000,
            "expected_parent_groups": 5000,
        }
        manifest["measured_batches"] = [
            {
                "id": "L02-distributions-40000",
                "label": "combined",
                "counts": manifest["workload_counts"],
                "metadata_targets": [r["ident_cely"] for r in documents],
            }
        ]
    else:
        raise ValueError("Unknown load workload")
    finish_known_defects(manifest)
    from .planning import complete

    manifest["preparation"] = complete(out, manifest, source)
    save_json(inside(out, "manifest.json"), manifest)
    return manifest


def load_binaries(out, manifest):
    """Připraví zdrojový adresář souborů pro samostatný distribuční load run."""
    import hashlib

    if manifest.get("workload") != "distributions":
        raise ValueError("Binary source preparation belongs to the distributions workload")
    ns = manifest["namespace"]
    pdf = binary_files(ns + "-load")[f"test-{ns}-load.pdf"]
    results = []
    for i in range(1, 10001):
        tag = ns + "-" + str(i)
        contents = {
            f"test-{tag}.pdf": pdf,
            f"distribution-{tag}.xml": (
                f'<?xml version="1.0"?><alto xmlns="http://www.loc.gov/standards/alto/ns-v4#"><Description><sourceImageInformation><fileName>{tag}.pdf</fileName></sourceImageInformation></Description><Layout/></alto>'
            ).encode(),
            f"distribution-{tag}.json": json_bytes({"test": tag, "text": "Synthetic OCR output"}),
            f"paradata-{tag}.json": json_bytes(
                {
                    "@context": "https://w3id.org/ro/crate/1.1/context",
                    "@graph": [{"@id": "./", "@type": "Dataset", "name": tag}],
                }
            ),
        }
        for filename, data in contents.items():
            write_new(inside(out, "binaries/" + filename), data)
            results.append(
                {
                    "filename": filename,
                    "bytes": len(data),
                    "sha256": digest(data),
                    "sha512": hashlib.sha512(data).hexdigest(),
                }
            )
    save_json(inside(out, "binary-manifest.json"), results)
    import zipfile

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for row in sorted(results, key=lambda r: r["filename"]):
            info = zipfile.ZipInfo(row["filename"], (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, inside(out, "binaries/" + row["filename"]).read_bytes())
    write_new(inside(out, "binary-sources.zip"), stream.getvalue())
    by_name = {row["filename"]: row for row in results}
    measured = manifest["batches"][-1]
    payload_bytes = sum(by_name[row["nazev"]]["bytes"] for inputs in measured["tables"].values() for row in inputs)
    expected = {
        "source_files": len(results),
        "source_bytes": sum(x["bytes"] for x in results),
        "source_zip_sha256": digest(stream.getvalue()),
        "measured_binary_writes": 40000,
        "measured_payload_bytes": payload_bytes,
        "setup_originals": 10000,
        "measured_source_files": 30000,
        "expected_distribution_history_entries": 20000,
        "paradata_history_entries": 0,
        "expected_parent_transaction_groups": 5000,
        "operations_per_parent": 8,
        "expected_parent_metadata_updates": 5000,
        "note": "Setup time/binaries/history are outside the measured input; every parent group and direct object must be reconciled",
    }
    save_json(inside(out, "load-expected.json"), expected)
    return expected
