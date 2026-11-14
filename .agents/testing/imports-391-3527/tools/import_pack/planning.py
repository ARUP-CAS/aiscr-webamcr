"""Concrete check manifests, resource links, bounds and source-to-ledger receipts."""

import ast
import hashlib
import zipfile

from .catalog import EFFECTS, VARIANTS
from .common import digest, inside, save_json, write_new
from .scenarios import scenarios
from .sql import reference_sql, schema_sql, snapshot_sql
from .verify import fedora_urls, record_urls


def complete(directory, manifest, source):
    """Emit complete machine-readable checkpoint/check contracts for each input."""
    identifiers = sorted(
        {
            r["ident_cely"]
            for b in manifest["batches"]
            for inputs in b["tables"].values()
            for r in inputs
            if r.get("ident_cely")
        }
    )
    write_new(inside(directory, "sql/references.sql"), reference_sql(source).encode())
    write_new(inside(directory, "sql/schema.sql"), schema_sql().encode())
    write_new(inside(directory, "sql/snapshot.sql"), snapshot_sql(source, identifiers).encode())
    binary_index = {}
    for path in sorted((directory / "binaries").glob("*")):
        content = path.read_bytes()
        binary_index[path.name] = {
            "bytes": len(content),
            "sha256": digest(content),
            "sha512": hashlib.sha512(content).hexdigest(),
        }
    save_json(inside(directory, "binary-checksums.json"), binary_index)
    coverage_map = {}
    sizes = []
    for batch in manifest["batches"]:
        for item in batch["coverage_ids"]:
            coverage_map.setdefault(item, []).append(batch["id"])
        input_path = inside(directory, batch["input"])
        try:
            with zipfile.ZipFile(input_path) as archive:
                expanded = sum(info.file_size for info in archive.infolist())
        except zipfile.BadZipFile:
            expanded = None
        sizes.append(
            {
                "batch": batch["id"],
                "compressed_bytes": input_path.stat().st_size,
                "expanded_bytes": expanded,
                "below_source_1GiB_guard": expanded is not None and expanded < 1024**3,
            }
        )
        contract = {
            "batch_id": batch["id"],
            "input_sha256": batch["input_sha256"],
            "operation": batch["operation"],
            "outcome": batch["expected"],
            "coverage_ids": batch["coverage_ids"],
            "row_values": "Every input row via verify-batch; independent exact-value/FK/geometry checks; report is not the oracle",
            "effects": {
                name: {
                    "metadata_targets": EFFECTS[name][0],
                    "history_targets": EFFECTS[name][1],
                    "former_and_new_parents": True,
                    "untouched_siblings": True,
                }
                for name in batch["tables"]
            },
            "history": {
                "actor": "verified session operator DB identity",
                "normal_type": "IMP",
                "normal_note": "sorted CSV basenames joined by comma per deduplicated target",
                "distribution_type": {"insert": "DIST01", "update": "DIST11", "delete": "DIST10"}.get(
                    batch["operation"]
                ),
                "distribution_note": "exact normalized distribution name",
                "paradata_only": "no history or DB/XML changes",
                "file_note": "PO imported-file text plus actual source directory/parent ID/filename; DELETE uses CSV basename",
            },
            "mandatory": [
                "DB row/value/relationship checks",
                "omitted fields and untouched sibling controls",
                "exact history target/actor/note/multiplicity",
                "direct metadata XML semantic values, bytes and versions",
                "binary status/SHA512/MIME/filename and expected absence",
                "actual human observation and intended report error",
            ],
            "negative_error": batch.get("negative_error"),
            "state": "prepared",
        }
        if any(c["variant"].startswith("cadastral-") for c in batch.get("case_details", [])):
            contract["derived_graph"] = {
                "cadastre": "Exact main cadastre of the selected Fieldwork event/Site; preserve all fields except the planned pian_id link",
                "spatial_unit": "Reuse prior exact ID or one new geometry identical to cadastral boundary; consistent 5514/4326 pair and map sheets",
                "history": "New spatial-unit creation history uses verified ADMIN_USER; Fieldwork event/Site import history uses the session operator",
                "metadata": "New spatial unit, changed cadastre and owning Fieldwork event/Site; assert untouched sibling controls",
                "cleanup": "Retain actual derived ID; never classify a reused pre-existing cadastral spatial unit as run-owned",
            }
        save_json(inside(directory, "checks/" + batch["id"] + ".json"), contract)
    missing = [
        item["id"]
        for item in manifest.get("coverage", [])
        if item["class"] != "session" and item["id"] not in coverage_map
    ]
    if missing:
        raise ValueError("Coverage without observable batch: " + str(missing))
    save_json(inside(directory, "coverage-map.json"), coverage_map)
    if manifest["suite"] == "behaviour":
        diagnostics = []
        for case in manifest["negative_probes"]:
            parent = next(
                b for b in manifest["batches"] if case["id"] in b["coverage_ids"] and not b.get("derived_from")
            )
            # Resolve any late numeric aliases exactly as the parent input did.
            original = {
                k: manifest.get("bindings", {}).get(v[6:], v) if isinstance(v, str) and v.startswith("$bind:") else v
                for k, v in case["row"].items()
            }
            ordinal = parent["tables"][case["class"]].index(original) + 1
            diagnostics.append(
                {
                    "id": case["id"],
                    "class": case["class"],
                    "field": case["field"],
                    "batch_id": parent["id"],
                    "csv_row": ordinal,
                    "diagnostic_column": None,
                    "diagnostic_regex": None,
                    "agent_action": "Resolve the intended field/error regex using definitions/import-messages.json and actual report diagnostics; do not accept an earlier unrelated error",
                }
            )
        save_json(inside(directory, "negative-diagnostics.template.json"), diagnostics)
    save_json(inside(directory, "scenarios.json"), scenarios() if manifest["suite"] == "behaviour" else [])
    if manifest["suite"] == "behaviour":
        from .branches import RUNTIME
        from .controlled import recipe

        save_json(
            inside(directory, "controlled-recipes.json"),
            [
                recipe(case, manifest["namespace"], {}, manifest.get("bindings"))
                for case in manifest["branch_scenarios"]
                if case["variant"] in RUNTIME or case["outcome"] == "acceptance-unresolved"
            ],
        )
    save_json(inside(directory, "sizes.json"), sizes)
    save_json(
        inside(directory, "preflight-template.json"),
        {
            key: None
            for key in (
                "deployed_commit",
                "application_timezone",
                "operator_ident",
                "import_volume_container_path",
                "import_volume_transfer_route",
                "report_container_path",
                "db_read_route",
                "fedora_read_route",
                "session_authorization",
                "load_window_authorization",
                "capacity_checked",
                "stop_conditions",
            )
        },
    )
    if manifest["suite"] == "load":
        from .reporting import measured_spec

        specs = manifest.get("measured_batches") or [measured_spec(manifest)[0]]
        by_id = {b["id"]: b for b in manifest["batches"]}
        for spec in specs:
            # One template per measured import; a single combined import keeps the original filename.
            name = "load-evidence.template.json" if len(specs) == 1 else f"load-evidence.{spec['id']}.template.json"
            save_json(
                inside(directory, name),
                {
                    "mode": "unexecuted",
                    "suite": "load",
                    "workload": manifest["workload"],
                    "namespace": manifest["namespace"],
                    "run_id": None,
                    "deployment": None,
                    "captured_at": None,
                    "manifest_sha256": None,
                    "input_sha256": by_id[spec["id"]]["input_sha256"],
                    "batch_id": spec["id"],
                    "measured_label": spec["label"],
                    "task_id": None,
                    "evidence": {},
                    "counts": {key: None for key in spec["counts"]},
                    "phases": [],
                    "assertions": [],
                    "metrics": {
                        key: None for key in ("cpu", "memory", "db", "fedora", "queue", "polls", "report_bytes")
                    },
                    "human_responsiveness": None,
                    "window_authorization": None,
                    "phase_format": {
                        "name": "data/history/metadata/binary/validation/setup",
                        "start": "ISO8601 with timezone",
                        "end": "ISO8601 with timezone",
                        "rows": None,
                        "measured": False,
                    },
                },
            )
        if manifest["workload"] == "relational":
            combined = by_id["L01-relational-50000"]
            original = {
                "measured_rows": 50000,
                "new_projects": 10000,
                "new_fieldwork_events": 10000,
                "new_documentation_units": 10000,
                "new_components": 10000,
                "new_finds": 10000,
                "expected_deduplicated_import_history": 20000,
                "expected_metadata_targets": [
                    r["ident_cely"] for name in ("projekty", "az_akce") for r in combined["tables"][name]
                ],
                "graph": "For every ordinal i: project[i] <- Fieldwork event[i] <- documentation unit[i] <- component[i] <- find[i]; reusable setup spatial unit is not a measured new row",
                "database_transactions": 1,
                "setup_excluded": True,
                "state": "blocked" if combined.get("deferred") else "prepared",
            }
            if manifest.get("substitute"):
                original["blocked_by"] = combined["deferred"]["defects"]
                save_json(
                    inside(directory, "load-expected.json"),
                    {
                        "combined": original,
                        "substitute": {
                            "label": manifest["substitute"]["label"],
                            "reason": manifest["substitute"]["reason"],
                            "imports": [
                                {
                                    "batch_id": s["id"],
                                    "counts": s["counts"],
                                    "expected_deduplicated_import_history": s["expected_deduplicated_import_history"],
                                    "expected_metadata_targets": s["metadata_targets"],
                                    "database_transactions": 1,
                                    "setup_excluded": True,
                                    "state": "prepared",
                                }
                                for s in specs
                            ],
                        },
                    },
                )
            else:
                save_json(inside(directory, "load-expected.json"), original)
    current = [b for b in manifest["batches"] if not b.get("deferred")]
    return {
        "uploads": sum(b.get("execution_kind") != "controlled-procedure" for b in current),
        "procedures": sum(b.get("execution_kind") == "controlled-procedure" for b in current),
        "controlled": sum(bool(b.get("execution_gate")) for b in current),
        "deferred_batches": [b["id"] for b in manifest["batches"] if b.get("deferred")],
        "deferred_coverage": sorted({c for b in manifest["batches"] if b.get("deferred") for c in b["coverage_ids"]}),
        "coverage_items": len(manifest.get("coverage", [])),
        "covered_by_inputs": len(coverage_map),
        "sizes": sizes,
    }


def urls(snapshot):
    result = {}
    for table, rows in snapshot.items():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if row.get("ident_cely"):
                result[row["ident_cely"]] = record_urls(row["ident_cely"])
    for row in snapshot.get("soubor", []):
        if row.get("path"):
            result["soub-" + str(row["id"])] = fedora_urls(row["path"])
    return result


def audit(source, repo):
    """Keep every class's special methods/branches beside its concrete cases."""
    tree = ast.parse((repo / "webclient/core/import_data_mappers.py").read_text(encoding="utf-8"))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    from .coverage import coverage

    ledger = coverage(source)
    result = []
    for mapper in source["mappers"]:
        node = classes[mapper["class"]]
        linked = [c["id"] for c in ledger if c["class"] == mapper["csv"]]
        branches = [
            {"line": n.lineno, "condition": ast.unparse(n.test), "ledger_ids": linked}
            for n in ast.walk(node)
            if isinstance(n, ast.If)
        ]
        result.append(
            {
                "class": mapper["csv"],
                "source_line": mapper["line"],
                "methods": mapper["special_methods"],
                "source_branches": branches,
                "coverage_variants": VARIANTS[mapper["csv"]],
                "lookup_fields": {k: v["definition"] for k, v in mapper["columns"].items() if v.get("definition")},
                "model_constraints": source["models"].get(mapper["model"], {}).get("constraints", []),
                "acceptance": "Cycles/self links and negative counts remain explicit questions; no inferred pass. Missing companion/thumbnail/backfill/fault cases require isolated authorized setup.",
            }
        )
    for name in (
        "ImportModelMapper",
        "MultipleClassImportModelMapper",
        "GeometryTransformMixin",
        "LookupImportField",
        "VazbaLookupImportField",
        "UserRelationMapperMixin",
    ):
        node = classes[name]
        result.append(
            {
                "shared_helper": name,
                "source_line": node.lineno,
                "branches": [
                    {"line": n.lineno, "condition": ast.unparse(n.test)}
                    for n in ast.walk(node)
                    if isinstance(n, ast.If)
                ],
                "ledger_contract": "Baseline operations plus per-field boundary probes and named geometry/owner/forward-reference cases. This is traceability, not measured runtime line coverage.",
            }
        )
    return result
