"""Jeden krok živého běhu: sloučit vazby, sestavit vázané vstupy, převést běh na revizi a vykreslit karty."""

import json
from pathlib import Path

from .common import PACK, read_json, repo_root


def merged_bindings(root):
    """
    Sloučí všechny ``bindings-*.json`` běhu do jedné mapy a zapíše ji jako ``bindings.json``.

    :param root: Adresář běhu.
    :return: Sloučená mapa vazeb.
    :raises ValueError: Pokud dva soubory váží stejný klíč na různé hodnoty.
    """
    merged, origin = {}, {}
    for path in sorted(root.glob("bindings-*.json")):
        for key, value in read_json(path).items():
            if key in merged and merged[key] != value:
                raise ValueError(f"Binding conflict for {key}: {origin[key]} vs {path.name}")
            merged[key], origin[key] = value, path.name
    (root / "bindings.json").write_text(json.dumps(merged, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return merged


def prune(root, manifest, current_instructions):
    """
    Odstraní nahrazené kopie vstupů a karet, na které neodkazuje žádný kontrolní bod.

    Zachová aktuální vstup každé dávky, každý vstup s kontrolním bodem (jeho bajty byly předloženy) a
    aktuální adresář karet. Mazání se týká jen kopií vytvořených balíčkem, nikoli důkazů.

    :param root: Adresář běhu.
    :param manifest: Aktuální manifest běhu.
    :param current_instructions: Adresář právě vykreslených karet.
    :return: Počty odstraněných kopií vstupů a adresářů karet.
    """
    import shutil

    from .session import checkpoints

    used = {(e["batch_id"], e.get("input_sha256")) for e in checkpoints(root)}
    current = {b["id"]: b["input_sha256"] for b in manifest["batches"]}
    removed_inputs = 0
    for batch_id, sha in current.items():
        for copy in (root / batch_id / "input").glob("*"):
            if copy.is_dir() and copy.name != sha and (batch_id, copy.name) not in used:
                shutil.rmtree(copy)
                removed_inputs += 1
    removed_cards = 0
    for folder in (root / "instructions").glob("*"):
        if folder.is_dir() and folder.resolve() != current_instructions.resolve():
            shutil.rmtree(folder)
            removed_cards += 1
    return {"removed_input_copies": removed_inputs, "removed_card_folders": removed_cards}


def refresh_snapshot(root, built):
    """
    Udrží v kořeni běhu jediný ``snapshot.sql``; dotaz je společný pro celý jmenný prostor běhu.

    Každý zveřejněný rozsah se uchová v ``snapshot-scopes/<scope_sha256>.json``, aby ověření dávky poznalo
    export z dříve otevřené (zastaralé) verze dotazu.

    :param root: Adresář běhu.
    :param built: Právě sestavený adresář ``bind-NNNN``.
    :return: ``True``, pokud se dotaz oproti předchozímu změnil a operátor má použít novou verzi.
    """
    target = root / "snapshot.sql"
    content = (built / "sql" / "snapshot.sql").read_bytes()
    changed = not target.is_file() or target.read_bytes() != content
    if changed:
        target.write_bytes(content)
    scope = built / "sql" / "snapshot-scope.json"
    if scope.is_file():
        kept = root / "snapshot-scopes" / (read_json(scope)["scope_sha256"] + ".json")
        if not kept.is_file():
            kept.parent.mkdir(exist_ok=True)
            kept.write_bytes(scope.read_bytes())
    return changed


def advance(root, references, output_root, reason=None, reviewer=None):
    """
    Provede v jednom kroku sestavení vázaných vstupů, případnou revizi balíčku, vykreslení karet a předání.

    Nová revize balíčku (změněné ``generator_hashes``) se přijme jen s důvodem a recenzentem a za stejných
    podmínek jako ``revise_pack``. Beze změny generátoru se vstupy jen zaregistrují při vykreslení.

    :param root: Adresář běhu.
    :param references: Cesta k exportu referencí z testovací DB.
    :param output_root: Adresář, do něhož se přidá další ``bind-NNNN``.
    :param reason: Důvod revize; povinný jen při změně generátoru.
    :param reviewer: Recenzent revize; povinný jen při změně generátoru.
    :return: Shrnutí: sestavený adresář, revize, další dávka a její karta.
    :raises ValueError: Při konfliktu vazeb nebo revizi bez důvodu a recenzenta.
    """
    from .build import build_behaviour, build_load
    from .operator import render
    from .session import checkpoints, executed_batches, handoff, identity_manifest, revise_pack

    run = read_json(root / "run.json")
    bindings = merged_bindings(root)
    executed = executed_batches(root)
    retained = {e["batch_id"]: e.get("input_sha256") for e in checkpoints(root) if e["batch_id"] in executed}
    from .session import current_manifest, effective_checkpoints

    terminal = {}
    for event in effective_checkpoints(root):
        if event.get("phase") == "terminal":
            terminal.setdefault(event["batch_id"], set()).add(event["state"])
    failed_executions = {}
    for batch in current_manifest(root)["batches"]:
        if terminal.get(batch["id"]) == {"failed"}:
            copy = root / batch["id"] / "input" / batch["input_sha256"] / Path(batch["input"]).name
            if copy.is_file():
                failed_executions[batch["id"]] = {"batch": batch, "data": copy.read_bytes()}
    output_root.mkdir(parents=True, exist_ok=True)
    numbers = [int(p.name[5:]) for p in output_root.glob("bind-[0-9][0-9][0-9][0-9]")]
    out = output_root / f"bind-{max(numbers, default=0) + 1:04}"
    source = read_json(PACK / "definitions/inventory.json")
    refs = read_json(references)
    if run["suite"] == "behaviour":
        try:
            repo = repo_root()
        except ValueError:
            repo = None
        manifest = build_behaviour(out, source, run["namespace"], refs, repo, bindings, retained, failed_executions)
    else:
        manifest = build_load(
            out, source, run["namespace"], refs, run["manifest"].get("workload"), bindings, retained, failed_executions
        )
    revision = None
    if manifest.get("generator_hashes") != identity_manifest(root).get("generator_hashes"):
        if not reason or not reviewer:
            raise ValueError("Pack code changed since the run's revision: pass --reason and --reviewer")
        revision = revise_pack(root, read_json(out / "manifest.json"), reason, reviewer)
    from .recipe_audit import audit_rows, audit_uniqueness

    # Catch recipe and unique-key defects before the operator uploads anything built here.
    # A kept failed original persisted nothing (its run was revoked), so it cannot collide with anything.
    live = [b for b in manifest["batches"] if b["id"] not in failed_executions]
    audit = {
        "recipe_findings": audit_rows(source, live)["findings"],
        "uniqueness_findings": audit_uniqueness(source, live),
    }
    rendered = render(out, root)
    snapshot_changed = refresh_snapshot(root, out)
    cards = Path(rendered[0]["instruction"]).parent if rendered else root / "instructions"
    pruned = prune(root, manifest, cards)
    state = handoff(root)
    batch = next((b for b in manifest["batches"] if b["id"] == state.get("next_candidate")), None)
    card = None
    entry = next((item for item in rendered if batch and item["batch"] == batch["id"]), None)
    if batch:
        card = {
            "batch": batch["id"],
            "card": entry and entry["instruction"],
            "input": str(root / batch["id"] / "input" / batch["input_sha256"] / Path(batch["input"]).name),
            "input_sha256": batch["input_sha256"],
            "operation": batch["operation"],
            "expected": batch.get("expected"),
            "rows": sum(len(rows) for rows in batch["tables"].values()),
            "ready": batch["ready"],
            "unresolved": batch["unresolved"],
        }
    return {
        "built": str(out),
        "bindings": len(bindings),
        "revision": revision and {k: revision[k] for k in ("manifest", "changed_batches")},
        "snapshot_sql": {"path": str(root / "snapshot.sql"), "changed": snapshot_changed},
        "pruned": pruned,
        "audit": audit,
        "completed_batches": state.get("completed_batches"),
        "next": card,
    }
