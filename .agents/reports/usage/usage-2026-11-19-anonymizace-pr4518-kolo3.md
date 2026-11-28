# Usage: anonymizace PR review round 3 aiscr-webamcr

- **When:** 2026-11-19
- **Agent / runtime:** Claude Code (VS Code extension)
- **Model / backend:** `claude-opus-5-5`
- **What:** Addressed the third review round on [ARUP-CAS/aiscr-webamcr#4518](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4518).
  - F6: the check for accessibility entries without `razeni` now runs whenever `texty` or `geometrie` is selected. The geometry part of the pre-flight check moved into `_problemy_geometrie`.
  - F7: a new regression runs the real geometry section while the RÚIAN lock is already held.
  - F8: the deployment doc now says that `anonymizace_dat` holds the RÚIAN lock for its whole run and that a skipped daily sync catches up from its anchor. The `lock_not_acquired` message in `cron/tasks.py` now names the holder generically.
- **Impacted:** `webclient/core/management/commands/anonymizace_dat.py`, `webclient/core/tests/test_anonymizace.py`, `webclient/cron/tasks.py`, `docs/source/02_instalace_nasazeni/ruian_sync_nasazeni.rst`, and this usage entry.
- **Subagents used:** None.
- **MCP servers used:** None.
- **Workflow context used:** PR review comments read via `gh`.
- **Verification:**
  - `core.tests.test_anonymizace` passed (98 tests), together with `heslar.tests.test_ruian_sync.SerializaceBehuTests` (101 in total).
  - The full `heslar.tests.test_ruian_sync` has 2 failures and 6 errors both with and without this change (stash comparison). They come from deleting cadastres in the full-copy test DB.
- **Close-out:** Not committed or pushed, and no replies posted to the review threads.
