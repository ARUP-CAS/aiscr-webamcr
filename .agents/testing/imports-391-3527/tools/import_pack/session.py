"""Lokální záznam kontrolních bodů a předání bez opakování importních akcí."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from .common import digest, inside, json_bytes, read_json, save_json, write_new


def start_run(root, manifest, run_id, deployment, mode="live", window=None, parity=None):
    """
    Založí nezávislý běh; nevykoná žádnou činnost v aplikaci.

    Nasazení jiné než pinovaný commit se přijme jen s platným záznamem zdrojové shody, který se uloží do běhu.

    :param root: Nový adresář běhu.
    :param manifest: Vybraný manifest sady.
    :param run_id: Bezpečné ID běhu.
    :param deployment: Ověřená nasazená revize.
    :param mode: ``live`` nebo ``simulation``.
    :param window: Schválené okno zátěžového běhu.
    :param parity: Záznam shody z ``deployment-parity``, nebo ``None`` pro pinovaný commit.
    :return: Uložený záznam běhu.
    :raises ValueError: Neznámé nebo neověřené nasazení či neplatné parametry běhu.
    """
    from .deployment import identity

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", run_id):
        raise ValueError("Unsafe run ID")
    if not deployment or deployment.lower() in ("unknown", "test", "latest"):
        raise ValueError("Record the actual deployed revision first")
    if parity is not None and not identity(manifest, deployment, parity)[0]:
        raise ValueError("Parity record does not verify this deployment: " + identity(manifest, deployment, parity)[2])
    if manifest["suite"] == "load" and not window:
        raise ValueError("Load suite needs its separately authorized window")
    if mode not in ("live", "simulation"):
        raise ValueError("Unknown evidence mode")
    record = {
        "run_id": run_id,
        "suite": manifest["suite"],
        "namespace": manifest["namespace"],
        "deployment": deployment,
        "mode": mode,
        "window": window,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": digest(json_bytes(manifest)),
        "manifest": manifest,
    }
    if parity is not None:
        record["deployment_parity"] = parity
    save_json(inside(root, "run.json"), record)
    return record


def checkpoints(root):
    """Načte původní události a ověří jejich návaznost."""
    previous, result = None, []
    for path in sorted((root / "events").glob("*.json")):
        event = read_json(path)
        if event.get("previous_sha256") != previous:
            raise ValueError("Checkpoint chain was altered")
        result.append(event)
        previous = digest(path.read_bytes())
    return result


def retain(root, batch_id, files):
    """Zachová původní důkazy; odlišné existující soubory nepřepíše."""
    result = {}
    if not re.fullmatch(r"[A-Za-z0-9_-]+", batch_id):
        raise ValueError("Unsafe batch ID")
    for kind, source in files.items():
        if not re.fullmatch(r"[a-z0-9-]+", kind):
            raise ValueError("Unsafe evidence kind")
        source = Path(source)
        if source.is_symlink() or not source.is_file():
            raise ValueError("Evidence must be an ordinary local file")
        data = source.read_bytes()
        destination = inside(root, f"{batch_id}/originals/{kind}/{digest(data)}{source.suffix}")
        write_new(destination, data)
        result[kind] = {"path": destination.relative_to(root).as_posix(), "sha256": digest(data), "bytes": len(data)}
    return result


def register_inputs(root, manifest):
    """Retain a late-bound revision without changing run identity or old inputs."""
    run = read_json(root / "run.json")
    for key in ("suite", "namespace", "source_commit", "source_hash_mode", "source_hashes", "generator_hashes"):
        if manifest.get(key) != run["manifest"].get(key):
            raise ValueError("Bound inputs do not belong to this run/source")
    old = {b["id"]: b for b in current_manifest(root)["batches"]}
    if not set(old).issubset({b["id"] for b in manifest["batches"]}):
        raise ValueError("Input revision changes the approved batch scope")
    for batch in manifest["batches"]:
        if batch["id"] not in old:
            parent = old.get(batch.get("derived_from"))
            if (
                not parent
                or batch["operation"] != parent["operation"]
                or not str(parent.get("expected", "")).startswith("reject")
                or not str(batch.get("expected", "")).startswith("reject")
            ):
                raise ValueError("Only isolated probes from an approved negative batch may be added")
            if not set(batch["coverage_ids"]).issubset(parent["coverage_ids"]):
                raise ValueError("Derived probe expands the approved coverage scope")
            bindings = manifest.get("bindings", {})

            def bound(row):
                return {
                    k: bindings.get(v[6:], v) if isinstance(v, str) and v.startswith("$bind:") else v
                    for k, v in row.items()
                }

            if any(
                name not in parent["tables"]
                or any(bound(row) not in [bound(r) for r in parent["tables"][name]] for row in inputs)
                for name, inputs in batch["tables"].items()
            ):
                raise ValueError("Derived probe changes the original input values")
            continue
        original = old[batch["id"]]
        if any(batch.get(key) != original.get(key) for key in ("operation", "coverage_ids", "prerequisites")):
            raise ValueError("Input revision changes the operation/coverage/dependency contract")
    files = sorted((root / "input-revisions").glob("*.json"))
    if files and read_json(files[-1]) == manifest:
        return files[-1]
    path = inside(root, f"input-revisions/{len(files) + 1:04}.json")
    save_json(path, manifest)
    return path


def current_manifest(root):
    files = sorted((root / "input-revisions").glob("*.json"))
    return read_json(files[-1]) if files else read_json(root / "run.json")["manifest"]


def record_checkpoint(root, batch_id, task_id, evidence, state, phase="terminal"):
    """Přidá kontrolní bod s identitou běhu a původním hashem důkazů."""
    run = read_json(root / "run.json")
    manifest = current_manifest(root)
    if batch_id not in {b["id"] for b in manifest["batches"]}:
        raise ValueError("Batch does not belong to this suite/run")
    if state not in ("awaiting-human", "awaiting-agent", "checked", "failed", "blocked"):
        raise ValueError("Unknown checkpoint state")
    if phase not in (
        "preflight",
        "upload",
        "validation",
        "approval",
        "data",
        "history",
        "metadata",
        "binary",
        "terminal",
        "recovery",
    ):
        raise ValueError("Unknown checkpoint phase")
    batch = next(b for b in manifest["batches"] if b["id"] == batch_id)
    if batch.get("deferred"):
        raise ValueError("Batch is deferred by a known importer defect; rebuild after the fix instead of executing it")
    if state == "checked" and (
        batch.get("ready") is False or (batch.get("execution_gate") and not batch.get("gate_resolution"))
    ):
        raise ValueError("Cannot check unresolved inputs or controlled setup as executed")
    for item in evidence.values():
        path = inside(root, item["path"])
        if digest(path.read_bytes()) != item["sha256"]:
            raise ValueError("Retained evidence changed")
    events = checkpoints(root)
    event = {
        "batch_id": batch_id,
        "task_id": task_id,
        "state": state,
        "evidence": evidence,
        "phase": phase,
        "input_sha256": batch.get("input_sha256"),
        "manifest_sha256": digest(json_bytes(manifest)),
        "mode": run["mode"],
        "deployment": run["deployment"],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "previous_sha256": digest(json_bytes(events[-1])) if events else None,
    }
    save_json(inside(root, f"events/{len(events) + 1:04}.json"), event)
    return event


def handoff(root):
    """Vrátí samostatně použitelnou zprávu pro nového agenta."""
    run = read_json(root / "run.json")
    events = checkpoints(root)
    last = events[-1] if events else None
    manifest = current_manifest(root)
    completed = {e["batch_id"] for e in events if e["state"] == "checked" and e.get("phase", "terminal") == "terminal"}
    next_batch = next(
        (
            b
            for b in manifest["batches"]
            if b["id"] not in completed
            and not b.get("deferred")
            and set(b.get("prerequisites", [])).issubset(completed)
        ),
        None,
    )
    if last and last["state"] in ("awaiting-agent", "failed", "blocked"):
        action = "Agent reviews/reconciles retained evidence first; no human mutation or replay."
    elif last and last["state"] == "checked" and last.get("phase") == "validation":
        action = "Agent checks expected outcome; human may start the same validated task only after a positive approval checkpoint. Do not re-upload."
    elif next_batch:
        action = "Agent resolves/preflights and renders the next exact-path card: " + next_batch["id"]
    else:
        action = "Agent checks remaining blocked scenarios and produces the evidence report; do not replay imports."
    return {
        "run_id": run["run_id"],
        "suite": run["suite"],
        "mode": run["mode"],
        "deployment": run["deployment"],
        "evidence_root": str(root.resolve()),
        "last_checkpoint": last,
        "completed_batches": sorted(completed),
        "next_candidate": next_batch["id"] if next_batch else None,
        "next_action": action,
        "deferred_batches": [b["id"] for b in manifest["batches"] if b.get("deferred")],
        "instruction": "Read START-HERE.md and run.json, verify retained hashes, resume from this checkpoint. "
        "The human operates the browser. Do not replay executed imports or delete evidence.",
    }


def recovery(manifest, row_states):
    """Povolí znovupřípravu jen pro explicitně nespuštěné či vrácené řádky."""
    allowed = {"committed", "rolled-back", "unprocessed", "unknown"}
    if any(isinstance(value, dict) for value in row_states.values()):
        if not all(
            isinstance(value, dict) and set(value) == {"db", "history", "metadata", "binary"}
            for value in row_states.values()
        ):
            raise ValueError("Reconcile every row across DB/history/metadata/binary")
        if any(state not in allowed or state == "unknown" for value in row_states.values() for state in value.values()):
            raise ValueError("Reconcile unknown DB/Fedora phase state before recovery")
        eligible = [
            key
            for key, value in row_states.items()
            if value["db"] in ("rolled-back", "unprocessed") and all(state != "committed" for state in value.values())
        ]
        complete = [key for key, value in row_states.items() if all(state == "committed" for state in value.values())]
        repair = [key for key in row_states if key not in eligible and key not in complete]
        return {
            "source_namespace": manifest["namespace"],
            "eligible_for_rebuild": eligible,
            "committed": complete,
            "requires_phase_specific_repair": repair,
            "execute": False,
            "note": "DB-committed partial work must never be replayed as INSERT. Review retained actionable Fedora plans and approve a specific repair method.",
        }
    if any(value not in allowed for value in row_states.values()):
        raise ValueError("Unknown recovery row state")
    if any(value == "unknown" for value in row_states.values()):
        raise ValueError("Reconcile unknown DB/Fedora row state before preparing recovery")
    return {
        "committed": [key for key, value in row_states.items() if value == "committed"],
        "eligible_for_rebuild": [key for key, value in row_states.items() if value in ("rolled-back", "unprocessed")],
        "source_namespace": manifest["namespace"],
        "execute": False,
        "note": "Reconcile report, DB and direct Fedora evidence before authorizing the remaining operations.",
    }


def cleanup_plan(manifest, snapshot, source, baseline=None):
    """Name exact actual run-owned candidates; produce no mutation or evidence deletion."""
    from .oracle import pk

    identities = {
        r["ident_cely"]
        for b in manifest["batches"]
        if b["operation"] == "insert"
        for inputs in b["tables"].values()
        for r in inputs
        if r.get("ident_cely")
    }
    targets = {}
    for table, records in snapshot.items():
        if not isinstance(records, list):
            continue
        model = next((m for m in source["models"].values() if m["table"] == table), None)
        if model:
            owned = [r for r in records if r.get("ident_cely") in identities]
            if owned:
                targets[table] = {"key": pk(model), "values": sorted({r[pk(model)] for r in owned})}
    links = {
        r["soubory"]
        for t in ("dokument", "projekt", "samostatny_nalez")
        for r in snapshot.get(t, [])
        if r.get("ident_cely") in identities and r.get("soubory")
    }
    files = [r for r in snapshot.get("soubor", []) if r.get("vazba") in links]
    previous_pians = {r["id"] for r in (baseline or {}).get("pian", [])}
    previous_pians.update(r["pian_id"] for r in (baseline or {}).get("ruian_katastr", []) if r.get("pian_id"))
    derived = {
        r["pian"]
        for r in snapshot.get("dokumentacni_jednotka", [])
        if r.get("ident_cely") in identities and r.get("pian")
    } - previous_pians
    derived_rows = [
        r for r in snapshot.get("pian", []) if r.get("id") in derived and r.get("ident_cely") not in identities
    ]
    return {
        "namespace": manifest["namespace"],
        "execute": False,
        "requires_separate_authorization": True,
        "root_targets": targets,
        "files": [
            {"import_key": "soub-" + str(r["id"]), "path": r.get("path"), "owner_link": r["vazba"]} for r in files
        ],
        "derived_spatial_units": (
            [{"id": r["id"], "ident_cely": r["ident_cely"]} for r in derived_rows]
            if baseline
            else "UNRECONCILED — provide before snapshot; preserve existing cadastral spatial units"
        ),
        "recipe": [
            "Retain the complete run/evidence folder and this exact target list first",
            "Agent resolves child/composite keys from the retained scoped snapshot; present child-first DELETE CSV inputs with exact hashes",
            "Review references/cascade/restrict effects and any unexpected descendants; do not remove unrelated added records",
            "Human performs approved deletion through the normal import UI; agent verifies these exact IDs/paths and retained evidence afterwards",
        ],
        "preserve": [
            "all original evidence",
            "shared vocabulary/reference rows",
            "non-listed records",
            "Fedora versions/tombstones unless separately approved",
        ],
        "baseline_restored": False,
    }
