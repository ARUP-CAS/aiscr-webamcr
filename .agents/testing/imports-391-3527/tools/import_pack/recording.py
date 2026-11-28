"""Záznam provedené dávky (ověření, audit Fedory, kontrolní body) a odvození hodnocení pro report běhu."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .common import PACK, digest, inside, json_bytes, read_json, save_json, write_new

OBSERVATIONS = "operator-observations.json"


def snapshot_diff(before, after):
    """
    Porovná dva exporty DB po tabulkách (bez klíčů ``_provenance`` apod.).

    :param before: Export před.
    :param after: Export po.
    :return: Slovník ``tabulka -> {"removed": n, "added": n}`` jen pro změněné tabulky.
    """
    result = {}
    for table in sorted(set(before) | set(after)):
        if table.startswith("_"):
            continue
        old = {json.dumps(r, sort_keys=True) for r in before.get(table, [])}
        new = {json.dumps(r, sort_keys=True) for r in after.get(table, [])}
        if old != new:
            result[table] = {"removed": len(old - new), "added": len(new - old)}
    return result


def free_name(directory, stem, suffix=".json"):
    """Vrátí první nepoužitý název ``stem.json``, ``stem-2.json`` …; existující důkazy se nikdy nepřepisují."""
    path, number = directory / f"{stem}{suffix}", 2
    while path.exists():
        path, number = directory / f"{stem}-{number}{suffix}", number + 1
    return path


def fedora_changes(root, batch_id, reader, since=None, until=None):
    """
    Uloží audit změn ve Fedoře v okně dávky (db-before → db-after) a rozdělí je na plánované, vlastní a cizí.

    :param root: Adresář běhu.
    :param batch_id: ID dávky.
    :param reader: Čtecí klient testovací Fedory.
    :param since: Začátek okna; výchozí je ``captured_at`` z ``db-before.json``.
    :param until: Konec okna; výchozí je ``captured_at`` z ``db-after.json``, pokud existuje.
    :return: Dvojice (cesta k uloženému auditu, výsledek).
    """
    from .fedora_audit import classify, modified_since, utc
    from .session import current_manifest

    batch_dir = root / batch_id
    since = utc(since or read_json(batch_dir / "db-before.json")["_provenance"]["captured_at"])
    plan = batch_dir / "fedora-plan.json"
    planned = (
        {u["url"].split("/record/")[1].split("/")[0] for u in read_json(plan)["resources"]} if plan.is_file() else set()
    )
    after = batch_dir / "db-after.json"
    until = until or (read_json(after)["_provenance"]["captured_at"] if after.is_file() else None)
    until = utc(until) if until else None
    found = modified_since(reader, since, until=until)
    result = {"batch": batch_id, "since": since, "until": until, "complete": found["complete"], "items": found["items"]}
    result.update(classify(found["items"], current_manifest(root), planned))
    body = json_bytes(result)
    path = batch_dir / f"fedora-changes-{digest(body)[:12]}.json"
    write_new(path, body)
    return path, result


def direct_reads(reader, idents):
    """
    Přímo přečte záznamy ve Fedoře: stav záznamu a členství v modelu ``deleted``.

    :param reader: Čtecí klient testovací Fedory.
    :param idents: Identifikátory záznamů.
    :return: Výsledek s časem pořízení a HTTP stavy.
    """
    base = "https://fedora-test.aiscr.cz/rest/AMCR/"
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "records": {
            ident: {
                "record": reader.get(f"{base}record/{ident}", "*/*")["status"],
                "deleted_member": reader.get(f"{base}model/deleted/member/{ident}", "*/*")["status"],
            }
            for ident in idents
        },
    }


def verify(root, batch_id, references):
    """
    Spustí orákulum dávky proti jejím exportům a uloží výsledek pod nepoužitým názvem.

    :param root: Adresář běhu.
    :param batch_id: ID dávky.
    :param references: Export referencí z testovací DB (slovník).
    :return: Dvojice (cesta, seznam kontrol).
    """
    from .oracle import captured_scopes, check_batch
    from .session import current_manifest

    batch = next(b for b in current_manifest(root)["batches"] if b["id"] == batch_id)
    before, after = read_json(root / batch_id / "db-before.json"), read_json(root / batch_id / "db-after.json")
    checks = check_batch(
        read_json(PACK / "definitions/inventory.json"),
        batch,
        before,
        after,
        references,
        captured_scopes(root, before, after),
    )
    path = free_name(root / batch_id, "verify-batch")
    save_json(path, checks)
    return path, checks


def record_batch(root, batch_id, task_id, screenshot, state, references, reader, summary="", idents=()):
    """
    Zaznamená provedenou dávku: ověření, audit Fedory, rozdíly exportů a kontrolní body validace a terminální fáze.

    Bez ``validation-report.xlsx``, ``db-before.json`` a ``db-after.json`` nic nezapíše. ``final-report.xlsx`` je
    terminální report; bez něj (odmítnutí ve validaci) je terminálním reportem report validace. Řízená příprava
    (``db-before-setup.json``, ``*-setup.sql``, ``*-restore.sql``, ``db-after-restore.json``) se přidá k důkazům
    i s rozdíly příprava/obnova. Přepsané snímky obrazovky se jako pozorování člověka neukládají.

    :param root: Adresář běhu.
    :param batch_id: ID dávky.
    :param task_id: ID úlohy z reportu (``report-…``).
    :param screenshot: Cesta ke snímku konečné obrazovky.
    :param state: Terminální stav ``checked`` nebo ``failed``.
    :param references: Export referencí z testovací DB (slovník).
    :param reader: Čtecí klient testovací Fedory.
    :param summary: Krátký popis výsledku do ``effects-check``.
    :param idents: Záznamy k přímému čtení ve Fedoře (např. smazané).
    :return: Shrnutí: kontroly, audit Fedory, rozdíly a zapsané kontrolní body.
    :raises ValueError: Při chybějících souborech, neznámém stavu nebo dávce bez kopie vstupu.
    """
    from .session import current_manifest, record_checkpoint, retain

    if state not in ("checked", "failed"):
        raise ValueError("Terminal state must be checked or failed")
    batch_dir = root / batch_id
    missing = [
        n for n in ("db-before.json", "validation-report.xlsx", "db-after.json") if not (batch_dir / n).is_file()
    ]
    if missing:
        raise ValueError("Missing evidence, nothing recorded: " + ", ".join(missing))
    batch = next(b for b in current_manifest(root)["batches"] if b["id"] == batch_id)
    inputs = sorted((batch_dir / "input" / batch["input_sha256"]).glob("*.zip"))
    if not inputs:
        raise ValueError("No retained input copy for the batch's current input")
    final = batch_dir / "final-report.xlsx"
    ui = batch_dir / ("ui-final.png" if final.is_file() else "ui-validation.png")
    shot = Path(screenshot).read_bytes()
    if ui.is_file() and ui.read_bytes() != shot:
        raise ValueError(f"{ui.name} already exists with different content")
    if not ui.is_file():
        shutil.copyfile(screenshot, ui)
    verify_path, checks = verify(root, batch_id, references)
    fedora_path, fedora = fedora_changes(root, batch_id, reader)
    before, after = read_json(batch_dir / "db-before.json"), read_json(batch_dir / "db-after.json")
    effects = {
        "summary": summary,
        "verify": {
            "file": verify_path.name,
            "checks": len(checks),
            "failed": sum(c["state"] == "failed" for c in checks),
            "blocked": sum(c["state"] == "blocked" for c in checks),
        },
        "import_diff": snapshot_diff(before, after),
        "fedora_audit": {
            "file": fedora_path.name,
            "complete": fedora["complete"],
            "own": fedora["unplanned_own"] + fedora["planned"],
            "outside": fedora["outside"],
        },
    }
    evidence = {
        "input": inputs[0],
        "db-before": batch_dir / "db-before.json",
        "report": batch_dir / "validation-report.xlsx",
    }
    terminal = {
        **evidence,
        "report": final if final.is_file() else batch_dir / "validation-report.xlsx",
        "validation-report": batch_dir / "validation-report.xlsx",
        "db-after": batch_dir / "db-after.json",
        "fedora-changes": fedora_path,
        "verify-batch": verify_path,
        "ui": ui,
    }
    setup = batch_dir / "db-before-setup.json"
    if setup.is_file():
        effects["setup_diff"] = snapshot_diff(read_json(setup), before)
        terminal["db-before-setup"] = setup
        restore = batch_dir / "db-after-restore.json"
        if restore.is_file():
            effects["restore_vs_before_setup"] = snapshot_diff(read_json(setup), read_json(restore))
            terminal["db-after-restore"] = restore
        for kind, pattern in (("setup-sql", "*-setup.sql"), ("restore-sql", "*-restore.sql")):
            found = sorted(batch_dir.glob(pattern))
            if found:
                terminal[kind] = found[0]
    if idents:
        direct = free_name(batch_dir, "fedora-direct")
        save_json(direct, direct_reads(reader, idents))
        effects["fedora_direct"] = direct.name
        terminal["fedora-direct"] = direct
    effects_path = free_name(batch_dir, "effects-check")
    save_json(effects_path, effects)
    terminal["effects"] = effects_path
    recorded = []
    validation_state = "checked" if final.is_file() else state
    for phase, files, phase_state in (("validation", evidence, validation_state), ("terminal", terminal, state)):
        retained = retain(root, batch_id, {k: str(v) for k, v in files.items()})
        event = record_checkpoint(root, batch_id, task_id, retained, phase_state, phase)
        recorded.append({"phase": phase, "state": event["state"]})
    return {"effects": effects, "checkpoints": recorded}


def operator_observation(root):
    """
    Vrátí odkaz na pozorování operátora za celý běh, pokud je platné (autor člověk, čas, neprázdné záznamy).

    :param root: Adresář běhu.
    :return: Odkaz ``{"path", "sha256"}`` nebo ``None``.
    """
    path = root / OBSERVATIONS
    if not path.is_file():
        return None
    observed = read_json(path)
    if observed.get("author") != "human" or not observed.get("observed_at") or not observed.get("observations"):
        return None
    return {"path": OBSERVATIONS, "sha256": digest(path.read_bytes())}


def assess(root):
    """
    Odvodí hodnocení pokrytí z terminálních kontrolních bodů a kontrol orákula provedených dávek.

    Každé pokrytí provedené dávky dostane terminální stav dávky a všechny její kontroly jako tvrzení; selhaná dávka
    je ``failed``, dávka se všemi kontrolami prošlými ``passed``, jinak ``blocked``. Pokrytí ve více dávkách
    (životní cykly) nese hodnocení všech fází. Pozorování operátora za běh se připojí jako ``human-ux``.

    :param root: Adresář běhu.
    :return: Slovník ``ID pokrytí -> hodnocení`` pro ``report``.
    """
    from .session import current_manifest, effective_checkpoints

    run = read_json(root / "run.json")
    manifest = current_manifest(root)
    terminal = {}
    for event in effective_checkpoints(root):
        if event.get("phase") == "terminal" and event["state"] in ("checked", "failed"):
            terminal[event["batch_id"]] = event
    observation = operator_observation(root)

    def one(batch_id):
        event = terminal[batch_id]
        reference = event["evidence"].get("verify-batch")
        checks = (
            [{"id": c["id"], "state": c["state"]} for c in read_json(inside(root, reference["path"]))]
            if reference
            else []
        )
        if event["state"] == "failed":
            state = "failed"
        else:
            state = "passed" if checks and all(c["state"] == "passed" for c in checks) else "blocked"
        evidence = {k: v for k, v in event["evidence"].items() if k != "human-ux"}
        if observation:
            evidence["human-ux"] = observation
        return {
            "run_id": run["run_id"],
            "deployment": run["deployment"],
            "batch_id": batch_id,
            "task_id": event["task_id"],
            "state": state,
            "evidence": evidence,
            "assertions": checks,
        }

    results = {}
    for item in manifest.get("coverage", []):
        holders = [
            b["id"] for b in manifest["batches"] if item["id"] in b.get("coverage_ids", []) and b["id"] in terminal
        ]
        if not holders:
            continue
        phases = [one(b) for b in holders]
        primary = (
            next((p for p in phases if p["state"] == "failed"), None)
            or next((p for p in phases if p["state"] == "blocked"), None)
            or phases[-1]
        )
        result = dict(primary)
        if len(holders) > 1:
            result["phase_assessments"] = [
                {"batch_id": p["batch_id"], "task_id": p["task_id"], "state": p["state"]} for p in phases
            ]
        results[item["id"]] = result
    return results
