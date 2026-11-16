# Usage: anonymizace PR review round 2 aiscr-webamcr

- **When:** 2026-11-16
- **Agent / runtime:** Claude Code (VS Code extension)
- **Model / backend:** `claude-opus-5-5`
- **What:** Addressed the second review round on [ARUP-CAS/aiscr-webamcr#4518](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4518).
  - F4: `handle()` now holds the RÚIAN sync advisory lock from the pre-flight check through all sections, so the protected-PIAN rows and district predicates cached by the pre-flight check cannot go stale before the geometry section uses them. The geometry section re-acquires the same session-level lock.
  - F5: read-only queries on `prod` and `aiscrrestore` found no accessibility vocabulary entry with NULL `razeni` and no record pointing to one. As a safeguard, the pre-flight check now stops the run when such an entry exists.
- **Impacted:** `webclient/core/management/commands/anonymizace_dat.py`, `webclient/core/tests/test_anonymizace.py`, and this usage entry.
- **Subagents used:** None.
- **MCP servers used:** None.
- **Workflow context used:** PR review comments read via `gh`.
- **Verification:** `manage.py test core.tests.test_anonymizace` passed (96 tests) against the local test DB. The run includes new regressions for holding the lock across pre-flight and sections, failing before pre-flight when a sync holds the lock, and blocking on an accessibility entry without `razeni`.
- **Close-out:** Not committed or pushed, and no replies posted to the review threads.
