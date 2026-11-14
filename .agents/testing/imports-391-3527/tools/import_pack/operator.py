"""Přesné lidské kroky, uchování důkazů a přenosný export balíčku."""

import html
from pathlib import Path

from .common import PACK, digest, inside, json_bytes, read_json, save_json, write_new


def render(directory, run_root):
    """Vygeneruje jednu kartu na dávku s již vyřešenými lokálními cestami."""
    manifest = read_json(directory / "manifest.json")
    if (run_root / "run.json").is_file():
        from .session import register_inputs

        register_inputs(run_root, manifest)
    revision = digest(json_bytes(manifest))[:12] + "-" + digest(str(run_root.resolve()).encode())[:8]
    instruction_root = inside(run_root, "instructions/" + revision)
    labels = read_json(PACK / "operator/terminology.json")["labels"]
    index = []
    deferred = []
    for batch in manifest["batches"]:
        if batch.get("deferred"):
            # No card: a known defect would abort it. The input stays in the prepared pack for a rerun after the fix.
            deferred.append(
                {
                    "batch": batch["id"],
                    "defects": batch["deferred"]["defects"],
                    "prerequisite": batch["deferred"]["prerequisite"],
                    "coverage_ids": batch["coverage_ids"],
                }
            )
            continue
        input_path = (directory / batch["input"]).resolve()
        if digest(input_path.read_bytes()) != batch["input_sha256"]:
            raise ValueError("Input changed after manifest creation")
        evidence_root = inside(run_root, batch["id"])
        input_root = inside(evidence_root, "input/" + batch["input_sha256"])
        save_json(inside(input_root, "input-manifest.json"), batch)
        write_new(inside(input_root, input_path.name), input_path.read_bytes())
        input_path = inside(input_root, input_path.name)
        blocked = batch["unresolved"] or batch.get("execution_gate")
        text = f"""# {batch['id']} — human instruction card

Suite: **{manifest['suite']}**. This card does not authorize a live import.

Input: `{input_path}`

SHA-256: `{batch['input_sha256']}`

Selected **{labels['operation']['cs']}**: **{labels[batch['operation']]['cs']}**.

Expected outcome: **{batch['expected']}**. Rows: {batch['rows']}.

Prerequisites: {', '.join(batch['prerequisites']) or 'verified preflight and authorized session'}.

Execution gate: **{'BLOCKED — resolve references/keys/controlled setup first' if blocked else 'agent must verify deployment, baseline, prerequisites and session authorization first'}**.

Unresolved values: {', '.join(batch['unresolved']) or 'none'}.

1. **Agent:** verify input hash and prerequisites, stage only this run's binary folder
   through an authorized non-browser route if available, capture DB/Fedora baseline,
   then confirm that this specific card is ready within the already approved session.
2. **Human:** open https://amcr-test.aiscr.cz/admin/import-data/ using the intended
   operator account. Select the operation above and choose the exact ZIP path above.
   Submit using **Uložit** (**Save**, Django admin PO msgid `Save`; verified in
   Django 6.0.8). Confirm the deployed translation at preflight. This step
   validates; it is distinct from **{labels['start']['cs']}**.
3. **Human:** report the observed validation state. Capture `ui-validation.png` where
   this card tests UX or an unexpected message appears. Download the validation XLSX
   using **{labels['download']['cs']}** and retain it at
   `{evidence_root / 'validation-report.xlsx'}`.
4. **Agent:** compare the validation report and unchanged domain baseline. For an
   expected rejection, do not start import; confirm the intended class/row/field error.
   For a positive case, verify all rows and ask the human to continue at this checkpoint.
5. **Human:** only after that checkpoint, click **{labels['start']['cs']}** for a positive
   import. Observe phase/progress and whether the controls reflect the current state.
   Wait for a terminal state; a full progress bar alone does not establish completion.
   If the agreed window/stall/resource stop condition is reached, retain the current
   screen/task ID and contact the agent; do not reset or resubmit on your own.
   Perform stop/cancel/reset only when the selected scenario explicitly calls for it.
6. **Human:** retain `ui-final.png` for required UX observations or any failure; use
   **{labels['download']['cs']}** to save `{evidence_root / 'final-report.xlsx'}`.
   If the current task is no longer open, use
   https://amcr-test.aiscr.cz/admin/import-data-reports/ (**{labels['reports']['cs']}**)
   and choose the matching task ID. Record task ID, exact observed messages, start/end
   times and any responsiveness problem. Do not transcribe all result rows.
7. **Agent:** fetch safe direct API evidence and run the read-only SQL checks where
   authorized. Otherwise provide the human the exact query/export command and target
   file. Inspect the XLSX and supplied screenshots, perform machine comparisons, retain
   originals and record the next checkpoint. Do not repeat the mutation after an error.

## Keep and hand back

Keep this input manifest, both XLSX stages, required screenshots/observations, SQL
exports, direct Fedora responses/hashes and verification results. A server path shown
beside **{labels['saved']['cs']}** is a container path, not a workstation download.

Place downloads in `{evidence_root}` and tell the agent:

> Suite {manifest['suite']}; batch {batch['id']}; task ID [copy from report/page];
> evidence is in `{evidence_root}`. Check it and identify the next step.

On another machine, attach these specifically listed files or copy the run folder into
an opened agent workspace and provide its new absolute path. Keep evidence after all
tests and after synthetic data cleanup until an explicit retention decision.
"""
        if batch.get("execution_kind") == "controlled-procedure":
            text = f"""# {batch['id']} — controlled management procedure

This is a separately authorized service-owner/agent procedure. No CSV upload or
browser import action belongs to this card.

Exact retained plan: `{input_path}`

SHA-256: `{batch['input_sha256']}`

Prerequisites: {', '.join(batch['prerequisites'])}. Execution remains BLOCKED until
the isolated fixture/scan scope, exact setup, access and restoration are authorized.
Read the complete plan above, including the command's lack of a file-ID filter.
The preceding ordinary file replacement must establish at least two thumbnail versions.

The authorized agent/service owner retains the dry-run output, first apply output,
second apply output, before/after DB snapshots and direct thumbnail version evidence
under `{evidence_root}` as `dry-run.txt`, `apply-1.txt`, `apply-2.txt`,
`db-before.json`, `db-after-1.json`, `db-after-2.json`, `fedora-before.json` and
`fedora-after.json`. These command outputs are this procedure's report evidence;
there is no import XLSX. The human supplies actual operator observations, or records
which UI interactions were unobserved. The agent compares exact actors, notes,
timestamps, versions and second-run idempotence, records a terminal checkpoint and
provides a handoff. Keep the complete evidence after restoration and cleanup.
"""
        if batch.get("controlled_setup"):
            text += (
                "\n## Controlled setup / unresolved acceptance\n\n"
                + "\n".join("- " + x for x in batch["controlled_setup"])
                + "\n"
            )
        if batch.get("case_details"):
            text += "\n## Cases and required observations\n\n"
            for case in batch["case_details"]:
                text += (
                    "- `"
                    + case["id"]
                    + "`: "
                    + (
                        " ".join(case["notes"])
                        or "Agent checks exact rows, target graph, history, metadata and untouched controls."
                    )
                    + "\n"
                )
        path = inside(instruction_root, batch["id"] + ".md")
        write_new(path, text.encode("utf-8"))
        index.append({"batch": batch["id"], "input": str(input_path), "instruction": str(path), "gate": bool(blocked)})
    save_json(inside(instruction_root, "index.json"), index)
    save_json(inside(instruction_root, "deferred.json"), deferred)
    body = "<!doctype html><meta charset=utf-8><title>Import test instructions</title><h1>Human-operated import instructions</h1><ol>"
    for item in index:
        body += (
            '<li><a href="'
            + html.escape(Path(item["instruction"]).as_uri(), quote=True)
            + '">'
            + html.escape(item["batch"])
            + "</a>"
            + (" — blocked inputs/setup" if item["gate"] else " — preflight required")
            + "</li>"
        )
    body += "</ol>"
    if deferred:
        body += "<h2>Deferred until a known importer defect is fixed (no card)</h2><ul>"
        for item in deferred:
            body += "<li>" + html.escape(item["batch"]) + " — " + html.escape(", ".join(item["defects"])) + "</li>"
        body += "</ul>"
    write_new(inside(instruction_root, "index.html"), body.encode())
    save_json(
        inside(run_root, "operator-observations.template.json"),
        {
            "author": None,
            "observed_at": None,
            "task_id": None,
            "observations": [],
            "screenshot_paths": [],
            "unobserved": [],
            "note": "Agent records actual human feedback/supplied images with provenance; this blank template is not evidence",
        },
    )
    return index


def export_pack(directory, output):
    """Exportuje explicitně vybranou sadu, kód a návody; nikdy složku runs."""
    import io
    import zipfile

    selected = {}
    for folder in ("tools", "operator", "definitions", "tests"):
        for path in (PACK / folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                selected[path.relative_to(PACK).as_posix()] = path
    for name in ("START-HERE.md", "README.md", "requirements.txt"):
        selected[name] = PACK / name
    datasets = directory if isinstance(directory, dict) else {"": directory}
    for label, dataset in datasets.items():
        if label not in ("", "behaviour", "load-relational", "load-distributions"):
            raise ValueError("Unknown export suite label")
        if not dataset.resolve().is_relative_to((PACK / "generated").resolve()):
            raise ValueError("Export only selected generated datasets, not arbitrary directories or evidence")
        manifest = read_json(dataset / "manifest.json")
        if label and label != ("behaviour" if manifest["suite"] == "behaviour" else "load-" + manifest["workload"]):
            raise ValueError("Export suite label and dataset disagree")
        for path in dataset.rglob("*"):
            if path.is_file():
                relative = path.relative_to(dataset)
                if "binaries" in relative.parts and (dataset / "binary-sources.zip").is_file():
                    continue  # the verified flat source archive already contains these bytes
                if path.name == "run.json" or {"events", "originals", "input-revisions", "runs"}.intersection(
                    relative.parts
                ):
                    raise ValueError("Run evidence cannot be included in a prepared-data export")
                selected["prepared/" + (label + "/" if label else "") + relative.as_posix()] = path
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(selected.items()):
            if path.is_symlink() or not path.resolve().is_relative_to(PACK.resolve()):
                raise ValueError("Export cannot follow a symlink or leave the pack")
            data = path.read_bytes()
            if path.suffix == ".json":
                import json

                def secret(value):
                    if isinstance(value, dict):
                        return any(
                            (
                                key.lower() in ("password", "authorization", "access_token", "api_key")
                                and isinstance(item, str)
                                and bool(item)
                            )
                            or secret(item)
                            for key, item in value.items()
                        )
                    return isinstance(value, list) and any(secret(item) for item in value)

                if secret(json.loads(data)):
                    raise ValueError("Secret-bearing content cannot be exported")
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    write_new(output, stream.getvalue())
    return {"path": str(output.resolve()), "sha256": digest(stream.getvalue()), "files": len(selected)}
