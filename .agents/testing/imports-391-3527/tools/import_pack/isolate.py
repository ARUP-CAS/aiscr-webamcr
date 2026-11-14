"""Preserve the parent pack and prepare only already planned negative probes."""

from copy import deepcopy

from .common import PACK, inside, read_json, save_json, write_new


def isolate(manifest_path, output, kind):
    from .branches import LIFECYCLES, RUNTIME
    from .build import add_batch
    from .planning import complete

    source_root = manifest_path.parent.resolve()
    output = output.resolve()
    if output.is_relative_to(source_root) or source_root.is_relative_to(output):
        raise ValueError("Choose a separate sibling output folder for isolated probes")
    manifest = deepcopy(read_json(manifest_path))
    if manifest["suite"] != "behaviour":
        raise ValueError("Only behaviour negative probes may be isolated")
    originals = list(manifest["batches"])
    for path in list(source_root.rglob("*")):
        if path.is_file() and path.name not in ("manifest.json", "coverage-map.json", "sizes.json"):
            if path.is_symlink():
                raise ValueError("Cannot copy a symlink")
            write_new(inside(output, path.relative_to(source_root).as_posix()), path.read_bytes())
    cases = (
        manifest["negative_probes"]
        if kind == "fields"
        else [
            c
            for c in manifest["branch_scenarios"]
            if c["outcome"] == "reject" and c["variant"] not in RUNTIME | LIFECYCLES
        ]
    )
    inventory = read_json(PACK / "definitions/inventory.json")
    from .build import finish_known_defects
    from .known_defects import load_definitions

    # Derived probes are classified like any other input; a deferred parent defers its probes.
    manifest["_defect_context"] = {"source": inventory, "defects": load_definitions(inventory)}
    by_name = {m["csv"]: m for m in inventory["mappers"]}
    children = []
    for index, case in enumerate(cases, 1):
        parent = next(
            b for b in originals if case["id"] in b["coverage_ids"] and str(b["expected"]).startswith("reject")
        )
        batch_id = f"S-{kind}-{index:03}"
        if any(b["id"] == batch_id for b in originals):
            continue
        tables = {case["class"]: case.get("rows", [case["row"]]), **case.get("extra_tables", {})}
        if parent["operation"] == "delete":
            tables = {
                name: [
                    {
                        key: row[key]
                        for key in (
                            list(by_name[name]["key"])
                            if isinstance(by_name[name]["key"], list)
                            else [by_name[name]["key"]]
                        )
                        + (["distribution"] if name in ("distribution", "paradata") else [])
                    }
                    for row in inputs
                ]
                for name, inputs in tables.items()
            }
        add_batch(
            output,
            manifest,
            batch_id,
            parent["operation"],
            tables,
            [case["id"]],
            [parent["id"]],
            "reject intended isolated diagnostic",
        )
        manifest["batches"][-1]["derived_from"] = parent["id"]
        children.append(manifest["batches"][-1])
    ordered = []
    for batch in originals:
        ordered.append(batch)
        ordered.extend(child for child in children if child["derived_from"] == batch["id"])
    manifest["batches"] = ordered
    finish_known_defects(manifest)
    manifest["preparation"] = complete(output, manifest, inventory)
    save_json(inside(output, "manifest.json"), manifest)
    return {
        "new_isolated_inputs": len(children),
        "note": "Use only concealed probes. Preserve earlier results; no imports are submitted and no executed mutation is replayed.",
    }
