"""Local readiness checks; missing deployment facts never inherit source facts."""

from .common import SOURCE_HASH_MODE, generator_hashes, source_digest

FIELDS = (
    "deployed_commit",
    "application_timezone",
    "operator_ident",
    "import_volume_container_path",
    "import_volume_transfer_route",
    "report_container_path",
    "db_read_route",
    "fedora_read_route",
    "session_authorization",
)


def evaluate(manifest, source, facts, schema, refs, baseline):
    checks = []

    def add(name, okay, reason):
        checks.append({"id": name, "state": "passed" if okay else "blocked", "reason": reason})

    for field in FIELDS:
        add(
            field,
            bool(facts.get(field)) and str(facts[field]).lower() not in ("unknown", "test", "latest"),
            "Record verified current test-instance value",
        )
    from .deployment import identity

    deployment_verified, withheld, deployment_reason = identity(
        manifest, facts.get("deployed_commit"), facts.get("deployment_parity")
    )
    add(
        "deployment-match",
        deployment_verified,
        deployment_reason + "; a different deployment needs a parity record "
        "(source-equivalent, or every differing file reviewed with its withheld coverage) or a refreshed inventory",
    )
    add(
        "application-timezone",
        facts.get("application_timezone") == "Europe/Prague",
        "This pack's expected date/datetime values use the inspected application timezone; a configuration difference needs explicit reconciliation",
    )
    add(
        "source-hash-mode",
        manifest.get("source_hash_mode") == source.get("source_hash_mode") == SOURCE_HASH_MODE,
        "Pack and inventory must use the current line-ending-normalised hash rule",
    )
    add(
        "source-drift",
        manifest["source_hashes"] == source["source_hashes"],
        "Pack and inspected source hashes must match",
    )
    add(
        "generator-drift",
        manifest.get("generator_hashes") == generator_hashes(),
        "Generator code/frozen definitions must match this immutable dataset",
    )
    add(
        "schema-export",
        bool(schema.get("columns")) and bool(schema.get("constraints")),
        "Current read-only schema export is required",
    )
    present = {(r["table_name"], r["column_name"]) for r in schema.get("columns", [])}
    required_columns = set()
    for mapper in source.get("mappers", []):
        model = source["models"].get(mapper["model"], {})
        for field, info in model.get("fields", {}).items():
            if info["type"] in ("ManyToManyField", "GenericForeignKey"):
                continue
            column = info.get("db_column", field + "_id" if info["type"] in ("ForeignKey", "OneToOneField") else field)
            required_columns.add((model["table"], column))
    add(
        "schema-columns",
        required_columns.issubset(present) and bool(present),
        "Missing columns: " + str(sorted(required_columns - present)),
    )
    add(
        "reference-identities",
        bool(refs.get("reference_rows")),
        "Missing lookup values block affected inputs; do not substitute production numeric keys",
    )
    terms = refs.get("reference_rows", {}).get("heslar", [])
    from .catalog import RECIPES

    classes = {name for b in manifest["batches"] for name in b["tables"]}
    used_families = {
        value[5:]
        for name in classes
        for value in RECIPES[name].values()
        if isinstance(value, str) and value.startswith("$ref:HESLAR_")
    }
    family_errors = [
        key
        for key, family in source.get("vocabulary_constants", {}).items()
        if key in used_families
        if len([r for r in terms if r.get("ident_cely") == refs.get(key) and r.get("nazev_heslare") == family]) != 1
    ]
    add("vocabulary-families", not family_errors and bool(terms), "Wrong/missing families: " + ",".join(family_errors))
    desired = {
        str(r["ident_cely"])
        for b in manifest["batches"]
        if b["operation"] == "insert"
        for inputs in b["tables"].values()
        for r in inputs
        if r.get("ident_cely")
    }
    found = {
        str(r["ident_cely"])
        for inputs in baseline.values()
        if isinstance(inputs, list)
        for r in inputs
        if isinstance(r, dict) and r.get("ident_cely") in desired
    }
    add(
        "unused-identifiers",
        bool(baseline) and not found,
        (
            "Conflicts: " + ",".join(sorted(found))
            if found
            else "Scoped initial snapshot must be captured before setup; resume uses retained checkpoints"
        ),
    )
    add(
        "input-resolution",
        all(b["ready"] for b in manifest["batches"] if not b.get("execution_gate") and not b.get("deferred")),
        "Late numeric keys must be bound at their own checkpoint before their dependent batch",
    )
    if manifest["suite"] == "load":
        add(
            "load-window",
            bool(facts.get("load_window_authorization")),
            "Separate approval, window and stop budget for this workload",
        )
        add(
            "capacity",
            bool(facts.get("capacity_checked")) and bool(facts.get("stop_conditions")),
            "Record expanded ZIP limit, storage capacity and agreed stop conditions",
        )
    return {
        "suite": manifest["suite"],
        "ready": all(c["state"] == "passed" for c in checks),
        "checks": checks,
        "withheld_coverage": sorted(withheld),
        "missing_reference_values": [key for key, value in refs.items() if value is None or value == ""],
        "batch_inputs": [
            {
                "id": b["id"],
                "ready": b["ready"],
                "unresolved": b["unresolved"],
                "controlled": bool(b.get("execution_gate")),
                "deferred": bool(b.get("deferred")),
            }
            for b in manifest["batches"]
        ],
        "known_defects": [
            {"id": d["id"], "deferred_batches": d["deferred_batches"]} for d in manifest.get("known_defects", [])
        ],
        "note": "Readiness is per checkpoint. Future binding blocks do not prevent independent foundation preparation.",
    }


def source_drift(source, repo):
    """
    Vrátí pinované zdrojové soubory, jejichž normalizovaný obsah v checkoutu neodpovídá inventáři.

    :param source: Zmrazený inventář s ``source_hashes`` a ``source_hash_mode``.
    :param repo: Kořen zdrojového checkoutu.
    :return: Seřazený seznam relativních cest chybějících nebo změněných souborů.
    :raises ValueError: Inventář byl otisknut jiným pravidlem, jeho otisky nelze porovnat.
    """
    if source.get("source_hash_mode") != SOURCE_HASH_MODE:
        raise ValueError("Inventory uses a different source hash mode; refresh it before comparing")
    return sorted(
        name
        for name, expected in source["source_hashes"].items()
        if not (repo / name).is_file() or source_digest((repo / name).read_bytes()) != expected
    )
