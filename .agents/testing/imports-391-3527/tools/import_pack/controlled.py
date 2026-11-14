"""Exact isolated-state recipes; these are plans, never executable tool actions."""

from .datasets import ident
from .sql import quote


def recipe(case, ns, refs, bindings=None):
    name, variant, index = case["class"], case["variant"], case["index"]
    result = {
        "case_id": case["id"],
        "execute": False,
        "state": "blocked",
        "setup_authorization": "Record environment, exact targets, method, retained baseline and restoration method before setup",
        "input_index": index,
        "expected": case["outcome"],
        "evidence": [
            "full isolated row backup",
            "setup authorization",
            "read-only setup proof",
            "input/report/UI",
            "DB/Fedora comparison",
            "restoration proof",
        ],
        "notes": case["notes"],
    }
    if variant in ("missing-companion", "missing-extra-data"):
        root = "dokument" if name == "dokumenty" else "archeologicky_zaznam"
        companion = "dokument_extra_data" if root == "dokument" else "akce" if name == "az_akce" else "lokalita"
        foreign = root
        identity = ident(name, ns, index, refs)
        predicate = f"{foreign}=(SELECT id FROM {root} WHERE ident_cely={quote(identity)})"
        result.update(
            readonly_backup_sql=f"BEGIN TRANSACTION READ ONLY; SELECT to_jsonb(c) FROM {companion} c WHERE {predicate}; COMMIT;",
            proposed_setup=f"After authorization only: remove the single retained {companion} row selected by {predicate}. Do not remove the root.",
            readonly_proof_sql=f"BEGIN TRANSACTION READ ONLY; SELECT (SELECT count(*) FROM {root} WHERE ident_cely={quote(identity)}) AS roots,(SELECT count(*) FROM {companion} WHERE {predicate}) AS companions; COMMIT;",
            setup_assertion={"roots": 1, "companions": 0},
            restoration="Before setup, service owner prepares explicit column/PK restoration from the retained complete JSON row against the captured schema. Verify it is usable on an isolated clone. Block setup until that restoration is reviewable.",
        )
    elif variant.startswith("cadastral-"):
        result.update(
            readonly_selection_sql="BEGIN TRANSACTION READ ONLY; SELECT id,kod,pian_id FROM ruian_katastr WHERE pian_id IS NULL ORDER BY kod LIMIT 20; COMMIT;",
            setup="Select a verified missing/existing cadastral spatial-unit reference and set this isolated Fieldwork event's main cadastre. If no missing reference exists, use an isolated fixture copy and detach only its retained pian_id link under approved restoration; never delete a shared spatial unit to manufacture the state.",
            assertions=[
                "Reuse the exact existing spatial-unit ID, or create exactly one new ID and attach it to the cadastre and documentation unit",
                "No unrelated cadastre changes; geometry/SRIDs/history/metadata complete",
                "Capture the derived ID even though it was not a CSV identifier; reconcile it separately for cleanup",
            ],
        )
    elif variant in ("thumb-backfill", "backfill-idempotence"):
        result.update(
            required_environment="Isolated application/DB/Fedora fixture copy, or separate explicit approval covering every file scanned on the shared test instance",
            source="webclient/core/management/commands/backfill_thumb_history.py",
            command_preview="python manage.py backfill_thumb_history --dry-run",
            commands_after_approval=[
                "python manage.py backfill_thumb_history",
                "python manage.py backfill_thumb_history",
            ],
            scope_warning="There is no file-ID filter. --limit selects the first numeric PKs, not the run's files; it cannot be used as run-owned scoping.",
            setup="In the isolated fixture only, retain complete history and version lists, then remove the selected files' thumbnail DIST history (and separately test absent history links). Preserve the thumbnail binaries and versions.",
            assertions=[
                "One DIST01 for the oldest version and DIST11 for each later version per thumb/thumb-large",
                "Actor is verified ADMIN_USER, timestamps equal corresponding Fedora version timestamps",
                "Second run adds zero rows; DB metadata/XML and binaries remain unchanged",
                "Missing history link created only for the selected isolated files",
            ],
        )
    elif variant in ("missing-file-uuid", "missing-file-owner"):
        import re

        value = (bindings or {}).get(f"file:{index}.id")
        match = re.fullmatch(r"soub-(\d+)", str(value)) if value else None
        predicate = "id=" + match.group(1) if match else "id=:VERIFIED_NUMERIC_FILE_KEY"
        result.update(
            binding=f"file:{index}.id",
            readonly_backup_sql=f"BEGIN TRANSACTION READ ONLY; SELECT to_jsonb(s) FROM soubor s WHERE {predicate}; COMMIT;",
            setup=(
                "After retaining the complete row and owner links: clear only this run-owned file's path to model a missing UUID"
                if variant == "missing-file-uuid"
                else "After retaining the complete row and owner links: detach only its run-owned document's soubory link; preserve the file/container and binary"
            ),
            restoration="Restore the exact captured path/owner link through the pre-approved method; compare all unrelated columns and direct bytes/versions with the retained baseline",
            assertion="Clean intended validation rejection; import performs no DB/history/Fedora writes. Restore the controlled fixture after evidence collection.",
        )
    elif variant == "active-user-delete":
        result.update(
            setup="Use an approved disposable active operator account; record its current logged-in identity as current_operator_ident. The human performs the attempted DELETE while owning the task.",
            assertions=[
                "Clean current-user rejection; account, login and ownership remain usable",
                "No user/history/metadata or unrelated record changes",
            ],
            restoration="Retain the disposable account snapshot and owner access recovery plan. Do not use a shared administrator account.",
        )
    else:
        result.update(
            setup="Resolve the stated acceptance question and retain the two isolated endpoint identities before running this prepared input.",
            assertions=[
                "No dangling relationship, unexpected cycle propagation or changes to unrelated controls",
                "Outcome agrees with the recorded policy; observations alone do not define acceptance",
            ],
        )
    return result
