"""Human checkpoints and phase-specific recovery; no infrastructure execution."""

from .catalog import SESSION_CASES

DETAILS = {
    "validation-no-domain-mutation": (
        "validation",
        "Upload the positive ZIP; do not click Zahájit import.",
        "All scoped domain/history/Fedora bytes unchanged; validation report accounts for every input.",
    ),
    "approval-cancel": (
        "awaiting approval",
        "After successful validation click Zrušit import; reopen the page.",
        "No domain/history/Fedora mutation; lock released; persisted report still retrievable.",
    ),
    "maintenance-required": (
        "before upload",
        "Service owner sets the approved maintenance state; try upload in each state.",
        "Required maintenance gate enforced before mutation; clear actionable explanation.",
    ),
    "superadmin-only": (
        "before upload",
        "Human uses a separately identified non-superadmin and then the approved operator account.",
        "Restricted controls/data unavailable to non-superadmin; no import starts.",
    ),
    "concurrent-admin": (
        "validation/approval",
        "Human opens a second separately identified admin session while the first owns the task.",
        "One owner; second attempt explains conflict; cannot stop/reset another owner's active job.",
    ),
    "reload-ui": (
        "running",
        "Reload/reopen the import page once and provide the resulting screenshot.",
        "Same task and ownership; progress resumes; no duplicate submission.",
    ),
    "polling-outage": (
        "running",
        "Human temporarily disconnects only their client connection, then restores it and reloads.",
        "Visible connection/stale-state handling; task reconciles to actual server state without replay.",
    ),
    "missing-binary-after-validation": (
        "after validation",
        "Authorized service owner moves only the named run-owned source file aside after validation; human starts import.",
        "Binary-phase failure attributed to this filename; prior DB/history/metadata commits reconciled; source restored for a remaining-only recovery.",
    ),
    "report-screen-agreement": (
        "terminal",
        "Human downloads the final report and captures the terminal screen and task ID.",
        "Terminal phase/errors/counters agree with XLSX and actual DB/Fedora evidence.",
    ),
    "thumbnail-backfill": (
        "terminal",
        "Human opens permitted file download/thumbnail routes; authorized owner invokes the approved backfill twice in its own scope.",
        "Missing thumbnails restored; second backfill idempotent; thumbnail history and permissions checked.",
    ),
}


def scenarios():
    result = []
    for name in SESSION_CASES:
        privileged = name not in DETAILS or name in (
            "maintenance-required",
            "missing-binary-after-validation",
            "thumbnail-backfill",
        )
        if name.startswith("stop-"):
            phase = name[5:]
            human = f"Wait until the agent confirms phase {phase}, then click Zastavit úlohu exactly once. Retain the terminal screen and final report."
            expected = "Reconcile per-row DB/history/Fedora state at this phase boundary. Data rollback and later-phase partial commits are distinct; stopped must not be displayed as successful completion."
            privileged = False
        elif name in DETAILS:
            phase, human, expected = DETAILS[name]
        else:
            phase = {"lock-loss": "lock ownership", "partial-record-groups": "between parent groups"}.get(
                name, name.replace("-failure", "")
            )
            human = "Perform upload/start only after the service owner and agent record the exact approved injection method, target, trigger and restoration command; preserve the failure screen/report."
            expected = "A failure before a transaction commits rolls that transaction back; earlier committed DB/history/metadata or parent groups remain distinguishable. Reconcile every row/resource; do not replay the original ZIP."
        result.append(
            {
                "id": "session." + name,
                "phase": phase,
                "state": "prepared",
                "fixture": "fresh isolated namespace built from the positive graph; never interrupt the shared baseline or a successful load measurement",
                "gate": (
                    "BLOCKED until target-specific method/restore authorization is recorded"
                    if privileged
                    else "authorized behaviour session and captured phase baseline"
                ),
                "agent_before": [
                    "Allocate fresh namespace and generate exact-path card",
                    "Capture scoped DB/history, direct Fedora bytes/versions and source-file hashes",
                    "Record actor, task ID and phase trigger; confirm the fault can be observed in this bounded graph",
                ],
                "human": human,
                "expected": expected,
                "agent_after": [
                    "Retain original XLSX, human observation and supplied screenshot; label unseen controls unobserved",
                    "Compare every row and direct resource; classify committed/rolled-back/unprocessed/unknown",
                    "If unknown exists, block recovery; otherwise prepare only eligible operations in a new input with new checksum",
                ],
                "retention": "Keep all evidence after restoration and cleanup; never infer a pass from a simulation.",
            }
        )
    return result
